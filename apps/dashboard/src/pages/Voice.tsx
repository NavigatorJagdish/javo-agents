import React, { useState } from 'react';
import { Mic, MicOff, Send, Volume2, Bot, User } from 'lucide-react';
import { Card, Badge, Button, WaveformVisualizer, Chip } from '@javo/design-system';
import { useAppStore } from '../store/useAppStore';

interface VoiceMessage {
  id: string;
  sender: 'user' | 'agent';
  agentName?: string;
  text: string;
  timestamp: string;
}

const INITIAL_HISTORY: VoiceMessage[] = [
  {
    id: 'v-1',
    sender: 'user',
    text: 'Hey Javo, what is scheduled for YouTube Shorts tomorrow?',
    timestamp: '16:40',
  },
  {
    id: 'v-2',
    sender: 'agent',
    agentName: 'Voice Agent (#07) + Content Publisher (#09)',
    text: 'One Short is queued for 18:00 EST: "5 Local AI Workflows That Save 12 Hours/Week". Quality Inspector scored it 94/100. Would you like me to approve it now?',
    timestamp: '16:40',
  },
];

export const Voice: React.FC = () => {
  const [listening, setListening] = useState(false);
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<VoiceMessage[]>(INITIAL_HISTORY);
  const addToast = useAppStore((s) => s.addToast);

  const sendCommand = (text: string) => {
    const clean = text.trim();
    if (!clean) return;
    const now = new Date().toTimeString().slice(0, 5);
    const userMsg: VoiceMessage = {
      id: `v-${Date.now()}`,
      sender: 'user',
      text: clean,
      timestamp: now,
    };
    const replyMsg: VoiceMessage = {
      id: `v-${Date.now() + 1}`,
      sender: 'agent',
      agentName: 'Voice Agent (#07)',
      text: `Dispatched "${clean}" to MasterAgent Orchestrator. 28 active specialists are synced and no policy conflicts were detected.`,
      timestamp: now,
    };
    setHistory((prev) => [...prev, userMsg, replyMsg]);
    setInput('');
  };

  const togglePushToTalk = () => {
    if (!listening) {
      setListening(true);
      addToast('Listening...', 'Whisper Large v3 local STT active.', 'info');
    } else {
      setListening(false);
      sendCommand('Run a quick health check and summarize pending approvals.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            Voice Command Interface
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Hands-free local speech recognition & neural TTS powered by Voice Agent (#07).
          </p>
        </div>
        <Badge status={listening ? 'info' : 'active'} pulse={listening}>
          {listening ? 'Capturing Audio...' : 'Whisper Local Ready'}
        </Badge>
      </div>

      {/* Waveform Hero Card */}
      <Card variant="feature" glow="cyan" className="text-center py-8">
        <div className="max-w-xl mx-auto space-y-6">
          <div className="flex justify-center">
            <WaveformVisualizer
              active={listening}
              bars={32}
              height={76}
              intensity={listening ? 1 : 0.45}
            />
          </div>

          <div>
            <button
              type="button"
              onClick={togglePushToTalk}
              aria-label={listening ? 'Stop voice capture' : 'Start push to talk'}
              className={`mx-auto h-20 w-20 rounded-full flex items-center justify-center transition-all cursor-pointer ${
                listening
                  ? 'bg-gradient-to-br from-[#00E5FF] to-[#8B5CF6] text-[#0B1026] shadow-[0_0_38px_rgba(0,229,255,0.6)] scale-105'
                  : 'bg-[#131C40] border-2 border-[#00E5FF]/50 text-[#00E5FF] hover:border-[#00E5FF] hover:shadow-[0_0_24px_rgba(0,229,255,0.3)]'
              }`}
            >
              {listening ? <MicOff className="h-8 w-8" /> : <Mic className="h-8 w-8" />}
            </button>
            <p className="mt-3 text-sm font-medium text-slate-700 dark:text-slate-300">
              {listening ? 'Click again to finish speaking & dispatch' : 'Click to Push-to-Talk (Ctrl + Space)'}
            </p>
          </div>

          <div className="flex flex-wrap justify-center gap-2">
            {[
              'Summarize today’s analytics',
              'Approve pending replies',
              'Pause autopilot mode',
            ].map((preset) => (
              <Chip
                key={preset}
                label={preset}
                onClick={() => sendCommand(preset)}
              />
            ))}
          </div>
        </div>
      </Card>

      {/* Conversation History */}
      <Card variant="default">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <Volume2 className="h-4 w-4 text-[#00E5FF]" /> Voice Transcript & History
          </h2>
        </div>

        <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
          {history.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 p-3.5 rounded-xl border ${
                msg.sender === 'user'
                  ? 'bg-[#00E5FF]/10 border-[#00E5FF]/25 ml-auto max-w-2xl'
                  : 'bg-slate-50 dark:bg-[#0B1026]/75 border-slate-200 dark:border-white/10 max-w-2xl'
              }`}
            >
              <div className="h-8 w-8 rounded-lg bg-white/10 flex items-center justify-center shrink-0">
                {msg.sender === 'user' ? (
                  <User className="h-4 w-4 text-[#00E5FF]" />
                ) : (
                  <Bot className="h-4 w-4 text-[#8B5CF6]" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span className="font-semibold text-slate-700 dark:text-slate-200">
                    {msg.sender === 'user' ? 'You' : msg.agentName}
                  </span>
                  <span>{msg.timestamp}</span>
                </div>
                <p className="text-sm text-slate-800 dark:text-[#E2E6F0]">{msg.text}</p>
              </div>
            </div>
          ))}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendCommand(input);
          }}
          className="mt-4 flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Or type a voice-routed command..."
            aria-label="Voice command text fallback"
            className="flex-1 h-10 px-3 rounded-xl text-sm bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 focus:outline-none focus:border-[#00E5FF]"
          />
          <Button type="submit" leftIcon={<Send className="h-4 w-4" />}>
            Send
          </Button>
        </form>
      </Card>
    </div>
  );
};
