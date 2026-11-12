'use client';

import React, { useState } from 'react';
import { Mic, ShieldCheck, Volume2 } from 'lucide-react';
import { WaveformGraphic, type WaveformState } from './WaveformGraphic';

interface VoiceSample {
  id: string;
  language: 'Hinglish' | 'Hindi' | 'English';
  utterance: string;
  intent: string;
  agentRoute: string;
  response: string;
}

const VOICE_SAMPLES: VoiceSample[] = [
  {
    id: 'hinglish-approvals',
    language: 'Hinglish',
    utterance: 'Javo, aaj ke Instagram reels draft check karo aur summary batao.',
    intent: 'APPROVAL_INBOX_SUMMARY(channel="instagram_pro", filter="today")',
    agentRoute: '07 Voice Agent → 15 Approval Manager',
    response:
      'Aapke Approval Inbox mein 2 Reels drafts ready hain. Dono Quality Inspector pass kar chuke hain—kya main Telegram par preview bhej doon?',
  },
  {
    id: 'hindi-pause',
    language: 'Hindi',
    utterance: 'जावो, अभी के लिए सभी शेड्यूल किए गए पोस्ट रोक दो।',
    intent: 'QUEUE_PAUSE(scope="all_scheduled_posts")',
    agentRoute: '07 Voice Agent → 22 Security Guardian',
    response:
      'सभी शेड्यूल किए गए पोस्ट सुरक्षित रूप से पॉज़ कर दिए गए हैं। जब आप चाहें तो डैशबोर्ड या टेलीग्राम से इन्हें फिर शुरू कर सकते हैं।',
  },
  {
    id: 'english-youtube',
    language: 'English',
    utterance: 'Javo, prepare a title and description draft for the latest video in my inbox folder.',
    intent: 'CONTENT_DRAFT(source="inbox/latest", target="youtube")',
    agentRoute: '07 Voice Agent → 02 Content Factory → 06 Brand Manager',
    response:
      'Local Ollama drafted 3 YouTube titles and chapter timestamps from your latest inbox video. The draft is queued for your approval.',
  },
];

const STATES: WaveformState[] = ['Idle', 'Listening', 'Thinking', 'Executing', 'Finished'];

export function VoiceModeDemo() {
  const [selectedSample, setSelectedSample] = useState(0);
  const [waveState, setWaveState] = useState<WaveformState>('Listening');

  const sample = VOICE_SAMPLES[selectedSample];

  const handleSelectSample = (index: number) => {
    setSelectedSample(index);
    setWaveState('Executing');
  };

  return (
    <div className="glass-card overflow-hidden p-6 sm:p-8">
      <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 dark:border-white/10 md:flex-row md:items-center">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-[#00E5FF]/40 bg-[#00E5FF]/10 px-3 py-1 text-xs font-semibold text-[#007B8F] dark:text-[#00E5FF]">
            <Mic className="h-3.5 w-3.5" />
            Simulated Voice Mode Preview (whisper.cpp + Piper TTS)
          </span>
          <h3 className="mt-2 font-display text-xl font-bold text-slate-900 dark:text-white">
            Speak Naturally in Hindi, Hinglish, or English
          </h3>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {STATES.map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setWaveState(st)}
              className={`rounded-lg px-2.5 py-1 text-xs font-medium transition ${
                waveState === st
                  ? 'bg-[#00E5FF]/20 text-[#007B8F] ring-1 ring-[#00E5FF]/50 dark:text-[#00E5FF]'
                  : 'bg-slate-100 text-slate-600 hover:text-slate-900 dark:bg-white/5 dark:text-[#94A3B8] dark:hover:text-white'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-12 lg:items-center">
        <div className="lg:col-span-5">
          <div className="rounded-2xl border border-slate-200 bg-slate-950 p-6 text-center dark:border-white/10 dark:bg-[#080C1D]">
            <p className="text-xs font-semibold uppercase tracking-widest text-[#00E5FF]">
              Wake Word: &ldquo;Javo&rdquo; · State: {waveState}
            </p>
            <div className="my-5">
              <WaveformGraphic state={waveState} />
            </div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
              <ShieldCheck className="h-3.5 w-3.5" />
              100% Offline Audio Processing
            </div>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {VOICE_SAMPLES.map((item, idx) => (
              <button
                key={item.id}
                type="button"
                onClick={() => handleSelectSample(idx)}
                className={`rounded-xl px-3 py-2 text-xs font-semibold transition ${
                  selectedSample === idx
                    ? 'bg-gradient-to-r from-[#00E5FF] to-[#8B5CF6] text-[#0B1026]'
                    : 'border border-slate-300 bg-white text-slate-700 dark:border-white/15 dark:bg-white/5 dark:text-[#E2E6F0]'
                }`}
              >
                {item.language} Example
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4 lg:col-span-7">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-[#0B1026]/80">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-[#94A3B8]">
              1. Local whisper.cpp Transcript ({sample.language})
            </p>
            <p className="mt-1.5 text-sm font-medium text-slate-900 dark:text-white">
              &ldquo;{sample.utterance}&rdquo;
            </p>
          </div>

          <div className="rounded-2xl border border-[#8B5CF6]/30 bg-[#8B5CF6]/5 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-[#6D28D9] dark:text-[#A78BFA]">
              2. Intent &amp; Agent Routing
            </p>
            <p className="mt-1.5 font-mono text-xs text-slate-800 dark:text-[#00E5FF]">
              {sample.intent}
            </p>
            <p className="mt-1 text-xs text-slate-600 dark:text-[#E2E6F0]/80">
              Pipeline: {sample.agentRoute}
            </p>
          </div>

          <div className="rounded-2xl border border-[#00E5FF]/30 bg-[#00E5FF]/5 p-4">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#007B8F] dark:text-[#00E5FF]">
              <Volume2 className="h-3.5 w-3.5" />
              3. Piper TTS Local Reply
            </div>
            <p className="mt-1.5 text-sm leading-relaxed text-slate-800 dark:text-[#E2E6F0]">
              {sample.response}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
