// Actual local HTTP/database and built UI. No model calls or cloud requests.
const { chromium } = require(process.env.JAVO_PLAYWRIGHT_MODULE || 'playwright-core');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.JAVO_CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true,
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.JAVO_SMOKE_URL, { waitUntil: 'domcontentloaded' });
    await page.getByLabel('Owner access token').fill(process.env.JAVO_OWNER_ACCESS_TOKEN);
    await page.getByRole('button', { name: 'Connect / retry' }).click();
    await page.getByRole('heading', { name: 'Local runtime', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Goals', exact: true }).click();
    await page.getByRole('heading', { name: 'Goals', exact: true }).waitFor();
    await page.getByText('No saved goals on this page. Create a goal to begin tracking.').waitFor();
    await page.getByRole('button', { name: 'New Goal', exact: true }).click();
    await page.getByLabel('Goal title', { exact: true }).fill('Local goal browser evidence');
    await page.getByLabel('Goal description', { exact: true }).fill('Saved through the real API');
    await page.getByLabel('Metric name', { exact: true }).fill('Audience');
    await page.getByLabel('Metric unit', { exact: true }).fill('subscribers');
    await page.getByLabel('Baseline', { exact: true }).fill('100');
    await page.getByLabel('Target', { exact: true }).fill('200');
    await page.getByLabel('Baseline source', { exact: true }).fill('Owner report');
    await page.getByLabel('Constraints', { exact: true }).fill('Zero spending');
    await page.getByLabel('Stopping conditions', { exact: true }).fill('Owner requests stop');
    await page.getByLabel('Goal deadline (IST)', { exact: true }).fill('2026-12-31');
    await page.getByRole('button', { name: 'Save goal', exact: true }).click();
    await page.getByRole('heading', { name: 'Local goal browser evidence', exact: true }).waitFor();
    await page.getByLabel('Measured value', { exact: true }).fill('150');
    await page.getByLabel('Measurement source', { exact: true }).fill('Manually checked account report');
    await page.getByRole('button', { name: 'Save measurement', exact: true }).click();
    await page.getByText(/Progress: 50%/).waitFor();
    await page.getByLabel('Milestone title', { exact: true }).fill('First review');
    await page.getByLabel('Milestone target', { exact: true }).fill('2');
    await page.getByRole('button', { name: 'Add milestone', exact: true }).click();
    await page.getByLabel('Current value for First review', { exact: true }).fill('2');
    await page.getByRole('button', { name: 'Save milestone', exact: true }).click();
    await page.getByText('First review ✓ Completed', { exact: true }).waitFor();
    // Reload discards React state; authenticate afresh and inspect saved records.
    await page.reload();
    await page.getByLabel('Owner access token').fill(process.env.JAVO_OWNER_ACCESS_TOKEN);
    await page.getByRole('button', { name: 'Connect / retry' }).click();
    await page.getByText(/Progress: 50%/).waitFor();
    await page.getByText('First review ✓ Completed', { exact: true }).waitFor();
    await page.getByText(/150 subscribers · Manually checked account report/).waitFor();
    await page.getByRole('button', { name: 'Edit goal', exact: true }).click();
    await page.getByLabel('Goal title', { exact: true }).fill('Renamed saved goal');
    await page.getByRole('button', { name: 'Save goal', exact: true }).click();
    await page.getByRole('heading', { name: 'Renamed saved goal', exact: true }).waitFor();
    await page.getByLabel('Goal status', { exact: true }).selectOption('paused');
    await page.getByText('paused', { exact: true }).first().waitFor();
    await page.setViewportSize({ width: 390, height: 844 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'Goals should fit the mobile viewport');
    if (process.env.JAVO_GOALS_SCREENSHOT) await page.screenshot({ path: process.env.JAVO_GOALS_SCREENSHOT, fullPage: true });
    await page.getByRole('button', { name: 'Remove milestone', exact: true }).click();
    await page.getByRole('button', { name: 'Confirm milestone removal', exact: true }).click();
    await page.getByLabel('Current value for First review', { exact: true }).waitFor({ state: 'detached' });
    await page.getByRole('button', { name: 'Remove goal', exact: true }).click();
    await page.getByText('Remove this goal and its milestones? Task execution history will be retained.').waitFor();
    await page.getByRole('button', { name: 'Confirm goal removal', exact: true }).click();
    await page.getByText('No saved goals on this page. Create a goal to begin tracking.').waitFor();
    assert.deepEqual(errors, []);
    console.log('GOALS_REAL_DATABASE_CREATE_MEASURE_MILESTONE_RELOAD_EDIT_REMOVE_OK');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
