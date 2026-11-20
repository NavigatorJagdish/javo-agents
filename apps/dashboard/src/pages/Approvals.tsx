import React, {useState} from 'react';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {Button, Card, Modal} from '@javo/design-system';
import {apiRequest} from '../api/client';
import {errorText} from '../components/SpeechStudio';
import {NativeWorkflowReviews} from '../components/NativeWorkflowReviews';

interface Proposal {id: string; title: string; status: string; revision: number; execution_id: string | null; expires_at: string; payload: {workflow_id: string; expected_revision: number; fingerprint: string; trigger_data: Record<string,unknown>}}
export const Approvals: React.FC = () => {
  const cache = useQueryClient();
  const inbox = useQuery({queryKey: ['integration-proposals'], queryFn: () => apiRequest<Proposal[]>('/api/integrations/proposals'), retry: false, refetchInterval: 5000});
  const [review, setReview] = useState<Proposal | null>(null); const [busy, setBusy] = useState(false); const [notice, setNotice] = useState('');
  const preview=useQuery({queryKey:['proposal-preview',review?.id],enabled:!!review,queryFn:()=>apiRequest<{definition:unknown;matches_reviewed_snapshot:boolean}>('/api/integrations/proposals/'+review!.id+'/preview'),retry:false,staleTime:0});
  async function decide(item: Proposal, decision: 'approve'|'reject') {
    setBusy(true); setNotice('');
    try {const result = await apiRequest<Proposal>('/api/integrations/proposals/'+item.id+'/review',{method:'POST',body:{expected_revision:item.revision,decision}}); setReview(null); await cache.invalidateQueries({queryKey:['integration-proposals']}); setNotice(result.execution_id ? 'Approved and queued actual run '+result.execution_id+'. Inspect Workflows for the execution outcome.' : 'Proposal rejected. No run was queued.');}
    catch(e) {setNotice(errorText(e));} finally {setBusy(false);}
  }
  return <section className="space-y-5"><h1 className="text-3xl font-bold">Review inbox</h1><p>Actual saved requests from scoped integration clients. Approval queues the exact supported local-text workflow; it does not resume the runtime, publish or authorize other actions.</p>
    <p className="text-sm">Content preview approvals remain in Content. Email drafts, paid actions, arbitrary code and broader approval types are not connected here.</p>
    <NativeWorkflowReviews/>
    {inbox.isError && <p role="alert">Review inbox unavailable. <button onClick={() => void inbox.refetch()}>Retry</button></p>}
    {inbox.data?.length === 0 && <Card>No saved integration proposals. Clients can propose a saved executable workflow after receiving an explicit grant.</Card>}
    {inbox.data?.map(item => <Card key={item.id}><div className="space-y-3"><h2 className="font-semibold">{item.title}</h2><p>{item.status} · revision {item.revision}</p><p className="text-xs break-all">Workflow {item.payload.workflow_id} · saved revision {item.payload.expected_revision} · expires {new Date(item.expires_at).toLocaleString()}</p>{item.execution_id && <p className="text-xs break-all">Actual run: {item.execution_id}. Review its final status in Workflows.</p>}{item.status === 'pending' && <div className="flex gap-3"><Button disabled={busy} onClick={() => setReview(item)}>Review {item.title}</Button><Button variant="ghost" disabled={busy} onClick={() => void decide(item,'reject')}>Reject {item.title}</Button></div>}</div></Card>)}
    {notice && <p role="status">{notice}</p>}
    <Modal open={!!review} onClose={() => {if(!busy)setReview(null);}} title="Review exact proposed run">{review && <div className="space-y-3"><p>{review.title} · saved workflow revision {review.payload.expected_revision}</p><p className="text-xs break-all">Fingerprint: {review.payload.fingerprint}</p><h3 className="font-semibold">Proposed input</h3><pre className="text-xs whitespace-pre-wrap break-all max-h-40 overflow-auto">{JSON.stringify(review.payload.trigger_data,null,2)}</pre><h3 className="font-semibold">Actual saved definition and prompts</h3>{preview.isError&&<p role="alert">Saved definition could not be loaded.</p>}{preview.data&&<pre className="text-xs whitespace-pre-wrap break-all max-h-60 overflow-auto">{JSON.stringify(preview.data.definition,null,2)}</pre>}{preview.data&&!preview.data.matches_reviewed_snapshot&&<p role="alert">Workflow changed. Reject this stale proposal and request a fresh one.</p>}<p>Approval queues this exact saved snapshot and input. AI outputs are saved locally. A changed workflow, revoked source grant, expired proposal or repeated decision is refused.</p><Button disabled={busy||!preview.data?.matches_reviewed_snapshot} onClick={() => void decide(review,'approve')}>Approve reviewed local run</Button></div>}</Modal>
  </section>;
};
