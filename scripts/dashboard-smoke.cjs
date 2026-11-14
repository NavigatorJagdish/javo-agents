// Runs against a temporary local backend; credentials are supplied only in env.
const { chromium } = require(process.env.JAVO_PLAYWRIGHT_MODULE || 'playwright-core');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.JAVO_CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.JAVO_SMOKE_URL, { waitUntil: 'domcontentloaded' });
    await page.getByLabel('Owner access token').fill(process.env.JAVO_OWNER_ACCESS_TOKEN);
    await page.getByRole('button', { name: 'Connect / retry' }).click();
    await page.getByRole('heading', { name: 'Local runtime', exact: true }).waitFor();
    assert.equal(await page.evaluate(() => performance.getEntriesByType('resource')
      .some(entry => /\/(Analytics|Workflows)-[^/]+\.js/.test(entry.name))), false,
      'Heavy routes should not download on initial dashboard load');
    await page.getByRole('button', { name: 'Autopilot: OFF' }).click();
    await page.getByRole('button', { name: 'Autopilot: ON' }).waitFor();
    await page.getByText('Content', { exact: true }).click();
    await page.getByRole('heading', { name: 'Content workflow' }).waitFor();
    await page.getByLabel('Local folder path').fill(process.env.JAVO_SMOKE_CONTENT);
    await page.getByRole('button', { name: 'Scan folder', exact: true }).click();
    await page.getByText('1 files discovered; 1 imported.', { exact: true }).waitFor();
    await page.getByLabel('Asset', { exact: true }).selectOption({ label: 'sample (text)' });
    await page.getByRole('button', { name: 'Add local simulation destination' }).click();
    await page.getByText(/Disconnected simulation destination created/).waitFor();
    await page.getByLabel('Caption', { exact: true }).fill('Browser verified caption');
    const tomorrow = new Date(Date.now() + 86400000).toLocaleString('sv-SE', { timeZone: 'Asia/Kolkata' }).slice(0, 16).replace(' ', 'T');
    await page.getByLabel(/Planned time/).fill(tomorrow);
    await page.getByRole('button', { name: 'Save schedule', exact: true }).click();
    await page.getByText(/Schedule saved. Review and approve separately/).waitFor();
    await page.getByRole('button', { name: 'Review preview', exact: true }).click();
    await page.getByRole('heading', { name: 'Exact review snapshot' }).waitFor();
    await page.getByRole('button', { name: 'Approve this snapshot for simulation' }).click();
    await page.getByText(/This exact snapshot is approved for simulation/).waitFor();
    await page.getByRole('button', { name: 'Simulate now', exact: true }).click();
    await page.getByRole('heading', { name: 'Receipt: simulated', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Load saved receipt', exact: true }).click();
    await page.getByText('Simulation only: no social media post was published.', { exact: true }).waitFor();
    await page.setViewportSize({ width: 390, height: 844 });
    assert(await page.getByRole('heading', { name: 'Content workflow' }).isVisible());
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2), false, 'Mobile page overflows horizontally');
    await page.setViewportSize({ width: 1360, height: 900 });
    // Exercise loading of separate JS/CSS chunks without reloading the owner session.
    await page.evaluate(() => { location.hash = '/workflows'; });
    await page.getByRole('textbox', { name: 'Workflow name', exact: true }).waitFor();
    await page.evaluate(() => { location.hash = '/analytics'; });
    await page.getByRole('heading', { name: 'Cross-Platform Analytics', exact: true }).waitFor();
    assert.deepEqual(errors, [], 'Browser JavaScript errors');
    console.log('DASHBOARD_BROWSER_FLOW_OK');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
