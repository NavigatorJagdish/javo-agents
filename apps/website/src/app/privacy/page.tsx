import type { Metadata } from 'next';
import Link from 'next/link';
import { PageHeader } from '@/components/PageHeader';

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description:
    'Javo Agents Privacy Policy covering local-first data storage, static website behavior, and optional user-configured third-party APIs.',
};

export default function PrivacyPage() {
  return (
    <div>
      <PageHeader
        badge="Last Updated: November 12, 2026"
        title="Privacy"
        highlight="Policy"
        subtitle="Javo Agents is architected so your workspace, media files, voice audio, and credentials stay on hardware you control."
      />

      <section className="mx-auto max-w-4xl space-y-6 px-4 py-14 sm:px-6 lg:px-8">
        {[
          {
            title: '1. Local-First Desktop & Android Software',
            body: 'When you run the Javo Agents Windows Local Runtime and Android Companion app, your SQLite database, brand profiles, Smart Memory entries, content drafts, and whisper.cpp voice transcripts are stored locally on your devices. Javo Agents v0.1.0-alpha does not transmit telemetry, analytics, or user content to any central Javo server.',
          },
          {
            title: '2. Credentials & Encryption',
            body: 'OAuth tokens, Telegram bot tokens, and optional Gemini Developer API keys are encrypted locally using operating-system mechanisms (Windows DPAPI / Android Keystore AES-256-GCM). Pairing tokens between Windows and Android expire shortly after creation and can be revoked anytime.',
          },
          {
            title: '3. Optional Third-Party Providers',
            body: 'By default, Javo Agents routes AI inference to local Ollama (127.0.0.1). If you explicitly enable Google Gemini Developer API, Telegram Bot, YouTube Data API, Meta Graph API (Facebook Pages / Instagram Professional), or GitHub using your own credentials, data you authorize for those tasks is transmitted directly from your device to those providers under their respective privacy policies. The Privacy Firewall strips sensitive secrets and paths before optional Gemini prompt egress.',
          },
          {
            title: '4. Official Website',
            body: 'This static informational website uses browser localStorage solely to remember your Dark/Light theme preference. Interactive Workflow and Voice demos run entirely inside your browser without uploading audio or data to external servers.',
          },
          {
            title: '5. Your Data Rights & Deletion',
            body: 'Because your data lives locally on your Windows PC and Android device, you can inspect, export encrypted backups, or permanently delete your local database and Keystore keys at any time using the in-app Privacy & Data controls.',
          },
        ].map((section) => (
          <article key={section.title} className="glass-card p-6">
            <h2 className="font-display text-xl font-bold text-slate-900 dark:text-white">
              {section.title}
            </h2>
            <p className="mt-2.5 text-sm leading-relaxed text-slate-600 dark:text-[#E2E6F0]/85">
              {section.body}
            </p>
          </article>
        ))}

        <div className="flex gap-3">
          <Link href="/security" className="btn-primary">
            Security Architecture
          </Link>
          <Link href="/terms" className="btn-secondary">
            Terms of Service
          </Link>
        </div>
      </section>
    </div>
  );
}
