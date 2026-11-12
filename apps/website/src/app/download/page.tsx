import type { Metadata } from 'next';
import Link from 'next/link';
import {
  AlertCircle,
  CheckCircle2,
  Download,
  ExternalLink,
  FileCheck2,
  Github,
  Info,
  Lock,
  Monitor,
  Package,
  ShieldCheck,
  Smartphone,
  Terminal,
} from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { SITE_CONFIG } from '@/data/site';

export const metadata: Metadata = {
  title: 'Download Alpha',
  description:
    'Download Javo Agents v0.1.0-alpha for Windows and Android Companion. Authentic build artifacts, SHA-256 checksums, and private alpha installation instructions.',
};

export default function DownloadPage() {
  return (
    <div>
      <PageHeader
        badge={`Version ${SITE_CONFIG.version} · ${SITE_CONFIG.releaseStatus}`}
        title="Download"
        highlight="Javo Agents"
        subtitle="100% Free ($0/month) AI Ecosystem. Download verified Windows installers and Android test APKs directly from authenticated GitHub Actions build artifacts."
      />

      <section className="mx-auto max-w-7xl space-y-10 px-4 py-14 sm:px-6 lg:px-8">
        {/* Private Alpha Authorization Notice */}
        <div className="rounded-2xl border border-[#00E5FF]/40 bg-[#00E5FF]/10 p-5 text-sm text-slate-800 dark:text-[#E2E6F0]">
          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-[#008BA3] dark:text-[#00E5FF]" />
            <div>
              <p className="font-semibold text-slate-900 dark:text-white">
                Private Alpha Channel: Version {SITE_CONFIG.version} (Reproducible CI Builds)
              </p>
              <p className="mt-1 text-slate-700 dark:text-[#E2E6F0]/85">
                Build artifacts are compiled and cryptographically verified on every push by automated GitHub Actions runners. Because this repository is currently in <strong>Private Alpha</strong>, downloading test binaries requires logging into an authorized GitHub account with repository access.
              </p>
            </div>
          </div>
        </div>

        {/* Platform Cards */}
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Windows Desktop */}
          <div id="windows" className="glass-card flex flex-col justify-between p-6 sm:p-8">
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-2 rounded-full bg-[#00E5FF]/15 px-3 py-1 text-xs font-semibold text-[#007B8F] dark:text-[#00E5FF]">
                  <Monitor className="h-3.5 w-3.5" />
                  Windows Desktop &amp; Local Runtime
                </span>
                <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400">
                  v{SITE_CONFIG.version} (Alpha)
                </span>
              </div>

              <h2 className="mt-4 font-display text-2xl font-bold text-slate-900 dark:text-white">
                Javo Agents for Windows
              </h2>
              <p className="mt-2 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
                Self-contained Electron desktop shell with bundled FastAPI backend, React dashboard, 29 specialist agents, local memory, and whisper/FFmpeg hardware probes.
              </p>

              {/* Package Artifacts & Checksums */}
              <div className="mt-6 space-y-3">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 font-mono text-xs font-semibold text-slate-900 dark:text-white">
                      <Package className="h-3.5 w-3.5 text-[#00E5FF]" />
                      {SITE_CONFIG.windowsArtifacts.installerName}
                    </div>
                    <span className="text-[11px] text-slate-500 dark:text-slate-400">NSIS Setup (~79 MB)</span>
                  </div>
                  <div className="mt-2 overflow-x-auto font-mono text-[11px] text-slate-600 dark:text-[#00E5FF]/90">
                    SHA256: {SITE_CONFIG.windowsArtifacts.installerSha256}
                  </div>
                </div>

                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 font-mono text-xs font-semibold text-slate-900 dark:text-white">
                      <Package className="h-3.5 w-3.5 text-[#8B5CF6]" />
                      {SITE_CONFIG.windowsArtifacts.portableName}
                    </div>
                    <span className="text-[11px] text-slate-500 dark:text-slate-400">Portable (~78.7 MB)</span>
                  </div>
                  <div className="mt-2 overflow-x-auto font-mono text-[11px] text-slate-600 dark:text-[#A78BFA]">
                    SHA256: {SITE_CONFIG.windowsArtifacts.portableSha256}
                  </div>
                </div>
              </div>

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
                  <span>Runtime: {SITE_CONFIG.windowsMinSpecs.runtime}</span>
                </li>
              </ul>
            </div>

            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href={SITE_CONFIG.windowsArtifacts.workflowUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary"
              >
                <Download className="h-4 w-4" />
                Download Windows Artifacts
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
              <Link href="/docs#installation" className="btn-secondary">
                Windows Setup Guide
              </Link>
            </div>
          </div>

          {/* Android Companion */}
          <div id="android" className="glass-card flex flex-col justify-between p-6 sm:p-8">
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-2 rounded-full bg-[#8B5CF6]/15 px-3 py-1 text-xs font-semibold text-[#6D28D9] dark:text-[#A78BFA]">
                  <Smartphone className="h-3.5 w-3.5" />
                  Android Companion App
                </span>
                <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-400">
                  v{SITE_CONFIG.version} (Debug Test APK)
                </span>
              </div>

              <h2 className="mt-4 font-display text-2xl font-bold text-slate-900 dark:text-white">
                Javo Agents for Android
              </h2>
              <p className="mt-2 text-sm text-slate-600 dark:text-[#E2E6F0]/80">
                Native Jetpack Compose companion with Android Keystore encryption, offline Room draft repository, Push-to-Talk Hinglish voice interface, and LAN QR challenge-pairing.
              </p>

              {/* Android Package Artifacts */}
              <div className="mt-6 space-y-3">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 font-mono text-xs font-semibold text-slate-900 dark:text-white">
                      <Package className="h-3.5 w-3.5 text-emerald-400" />
                      {SITE_CONFIG.androidArtifacts.debugApkName}
                    </div>
                    <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-300">Test APK</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-600 dark:text-[#E2E6F0]/75">
                    Internal test APK for sideloading on Android 10+ devices or Android Virtual Devices (AVD).
                  </p>
                </div>

                {/* Google Play Store Badge (Coming After Testing) */}
                <div className="rounded-xl border border-dashed border-slate-300 bg-slate-100/60 p-4 dark:border-white/15 dark:bg-white/5">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
                      <Lock className="h-3.5 w-3.5 text-amber-400" />
                      Google Play Store Distribution
                    </div>
                    <span className="rounded bg-slate-200 px-2 py-0.5 text-[10px] font-medium text-slate-700 dark:bg-white/10 dark:text-slate-300">
                      Coming after testing
                    </span>
                  </div>
                  <p className="mt-1 text-[11px] text-slate-500 dark:text-[#E2E6F0]/60">
                    Play Console store listing will open following private alpha hardware validation.
                  </p>
                </div>
              </div>

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
                  <span>Pairing: {SITE_CONFIG.androidMinSpecs.note}</span>
                </li>
              </ul>
            </div>

            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href={SITE_CONFIG.androidArtifacts.workflowUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary"
              >
                <Download className="h-4 w-4" />
                Download Android APK Artifacts
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
              <Link href="/roadmap" className="btn-secondary">
                Testing Roadmap
              </Link>
            </div>
          </div>
        </div>

        {/* Installation & Checksum Verification Guides */}
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Windows Installation Notes */}
          <div className="glass-card p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
              <Monitor className="h-4 w-4 text-[#00E5FF]" />
              Windows Installation &amp; SmartScreen Guide
            </div>
            <div className="mt-3 space-y-2 text-xs leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
              <p>
                <strong>1. Choose Installer or Portable:</strong> <code className="font-mono">JavoAgents-0.1.0-x64.exe</code> installs start-menu shortcuts and desktop tray autostart. The Portable build runs in-place without touching Windows registries.
              </p>
              <p>
                <strong>2. SmartScreen Notice:</strong> As a private alpha build, the binary is not yet code-signed with a commercial EV certificate. If Windows SmartScreen appears: click <em>&quot;More info&quot;</em> &rarr; <em>&quot;Run anyway&quot;</em>.
              </p>
              <p>
                <strong>3. Local Python Runtime:</strong> If Python 3.10+ is installed, Javo Agents automatically spawns the local runtime. You can also specify an isolated environment with <code className="font-mono">JAVO_PYTHON_PATH</code>.
              </p>
            </div>
          </div>

          {/* SHA-256 Verification Guide */}
          <div className="glass-card p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
              <FileCheck2 className="h-4 w-4 text-[#8B5CF6]" />
              SHA-256 Checksum Verification
            </div>
            <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
              Verify your downloaded package against the official cryptographic hashes before executing:
            </p>
            <pre className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-slate-950 p-4 font-mono text-xs leading-relaxed text-slate-100 dark:border-white/10">
{`# Windows PowerShell
Get-FileHash .\\JavoAgents-0.1.0-x64.exe -Algorithm SHA256

# Linux / macOS / Android terminal
sha256sum javo-agents-android-v0.1.0-alpha-debug.apk`}
            </pre>
          </div>
        </div>

        {/* Source Quickstart */}
        <div className="glass-card p-6">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
            <Terminal className="h-4 w-4 text-[#00E5FF]" />
            Developer Source Quickstart
          </div>
          <pre className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-slate-950 p-4 font-mono text-xs leading-relaxed text-slate-100 dark:border-white/10">
{`git clone https://github.com/NavigatorJagdish/javo-agents.git
cd javo-agents
python -m venv .venv
.\\.venv\\Scripts\\activate
pip install -r services/local-runtime/requirements.txt
python -m uvicorn app.main:app --app-dir services/local-runtime --host 127.0.0.1 --port 8000`}
          </pre>
          <p className="mt-3 text-xs text-slate-600 dark:text-[#E2E6F0]/75">
            Starts the backend on loopback <code className="font-mono">127.0.0.1:8000</code>. Dashboard is served locally at <code className="font-mono">http://127.0.0.1:8000/dashboard/</code>.
          </p>
        </div>
      </section>
    </div>
  );
}
