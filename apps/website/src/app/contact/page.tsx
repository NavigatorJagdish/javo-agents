import type { Metadata } from 'next';
import Link from 'next/link';
import { BookOpen, Bug, ExternalLink, Github, MessageSquare, ShieldAlert } from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { SITE_CONFIG } from '@/data/site';

export const metadata: Metadata = {
  title: 'Contact & Community',
  description:
    'Official Javo Agents community channels: GitHub Issues, GitHub Discussions, Documentation, and Security Vulnerability Reporting.',
};

export default function ContactPage() {
  const channels = [
    {
      icon: MessageSquare,
      title: 'GitHub Discussions',
      desc: 'Ask setup questions, share workflow templates, and discuss roadmap priorities with contributors.',
      cta: 'Open Discussions',
      href: SITE_CONFIG.githubDiscussionsUrl,
      external: true,
    },
    {
      icon: Bug,
      title: 'Bug Reports & Feature Requests',
      desc: 'Report reproducible Windows runtime, dashboard, or Android companion bugs using our issue templates.',
      cta: 'Open GitHub Issues',
      href: SITE_CONFIG.githubIssuesUrl,
      external: true,
    },
    {
      icon: ShieldAlert,
      title: 'Security Vulnerability Reporting',
      desc: 'Never post suspected security vulnerabilities in public issues. Follow our coordinated disclosure guide.',
      cta: 'Security Reporting Policy',
      href: '/security-reporting',
      external: false,
    },
    {
      icon: BookOpen,
      title: 'Documentation & Troubleshooting',
      desc: 'Search all 12 setup and troubleshooting guides for Ollama, Gemini, Telegram, Voice Mode, and OAuth.',
      cta: 'Browse Documentation',
      href: '/docs',
      external: false,
    },
  ];

  return (
    <div>
      <PageHeader
        badge="Open Source Community"
        title="Contact &"
        highlight="Community"
        subtitle="Javo Agents is developed openly on GitHub. Reach maintainers and fellow creators through verified public repositories and security channels."
      />

      <section className="mx-auto max-w-5xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-6 md:grid-cols-2">
          {channels.map((ch) => (
            <div key={ch.title} className="glass-card flex flex-col justify-between p-6">
              <div>
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-[#00E5FF]/15 text-[#008BA3] dark:text-[#00E5FF]">
                  <ch.icon className="h-5 w-5" />
                </div>
                <h2 className="mt-4 font-display text-xl font-bold text-slate-900 dark:text-white">
                  {ch.title}
                </h2>
                <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
                  {ch.desc}
                </p>
              </div>
              <div className="mt-6">
                {ch.external ? (
                  <a
                    href={ch.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary"
                  >
                    <Github className="h-4 w-4" />
                    {ch.cta}
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                ) : (
                  <Link href={ch.href} className="btn-primary">
                    {ch.cta}
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
