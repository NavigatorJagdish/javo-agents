import { useMutation } from '@tanstack/react-query';
import { Button } from '@javo/design-system';
import { apiRequest } from '../api/client';

interface LocalModelStatus {
  status: 'available' | 'model_missing' | 'disabled' | 'unavailable' | 'invalid_configuration';
  selected_model: string | null;
  available_models: string[];
  more_models: boolean;
  message: string;
  checked_at: string;
  generation_verified: false;
}

export function LocalModelCheck() {
  const check = useMutation({ mutationFn: () => apiRequest<LocalModelStatus>('/api/settings/ai-providers/ollama/check', { method: 'POST' }) });
  return <div className="space-y-3 rounded-xl border border-slate-300 dark:border-white/20 p-4">
    <h3 className="font-semibold">Local model availability</h3>
    <p className="text-sm">Read the model list from the saved loopback Ollama endpoint. This check does not download a model, generate text or send a cloud AI request.</p>
    <Button disabled={check.isPending} onClick={() => check.mutate()}>{check.isPending ? 'Checking local model…' : 'Check saved local model'}</Button>
    {check.isError && <p role="alert">The runtime could not complete this check. Reconnect and retry.</p>}
    {check.data && <div role="status" className="text-sm space-y-2 break-words">
      <p>Local model check: {check.data.status.replaceAll('_', ' ')}</p>
      <p>{check.data.message}</p>
      <p>Saved model: {check.data.selected_model ?? 'Unavailable'}</p>
      <p>Reported models: {check.data.available_models.length ? check.data.available_models.join(', ') : 'None reported'}{check.data.more_models ? ' (first 100 shown)' : ''}</p>
      <p className="text-xs text-slate-500">Checked {new Date(check.data.checked_at).toLocaleString()}. A listed model is not a successful generation or hardware benchmark.</p>
    </div>}
  </div>;
}
