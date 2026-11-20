// Real built UI, saved encrypted settings, scoped grants and owner review.
// Audio bytes/transcript ONLY are labelled browser fixtures; real model smoke is separate.
const { chromium } = require(process.env.JAVO_PLAYWRIGHT_MODULE || 'playwright-core');
const assert = require('node:assert/strict');
const {randomUUID} = require('node:crypto');

(async () => {
  const browser = await chromium.launch({executablePath:process.env.JAVO_CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']});
  try {
    const context = await browser.newContext({permissions:['microphone'],viewport:{width:1400,height:1000}});
    const page = await context.newPage();
    const errors=[]; page.on('pageerror',e=>errors.push(e.message));
    const base = new URL(process.env.JAVO_SMOKE_URL).origin;
    const headers={Authorization:'Bearer '+process.env.JAVO_OWNER_ACCESS_TOKEN};
    const request = async (route,data,method='POST',extra=headers) => {
      const response=await page.request.fetch(base+route,{method,headers:extra,...(data===undefined?{}:{data})});
      assert(response.ok(), 'Actual API refused '+route+' with '+response.status()); return response.json();
    };
    const auth=async()=>{await page.getByLabel('Owner access token').fill(process.env.JAVO_OWNER_ACCESS_TOKEN);await page.getByRole('button',{name:'Connect / retry'}).click();await page.getByLabel('Owner access token').waitFor({state:'detached'});};
    await page.goto(process.env.JAVO_SMOKE_URL); await auth();
    await page.evaluate(()=>{location.hash='/voice';});
    await page.getByRole('heading',{name:'Voice studio',exact:true}).waitFor();
    await page.getByText('Local model setup',{exact:true}).click();
    await page.getByLabel('Pronunciation overrides',{exact:true}).fill('{"javo":"dʒɑːvoʊ"}');
    await page.getByRole('button',{name:'Save voice setup',exact:true}).click();
    await page.getByText('Voice configuration saved. Generate a short sample to test it.',{exact:true}).waitFor();
    await page.reload(); await auth();
    await page.getByText('Local model setup',{exact:true}).click();
    assert(JSON.parse(await page.getByLabel('Pronunciation overrides',{exact:true}).inputValue()).javo);
    // Browser fixtures avoid downloading models inside a UI test.
    await page.route('**/api/voice/capabilities',async route=>{const response=await route.fetch();const body=await response.json();await route.fulfill({json:{...body,text_to_speech:true,speech_to_text:true}});});
    let wave=Buffer.alloc(44+3200);wave.write('RIFF');wave.writeUInt32LE(wave.length-8,4);wave.write('WAVE',8);wave.write('fmt ',12);wave.writeUInt32LE(16,16);wave.writeUInt16LE(1,20);wave.writeUInt16LE(1,22);wave.writeUInt32LE(16000,24);wave.writeUInt32LE(32000,28);wave.writeUInt16LE(2,32);wave.writeUInt16LE(16,34);wave.write('data',36);wave.writeUInt32LE(3200,40);
    await page.route('**/api/voice/tts',route=>route.fulfill({contentType:'audio/wav',body:wave}));
    await page.route('**/api/voice/transcribe',route=>route.fulfill({json:{text:'Synthetic reviewed browser transcript.'}}));
    await page.reload(); await auth();
    await page.getByLabel('Speech effect').selectOption('radio');
    await page.getByRole('button',{name:'Generate voice',exact:true}).click();
    await page.getByLabel('Generated AI voice').waitFor();
    await page.waitForFunction(()=>document.querySelector('audio')?.readyState>=1);
    await page.getByLabel('Upload speech WAV').setInputFiles({name:'synthetic.wav',mimeType:'audio/wav',buffer:wave});
    await page.getByLabel('Review transcript',{exact:true}).waitFor();
    assert.equal(await page.getByLabel('Review transcript',{exact:true}).inputValue(),'Synthetic reviewed browser transcript.');
    await page.getByRole('button',{name:'Record microphone',exact:true}).click();
    await page.getByRole('button',{name:'Stop and transcribe',exact:true}).waitFor();
    await page.getByRole('button',{name:'Cancel audio operation',exact:true}).click();
    await page.getByRole('button',{name:'Record microphone',exact:true}).waitFor();
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Voice must fit mobile');
    await page.evaluate(()=>{location.hash='/integrations';});
    await page.getByLabel('Integration client').selectOption('n8n');
    await page.getByLabel('Grant label').fill('Browser n8n grant');
    await page.getByRole('checkbox',{name:'read workflows',exact:true}).check();
    await page.getByRole('checkbox',{name:'propose workflow',exact:true}).check();
    await page.getByRole('checkbox',{name:'read own results',exact:true}).check();
    await page.getByRole('button',{name:'Review client access',exact:true}).click();
    await page.getByRole('button',{name:'Create reviewed grant',exact:true}).click();
    const secret=await page.getByLabel('New integration token').inputValue();
    assert(secret.length>20);
    const start=randomUUID(),end=randomUUID();
    const saved=await request('/api/workflows/',{name:'Browser exact reviewed definition',nodes:[{id:start,node_type:'trigger',label:'Start',is_entry_point:true},{id:end,node_type:'end',label:'End'}],edges:[{source_node_id:start,target_node_id:end}]});
    const reply=await request('/api/integrations/mcp',{jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'javo_propose_workflow',arguments:{request_key:'browser_'+randomUUID(),title:'Browser review proposal',workflow_id:saved.id,expected_revision:saved.revision,fingerprint:saved.fingerprint,trigger_data:{brief:'Synthetic browser brief'}}}},'POST',{Authorization:'Bearer '+secret});
    assert(!reply.error);const proposal=JSON.parse(reply.result.content[0].text);
    await page.evaluate(()=>{location.hash='/approvals';});
    await page.getByRole('button',{name:'Review Browser review proposal',exact:true}).click();
    await page.getByText('Actual saved definition and prompts',{exact:true}).waitFor();
    await page.getByRole('button',{name:'Approve reviewed local run',exact:true}).click();
    await page.getByText(/Approved and queued actual run/).waitFor();
    const rows=await request('/api/integrations/proposals',undefined,'GET');
    assert.equal(rows.find(p=>p.id===proposal.id).status,'approved');
    await page.evaluate(()=>{location.hash='/integrations';});
    await page.getByRole('button',{name:'Revoke Browser n8n grant',exact:true}).click();
    await page.getByText('Client grant revoked. Pending proposals from this grant cannot be approved.',{exact:true}).waitFor();
    const refused=await page.request.post(base+'/api/integrations/mcp',{headers:{Authorization:'Bearer '+secret},data:{jsonrpc:'2.0',id:2,method:'tools/list'}});assert.equal(refused.status(),401);
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Integrations must fit mobile');
    await page.evaluate(()=>{location.hash='/studio';});
    await page.getByRole('heading',{name:'Creation studio',exact:true}).waitFor();
    await page.getByLabel('Generation prompt',{exact:true}).fill('Synthetic image brief.');
    assert(await page.getByRole('button',{name:'Review generation',exact:true}).isDisabled());
    await page.getByRole('button',{name:'Check selected generation setup',exact:true}).click();
    await page.getByText(/disabled|unavailable|not enabled/i).first().waitFor();
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Studio must fit mobile');
    if(process.env.JAVO_CREATOR_SCREENSHOT){await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:process.env.JAVO_CREATOR_SCREENSHOT,fullPage:true});}
    assert.deepEqual(errors,[]);
    console.log('CREATOR_BROWSER_SAVED_VOICE_SYNTHETIC_AUDIO_MIC_CANCEL_SCOPED_GRANT_EXACT_REVIEW_REVOKE_STUDIO_GUARD_MOBILE_OK');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
