# Javo Website — GitHub Pages (no custom domain)

**Intended project URL:** https://navigatorjagdish.github.io/javo-agents/

**Deployment source:** existing private `NavigatorJagdish/javo-agents` repository. The workflow is on **main**:
[`.github/workflows/deploy-github-pages.yml`](../../.github/workflows/deploy-github-pages.yml).

## What has been configured in the repository
- Next.js static export (`output: 'export'`, `trailingSlash: true`).
- `GITHUB_PAGES=true` activates `basePath: '/javo-agents'` to keep all internal links under the correct GitHub Pages project route.
- Website metadata, icon, sitemap and robots refer to the GitHub Pages project path (no `javoagents.org` domain dependency in the Pages build).
- Production Pages workflow on `main` checks out the existing `fix/android-ci-and-production-hardening` branch for the updated website source. **This does not merge PR #1.** Once approved/merged, change checkout to `main`.
- `pnpm install --frozen-lockfile`, type check, static build, page existence checks, `.nojekyll`, then `configure-pages`, `upload-pages-artifact`, `deploy-pages`.
- GitHub Pages workflow uses only `contents:read`, `pages:write`, `id-token:write`. It does not upload source tokens or credentials.

## Required GitHub account action (only once)

1. Open [Repository Settings → Pages](https://github.com/NavigatorJagdish/javo-agents/settings/pages) using the account with admin access.
2. Under **Build and deployment → Source**, select **GitHub Actions**, and save if prompted.
3. Check that GitHub Pages is supported by your account plan. **GitHub Free supports Pages for public repositories; Pages from a private repository requires GitHub Pro or an eligible Team/Enterprise plan.** Do **not** make this mixed code/agent repository public to get Pages on a Free plan.
4. Open [GitHub Actions → Deploy Javo Website to GitHub Pages](https://github.com/NavigatorJagdish/javo-agents/actions/workflows/deploy-github-pages.yml) and choose **Run workflow → main** after Pages is enabled. GitHub Actions may need approval/usable billing quota if other repository workflows immediately fail.
5. Wait for a successful **deploy** job; GitHub will show an actual Pages environment URL. Open it and verify **home**, **/features/**, **/download/**, and favicon. If the build fails, inspect the failed job log; no deployment is complete until the workflow succeeds.

## Private project vs public website

GitHub Pages generally publishes website output publicly even if source repository is private. Keep secrets and private code out of `apps/website/public`, Next.js client bundles and public metadata. The Pages output is static front-end only; **GitHub Pages cannot execute Javo's FastAPI, OAuth token broker, Windows/Android runtime, database or autonomous workers**.

If your account is **GitHub Free** and you want to **keep this code repository private**, the no-cost GitHub-only route is a **separate public website-only repository** containing only the generated safe static HTML/CSS/JS (not your private app source). Creating such a repo or changing repository visibility requires explicit user action/authorization and has **not** been done.

## Diagnostic checks

- **404 immediately:** Pages not enabled or workflow has not successfully deployed.
- **No Actions build steps:** repository Actions availability, billing, or permissions blocked; this is not proof of a website code bug.
- **Missing styles, CSS or broken links:** ensure `GITHUB_PAGES=true`, matching `basePath: '/javo-agents'`, and rebuild the Pages artifact.
- **Page load but favicon missing:** ensure exported path `/javo-agents/favicon.svg`.
- **Private Pages unavailable:** verify GitHub account plan; do not change repo visibility without explicit owner approval.

**Acceptance criteria:** a verified HTTP 200 public response at the exact Pages URL, loaded JS/CSS, working internal routes, valid HTTPS and an actual successful GitHub Pages deployment event. Workflow and source commits alone are not website-live proof.
