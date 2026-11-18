# Javo Agents on Northflank

Deploy the runtime and dashboard together as **one service**, using the root
`Dockerfile`. The cloud entrypoint adds a browser login, mounts the runtime at
`/api`, and serves the dashboard at `/`. The Windows/Android apps and the normal
local runtime entrypoint are unchanged.

## Free hosting boundary

Use **Northflank Cloud -> Developer Sandbox**, not Bring Your Own Cloud (BYOC)
or Pay As You Go. Northflank advertises a free allowance and always-on services:
<https://northflank.com/pricing>. Its billing documentation separately says card
verification can be required, so confirm the actual onboarding requirements in
your account: <https://northflank.com/docs/v1/application/billing/pricing-on-northflank>.

Start with **one instance**, the smallest available Sandbox compute allocation,
and a small persistent volume mounted at `/data`. Confirm that **compute,
storage, builds and network usage all fit the free allowance** before creating
resources. Do not upgrade the plan or add a paid disk to complete this guide.
If the free plan does not offer persistent storage, stop: this runtime's SQLite
database and scheduler need durable storage for real use. An ephemeral preview
would lose goals, schedules and content when the container is replaced.

The free plan is intended for hobby/testing use, not production. This image
does not run Ollama or download model weights. Model API calls, connected social
accounts and external services are separate from free application hosting.

## 1. Build source

- Repository: `NavigatorJagdish/javo-agents`
- Select the reviewed branch/commit containing this guide and the Dockerfile.
- Build type: Dockerfile
- Build context: repository root (`/`)
- Dockerfile path: `/Dockerfile`
- Start command: leave the image default (`python -m app.cloud`).

The multi-stage build compiles the dashboard, installs the Python runtime and
FFmpeg, and runs as UID/GID `10001:10001`. Do not use the desktop Electron app
as the service's entrypoint.

## 2. Secrets

Set these as **runtime secrets**, never build arguments, source files, GitHub
commits, or frontend `VITE_*` variables:

| Variable | Purpose |
| --- | --- |
| `JAVO_CLOUD_USERNAME` | Browser login name; no colon characters |
| `JAVO_CLOUD_PASSWORD` | Unique login password, at least 20 characters |
| `JAVO_SECRET_KEY` | Independent random secret, at least 32 characters |
| `JAVO_ENCRYPTION_KEY` | Independent random secret, at least 32 characters |

Generate each secret independently with a password manager. Keep the signing
and encryption keys stable when redeploying; changing the encryption key makes
previously encrypted data unreadable. The image refuses to start if a required
secret is missing or too short. The browser will ask for the cloud username and
password when you open the HTTPS service URL.

The image defaults to one concurrent agent and zero AI spending budgets. Keep
those defaults for the initial hosting test. A reachable AI provider must be
configured separately before tasks requiring model inference can work; the
container's `localhost` is not your Windows PC. Do not expose a local Ollama
server publicly to connect it. No provider API request is needed for the smoke
test below.

## 3. Storage and networking

- Attach durable storage at **`/data`**, accessible to UID/GID `10001:10001`.
- Use **one replica and one Uvicorn worker**. SQLite and the scheduler are not
  configured for horizontally scaled replicas.
- Expose container port **8000** as an HTTP service with Northflank HTTPS.
- Configure readiness/liveness as **HTTP GET `/healthz`** on port 8000.
- Optional `PORT` overrides the listener; otherwise `JAVO_PORT` defaults to 8000.
- Database, scheduler, content, uploads, thumbnails and backups default to `/data`.

The container trusts forwarded headers from Northflank's reverse proxy so API
redirects retain HTTPS. Expose it through that managed HTTPS ingress, not directly
to the internet. For another host, restrict `FORWARDED_ALLOW_IPS` to its trusted
proxy addresses.

Only `/healthz` is public and returns a minimal database readiness status.
The dashboard, API documentation, runtime endpoints and WebSockets require the
same cloud login. Anonymous Telegram webhooks and OAuth callbacks are not
enabled by this deployment; configure those integrations separately rather than
removing the login gate.

Northflank volume guidance:
<https://northflank.com/docs/v1/application/databases-and-persistence/add-a-volume>

## 4. Verify the deployment

1. Wait for a successful build and a passing `/healthz` probe.
2. Open the HTTPS URL. Confirm a login is required before the dashboard appears.
3. Open `/api/docs` after logging in and call `GET /agents/`. The fresh database
   should contain 30 definitions (MasterAgent plus 29 specialists).
4. Create a harmless task through `POST /tasks/`, restart the container, and
   confirm `GET /tasks/` still contains it. This checks the actual volume mount.
5. Inspect memory usage and logs before adding an AI provider or real workloads.

Important existing application limitations: some dashboard panels use sample
data and some actions fall back to simulated results. The current agent `run`
endpoint creates a queued execution record; hosting it alone does not implement
an execution dispatcher. A successful build, green probe or dashboard screen is
**not** proof that an autonomous task or social publication completed. Verify
real results before enabling external actions.

## Local container check

With the four secrets set in your shell environment:

```sh
docker build -t javo-agents:cloud .
docker volume create javo-cloud-data
docker run --rm -p 127.0.0.1:8000:8000 \
  --mount source=javo-cloud-data,target=/data \
  -e JAVO_CLOUD_USERNAME -e JAVO_CLOUD_PASSWORD \
  -e JAVO_SECRET_KEY -e JAVO_ENCRYPTION_KEY \
  javo-agents:cloud
```

The named volume survives container removal. Back it up before changing storage.
