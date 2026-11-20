import React, {useEffect, useRef, useState} from 'react';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {Button, Card} from '@javo/design-system';
import {ApiError, apiMediaRequest, apiRequest} from '../api/client';

interface Capabilities { text_to_speech: boolean; speech_to_text: boolean; message: string; voices: {id: string; name: string; language: string}[]; effects: string[] }
interface Configuration {tts_model_dir: string; asr_model_dir: string; pronunciations?: Record<string,string>}
export function errorText(error: unknown) {
  const detail = error instanceof ApiError ? (error.detail as {detail?: unknown})?.detail : null;
  return typeof detail === 'string' ? detail : error instanceof Error && error.name === 'AbortError' ? 'Operation cancelled.' : 'Operation unavailable. Check setup and runtime controls.';
}
const style = 'w-full rounded-lg border border-slate-300 dark:border-white/20 bg-white dark:bg-slate-900 p-2 text-sm';

function encodeWave(chunks: Float32Array[], rate: number) {
  const length = chunks.reduce((total, chunk) => total + chunk.length, 0);
  const data = new ArrayBuffer(44 + length * 2); const view = new DataView(data);
  const word = (offset: number, value: string) => [...value].forEach((ch, i) => view.setUint8(offset + i, ch.charCodeAt(0)));
  word(0, 'RIFF'); view.setUint32(4, 36 + length * 2, true); word(8, 'WAVE'); word(12, 'fmt ');
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, rate, true); view.setUint32(28, rate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  word(36, 'data'); view.setUint32(40, length * 2, true); let offset = 44;
  chunks.forEach(chunk => chunk.forEach(sample => {view.setInt16(offset, Math.max(-1, Math.min(1, sample)) * 32767, true); offset += 2;}));
  return new Blob([data], {type: 'audio/wav'});
}

