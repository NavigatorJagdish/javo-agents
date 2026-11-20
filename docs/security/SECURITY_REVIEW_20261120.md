# Defensive review — 20 November 2026

Scope: current local FastAPI/React/Electron source, skill execution, optional
speech workers, reviewed integration bridge, media submission and dependencies.
No production user telemetry or external user-session evidence was available.
This is a development review, not an independent penetration test or guarantee
that every vulnerability has been found.

## Fixed findings

| Priority | Finding and repair | Evidence |
| --- | --- | --- |
| High | AST checks allowed indirect access to Python function globals/builtins. Runner now permits only the two source-pinned original built-ins in their trusted directories; modified/downloaded Python is refused | Regression vectors cover indirect dynamic access and forged core trust;16 sandbox/core tests passed. Arbitrary Python needs real OS isolation |
| High | Request parsing could happen before owner authentication. New early boundary authenticates before body/multipart parsing, spools bounded data and checks declared/actual size | Actual API checks for unauthorized, oversize and private headers; scoped MCP retains its separate grant validation |
| Medium | Windows venv wrapper termination could leave the speech interpreter/descendants alive with pipes open | Full owned process-tree cancellation on Windows, process groups on POSIX; regression spawns actual descendants and verifies cleanup |
| Medium | External proposals needed source isolation and protection against stale/repeated approval | Separate hashed, expiring, revocable scopes; graph revision/fingerprint and expiry rechecked; atomic decision/enqueue; same-grant result access only |
| Medium | Model/media/network inputs could otherwise introduce unbounded or unsafe content | Loopback-only generation endpoints, fixed native graphs, strict review/seed/input types, bounded output/XML, no redirects/proxies/compressed responses, safe artifact refs and hash-verified downloads |
| Medium | Uncertain model submission could be replayed or cancellation misreported | Durable intent and provider IDs, idempotency, no blind retry/global interrupt; owner abandon decisions retained |
| Medium | Old pip/setuptools had known advisories | Local environment upgraded topip26.3/setuptools84.2.1; final pip-audit reported no known vulnerabilities |

Additional hardening: TrustedHost allowlist, no-store/nosniff/frame/referrer
headers, build-time CSP, streamed bounded content uploads and worker environment
scrubbing. Intentional Electron file-origin support was preserved. Browser checks
exercise actual production assets; audio/transcript fixtures are labelled and
do not stand in for real model acceptance.

## Dependency advisory recheck and correction

The initial dashboard audit reported11 high build-tool entries associated with
[GHSA-fc5q-39xc-vjpf](https://github.com/advisories/GHSA-fc5q-39xc-vjpf).
The final20November primary-source recheck found GitHub had withdrawn this
advisory on18November as not a security issue, with its page updated19November.
A fresh npm audit then returned zero known vulnerabilities in every severity.
Earlier “unpatched open advisory” reports describe the earlier audit response,
not the final current status. No dependency upgrade fixed this advisory;
the registry classification changed.

Removed the temporary dependency-rewriting build guard because its premise no
longer holds. Build/dev use normal Vite after locked `npm ci --ignore-scripts`
installs. Do not expose a development server or let untrusted users supply build
configuration/regex/glob patterns. A clean audit means no currently reported
known advisories for that snapshot, not proof of complete security.

## Secret and distribution checks

Gitleaks8.30.1 was downloaded with matching vendor SHA256. History scan44commits
found only four matches for two deterministic public Android fixture values.
A narrow AND allowlist binds exactly that test path and those fixture values;
reviewed history then passed. No broad test-directory exclusion was introduced.
The final source-only scan/checkpoint result is recorded in the delivery memory.
Installed dependencies, owner databases, credentials and models are excluded
from source checkpoints. No unknown raw secret is printed into reports.

The licensing pass caught the sherpa1.x GPL frontend and migrated to2.0.1 with
no legacy frontend/data use. See [third-party boundary](../THIRD_PARTY_BOUNDARY.md).
Original MIT license stays unchanged. Technical package checks do not replace
a full native dependency/model license audit before commercial distribution.

## Residual work

Native review-gate follow-up: owner-only checkpoint decisions now bind actual
draft/input/definition and completed events, recheck revision/hash/expiry and
serialize the decision with continuation queueing. Client grants have no review
privilege. Waiting releases the resource task and survives restart; completed
steps do not replay. Changed/tampered/expired/cancelled/foreign checkpoints are
covered by actual API/SQLite regressions. Branch conditions use bounded data
predicates without regex/eval, preserve scalar types and return false for
missing comparison fields. These hashes detect accidental changes; they do not
protect a database against an attacker who can rewrite its contents and hashes.

Keep the API loopback-only and never share the owner token with external tools.
Framework runtimes require independent isolation, version/dependency review and
acceptance; this bridge does not constrain a separately started program's shell
or network permissions. Official OAuth, authenticated device/Telegram transport,
complete encrypted profile recovery, all action budgets, signed distribution,
general workflow side effects and public-service load/abuse testing remain open.
No external email, social action, paid model or remote deployment was activated.
