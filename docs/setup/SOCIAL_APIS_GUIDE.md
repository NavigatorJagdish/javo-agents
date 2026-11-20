# Official Social Media APIs Guide (YouTube, Instagram Professional, Facebook Pages)

> Historical planning notes, not a working connection guide for this build.
> Official OAuth/client setup, persisted state, callback validation and capability
> discovery are incomplete. Accounts returns501 for sign-in initiation; the
> callback instructions below cannot currently connect an account. Consult
> [current account and credential boundaries](../SOCIAL_ACCOUNTS.md). Recheck
> official platform requirements before implementing a live connector.

Javo Agents **only integrates with official platform APIs** using user-authorized OAuth 2.0 tokens. Unofficial scraping or password login automation is strictly unsupported.

---

## 1. YouTube Data API v3

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create a project (`Javo-Creator-Runtime`).
2. Enable **YouTube Data API v3** and **YouTube Analytics API**.
3. Configure the **OAuth Consent Screen** (External, add your own Google account as a Test User while in testing mode).
4. Create **OAuth 2.0 Client ID** (`Desktop app` or `Web application` with redirect URI `http://localhost:8000/api/accounts/oauth/callback`).
5. Required scopes:
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/youtube.readonly`
   - `https://www.googleapis.com/auth/youtube.force-ssl` (for approved comment replies)

---

## 2. Instagram Professional & Facebook Pages (Meta Graph API)

> [!NOTE]
> Meta's Content Publishing API works **only for Instagram Professional accounts (Business or Creator)** linked to a **Facebook Page** — personal Instagram profiles are not supported by Meta's API.

1. Switch your Instagram account to **Creator** or **Business** and link it to a Facebook Page you admin.
2. Create an App at [developers.facebook.com](https://developers.facebook.com/) (Type: **Business**).
3. Add the **Facebook Login for Business** and **Instagram Graph API** products.
4. Set Valid OAuth Redirect URI to `http://localhost:8000/api/accounts/oauth/callback`.
5. Request permissions:
   - `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`
   - `instagram_basic`, `instagram_content_publish`, `instagram_manage_comments`
6. Store the App ID / Secret locally in `.env` and complete OAuth inside **Dashboard → Accounts**.
