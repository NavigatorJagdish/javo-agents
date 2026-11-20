import React, { useId, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Users } from 'lucide-react';
import { Card, Badge, Button, Modal } from '@javo/design-system';
import { apiRequest, ApiError, type AccountDto, type AccountPlatform, type BrandDto } from '../api/client';
import { useAppStore } from '../store/useAppStore';

const inputClass = 'w-full rounded-xl border border-slate-300 dark:border-white/20 bg-white dark:bg-[#0B1026] px-3 py-2 text-sm';
const platforms: AccountPlatform[] = ['youtube', 'instagram', 'facebook', 'twitter', 'tiktok', 'linkedin', 'pinterest', 'threads', 'telegram', 'other'];
function failureMessage(error: unknown): string {
  const detail = error instanceof ApiError ? (error.detail as { detail?: unknown })?.detail : null;
  return typeof detail === 'string' ? detail : 'The runtime did not confirm this change. Please retry.';
}
function Field({ label, children }: { label: string; children: React.ReactElement<{ id?: string }> }) {
  const id = useId();
  return <div className="space-y-1"><label htmlFor={id} className="block text-sm">{label}</label>{React.cloneElement(children, { id })}</div>;
}

function AccountForm({ account, onSaved }: { account?: AccountDto; onSaved: () => void }) {
  const [platform, setPlatform] = useState<AccountPlatform>(account?.platform ?? 'youtube');
  const [username, setUsername] = useState(account?.username ?? '');
  const [name, setName] = useState(account?.display_name ?? '');
  const save = useMutation({
    mutationFn: () => apiRequest<AccountDto>(account ? `/api/accounts/${encodeURIComponent(account.id)}` : '/api/accounts/', {
      method: account ? 'PUT' : 'POST',
      body: { ...(!account ? { platform } : {}), username, display_name: name || null },
    }),
    onSuccess: onSaved,
  });
  return <form className="space-y-4" onSubmit={e => { e.preventDefault(); save.mutate(); }}>
    {!account && <Field label="Platform"><select className={inputClass} value={platform} onChange={e => setPlatform(e.target.value as AccountPlatform)}>{platforms.map(p => <option key={p} value={p}>{p === 'twitter' ? 'X (Twitter)' : p}</option>)}</select></Field>}
    <Field label="Account handle"><input className={inputClass} required maxLength={128} value={username} onChange={e => setUsername(e.target.value)} /></Field>
    <Field label="Display name"><input className={inputClass} maxLength={256} value={name} onChange={e => setName(e.target.value)} /></Field>
    <p className="text-sm text-slate-500">This saves a local record. Official platform sign-in and live publishing are not available in this build.</p>
    {save.isError && <p role="alert" className="text-sm text-red-500">{failureMessage(save.error)}</p>}
    <Button type="submit" disabled={save.isPending}>{save.isPending ? 'Saving…' : 'Save account'}</Button>
  </form>;
}

function BrandForm({ account, initial }: { account: AccountDto; initial?: BrandDto }) {
  const [name, setName] = useState(initial?.brand_name ?? account.display_name ?? account.username);
  const [voice, setVoice] = useState(initial?.brand_voice ?? '');
  const [audience, setAudience] = useState(initial?.target_audience ?? '');
  const [pillars, setPillars] = useState(initial?.content_pillars?.join('\n') ?? '');
  const qc = useQueryClient();
  const addToast = useAppStore(s => s.addToast);
  const save = useMutation({
    mutationFn: () => apiRequest<BrandDto>(`/api/accounts/${encodeURIComponent(account.id)}/brand-profile`, {
      method: 'PUT', body: { brand_name: name, brand_voice: voice || null, target_audience: audience || null, content_pillars: pillars.split('\n').map(p => p.trim()).filter(Boolean) },
    }),
    onSuccess: async () => { await qc.invalidateQueries({ queryKey: ['account-brand', account.id] }); addToast('Brand profile saved', 'Your rules are saved for this account.', 'success'); },
  });
  return <form className="space-y-3" onSubmit={e => { e.preventDefault(); save.mutate(); }}>
    <Field label="Brand name"><input className={inputClass} required maxLength={128} value={name} onChange={e => setName(e.target.value)} /></Field>
    <Field label="Brand voice"><textarea className={inputClass} rows={3} maxLength={4000} value={voice} onChange={e => setVoice(e.target.value)} /></Field>
    <Field label="Target audience"><textarea className={inputClass} rows={2} maxLength={2000} value={audience} onChange={e => setAudience(e.target.value)} /></Field>
    <Field label="Content pillars (one per line, up to 20)"><textarea className={inputClass} rows={4} maxLength={4000} value={pillars} onChange={e => setPillars(e.target.value)} /></Field>
    {save.isError && <p role="alert" className="text-sm text-red-500">{failureMessage(save.error)}</p>}
    <Button type="submit" disabled={save.isPending}>{save.isPending ? 'Saving…' : 'Save brand profile'}</Button>
  </form>;
}

