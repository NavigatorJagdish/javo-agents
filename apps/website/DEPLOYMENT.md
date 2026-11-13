# Javo Agents Website — Deployment & DNS Recovery

The site source is **already present** in `apps/website/` and uses Next.js 15 with `output: 'export'` and `trailingSlash: true`. However, **writing `https://javoagents.org` in the source or GitHub README does not register a domain, configure DNS, or deploy the website**.

## Fastest deployment (Vercel)

1. Use the official [Vercel New Project](https://vercel.com/new) flow. Connect the existing **private** GitHub repository `NavigatorJagdish/javo-agents`. Keep the repository private; the website can be public.
2. Under **Root Directory**, select **`apps/website`** (important; the repository root is not a Next.js project). Framework preset: **Next.js**.
3. Use the existing package manager lockfile in that directory: **pnpm**. Build command: **`pnpm build`**; the existing `next.config.mjs` creates a static `out/` directory. Leave Next.js defaults unless Vercel requests the static output directory.
4. Click **Deploy**. Wait for the deployment to finish, then **open the actual `*.vercel.app` URL from the Vercel dashboard**. Do not substitute an invented URL. If build fails, inspect the **Build Logs** and repair the source or dependency issue first.
5. In **Project → Settings → Domains**, add **`javoagents.org`** and optionally **`www.javoagents.org`**. Domain ownership is required; if the domain has not been registered, purchase it from your chosen registrar first.
6. Read the **exact DNS A/CNAME/TXT values displayed for your Vercel project**. In the DNS provider where this domain is managed, apply those values, including any ownership verification records. Remove conflicting obsolete records. Do not replace MX records for working email.
7. In Vercel Domains, wait for **Valid Configuration / Verified** and HTTPS certificate ready. Then check `https://javoagents.org/`, `/features/`, `/download/`, `/sitemap.xml`, and `/robots.txt` with a real browser.
8. Once both the Vercel deployment and custom domain are verified, update the GitHub repository Homepage field, README website button, `apps/website/src/data/site.ts`, and release/source links **with the verified live URL**. Do not mark the domain live sooner.

### If you only need a preview first

You can use the generated Vercel deployment URL without owning `javoagents.org`; the custom domain is an **optional** later step. The actual Vercel URL must come from your account after deploy.

### Current known limitations

- GitHub repo `homepage` metadata is empty.
- `apps/website/src/data/site.ts` contains the **configured/intended** `https://javoagents.org` domain.
- The existing GitHub workflows focus on Windows/Android/Backend/Frontend; a website-specific build check was added separately to prevent untested web changes.
- No authenticated Vercel project, verified domain DNS, production deployment URL, or registrar access has been available through this GitHub connection. The static site cannot be made live merely by committing a README link.
- If your domain is owned by another registrar, DNS records must be changed in that registrar/DNS provider, not in GitHub.
- Keep actual social OAuth tokens, API secrets and backend credentials **out of the static site**. A static export cannot safely host confidential server endpoints.

### Local build / smoke test

```bash
cd apps/website
corepack enable
pnpm install --frozen-lockfile
pnpm run typecheck
pnpm run build
test -f out/index.html
```

### How to diagnose "Site can't be reached"

| Browser symptom | Likely class of failure | Check |
|---|---|---|
| `DNS_PROBE_FINISHED_NXDOMAIN` | Domain name does not resolve | Domain registration, nameservers, DNS A/CNAME |
| `ERR_NAME_NOT_RESOLVED` | DNS unavailable/misconfigured | Registrar/DNS provider and DNS propagation |
| `ERR_CONNECTION_REFUSED` | Site not serving traffic | Vercel deployment/domain target and ports |
| `ERR_SSL_PROTOCOL_ERROR` | Certificate mismatch/pending | HTTPS verification and DNS records |
| Vercel `404 DEPLOYMENT_NOT_FOUND` | No deployment mapped to hostname | Vercel project and domain mapping |
| Works on `vercel.app` but not custom domain | Domain DNS/mapping fault | Vercel Domains diagnostics |

Use the Vercel dashboard as the source of truth for the exact A/CNAME targets; do not invent them. For additional background: [Vercel: set up a custom domain](https://vercel.com/docs/domains/set-up-custom-domain), [troubleshooting](https://vercel.com/docs/domains/troubleshooting).

**Definition of done:** an actual public HTTPS URL responds with the site's generated HTML, interior routes work, sitemap and robots return successfully, and the GitHub website button links to the verified public URL. CI green **alone does not satisfy this**.
