import React, {useState} from 'react';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {Button, Card, Modal} from '@javo/design-system';
import {apiMediaRequest, apiRequest} from '../api/client';
import {errorText} from '../components/SpeechStudio';

interface Configuration {enabled: boolean; base_url: string; image_checkpoint: string; video_unet: string; video_clip: string; video_vae: string; fingerprint: string}
interface Job {id: string; kind: string; status: string; message: string; model: string; artifact_ready: boolean; created_at: string; request: {prompt: string; seed: number}}
interface Trends {fetched_at: string; source: string; scope: string; items: {title: string; published_at: string | null; approximate_traffic_label: string | null}[]}
const inputClass = 'w-full p-2 rounded border bg-white dark:bg-slate-900 border-slate-300 dark:border-white/20';
export const Studio: React.FC = () => {
  const cache=useQueryClient();
  const [kind,setKind]=useState<'image'|'video'>('image'); const [prompt,setPrompt]=useState(''); const [negative,setNegative]=useState(''); const [seed,setSeed]=useState(0);
  const [country,setCountry]=useState('IN'); const [notice,setNotice]=useState(''); const [busy,setBusy]=useState(false);
  const [draft,setDraft]=useState<Configuration | null>(null); const [review,setReview]=useState<{kind:'image'|'video'; prompt:string; negative_prompt:string; seed:number; configuration_fingerprint:string; request_key:string} | null>(null);
  const [abandon,setAbandon]=useState<Job|null>(null);
  const configuration=useQuery({queryKey:['studio-configuration'],queryFn:()=>apiRequest<Configuration>('/api/studio/configuration'),retry:false});
  const jobs=useQuery({queryKey:['studio-jobs'],queryFn:()=>apiRequest<Job[]>('/api/studio/jobs'),retry:false});
  const trends=useQuery({queryKey:['studio-trends',country],queryFn:()=>apiRequest<Trends|null>('/api/studio/trends?country='+country),retry:false});
  const cfg=draft ?? configuration.data;
  async function action(work:()=>Promise<void>) {setBusy(true);setNotice('');try{await work();}catch(e){setNotice(errorText(e));}finally{setBusy(false);}}
  function update(key: keyof Configuration, value:string|boolean) {if(cfg)setDraft({...cfg,[key]:value});}
  async function download(job:Job) {const response=await apiMediaRequest('/api/studio/jobs/'+job.id+'/artifact');const url=URL.createObjectURL(await response.blob());const link=document.createElement('a');link.href=url;link.download='javo-'+job.kind+'-'+job.id+(response.headers.get('content-type')?.includes('png')?'.png':response.headers.get('content-type')?.includes('jpeg')?'.jpg':response.headers.get('content-type')?.includes('webp')?'.webp':response.headers.get('content-type')?.includes('webm')?'.webm':'.mp4');link.click();window.setTimeout(()=>URL.revokeObjectURL(url),1000);}
  return <section className="space-y-5 min-w-0">
    <h1 className="text-3xl font-bold">Creation studio</h1>
    <p>Create images or short videos through your compatible local ComfyUI service, and research source-labelled search trends. Voice presets/effects are in Voice.</p>
    <Card><p className="text-sm">This computer has a small local speech/text setup. Image/video generation needs a separately installed compatible service and licensed model files; GPU-heavy model performance has not been verified here. No model download, cloud account or paid fallback is activated by this screen.</p></Card>
    <details className="border rounded-xl p-4"><summary>Local image/video model setup</summary><div className="space-y-3 mt-3">
      {configuration.isError && <p role="alert">Creation settings unavailable.</p>}
      {cfg && <><label className="block"><input type="checkbox" checked={cfg.enabled} onChange={e=>update('enabled',e.target.checked)}/> Allow reviewed submissions to my local service</label>
      {([['base_url','Local ComfyUI URL'],['image_checkpoint','Image checkpoint name'],['video_unet','Wan2.1 text-to-video UNet name'],['video_clip','Wan text encoder name'],['video_vae','Wan VAE name']] as const).map(([key,label])=><label className="block text-sm" key={key}>{label}<input aria-label={label} className={inputClass} value={cfg[key]} onChange={e=>update(key,e.target.value)}/></label>)}
      <p className="text-xs">Use exact names from your installed service. Image uses the native checkpoint workflow at512×512. Video uses the native Wan2.1 path at832×480,49frames,16fps. Quality depends on the actual model; no “realistic” result is guaranteed by selecting a name.</p>
      <Button disabled={busy} onClick={()=>void action(async()=>{const {fingerprint,...body}=cfg;void fingerprint;await apiRequest('/api/studio/configuration',{method:'PUT',body});setDraft(null);await cache.invalidateQueries({queryKey:['studio-configuration']});setNotice('Creation settings saved. Check native nodes and model inventory before generating.');})}>Save creation setup</Button></>}
    </div></details>
    <Card><div className="space-y-3"><h2 className="text-xl font-semibold">Image &amp; video generation</h2>
      <label className="block text-sm">Output<select aria-label="Generation kind" className={inputClass} value={kind} disabled={busy} onChange={e=>setKind(e.target.value as 'image'|'video')}><option value="image">Image</option><option value="video">Short video</option></select></label>
      <Button variant="ghost" disabled={busy || !!draft} onClick={()=>void action(async()=>{const result=await apiRequest<{ready:boolean;message?:string}>('/api/studio/check/'+kind,{method:'POST'});setNotice(result.ready?'Required native nodes and selected model filenames are present. Actual generation is still unverified.':result.message ?? 'Setup unavailable.');})}>Check selected generation setup</Button>
      <label className="block text-sm">Describe the scene<textarea aria-label="Generation prompt" className={inputClass} maxLength={2000} rows={4} value={prompt} onChange={e=>setPrompt(e.target.value)}/></label>
      <label className="block text-sm">Avoid<textarea aria-label="Negative generation prompt" className={inputClass} maxLength={1000} rows={2} value={negative} onChange={e=>setNegative(e.target.value)}/></label>
      <label className="block text-sm">Seed<input aria-label="Generation seed" type="number" className={inputClass} min={0} max={4294967295} value={seed} onChange={e=>setSeed(Number(e.target.value))}/></label>
      <Button disabled={busy || !prompt.trim() || !configuration.data?.enabled || !!draft} onClick={()=>setReview({kind,prompt,negative_prompt:negative,seed,configuration_fingerprint:configuration.data!.fingerprint,request_key:crypto.randomUUID()})}>Review generation</Button>
      <p className="text-xs">Javo pause/stop blocks new submissions. An already submitted service job may continue there. Only its queued ID can be requested for removal; this app never sends a global interrupt that might stop someone else’s work.</p>
    </div></Card>
    <Card><h2 className="text-xl font-semibold">Saved generation receipts</h2>{jobs.isError&&<p role="alert">Generation history unavailable.</p>}{jobs.data?.length===0&&<p>No saved generations.</p>}
      {jobs.data?.map(job=><div key={job.id} className="border-b py-4 space-y-2"><h3 className="font-semibold">{job.kind} · {job.status}</h3><p className="text-sm whitespace-pre-wrap break-words">{job.request.prompt}</p><p className="text-xs break-all">{job.id} · {job.model} · {new Date(job.created_at).toLocaleString()}</p><p className="text-sm">{job.message}</p><div className="flex flex-wrap gap-2">
        {!['completed','failed','abandoned'].includes(job.status)&&<><Button disabled={busy} onClick={()=>void action(async()=>{await apiRequest('/api/studio/jobs/'+job.id+'/refresh',{method:'POST'});await cache.invalidateQueries({queryKey:['studio-jobs']});})}>Refresh {job.id.slice(0,8)}</Button><Button variant="ghost" disabled={busy} onClick={()=>void action(async()=>{await apiRequest('/api/studio/jobs/'+job.id+'/remove-queued',{method:'POST'});await cache.invalidateQueries({queryKey:['studio-jobs']});})}>Request queued removal</Button><Button variant="ghost" disabled={busy} onClick={()=>setAbandon(job)}>Stop tracking</Button></>}
        {job.artifact_ready&&<Button disabled={busy} onClick={()=>void action(()=>download(job))}>Download generated {job.kind}</Button>}
      </div></div>)}
    </Card>
    <Card><div className="space-y-3"><h2 className="text-xl font-semibold">Trend discovery</h2><p className="text-sm">An explicit refresh contacts Google’s official public search-trend feed with the country only. Your briefs and account data are not sent. A popular search is not proof of demand on YouTube or Instagram.</p>
      <label className="block text-sm">Country<select aria-label="Trend country" className={inputClass} value={country} onChange={e=>setCountry(e.target.value)}>{['IN','US','GB','CA','AU'].map(c=><option key={c}>{c}</option>)}</select></label>
      <Button disabled={busy} onClick={()=>void action(async()=>{await apiRequest('/api/studio/trends/refresh?country='+country,{method:'POST'});await cache.invalidateQueries({queryKey:['studio-trends',country]});setNotice('Official search-trend snapshot saved. Review the source and publication times.');})}>Refresh official trends</Button>
      {trends.isError&&<p role="alert">Saved trend snapshot unavailable.</p>}{trends.data===null&&<p>No saved snapshot for this country.</p>}
      {trends.data&&<><p className="text-xs">Fetched {new Date(trends.data.fetched_at).toLocaleString()} · <a className="underline" href={trends.data.source} target="_blank" rel="noreferrer noopener">Official source</a></p><p className="text-xs">{trends.data.scope}</p><ul className="space-y-3">{trends.data.items.map((item,i)=><li key={i} className="border-b pb-3"><p>{item.title}</p><p className="text-xs">{item.approximate_traffic_label??'Traffic unavailable'} · {item.published_at?new Date(item.published_at).toLocaleString():'Publication time unavailable'}</p><Button variant="ghost" disabled={busy} onClick={()=>{setPrompt('Create an original visual concept inspired by this search topic: '+item.title+'. Verify context and avoid inventing facts.');setNotice('Topic copied into the scene brief. Nothing was generated or published.');}}>Use topic in brief</Button></li>)}</ul></>}
    </div></Card>
    {notice&&<p role="status" className="text-sm text-amber-700 dark:text-amber-300">{notice}</p>}
    <Modal open={!!review} onClose={()=>{if(!busy)setReview(null);}} title="Review exact generation">{review&&<div className="space-y-3"><p>{review.kind} · seed {review.seed}</p><p className="whitespace-pre-wrap break-words">{review.prompt}</p><p>Avoid: {review.negative_prompt||'None'}</p><p className="text-xs break-all">{configuration.data?.base_url} · configuration {review.configuration_fingerprint}</p><p>This sends the brief to your configured local generator and stores its receipt/output. Confirm that the selected service and model license fit your intended use.</p><Button disabled={busy} onClick={()=>void action(async()=>{await apiRequest('/api/studio/jobs',{method:'POST',body:{...review,reviewed:true}});setReview(null);await cache.invalidateQueries({queryKey:['studio-jobs']});setNotice('Submission receipt saved. Inspect its actual status before assuming success.');})}>Confirm reviewed generation</Button></div>}</Modal>
    <Modal open={!!abandon} onClose={()=>setAbandon(null)} title="Stop tracking this request?"><p className="mb-3">The local generator may continue this job. Stopping tracking does not stop inference or certify cancellation. Inspect its queue before submitting a replacement.</p><Button disabled={busy} onClick={()=>void action(async()=>{await apiRequest('/api/studio/jobs/'+abandon!.id+'/abandon?confirmed=true',{method:'POST'});setAbandon(null);await cache.invalidateQueries({queryKey:['studio-jobs']});})}>Confirm stop tracking</Button></Modal>
  </section>;
};
