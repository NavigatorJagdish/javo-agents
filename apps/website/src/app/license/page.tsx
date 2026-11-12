import type { Metadata } from 'next';
import Link from 'next/link';
import { PageHeader } from '@/components/PageHeader';
import { SITE_CONFIG } from '@/data/site';

export const metadata: Metadata = {
  title: 'Open Source License (MIT)',
  description:
    'MIT License text and third-party local AI model license guidance for Javo Agents.',
};

const MIT_LICENSE_TEXT = `MIT License

Copyright (c) 2026 Javo Agents Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.`;

export default function LicensePage() {
  return (
    <div>
      <PageHeader
        badge="Open Source Licensing"
        title="MIT"
        highlight="License"
        subtitle="Javo Agents application source code is licensed under the permissive MIT License. Local AI weights downloaded separately via Ollama or whisper.cpp carry their own upstream model licenses."
      />

      <section className="mx-auto max-w-4xl space-y-8 px-4 py-14 sm:px-6 lg:px-8">
        <div className="glass-card p-6 sm:p-8">
          <h2 className="font-display text-xl font-bold text-slate-900 dark:text-white">
            Javo Agents Software License
          </h2>
          <pre className="mt-4 overflow-x-auto whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-950 p-5 font-mono text-xs leading-relaxed text-slate-100 dark:border-white/10">
            {MIT_LICENSE_TEXT}
          </pre>
        </div>

        <div className="glass-card p-6">
          <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">
            Third-Party Local Model &amp; Runtime Licenses
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-[#E2E6F0]/85">
            Local models pulled through Ollama (such as Llama, Qwen, or Mistral variants), whisper.cpp models, and Piper TTS voices are governed by their respective upstream licenses. Compliance Agent (Agent 29) and <code className="font-mono">models/manifests/ollama-8gb-profiles.json</code> surface license audit notes inside the setup flow.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <a
              href={SITE_CONFIG.githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary"
            >
              Inspect Repository
            </a>
            <Link href="/pricing" className="btn-secondary">
              Free $0 Release Details
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
