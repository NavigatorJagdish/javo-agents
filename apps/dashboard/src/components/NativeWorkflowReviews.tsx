import React, {useState} from 'react';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {Button, Card, Modal} from '@javo/design-system';
import {apiRequest} from '../api/client';
import {errorText} from './SpeechStudio';

interface Review {id:string;workflow_name:string;execution_id:string;status:string;revision:number;waiting:boolean;execution_status:string;expires_at:string}
interface Preview {id:string;revision:number;fingerprint:string;approvable:boolean;definition:unknown;checkpoint:{instructions:string;input:unknown;previous_output:string;workflow_revision:number}}
export const NativeWorkflowReviews: React.FC = () => {
  const cache=useQueryClient();
  const list=useQuery({queryKey:['native-workflow-reviews'],queryFn:()=>apiRequest<Review[]>('/api/workflows/approvals'),retry:false,refetchInterval:5000});
  const [selected,setSelected]=useState<Review|null>(null); const [busy,setBusy]=useState(false);const [notice,setNotice]=useState('');
  const preview=useQuery({queryKey:['native-workflow-review',selected?.id],enabled:!!selected,queryFn:()=>apiRequest<Preview>('/api/workflows/approvals/'+selected!.id),retry:false,staleTime:0});
  async function decide(decision:'approve'|'reject') {
    if(!preview.data)return;setBusy(true);setNotice('');
    try {const p=preview.data;await apiRequest('/api/workflows/approvals/'+p.id+'/decision',{method:'POST',body:{expected_revision:p.revision,fingerprint:p.fingerprint,decision}});setSelected(null);await cache.invalidateQueries({queryKey:['native-workflow-reviews']});await cache.invalidateQueries({queryKey:['workflow-runs']});setNotice(decision==='approve'?'Continuation queued. Completed steps will not replay. Inspect the actual run outcome in Workflows.':'Checkpoint rejected; run cancelled.');}
    catch(e){setNotice(errorText(e));}finally{setBusy(false);}
  }
  return <div className="space-y-3"><h2 className="text-xl font-semibold">Workflow checkpoints</h2><p className="text-sm">Review an actual intermediate draft before the workflow continues. Waiting is saved and releases the worker. Approval queues continuation; runtime pause still applies.</p>
    {list.isError&&<p role="alert">Workflow checkpoint inbox unavailable.</p>}{list.data?.length===0&&<Card>No saved workflow checkpoints.</Card>}
    {list.data?.map(item=><Card key={item.id}><div className="space-y-2"><h3 className="font-semibold">{item.workflow_name}</h3><p className="text-sm">{item.status} · run {item.execution_status}</p><p className="text-xs break-all">{item.execution_id} · expires {new Date(item.expires_at).toLocaleString()}</p>{item.waiting&&<Button disabled={busy} onClick={()=>setSelected(item)}>Review checkpoint {item.workflow_name}</Button>}</div></Card>)}
    {notice&&<p role="status">{notice}</p>}
    <Modal open={!!selected} onClose={()=>{if(!busy)setSelected(null);}} title="Review saved workflow checkpoint"><div className="space-y-3">
      {preview.isError&&<p role="alert">Checkpoint could not be verified. Reload its current receipt.</p>}
      {preview.data&&<><p>Saved workflow revision {preview.data.checkpoint.workflow_revision}</p><p className="whitespace-pre-wrap break-words">{preview.data.checkpoint.instructions}</p><h3 className="font-semibold">Actual draft for review</h3><pre className="text-xs whitespace-pre-wrap break-words max-h-64 overflow-auto">{preview.data.checkpoint.previous_output||'No text output before this checkpoint.'}</pre><details><summary>Exact saved definition and input</summary><pre className="text-xs whitespace-pre-wrap break-all max-h-64 overflow-auto">{JSON.stringify({definition:preview.data.definition,input:preview.data.checkpoint.input},null,2)}</pre></details>{!preview.data.approvable&&<p role="alert">Checkpoint expired, changed, cancelled or archived. Approval is unavailable; reject or cancel and review a fresh run.</p>}<div className="flex flex-wrap gap-3"><Button disabled={busy||!preview.data.approvable} onClick={()=>void decide('approve')}>Approve checkpoint continuation</Button><Button variant="ghost" disabled={busy} onClick={()=>void decide('reject')}>Reject checkpoint</Button></div></>}
    </div></Modal>
  </div>;
};
