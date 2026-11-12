import type { Metadata } from 'next';
import Link from 'next/link';
import { PageHeader } from '@/components/PageHeader';
import { FaqExplorer } from '@/components/FaqExplorer';

export const metadata: Metadata = {
  title: 'Frequently Asked Questions',
  description:
    'Answers to common questions about Javo Agents pricing ($0/month), 8GB RAM support, Supervised Autopilot, Privacy Firewall, and Voice Mode.',
};

export default function FaqPage() {
  return (
    <div>
      <PageHeader
        badge="Answers & Clarity"
        title="Frequently Asked"
        highlight="Questions"
        subtitle="Everything you need to know about running Javo Agents locally, supported platforms, hardware limits, and our $0 open-source release."
      />
      <section className="mx-auto max-w-4xl space-y-8 px-4 py-14 sm:px-6 lg:px-8">
        <FaqExplorer />
        <div className="glass-card flex flex-col items-start justify-between gap-4 p-6 sm:flex-row sm:items-center">
          <div>
            <h3 className="font-display text-lg font-bold text-slate-900 dark:text-white">
              Still have questions?
            </h3>
            <p className="text-sm text-slate-600 dark:text-[#E2E6F0]/80">
              Browse the 12 setup guides or open a topic on GitHub Discussions.
            </p>
          </div>
          <div className="flex gap-3">
            <Link href="/docs" className="btn-secondary">
              Read Docs
            </Link>
            <Link href="/contact" className="btn-primary">
              Community Links
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
