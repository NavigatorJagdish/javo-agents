import type { Metadata } from 'next';
import { PageHeader } from '@/components/PageHeader';
import { DocsExplorer } from '@/components/DocsExplorer';

export const metadata: Metadata = {
  title: 'Documentation',
  description:
    'Searchable Javo Agents documentation covering Installation, Local AI (Ollama), Gemini, Telegram, Facebook, Instagram, YouTube, Content Folders, Voice Mode, Security, Backups, and Troubleshooting.',
};

export default function DocsPage() {
  return (
    <div>
      <PageHeader
        badge="12 Essential Guides"
        title="Javo Agents"
        highlight="Documentation"
        subtitle="Step-by-step setup and operations guides for Windows Local Runtime, Ollama 8GB profiles, official channel OAuth, Voice Mode, Security, and Backups."
      />
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <DocsExplorer />
      </section>
    </div>
  );
}
