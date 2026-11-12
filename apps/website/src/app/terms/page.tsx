import type { Metadata } from 'next';
import Link from 'next/link';
import { PageHeader } from '@/components/PageHeader';

export const metadata: Metadata = {
  title: 'Terms of Service',
  description:
    'Terms of Service for Javo Agents open-source local-first software and informational website.',
};

export default function TermsPage() {
  return (
    <div>
      <PageHeader
        badge="Last Updated: November 12, 2026"
        title="Terms of"
        highlight="Service"
        subtitle="Clear terms governing use of the Javo Agents open-source software (v0.1.0-alpha) and this public website."
      />

      <section className="mx-auto max-w-4xl space-y-6 px-4 py-14 sm:px-6 lg:px-8">
        {[
          {
            title: '1. Open-Source Software License',
            body: 'Javo Agents source code is provided under the MIT License. You may use, copy, modify, and distribute the software in accordance with the MIT License terms published on the License page.',
          },
          {
            title: '2. Supervised Autopilot & User Responsibility',
            body: 'You remain solely responsible for all content, comments, uploads, and actions approved or published through your connected social accounts, Telegram bots, and API keys. Always review drafts inside the Approval Inbox before publishing and comply with applicable laws and third-party platform terms (YouTube, Meta, Telegram, Google AI, GitHub).',
          },
          {
            title: '3. Prohibited Misuse',
            body: 'You agree not to use Javo Agents for deceptive engagement, spam, unauthorized scraping, credential harvesting, or circumvention of platform rate limits and safety controls.',
          },
          {
            title: '4. Alpha Software & No Warranty',
            body: 'Version 0.1.0-alpha is provided "AS IS" without warranties of merchantability, fitness for a particular purpose, or uninterrupted availability of third-party APIs. Maintain encrypted backups of important local data.',
          },
          {
            title: '5. Future Optional Services',
            body: 'No paid subscriptions or billing agreements are active in v0.1.0-alpha. Any optional hosted relay or enterprise offerings introduced in future releases will be governed by separate opt-in terms.',
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
          <Link href="/license" className="btn-primary">
            Read MIT License
          </Link>
          <Link href="/privacy" className="btn-secondary">
            Privacy Policy
          </Link>
        </div>
      </section>
    </div>
  );
}