export const SpeechStudio: React.FC<{onTranscript?: (text: string) => void}> = ({onTranscript}) => {
  const queries = useQueryClient();
  const capabilities = useQuery({queryKey: ['voice-capabilities'], queryFn: () => apiRequest<Capabilities>('/api/voice/capabilities'), retry: false});
  const [configuration, setConfiguration] = useState<Configuration>({tts_model_dir: '', asr_model_dir: ''});
  const [text, setText] = useState('Hello! Welcome to Javo. Let’s create something useful today.');
  const [voice, setVoice] = useState('af_heart'); const [speed, setSpeed] = useState(1); const [effect, setEffect] = useState('natural');
  const [recognition, setRecognition] = useState('auto'); const [transcript, setTranscript] = useState('');
  const [notice, setNotice] = useState(''); const [busy, setBusy] = useState(false); const [recording, setRecording] = useState(false);
  const [audio, setAudio] = useState(''); const audioUrl = useRef(''); const controller = useRef<AbortController | null>(null);
  const [pronunciations, setPronunciations] = useState('{"javo":"dʒɑːvoʊ"}');
  const live = useRef(true); const stopRecorder = useRef<((discard?: boolean) => void) | null>(null);
  const captureAttempt = useRef(0);
  useEffect(() => {
    live.current = true;
    void apiRequest<Configuration>('/api/voice/configuration').then(value => {if (live.current) {setConfiguration(value);setPronunciations(JSON.stringify(value.pronunciations ?? {},null,2));}}).catch(() => {if (live.current) setNotice('Voice setup could not be loaded.');});
    return () => { live.current = false; captureAttempt.current++; controller.current?.abort(); stopRecorder.current?.(true); URL.revokeObjectURL(audioUrl.current); };
  }, []);
  async function perform(operation: (signal: AbortSignal) => Promise<void>) {
    if (controller.current) return;
    const current = new AbortController(); controller.current = current; setBusy(true); setNotice('');
    try { await operation(current.signal); }
    catch (error) {if (live.current) setNotice(errorText(error));}
    finally {if (controller.current === current) controller.current = null; if (live.current) setBusy(false);}
  }
  const transcribe = (blob: Blob) => perform(async signal => {
    const form = new FormData(); form.append('file', blob, 'recording.wav'); form.append('language', recognition);
    const response = await apiMediaRequest('/api/voice/transcribe', {method: 'POST', body: form, signal});
    const result: {text: string} = await response.json();
    if (live.current && !signal.aborted) {setTranscript(result.text); setNotice(result.text ? 'Review the transcript. Nothing has been sent as a command.' : 'No clear speech detected. Try a shorter, clearer recording.');}
  });
  async function record() {
    if (!navigator.mediaDevices?.getUserMedia) {setNotice('Microphone access is unavailable in this browser. Upload a mono WAV instead.'); return;}
    setNotice(''); setBusy(true);
    const attempt = ++captureAttempt.current;
    let stream: MediaStream | undefined; let context: AudioContext | undefined;
    try {
      stream = await navigator.mediaDevices.getUserMedia({audio: {channelCount: 1, echoCancellation: true}, video: false});
      if (!live.current || attempt !== captureAttempt.current) {stream.getTracks().forEach(track => track.stop()); return;}
      context = new AudioContext({sampleRate: 16000}); await context.resume();
      if (!live.current || attempt !== captureAttempt.current) {stream.getTracks().forEach(track => track.stop()); await context.close(); return;}
      const source = context.createMediaStreamSource(stream); const processor = context.createScriptProcessor(4096, 1, 1);
      const mute = context.createGain(); mute.gain.value = 0; source.connect(processor); processor.connect(mute); mute.connect(context.destination);
      const chunks: Float32Array[] = []; let samples = 0; let finished = false;
      const rate = context.sampleRate;
      const stop = (discard = false) => {
        if (finished) return; finished = true; clearTimeout(timer); processor.onaudioprocess = null;
        processor.disconnect(); source.disconnect(); mute.disconnect(); stream!.getTracks().forEach(track => track.stop()); void context!.close();
        stopRecorder.current = null;
        if (live.current) {setRecording(false); setBusy(false); if (!discard && samples) void transcribe(encodeWave(chunks, rate));}
      };
      const timer = window.setTimeout(() => stop(), 30000);
      processor.onaudioprocess = event => {
        const remaining = Math.max(0, rate * 30 - samples);
        const chunk = event.inputBuffer.getChannelData(0).slice(0, remaining); samples += chunk.length; chunks.push(chunk);
        if (samples >= rate * 30) stop();
      };
      stopRecorder.current = stop; setRecording(true);
    } catch {stream?.getTracks().forEach(track => track.stop()); void context?.close(); if (live.current) {setBusy(false); setNotice('Microphone permission or recording failed. Check device permissions or upload a mono WAV.');}}
  }
  const cfg = capabilities.data;
  return <Card><div className="space-y-4">
    <h2 className="text-xl font-semibold">Voice studio</h2>
    <p className="text-sm">Local neural speech with English and Hindi presets. Speech is AI-generated. Effects customize the sound; training a new voice is not enabled.</p>
    <p role="status" className="text-sm">{capabilities.isError ? 'Voice availability could not be checked.' : `Speech: ${cfg?.text_to_speech ? 'model files ready' : 'setup needed'} · Recognition: ${cfg?.speech_to_text ? 'model files ready' : 'setup needed'}`}</p>
    <details><summary>Local model setup</summary><div className="mt-3 space-y-3">
      <p className="text-sm">Choose trusted extracted Kokoro int8 multilingual v1.0 and Whisper tiny directories. Saving does not download or certify a model.</p>
      <label className="block text-sm">Kokoro model directory<input aria-label="Kokoro model directory" className={style} value={configuration.tts_model_dir} onChange={e => setConfiguration({...configuration, tts_model_dir: e.target.value})}/></label>
      <label className="block text-sm">Whisper model directory<input aria-label="Whisper model directory" className={style} value={configuration.asr_model_dir} onChange={e => setConfiguration({...configuration, asr_model_dir: e.target.value})}/></label>
      <label className="block text-sm">Pronunciation overrides (word → IPA JSON)<textarea aria-label="Pronunciation overrides" className={style} rows={3} maxLength={16000} value={pronunciations} onChange={e=>setPronunciations(e.target.value)}/></label>
      <p className="text-xs">An optional local word dictionary customizes pronunciation. The original Hindi frontend is approximate; this is not voice-model training.</p>
      <Button disabled={busy} onClick={() => void perform(async signal => {let words: unknown; try {words=JSON.parse(pronunciations);} catch {setNotice('Pronunciation overrides must be a JSON object of words and IPA strings.');return;} await apiRequest('/api/voice/configuration', {method: 'PUT', body: {...configuration,pronunciations:words}, signal}); await queries.invalidateQueries({queryKey: ['voice-capabilities']}); if (live.current) setNotice('Voice configuration saved. Generate a short sample to test it.');})}>Save voice setup</Button>
    </div></details>
    <div className="grid sm:grid-cols-3 gap-3">
      <label className="text-sm">Voice<select aria-label="Speech voice" className={style} value={voice} disabled={busy} onChange={e => setVoice(e.target.value)}>{cfg?.voices.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}</select></label>
      <label className="text-sm">Effect<select aria-label="Speech effect" className={style} value={effect} disabled={busy} onChange={e => setEffect(e.target.value)}>{(cfg?.effects ?? ['natural']).map(e => <option key={e}>{e}</option>)}</select></label>
      <label className="text-sm">Speed {speed.toFixed(2)}×<input aria-label="Speech speed" type="range" min="0.75" max="1.5" step="0.05" value={speed} disabled={busy} onChange={e => setSpeed(Number(e.target.value))}/></label>
    </div>
    <label className="block text-sm">Text to speak<textarea aria-label="Text to speak" className={style} rows={3} maxLength={800} value={text} onChange={e => setText(e.target.value)}/></label>
    <p className="text-xs">Deep/bright effects shift pitch and duration together. Hindi presets work best with Devanagari; mixed Hinglish pronunciation needs review.</p>
    <Button disabled={busy || !cfg?.text_to_speech || !text.trim()} onClick={() => void perform(async signal => {
      const response = await apiMediaRequest('/api/voice/tts', {method: 'POST', signal, headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text, voice, speed, effect})});
      const blob = await response.blob(); if (!live.current || signal.aborted) return;
      URL.revokeObjectURL(audioUrl.current); audioUrl.current = URL.createObjectURL(blob); setAudio(audioUrl.current); setNotice('Audio generated locally. Play or download the AI voice.');
    })}>Generate voice</Button>
    {audio && <div className="space-y-2"><audio controls src={audio} aria-label="Generated AI voice" className="w-full"/><a className="underline" href={audio} download="javo-ai-voice.wav">Download WAV</a></div>}
    <div className="border-t pt-4 space-y-3">
      <h3 className="font-semibold">Record, review, then send</h3>
      <p className="text-sm">Record up to30 seconds or upload mono16-bit PCM WAV. The local runtime transcribes it; a transcript never executes a command automatically.</p>
      <label className="block text-sm">Recognition language<select aria-label="Recognition language" className={style} value={recognition} disabled={busy} onChange={e => setRecognition(e.target.value)}><option value="auto">Auto · English/Hindi/Hinglish</option><option value="en">English</option><option value="hi">Hindi</option></select></label>
      <div className="flex flex-wrap gap-3">{recording ? <Button onClick={() => stopRecorder.current?.()}>Stop and transcribe</Button> : <Button disabled={busy || !cfg?.speech_to_text} onClick={() => void record()}>Record microphone</Button>}
      <label className="text-sm">Upload WAV<input aria-label="Upload speech WAV" type="file" accept=".wav,audio/wav" disabled={busy || !cfg?.speech_to_text} onChange={e => {const file = e.target.files?.[0]; if (file && file.size <= 3 * 1024 * 1024) void transcribe(file); else setNotice('Use a WAV smaller than3MiB.'); e.target.value = '';}}/></label></div>
      {transcript && <><label className="block text-sm">Review transcript<textarea aria-label="Review transcript" className={style} value={transcript} onChange={e => setTranscript(e.target.value)} maxLength={8000}/></label>{onTranscript && <Button onClick={() => onTranscript(transcript)}>Use transcript in message</Button>}</>}
    </div>
    {busy && <Button variant="ghost" onClick={() => {captureAttempt.current++; stopRecorder.current?.(true); controller.current?.abort(); setBusy(false);}}>Cancel audio operation</Button>}
    {notice && <p role="status" className="text-sm text-amber-700 dark:text-amber-300">{notice}</p>}
  </div></Card>;
};
