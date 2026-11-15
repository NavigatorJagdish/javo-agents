// Browser-only route/chunk verification. API replies are explicit fixtures;
// this does not verify backend integration or social publishing.
const { chromium } = require(process.env.JAVO_PLAYWRIGHT_MODULE || 'playwright-core');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const dist = path.resolve(__dirname, '../apps/dashboard/dist');

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.JAVO_CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const resources = [];
    let timerState = null;
    let approved = false;
    const fingerprint = 'a'.repeat(64);
    await page.route('http://javo.test/**', async route => {
      const url = new URL(route.request().url());
      const file = path.resolve(dist, '.' + (url.pathname === '/' ? '/index.html' : url.pathname));
      if (!file.startsWith(dist + path.sep)) return route.abort();
      resources.push(path.basename(file));
      const contentType = file.endsWith('.js') ? 'text/javascript' : file.endsWith('.css') ? 'text/css' : 'text/html';
      await route.fulfill({ path: file, contentType });
    });
    await page.route('http://127.0.0.1:8000/**', async route => {
      const url = new URL(route.request().url());
      let body = [];
      const schedulePath = '/api/content/schedule/timer-fixture';
      if (url.pathname === '/api/content/schedule') body = [{ id: 'timer-fixture', asset_id: 'asset',
        account_id: 'account', caption: 'Explicit timer fixture', status: 'approved', scheduled_at: '2030-01-01T12:00:00' }];
      if (url.pathname === schedulePath + '/preview') body = { schedule_id: 'timer-fixture', fingerprint,
        snapshot: { caption: 'Explicit timer fixture' } };
      if (url.pathname === schedulePath + '/approve') {
        assert.equal(route.request().postDataJSON().fingerprint, fingerprint);
        approved = true; body = { status: 'approved' };
      }
      if (url.pathname === schedulePath + '/timer') {
        if (route.request().method() === 'POST') {
          assert(approved, 'UI timer fixture expects explicit approval before arming');
          assert.equal(route.request().postDataJSON().fingerprint, fingerprint);
          timerState = 'armed';
        } else if (route.request().method() === 'DELETE') timerState = 'cancelled';
        body = { schedule_id: 'timer-fixture', state: timerState };
      }
      if (url.pathname === '/api/content/timers') body = timerState ? [{ schedule_id: 'timer-fixture',
        state: timerState, due_at: '2030-01-01T12:00:00Z', reason: null }] : [];
      if (url.pathname === '/api/health/') body = { status: 'healthy', database: 'fixture' };
      if (url.pathname === '/api/health/system') body = { cpu_percent: 1, ram_percent: 20,
        ram_total_mb: 8192, resource_profile: { name: 'fixture', max_concurrent_agents: 1,
          memory_headroom_mb: 1536, basis: 'route test fixture' } };
      if (url.pathname === '/api/security/autopilot-status') body = { paused: true, emergency_stopped: false };
      await route.fulfill({ json: body, headers: { 'access-control-allow-origin': '*' } });
    });
    await page.goto('http://javo.test/?apiBase=http://127.0.0.1:8000');
    await page.getByRole('heading', { name: 'Local runtime', exact: true }).waitFor();
    assert(!resources.some(name => /^(Analytics|Workflows)-.*\.js$/.test(name)), 'Heavy routes loaded eagerly');
    // Delay a chunk to verify that runtime controls stay mounted during loading.
    let release;
    const hold = new Promise(resolve => { release = resolve; });
    await page.route('**/Content-*.js', async route => { await hold; await route.fallback(); });
    await page.evaluate(() => { location.hash = '/content'; });
    await page.getByRole('status').filter({ hasText: 'Loading page' }).waitFor();
    assert(await page.getByRole('button', { name: 'Emergency Stop', exact: true }).isVisible());
    release();
    await page.getByRole('heading', { name: 'Content workflow', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Review preview', exact: true }).click();
    await page.getByRole('button', { name: 'Approve this snapshot for simulation', exact: true }).click();
    await page.getByRole('status').filter({ hasText: 'This exact snapshot is approved' }).waitFor();
    await page.getByRole('button', { name: 'Arm timed simulation', exact: true }).click();
    await page.getByText('Timed simulation: armed.', { exact: false }).waitFor();
    await page.getByRole('button', { name: 'Cancel timer', exact: true }).click();
    await page.getByText('Timed simulation: cancelled.', { exact: false }).waitFor();
    assert.equal(timerState, 'cancelled');
    await page.evaluate(() => { location.hash = '/workflows'; });
    await page.getByRole('textbox', { name: 'Workflow name', exact: true }).waitFor();
    await page.evaluate(() => { location.hash = '/analytics'; });
    await page.getByRole('heading', { name: 'Cross-Platform Analytics', exact: true }).waitFor();
    await page.evaluate(() => { location.hash = '/setup/welcome'; });
    await page.getByRole('button', { name: 'Dashboard', exact: true }).waitFor();
    assert(resources.some(name => /^Welcome-.*\.js$/.test(name)));
    assert.deepEqual(errors, [], 'Unexpected browser errors');
    // Deliberately fail a previously unrequested chunk; navigation must recover.
    await page.route('**/GitHub-*.js', route => route.abort());
    await page.evaluate(() => { location.hash = '/github'; });
    await page.getByRole('button', { name: 'Reload page', exact: true }).waitFor();
    assert(await page.getByRole('button', { name: 'Emergency Stop', exact: true }).isVisible());
    await page.evaluate(() => { location.hash = '/'; });
    await page.getByRole('heading', { name: 'Local runtime', exact: true }).waitFor();
    console.log('DASHBOARD_ROUTE_CHUNKS_OK (API fixtures; not backend integration)');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
