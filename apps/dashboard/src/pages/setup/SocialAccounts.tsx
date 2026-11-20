import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Share2 } from 'lucide-react';
import { apiRequest, type AccountDto } from '../../api/client';
import { SetupStepCard } from './SetupStepCard';

export const SocialAccounts: React.FC = () => {
  const accounts = useQuery({ queryKey: ['setup-accounts'], queryFn: () => apiRequest<AccountDto[]>('/api/accounts/', { params: { limit: 50 } }), retry: false });
  return <SetupStepCard title="Social account records" subtitle="Official platform sign-in is not available in this build." icon={<Share2 className="h-6 w-6" />} prevPath="/setup/folder" nextPath="/setup/brand">
    <p className="text-sm">You can save local account records and brand profiles in Accounts. Adding a record does not authorize platform access or enable live publishing.</p>
    {accounts.isPending && <p>Checking saved records…</p>}
    {accounts.isError && <p role="alert">Saved records could not be loaded. Check the local runtime and retry in Accounts.</p>}
    {accounts.data && <p className="text-sm">{accounts.data.length === 50 ? 'At least 50' : accounts.data.length} saved records. No platform connections are verified by this build.</p>}
    <Link to="/accounts" className="inline-block text-cyan-600 dark:text-cyan-300 underline">Open Accounts</Link>
    <p className="text-xs text-slate-500">You may continue the guide without connecting a platform.</p>
  </SetupStepCard>;
};
