import React, { useEffect, useRef, useState } from 'react';
import { Send, Bot, User, Square, Trash2 } from 'lucide-react';
import { SpeechStudio } from '../components/SpeechStudio';
import { Card, Badge, Button } from '@javo/design-system';
import { ApiError, apiRequest } from '../api/client';
import { useQueryClient } from '@tanstack/react-query';

interface Turn { role: 'user' | 'assistant'; text: string; source?: string }
interface Reply {
  intent: string; response_text: string; action_taken: string | null;
  requires_confirmation: boolean; data: { provider?: string; model?: string };
}

export const Voice: React.FC = () => {
  const queries = useQueryClient();
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<Turn[]>([]);
  const [provider, setProvider] = useState('ollama');
  const [language, setLanguage] = useState('hinglish');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [pending, setPending] = useState<string | null>(null);
  const abort = useRef<AbortController | null>(null);
  const mounted = useRef(true);
  const context = useRef<Turn[]>([]);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; abort.current?.abort(); };
  }, []);

  const send = async (text: string, confirmed = false) => {
    const clean = text.trim();
    if (!clean || abort.current) return;
    const controller = new AbortController();
    abort.current = controller;
    setBusy(true); setNotice(''); setPending(null); setInput('');
    if (!confirmed) setHistory(previous => [...previous, { role: 'user' as const, text: clean }].slice(-40));
    try {
      // Context is session-only, bounded, and contains only completed text exchanges.
      const reply = await apiRequest<Reply>('/api/voice/command', {
        method: 'POST', signal: controller.signal,
        body: { transcript: clean, confirmed, provider, language,
          history: context.current.slice(-4).map(turn => ({ role: turn.role, text: turn.text.slice(0, 2000) })) },
      });
      if (!mounted.current || controller.signal.aborted) return;
      if (reply.action_taken) void queries.invalidateQueries({ queryKey: ['runtime-control'] });
      const source = reply.intent === 'assistant_text'
        ? `AI advice · ${reply.data.provider} / ${reply.data.model} · no action performed`
        : reply.action_taken ? `Runtime result · ${reply.action_taken}` : 'Information';
      const assistant: Turn = { role: 'assistant', text: reply.response_text, source };
      setHistory(previous => [...previous, assistant].slice(-40));
      if (reply.intent === 'assistant_text') {
        context.current = [...context.current, { role: 'user', text: clean } as Turn, assistant].slice(-4);
      }
      if (reply.requires_confirmation) setPending(clean);
    } catch (error) {
      if (!mounted.current) return;
      if (controller.signal.aborted) setNotice('Request cancelled. Check runtime status for any control changes.');
      else {
        const detail = error instanceof ApiError ? (error.detail as { detail?: unknown })?.detail : null;
        setNotice(typeof detail === 'string' ? detail : 'Runtime unavailable. Connect to the local runtime and retry.');
      }
    } finally {
      if (abort.current === controller) abort.current = null;
      if (mounted.current) setBusy(false);
    }
  };

  return <div className="space-y-6">
    <div className="flex flex-wrap justify-between gap-3">
      <div><h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Javo companion</h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Text conversation and real runtime controls. Conversation stays in this tab until cleared or closed.</p></div>
      <Badge status="info">Local speech studio</Badge>
    </div>
    <Card variant="default">
      <p className="text-sm">Use the voice studio to record and review a transcript, or generate spoken text. Microphone access starts only when you choose Record. Wake word is unavailable.</p>
      <div className="mt-4 flex flex-wrap gap-4">
        <label className="text-sm">Provider
          <select aria-label="Companion provider" className="ml-2 rounded border p-2 bg-white dark:bg-slate-900" value={provider} disabled={busy} onChange={event => { setProvider(event.target.value); context.current = []; setHistory([]); setPending(null); }}>
            <option value="ollama">Ollama · local</option><option value="gemini">Gemini · cloud</option><option value="openai">OpenAI compatible · cloud</option>
          </select></label>
        <label className="text-sm">Language
          <select aria-label="Companion language" className="ml-2 rounded border p-2 bg-white dark:bg-slate-900" value={language} disabled={busy} onChange={event => setLanguage(event.target.value)}>
            <option value="hinglish">Hinglish</option><option value="hi">हिन्दी</option><option value="en">English</option>
          </select></label>
      </div>
      {provider !== 'ollama' && <p className="mt-3 text-sm text-amber-600 dark:text-amber-300">Sending a message sends its conversation context to the selected configured cloud provider. Zero-cost budgets block cloud generation. Choose Ollama for local conversation.</p>}
    </Card>
    <SpeechStudio onTranscript={setInput}/>
    <Card variant="default">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <h2 className="font-semibold">Conversation</h2>
        <Button variant="ghost" disabled={busy} leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => { setHistory([]); context.current = []; setPending(null); setNotice('Conversation cleared from this tab.'); }}>Clear conversation</Button>
      </div>
      <div role="log" aria-label="Companion conversation" aria-live="polite" className="space-y-3 max-h-96 overflow-y-auto">
        {history.length === 0 && <p className="text-sm text-slate-500">Ask for a caption, script or explanation. AI text does not execute account, publishing or approval actions.</p>}
        {history.map((turn, index) => <div key={index} className="flex gap-3 rounded-xl border border-slate-300 dark:border-white/10 p-3">
          {turn.role === 'user' ? <User className="h-5 w-5 shrink-0 text-cyan-600" /> : <Bot className="h-5 w-5 shrink-0 text-violet-500" />}
          <div className="min-w-0"><p className="text-xs text-slate-500 mb-1">{turn.role === 'user' ? 'You' : turn.source}</p>
            <p className="text-sm whitespace-pre-wrap break-words">{turn.text}</p></div>
        </div>)}
      </div>
      {notice && <p role="status" className="mt-3 text-sm text-amber-600 dark:text-amber-300">{notice}</p>}
      {pending && <div className="mt-3 flex flex-wrap gap-2"><Button disabled={busy} onClick={() => void send(pending, true)}>Confirm resume</Button><Button variant="ghost" onClick={() => setPending(null)}>Dismiss</Button></div>}
      <form onSubmit={event => { event.preventDefault(); void send(input); }} className="mt-4 flex gap-2">
        <input value={input} maxLength={8000} onChange={event => setInput(event.target.value)} disabled={busy}
          placeholder="Type a message…" aria-label="Companion message"
          className="min-w-0 flex-1 rounded-xl border border-slate-300 dark:border-white/20 bg-white dark:bg-slate-900 p-3 text-sm" />
        {busy ? <Button type="button" onClick={() => abort.current?.abort()} leftIcon={<Square className="h-4 w-4" />}>Cancel</Button>
          : <Button type="submit" disabled={!input.trim()} leftIcon={<Send className="h-4 w-4" />}>Send</Button>}
      </form>
      <div className="mt-4 flex flex-wrap gap-2">
        {['Runtime status', 'Pause autopilot', 'Resume autopilot', 'Emergency stop'].map(command => <Button key={command} variant="ghost" disabled={busy} onClick={() => void send(command)}>{command}</Button>)}
      </div>
    </Card>
  </div>;
};
