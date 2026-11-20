import React, {useState} from 'react';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {Card, Button, Modal} from '@javo/design-system';
import {apiRequest, apiMediaRequest} from '../api/client';
import {errorText} from '../components/SpeechStudio';

interface Item {id: string; repository: string; commit: string; license: string; archived: boolean; purpose: string; integration: string}
interface Grant {id: string; client: string; label: string; scopes: string[]; expires_at: string; revoked_at: string | null}
const scopes = ['read_status', 'read_goals', 'read_workflows', 'propose_workflow', 'read_own_results'];
export const Integrations: React.FC = () => {
  const cache = useQueryClient();
  const catalog = useQuery({queryKey: ['integration-catalog'], queryFn: () => apiRequest<{items: Item[]; message: string; policy: {memory_headroom_mb: number; max_local_workers: number}}>('/api/integrations/catalog'), retry: false});
  const grants = useQuery({queryKey: ['integration-grants'], queryFn: () => apiRequest<Grant[]>('/api/integrations/grants'), retry: false});
  const [client, setClient] = useState('hermes'); const [label, setLabel] = useState('My local client');
  const [selected, setSelected] = useState(['read_status']); const [hours, setHours] = useState(24);
  const [secret, setSecret] = useState(''); const [notice, setNotice] = useState(''); const [busy, setBusy] = useState(false); const [confirm, setConfirm] = useState(false);
  async function action(work: () => Promise<void>) {setBusy(true); setNotice(''); try {await work();} catch (e) {setNotice(errorText(e));} finally {setBusy(false);}}
  async function download(format: string) {
    const response = await apiMediaRequest('/api/integrations/exports/'+format);
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a'); link.href = url; link.download = 'javo-'+format+(format === 'aider' ? '.txt' : '.json'); link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <section className="space-y-5 min-w-0">
    <h1 className="text-3xl font-bold">Integrations &amp; reviewed tools</h1>
    <p>Connect an external client through a separate scoped token. It can read permitted data or propose a supported local workflow; owner approval remains in Javo.</p>
    <Card><p className="text-sm">{catalog.data?.message ?? 'Checking integration catalog…'}</p>
      <p className="mt-2 text-sm">Keep one heavy external runtime active at a time. Javo currently allows {catalog.data?.policy.max_local_workers ?? '…'} local workers and reserves {catalog.data?.policy.memory_headroom_mb ?? '…'}MiB memory headroom. External programs must also enforce their own limits.</p>
      <p className="mt-2 text-sm">No external tool receives the owner token, shell access, publishing rights or a paid budget from creating a grant. Do not paste tokens into prompts.</p>
    </Card>
    {catalog.isError && <p role="alert">Integration catalog could not be loaded. <button onClick={() => void catalog.refetch()}>Retry</button></p>}
    <div className="grid md:grid-cols-2 gap-4">{catalog.data?.items.map(item => <Card key={item.id}>
      <h2 className="font-semibold">{item.id}{item.archived ? ' · archived upstream' : ''}</h2><p className="text-sm mt-2">{item.purpose}</p>
      <p className="text-sm mt-2">{item.integration}</p><p className="text-xs mt-2 break-all">Reference pinned at {item.commit.slice(0,12)} · {item.license}</p>
      <p className="text-xs mt-2">Upstream runtime: not activated or verified by this catalog.</p>
      <a href={item.repository+'/tree/'+item.commit} target="_blank" rel="noreferrer noopener" className="inline-block underline mt-2 text-sm">View pinned source</a>
    </Card>)}</div>
    <Card><div className="space-y-3">
      <h2 className="text-xl font-semibold">Create a client grant</h2>
      <label className="block text-sm">Client<select aria-label="Integration client" value={client} onChange={e => setClient(e.target.value)} className="block w-full bg-transparent border rounded p-2">{catalog.data?.items.filter(i => i.id !== 'mcp-directory').map(i => <option key={i.id} value={i.id}>{i.id}</option>)}</select></label>
      <label className="block text-sm">Grant label<input aria-label="Grant label" className="block w-full bg-transparent border rounded p-2" maxLength={100} value={label} onChange={e => setLabel(e.target.value)}/></label>
      <label className="block text-sm">Expiry in hours<input aria-label="Grant lifetime" type="number" className="block bg-transparent border rounded p-2" min={1} max={168} value={hours} onChange={e => setHours(Number(e.target.value))}/></label>
      <div className="flex flex-wrap gap-4">{scopes.map(scope => <label className="text-sm" key={scope}><input type="checkbox" checked={selected.includes(scope)} onChange={e => setSelected(e.target.checked ? [...selected, scope] : selected.filter(s => s !== scope))}/> {scope.replaceAll('_',' ')}</label>)}</div>
      <p className="text-xs">Workflow reads share names/revision metadata; goal reads share goal titles. Proposal access cannot approve requests. Own-results access shares actual generated output for this same grant’s reviewed requests.</p>
      <Button disabled={busy || !label.trim() || selected.length === 0} onClick={() => setConfirm(true)}>Review client access</Button>
      {secret && <div className="border rounded p-3 space-y-2"><p>Copy this token once into the selected client’s protected credential settings. Closing this page discards this displayed copy.</p><input aria-label="New integration token" type="password" readOnly value={secret} className="w-full bg-transparent border p-2"/><div className="flex gap-2"><Button onClick={() => void navigator.clipboard.writeText(secret).then(() => setNotice('Token copied.')).catch(() => setNotice('Clipboard unavailable. Select and copy the token manually.'))}>Copy token</Button><Button variant="ghost" onClick={() => setSecret('')}>Hide token</Button></div></div>}
    </div></Card>
    <Card><h2 className="text-xl font-semibold">Saved grants</h2>{grants.isError && <p role="alert">Grants could not be loaded.</p>}{grants.data?.length === 0 && <p>No saved client grants.</p>}
      {grants.data?.map(grant => <div key={grant.id} className="border-b py-3 space-y-2"><p>{grant.label} · {grant.client} · {grant.revoked_at ? 'revoked' : new Date(grant.expires_at).getTime() <= Date.now() ? 'expired' : 'configured grant'}</p><p className="text-xs break-words">{grant.scopes.join(', ')} · expires {new Date(grant.expires_at).toLocaleString()}</p>{!grant.revoked_at && <Button variant="ghost" disabled={busy} onClick={() => void action(async () => {await apiRequest('/api/integrations/grants/'+grant.id+'/revoke',{method:'POST'}); setSecret(''); await cache.invalidateQueries({queryKey:['integration-grants']}); setNotice('Client grant revoked. Pending proposals from this grant cannot be approved.');})}>Revoke {grant.label}</Button>}</div>)}
    </Card>
    <Card><h2 className="text-xl font-semibold">Project handoff exports</h2><p className="text-sm mb-3">Exports contain the latest100 review proposals. They do not run Aider/Task Master, deploy an inbox, send email or certify completed work.</p><div className="flex flex-wrap gap-2">{['aider','task-master','agent-inbox'].map(format => <Button key={format} disabled={busy} onClick={() => void action(() => download(format))}>Export {format}</Button>)}</div></Card>
    {notice && <p role="status">{notice}</p>}
    <Modal open={confirm} onClose={() => setConfirm(false)} title="Review integration permissions"><div className="space-y-3"><p>Create a {hours}-hour grant for {client} with: {selected.join(', ')}?</p><p>Only share it with the selected trusted client. Reads may disclose saved private data to that client. No tool is started automatically.</p><Button disabled={busy} onClick={() => void action(async () => {const value=await apiRequest<{token:string}>('/api/integrations/grants',{method:'POST',body:{client,label,scopes:selected,lifetime_hours:hours}}); setSecret(value.token); setConfirm(false); await cache.invalidateQueries({queryKey:['integration-grants']});})}>Create reviewed grant</Button></div></Modal>
  </section>;
};
