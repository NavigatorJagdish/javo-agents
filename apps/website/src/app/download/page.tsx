import type { Metadata } from 'next';
import Link from 'next/link';
import {
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  FileCheck2,
  Github,
  Monitor,
  Smartphone,
  Terminal,
} from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { SITE_CONFIG } from '@/data/site';

export const metadata: Metadata = {
  title: 'Download',
  description:
    'Download Javo Agents v0.1.0-alpha for Windows and Android Companion. System requirements, SHA-256 verification instructions, and source-available setup.',
};

export default function DownloadPage() {
  return (
    <div>
      <PageHeader
        badge={`Version ${SITE_CONFIG.version} · ${SITE_CONFIG.releaseStatus}`}
        title="Download"
        highlight="Javo Agents"
        subtitle="Free ($0/month), open-source MIT software. Run the Windows Local Runtime from source or official GitHub Releases, and pair your Android Companion over LAN."
      />

      <section className="mx-auto max-w-7xl space-y-10 px-4 py-14 sm:px-6 lg:px-8">
        {/* Honest Availability Notice */}
        <div className="rounded-2xl border border-[#00E5FF]/35 bg-[#00E5FF]/10 p-5 text-sm text-slate-800 dark:text-[#E2E6F0]">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-[#008BA3] dark:text-[#00E5FF]" />
            <div>
              <p className="font-semibold text-slate-900 dark:text-white">
                Honest Release Status: v0.1.0-alpha (Source Available / Pre-Release)
              </p>
              <p className="mt-1 text-slate-700 dark:text-[#E2E6F0]/85">
                Signed Windows NSIS installers and Google Play Store listings are tracked on our release pipeline. Today, you can run directly from the verified GitHub repository or inspect release artifacts on GitHub Releases—we never publish broken placeholder download links.
              </p>
            </div>
          </div>
        </div>

        {/* Platform Cards */}
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Windows */}
          <div id="windows" className="glass-card flex flex-col justify-between p-6 sm:p-8">
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-2 rounded-full bg-[#00E5FF]/15 px-3 py-1 text-xs font-semibold text-[#007B8F] dark:text-[#00E5FF]">
                  <Monitor className="h-3.5 w-3.5" />
                  Windows Desktop &amp; Local Runtime
                </span>
                <span className="font-mono text-xs text-slate-500 dark:text-[#94A3B8]">
                  v{SITE_CONFIG.version}
                </span>
              </div>

              <h2 className="mt-4 font-display text-2xl font-bold text-slate-900 dark:text-white">
                Javo Agents for Windows
              </h2>
              <p className="mt-2 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
                Includes the Electron tray shell, React + TypeScript Dashboard, Python FastAPI Local Runtime, 29 specialist agents, and Ollama / whisper.cpp integration.
              </p>

              <h3 className="mt-6 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-[#94A3B8]">
                System Requirements
              </h3>
              <ul className="mt-3 space-y-2 text-sm text-slate-700 dark:text-[#E2E6F0]/90">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                  <span>OS: {SITE_CONFIG.windowsMinSpecs.os}</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                  <span>Memory: {SITE_CONFIG.windowsMinSpecs.ram}</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                  <span>Storage: {SITE_CONFIG.windowsMinSpecs.storage}</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                  <span>Dependencies: {SITE_CONFIG.windowsMinSpecs.runtime}</span>
                </li>
              </ul>
            </div>

            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href={SITE_CONFIG.githubReleasesUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary"
              >
                <Github className="h-4 w-4" />
                GitHub Releases
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
              <Link href="/docs#installation" className="btn-secondary">
                Windows Setup Guide
              </Link>
            </div>
          </div>

          {/* Android */}
          <div id="android" className="glass-card flex flex-col justify-between p-6 sm:p-8">
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-2 rounded-full bg-[#8B5CF6]/15 px-3 py-1 text-xs font-semibold text-[#6D28D9] dark:text-[#A78BFA]">
                  <Smartphone className="h-3.5 w-3.5" />
                  Android Companion App
                </span>
                <span className="rounded-full border border-[#00E5FF]/40 px-2.5 py-0.5 text-xs font-medium text-[#007B8F] dark:text-[#00E5FF]">
                  Beta / Source Ready
                </span>
              </div>

              <h2 className="mt-4 font-display text-2xl font-bold text-slate-900 dark:text-white">
                Javo Agents for Android
              </h2>
              <p className="mt-2 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
                Native Jetpack Compose companion with Keystore-encrypted QR pairing, offline Room draft cache, Approval Inbox, and push-to-talk Voice Mode.
              </p>

              <h3 className="mt-6 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-[#94A3B8]">
                Requirements &amp; Pairing
              </h3>
              <ul className="mt-3 space-y-2 text-sm text-slate-700 dark:text-[#E2E6F0]/90">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                  <span>OS: {SITE_CONFIG.androidMinSpecs.os}</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                  <span>Memory: {SITE_CONFIG.androidMinSpecs.ram}</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                  <span>Storage: {SITE_CONFIG.androidMinSpecs.storage}</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                  <span>{SITE_CONFIG.androidMinSpecs.note}</span>
                </li>
              </ul>
            </div>

            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href={SITE_CONFIG.githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary"
              >
                <Github className="h-4 w-4" />
                Android Source (apps/android)
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
              <Link href="/roadmap" className="btn-secondary">
                Play Store Track Roadmap
              </Link>
            </div>
          </div>
        </div>

        {/* Quick Start & SHA-256 Verification */}
        <div className="grid gap-8 lg:grid-cols-2">
          <div className="glass-card p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
              <Terminal className="h-4 w-4 text-[#00E5FF]" />
              Run From Verified Source (PowerShell)
            </div>
            <pre className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-slate-950 p-4 font-mono text-xs leading-relaxed text-slate-100 dark:border-white/10">
{`git clone https://github.com/NavigatorJagdish/javo-agents.git
cd javo-agents
.\\scripts\\setup-windows.ps1
.\\scripts\\start-windows.ps1`}
            </pre>
            <p className="mt-3 text-xs text-slate-600 dark:text-[#E2E6F0]/75">
              Starts the FastAPI Local Runtime on <code className="font-mono">127.0.0.1:8000</code> and the Dashboard UI locally.
            </p>
          </div>

          <div className="glass-card p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
              <FileCheck2 className="h-4 w-4 text-[#8B5CF6]" />
              SHA-256 Checksum Verification Guide
            </div>
            <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
              Whenever downloading packaged Windows `.exe` or Android `.apk` files from GitHub Releases, always compare your local SHA-256 digest against the <code className="font-mono">SHA256SUMS.txt</code> file published in that exact release tag:
            </p>
            <pre className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-slate-950 p-4 font-mono text-xs leading-relaxed text-slate-100 dark:border-white/10">
{`# Windows PowerShell
Get-FileHash .\\Javo-Agents-Setup-0.1.0-alpha.exe -Algorithm SHA256

# Compare output against SHA256SUMS.txt from GitHub Releases`}
            </pre>
          </div>
        </div>
      </section>
    </div>
  );
}
