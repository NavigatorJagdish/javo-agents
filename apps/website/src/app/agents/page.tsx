import type { Metadata } from 'next';
import { PageHeader } from '@/components/PageHeader';
import { AgentsExplorer } from '@/components/AgentsExplorer';

export const metadata: Metadata = {
  title: 'AI Agent Team (29 Specialists)',
  description:
    'Explore all 29 specialist AI agents and the Master Orchestrator powering Javo Agents with explicit permission scopes and 8GB RAM scheduling.',
};

export default function AgentsPage() {
  return (
    <div>
      <PageHeader
        badge="29 Specialist Agents + Master Orchestrator"
        title="Meet Your Local-First"
        highlight="AI Agent Team"
        subtitle="Every specialist has a clear contract: typed inputs and outputs, bounded permission scopes, enable/disable toggles, and human-in-the-loop checkpoints."
      />
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <AgentsExplorer />
      </section>
    </div>
  );
}
