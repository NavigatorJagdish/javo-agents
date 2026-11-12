import type { Metadata } from 'next';
import { PageHeader } from '@/components/PageHeader';
import { IntegrationsMatrix } from '@/components/IntegrationsMatrix';

export const metadata: Metadata = {
  title: 'Integrations Matrix',
  description:
    'Truthful integration status matrix for Javo Agents: Supported, Beta, Planned, and Unavailable connectors including Ollama, Gemini, Telegram, YouTube, Facebook Pages, Instagram, and GitHub.',
};

export default function IntegrationsPage() {
  return (
    <div>
      <PageHeader
        badge="Truthful Connector Status"
        title="Integrations"
        highlight="Status Matrix"
        subtitle="We clearly distinguish what works today (Supported), what requires your own developer OAuth app (Beta), what is on the roadmap (Planned), and what is blocked by paid third-party APIs (Unavailable)."
      />
      <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <IntegrationsMatrix />
      </section>
    </div>
  );
}
