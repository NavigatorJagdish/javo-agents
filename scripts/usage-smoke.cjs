// Read actual API/database totals seeded with synthetic local usage by the harness.
const { chromium } = require(process.env.JAVO_PLAYWRIGHT_MODULE || 'playwright-core');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.JAVO_CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.JAVO_SMOKE_URL);
    await page.getByLabel('Owner access token').fill(process.env.JAVO_OWNER_ACCESS_TOKEN);
    await page.getByRole('button', { name: 'Connect / retry' }).click();
    await page.getByRole('heading', { name: 'Local runtime', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Settings', exact: true }).click();
    await page.getByRole('heading', { name: 'Saved AI usage', exact: true }).waitFor();
    await page.getByText('Completed AI requests: 1', { exact: true }).waitFor();
    await page.getByText('Reported tokens: 8', { exact: true }).waitFor();
    await page.getByText('Requests with unknown token counts: 0', { exact: true }).waitFor();
    await page.reload();
    await page.getByLabel('Owner access token').fill(process.env.JAVO_OWNER_ACCESS_TOKEN);
    await page.getByRole('button', { name: 'Connect / retry' }).click();
    await page.getByText('Completed AI requests: 1', { exact: true }).waitFor();
    await page.setViewportSize({ width: 390, height: 844 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    assert.deepEqual(errors, []);
    console.log('USAGE_SAVED_API_COUNTERS_RELOAD_OK');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
