import type { Metadata } from 'next';
import Link from 'next/link';
import { Cpu, Globe, Mic, ShieldCheck, Smartphone, Volume2 } from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { VoiceModeDemo } from '@/components/VoiceModeDemo';

export const metadata: Metadata = {
  title: 'Voice Mode (Javo Wake Word)',
  description:
    'Offline-first Voice Mode with "Javo" wake word, Hindi, Hinglish, and English understanding, whisper.cpp STT, and Piper TTS.',
};

export default function VoicePage() {
  return (
    <div>
      <PageHeader
        badge="Local whisper.cpp + Piper TTS"
        title="Voice Assistant in"
        highlight="Hindi, Hinglish & English"
        subtitle='Trigger tasks with the "Javo" wake word or push-to-talk. Speech is transcribed locally via whisper.cpp and spoken back via Piper TTS—no cloud audio uploads.'
      >
        <Link href="/download" className="btn-primary">
          Download Windows + Android
        </Link>
        <Link href="/docs#voice-mode" className="btn-secondary">
          Voice Setup Docs
        </Link>
      </PageHeader>

      <section className="mx-auto max-w-7xl space-y-12 px-4 py-14 sm:px-6 lg:px-8">
        <VoiceModeDemo />

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[
            {
              icon: Mic,
              title: 'Wake Word & Push-to-Talk',
              body: 'Say "Javo" hands-free on Windows or use push-to-talk on Android to minimize battery and microphone active time.',
            },
            {
              icon: Globe,
              title: 'Bilingual & Hinglish Routing',
              body: 'Designed for Indian and global creators alike—switch seamlessly between English, Hindi, and mixed Hinglish commands.',
            },
            {
              icon: ShieldCheck,
              title: 'Zero Cloud Audio Upload',
              body: 'whisper.cpp executes offline inside your local Windows environment; recordings are never shipped to remote voice servers.',
            },
            {
              icon: Cpu,
              title: '8GB RAM Auto-Unload',
              body: 'Resource Optimizer loads quantized Whisper models only during voice sessions and frees RAM before Ollama generates long drafts.',
            },
            {
              icon: Volume2,
              title: 'Piper Neural TTS',
              body: 'Fast, lightweight local text-to-speech reads back approval counts, task confirmations, and daily summaries.',
            },
            {
              icon: Smartphone,
              title: 'Android Companion Sync',
              body: 'Trigger Voice Mode from your Android phone over your paired LAN connection and review transcripts on the go.',
            },
          ].map((card) => (
            <div key={card.title} className="glass-card p-6">
              <card.icon className="h-6 w-6 text-[#00E5FF]" />
              <h2 className="mt-3 font-display text-lg font-bold text-slate-900 dark:text-white">
                {card.title}
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-[#E2E6F0]/80">
                {card.body}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
