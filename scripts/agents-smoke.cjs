// Actual saved job queue/worker and UI. No model or social platform calls.
const { chromium } = require(process.env.JAVO_PLAYWRIGHT_MODULE || 'playwright-core');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.JAVO_CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    const base = new URL(process.env.JAVO_SMOKE_URL).origin;
    const created = await fetch(base+'/api/goals/', {method:'POST', headers:{'Content-Type':'application/json',Authorization:'Bearer '+process.env.JAVO_OWNER_ACCESS_TOKEN}, body:JSON.stringify({title:'Agent saved goal fixture'})});
    assert.equal(created.status, 201);
    const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.JAVO_SMOKE_URL);
    await page.getByLabel('Owner access token').fill(process.env.JAVO_OWNER_ACCESS_TOKEN);
    await page.getByRole('button', { name:'Connect / retry' }).click();
    await page.getByRole('heading', { name:'Local runtime',exact:true }).waitFor();
    await page.getByRole('button', { name:'AI Team',exact:true }).click();
    await page.getByRole('button', { name:'Inspect Budget Guardian',exact:true }).click();
    await page.getByRole('button', { name:'Queue saved summary',exact:true }).click();
    await page.getByText('Execution: queued',{exact:true}).waitFor();
    await page.getByRole('button', { name:'Cancel operation',exact:true }).click();
    await page.getByText('Execution: cancelled',{exact:true}).waitFor();
    await page.getByRole('button',{name:'Close modal',exact:true}).click();
    await page.getByRole('button',{name:'Autopilot: OFF',exact:true}).click();
    await page.getByRole('button',{name:'Autopilot: ON',exact:true}).waitFor();
    await page.getByRole('button',{name:'Inspect Budget Guardian',exact:true}).click();
    await page.getByRole('button',{name:'Queue saved summary',exact:true}).click();
    await page.getByText('Execution: completed',{exact:true}).waitFor();
    await page.getByText('View saved result',{exact:true}).click();
    await page.getByText('Completed AI requests: 0',{exact:true}).waitFor();
    await page.getByRole('button',{name:'Close modal',exact:true}).click();
    await page.getByRole('button',{name:'Inspect Goal Persistence',exact:true}).click();
    await page.getByLabel('Saved goal',{exact:true}).selectOption({label:'Agent saved goal fixture'});
    await page.getByRole('button',{name:'Queue saved summary',exact:true}).click();
    await page.getByText('Execution: completed',{exact:true}).waitFor();
    await page.getByText('View saved result',{exact:true}).click();
    await page.getByRole('heading',{name:'Agent saved goal fixture',exact:true}).waitFor();
    await page.reload();
    await page.getByLabel('Owner access token').fill(process.env.JAVO_OWNER_ACCESS_TOKEN);
    await page.getByRole('button',{name:'Connect / retry'}).click();
    await page.getByRole('button',{name:'Inspect Goal Persistence',exact:true}).click();
    await page.getByText('Execution: completed',{exact:true}).waitFor();
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
    assert.deepEqual(errors,[]);
    console.log('AGENTS_REAL_QUEUE_CANCEL_BUDGET_GOAL_RELOAD_OK');
  } finally { await browser.close(); }
})().catch(error=>{ console.error(error); process.exit(1); });