function BrandEditor({ account }: { account: AccountDto }) {
  const brand = useQuery({ queryKey: ['account-brand', account.id], queryFn: async () => {
    try { return await apiRequest<BrandDto>(`/api/accounts/${encodeURIComponent(account.id)}/brand-profile`); }
    catch (error) { if (error instanceof ApiError && error.status === 404) return null; throw error; }
  }, retry: false });
  if (brand.isPending) return <p>Loading saved brand profile…</p>;
  if (brand.isError) return <div role="alert"><p>{failureMessage(brand.error)}</p><Button onClick={() => brand.refetch()}>Retry brand profile</Button></div>;
  return <BrandForm account={account} initial={brand.data ?? undefined} />;
}

const credentialText: Record<AccountDto['credential_state'], string> = {
  none: 'No saved credentials',
  saved_unverified: 'Encrypted credentials saved; platform connection unverified',
  legacy_unprotected: 'Legacy credentials need protection',
  unavailable: 'Credential storage locked or unavailable',
};

export const Accounts: React.FC = () => {
  const [offset, setOffset] = useState(0);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<AccountDto | null>(null);
  const [brand, setBrand] = useState<AccountDto | null>(null);
  const [confirmation, setConfirmation] = useState<{ account: AccountDto; kind: 'credentials' | 'account' } | null>(null);
  const qc = useQueryClient();
  const addToast = useAppStore(s => s.addToast);
  const accounts = useQuery({ queryKey: ['saved-accounts', offset], queryFn: () => apiRequest<AccountDto[]>('/api/accounts/', { params: { limit: 50, offset } }), retry: false });
  const refresh = () => qc.invalidateQueries({ queryKey: ['saved-accounts'] });
  const protect = useMutation({
    mutationFn: (id: string) => apiRequest<AccountDto>(`/api/accounts/${encodeURIComponent(id)}/credentials/migrate`, { method: 'POST' }),
    onSuccess: async () => { await refresh(); addToast('Credential protection checked', 'The saved account still requires verified platform sign-in.', 'success'); },
  });
  const removal = useMutation({
    mutationFn: ({ account, kind }: { account: AccountDto; kind: 'credentials' | 'account' }) => apiRequest<void>(`/api/accounts/${encodeURIComponent(account.id)}${kind === 'credentials' ? '/credentials' : ''}`, { method: 'DELETE' }),
    onSuccess: async (_, { account, kind }) => {
      qc.removeQueries({ queryKey: ['account-brand', account.id] });
      setConfirmation(null); await refresh();
      addToast(kind === 'credentials' ? 'Saved credentials removed' : 'Account record removed', kind === 'credentials' ? 'Local copies removed. Platform access has not been revoked.' : 'The runtime confirmed removal.', 'success');
    },
  });
  function saved() { setCreating(false); setEditing(null); void refresh(); addToast('Account saved', 'The unconnected record is saved locally.', 'success'); }
  return <div className="space-y-6">
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div><h1 className="font-display text-2xl sm:text-3xl font-bold">Social Accounts &amp; Brand Profiles</h1><p className="mt-1 text-sm text-slate-500">Saved account records, brand rules and credential protection.</p></div>
      <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setCreating(true)}>Add account record</Button>
    </div>
    <Card><p className="text-sm">Official platform sign-in and live publishing are not available in this build. Saved credentials do not prove a working connection. No follower counts or platform results have been fetched.</p></Card>
    {accounts.isPending && <p>Loading saved accounts…</p>}
    {accounts.isError && <div role="alert"><p>{failureMessage(accounts.error)}</p><Button onClick={() => accounts.refetch()}>Retry accounts</Button></div>}
    {protect.isError && <p role="alert" className="text-red-500">{failureMessage(protect.error)}</p>}
    {accounts.data?.length === 0 && <Card><p>No saved accounts on this page. Add a record to save your brand rules.</p></Card>}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {accounts.data?.map(account => <Card key={account.id}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 break-words"><div className="flex items-center gap-2"><Users className="h-5 w-5 shrink-0" /><h2 className="font-semibold break-all">{account.display_name || account.username}</h2></div><p className="mt-1 text-sm break-all">{account.platform} · {account.username}</p></div>
          <Badge status="warning" size="sm">Not connected</Badge>
        </div>
        <p className="mt-4 text-sm">{credentialText[account.credential_state]}</p>
        {account.credential_state !== 'none' && <p className="mt-1 text-xs text-slate-500">Protection: {account.credentials_protection}. {account.credential_expires_at ? `Recorded expiry: ${new Date(account.credential_expires_at).toLocaleString()}.` : 'No verified expiry available.'}</p>}
        {account.credential_state === 'unavailable' && <p className="mt-2 text-sm">Recover the original Windows profile or configured key before changing credentials.</p>}
        <div className="mt-4 flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" onClick={() => setEditing(account)}>Edit account</Button>
          <Button size="sm" variant="secondary" onClick={() => setBrand(account)}>Brand profile</Button>
          {account.credential_state === 'legacy_unprotected' && <Button size="sm" disabled={protect.isPending || removal.isPending} onClick={() => protect.mutate(account.id)}>Protect legacy credentials</Button>}
          {account.credential_state !== 'none' && <Button size="sm" variant="ghost" disabled={removal.isPending} onClick={() => { removal.reset(); setConfirmation({ account, kind: 'credentials' }); }}>Remove saved credentials</Button>}
          <Button size="sm" variant="ghost" disabled={removal.isPending} onClick={() => { removal.reset(); setConfirmation({ account, kind: 'account' }); }}>Remove account</Button>
        </div>
      </Card>)}
    </div>
    <div className="flex items-center gap-3"><Button variant="secondary" disabled={offset === 0 || accounts.isPending} onClick={() => setOffset(Math.max(0, offset - 50))}>Previous accounts</Button><span className="text-sm">Page {offset / 50 + 1}</span><Button variant="secondary" disabled={accounts.data?.length !== 50 || accounts.isPending} onClick={() => setOffset(offset + 50)}>Next accounts</Button></div>
    <Modal open={creating || !!editing} onClose={() => { setCreating(false); setEditing(null); }} title={editing ? 'Edit saved account' : 'Add account record'}>{(creating || editing) && <AccountForm key={editing?.id ?? 'new'} account={editing ?? undefined} onSaved={saved} />}</Modal>
    <Modal open={!!brand} onClose={() => setBrand(null)} title="Account brand profile">{brand && <BrandEditor key={brand.id} account={brand} />}</Modal>
    <Modal open={!!confirmation} onClose={() => { if (!removal.isPending) setConfirmation(null); }} title={confirmation?.kind === 'credentials' ? 'Remove saved credentials?' : 'Remove account record?'}>
      <p className="text-sm mb-4">{confirmation?.kind === 'credentials' ? 'Remove saved local credentials for this account? This does not revoke access on the platform or erase older backups.' : 'Remove this unused account and its brand profile? Accounts with saved work or execution history must be retained; you can remove their credentials separately.'}</p>
      {removal.isError && <p role="alert" className="text-sm text-red-500 mb-3">{failureMessage(removal.error)}</p>}
      <Button disabled={removal.isPending || protect.isPending} onClick={() => confirmation && removal.mutate(confirmation)}>{removal.isPending ? 'Removing…' : confirmation?.kind === 'credentials' ? 'Confirm credential removal' : 'Confirm account removal'}</Button>
    </Modal>
  </div>;
};
