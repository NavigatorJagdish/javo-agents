# Google Gemini API Setup (Free Tier & Data Handling Notice)

Javo Agents supports Google Gemini (`gemini-2.0-flash`) as an **optional** cloud AI provider when you want faster long-context reasoning or when your 8 GB laptop is busy rendering video.

## 1. Getting a Free Gemini Developer API Key

1. Visit **Google AI Studio**: [aistudio.google.com](https://aistudio.google.com/).
2. Sign in with your Google account and click **Get API Key → Create API key**.
3. Open **Javo Dashboard → Settings → AI Providers** (or edit `services/local-runtime/.env`):
   ```env
   JAVO_GEMINI_API_KEY=your-api-key-here
   JAVO_GEMINI_MODEL=gemini-2.0-flash
   ```
4. Set a strict budget guardrail (`JAVO_AI_DAILY_BUDGET=0.0` if staying strictly on the Free Tier).

---

## 2. Important Data Handling Notice

> [!IMPORTANT]
> **Free Tier vs. Paid Tier Privacy**: Under Google AI Studio's Free Developer API tier, prompts and outputs may be reviewed or used by Google to improve products in accordance with Google's Generative AI Terms. Under Paid/Cloud billing tiers, prompts are not used to train models.

**Best Practices in Javo Agents:**
- Keep **Strict Local Mode (Ollama)** enabled for unreleased client projects, passwords, financial data, or personal scripts.
- Use `privacy_firewall.py` sanitization rules so personal identifiers are stripped before any cloud call.
- Never paste OAuth tokens or secrets into AI prompts.
