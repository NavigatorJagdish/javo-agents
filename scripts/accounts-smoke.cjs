// Real local HTTP/SQLite and built UI; no OAuth, tokens or platform requests.
const { chromium } = require(process.env.JAVO_PLAYWRIGHT_MODULE || 'playwright-core');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.JAVO_CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1360, height: 900 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.JAVO_SMOKE_URL, { waitUntil: 'domcontentloaded' });
    async function authenticate() {
      await page.getByLabel('Owner access token').fill(process.env.JAVO_OWNER_ACCESS_TOKEN);
      await page.getByRole('button', { name: 'Connect / retry' }).click();
      await page.getByLabel('Owner access token').waitFor({ state: 'detached' });
    }
    await authenticate();
    await page.getByRole('button', { name: 'Accounts', exact: true }).click();
    await page.getByRole('heading', { name: 'Synthetic legacy migration', exact: true }).waitFor();
    await page.getByText('Encrypted credentials saved; platform connection unverified', { exact: true }).waitFor();
    await page.getByText('Not connected', { exact: true }).waitFor();
    const base = new URL(process.env.JAVO_SMOKE_URL).origin;
    const migrated = await page.request.get(base+'/api/accounts/synthetic-legacy-account', { headers: { Authorization: 'Bearer '+process.env.JAVO_OWNER_ACCESS_TOKEN } });
    assert.equal(migrated.status(), 200);
    const saved = await migrated.json();
    assert.equal(saved.has_saved_credentials, true);
    assert.equal(saved.has_refresh_token, true);
    assert.equal(saved.connection_verified, false);
    assert(!(JSON.stringify(saved).includes('synthetic-ui-')), 'Account API exposed synthetic credential values');
    const oauth = await page.request.post(base+'/api/accounts/synthetic-legacy-account/oauth/initiate', { headers: { Authorization: 'Bearer '+process.env.JAVO_OWNER_ACCESS_TOKEN }, data: {} });
    assert.equal(oauth.status(), 501);
    await page.getByRole('button', { name: 'Remove saved credentials', exact: true }).click();
    await page.getByRole('button', { name: 'Confirm credential removal', exact: true }).click();
    await page.getByText('No saved credentials', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Remove account', exact: true }).click();
    await page.getByRole('button', { name: 'Confirm account removal', exact: true }).click();
    await page.getByText('No saved accounts on this page. Add a record to save your brand rules.').waitFor();
    await page.getByRole('button', { name: 'Add account record', exact: true }).click();
    await page.getByRole('combobox', { name: 'Platform', exact: true }).selectOption('youtube');
    await page.getByLabel('Account handle', { exact: true }).fill('@synthetic-browser-account');
    await page.getByLabel('Display name', { exact: true }).fill('Saved browser account');
    await page.getByRole('button', { name: 'Save account', exact: true }).click();
    await page.getByRole('heading', { name: 'Saved browser account', exact: true }).waitFor();
    await page.getByText('No saved credentials', { exact: true }).waitFor();
    await page.getByText('Not connected', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Brand profile', exact: true }).click();
    await page.getByLabel('Brand name', { exact: true }).fill('Persisted browser brand');
    await page.getByLabel('Brand voice', { exact: true }).fill('Clear Hinglish');
    await page.getByLabel('Target audience', { exact: true }).fill('Local creators');
    await page.getByLabel('Content pillars (one per line, up to 20)', { exact: true }).fill('Local tools\nCreator education');
    await page.getByRole('button', { name: 'Save brand profile', exact: true }).click();
    await page.getByText('Brand profile saved', { exact: true }).waitFor();
    await page.getByRole('dialog').getByRole('button', { name: 'Close modal', exact: true }).click();
    await page.getByRole('button', { name: 'Edit account', exact: true }).click();
    await page.getByLabel('Display name', { exact: true }).fill('Renamed saved account');
    await page.getByRole('button', { name: 'Save account', exact: true }).click();
    await page.getByRole('heading', { name: 'Renamed saved account', exact: true }).waitFor();
    await page.reload();
    await authenticate();
    await page.getByRole('heading', { name: 'Renamed saved account', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Brand profile', exact: true }).click();
    await page.getByLabel('Brand name', { exact: true }).waitFor();
    assert.equal(await page.getByLabel('Brand name', { exact: true }).inputValue(), 'Persisted browser brand');
    assert.equal(await page.getByLabel('Brand voice', { exact: true }).inputValue(), 'Clear Hinglish');
    assert.equal(await page.getByLabel('Target audience', { exact: true }).inputValue(), 'Local creators');
    assert.equal(await page.getByLabel('Content pillars (one per line, up to 20)', { exact: true }).inputValue(), 'Local tools\nCreator education');
    await page.setViewportSize({ width: 390, height: 844 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'Brand form must fit mobile viewport');
    await page.getByRole('dialog').getByRole('button', { name: 'Close modal', exact: true }).click();
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'Accounts must fit mobile viewport');
    if (process.env.JAVO_ACCOUNTS_SCREENSHOT) await page.screenshot({ path: process.env.JAVO_ACCOUNTS_SCREENSHOT, fullPage: true });
    await page.getByRole('button', { name: 'Remove account', exact: true }).click();
    await page.getByRole('button', { name: 'Confirm account removal', exact: true }).click();
    await page.getByText('No saved accounts on this page. Add a record to save your brand rules.').waitFor();
    assert.deepEqual(errors, []);
    console.log('ACCOUNTS_ENCRYPTED_LEGACY_MIGRATION_RECORD_BRAND_RELOAD_EDIT_REMOVE_OK');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
