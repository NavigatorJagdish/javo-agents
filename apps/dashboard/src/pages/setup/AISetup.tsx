import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { BrainCircuit } from 'lucide-react';
import { apiRequest } from '../../api/client';
import { ProviderEditor, type ProviderInfo } from '../../components/ProviderEditor';
import { LocalModelCheck } from '../../components/LocalModelCheck';
import { SetupStepCard } from './SetupStepCard';

export const AISetup: React.FC = () => {
  const providers = useQuery({ queryKey: ['runtime-providers'], queryFn: () => apiRequest<ProviderInfo[]>('/api/settings/ai-providers'), retry: false });
  const storage = useQuery({ queryKey: ['provider-storage'], queryFn: () => apiRequest<{ available: boolean }>('/api/settings/provider-storage'), retry: false });
  const local = providers.data?.find(provider => provider.name === 'ollama');
  return <SetupStepCard title="AI provider setup" subtitle="Save the local provider configuration, then check its model list." icon={<BrainCircuit className="h-6 w-6" />} prevPath="/setup/hardware" nextPath="/setup/folder">
    {providers.isPending && <p>Loading saved configuration…</p>}
    {(providers.isError || storage.isError) && <p role="alert">Saved configuration is unavailable. Check the runtime or recover its original encryption key.</p>}
    {storage.data?.available === false && <p role="alert">Encrypted storage is locked or unavailable. Configuration changes are disabled.</p>}
    {local && <ProviderEditor key={local.name} provider={local} available={storage.data?.available === true} onSaved={async () => { await providers.refetch(); }} />}
    <LocalModelCheck key={JSON.stringify(local)} />
    <p className="text-sm">Models must be installed separately. Cloud execution remains disabled; no automatic paid fallback is enabled.</p>
    <Link to="/settings" className="text-cyan-600 dark:text-cyan-300 underline">Open all provider settings</Link>
  </SetupStepCard>;
};
