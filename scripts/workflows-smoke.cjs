// Real built UI/database/worker. AI text comes from a labelled loopback fixture.
const { chromium } = require(process.env.JAVO_PLAYWRIGHT_MODULE || 'playwright-core');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.JAVO_CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const authenticate = async () => {
      await page.getByLabel('Owner access token').fill(process.env.JAVO_OWNER_ACCESS_TOKEN);
      await page.getByRole('button', { name: 'Connect / retry' }).click();
      await page.getByLabel('Owner access token').waitFor({ state: 'detached' });
    };
    await page.goto(process.env.JAVO_SMOKE_URL, { waitUntil: 'domcontentloaded' });
    await authenticate();
    await page.getByRole('button', { name: 'Workflows', exact: true }).click();
    await page.getByRole('heading', { name: 'Workflows', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Use caption draft template', exact: true }).click();
    await page.getByLabel('Workflow name', { exact: true }).fill('Browser workflow evidence');
    await page.getByRole('button', { name: 'Save workflow', exact: true }).click();
    await page.getByText('Saved revision 1', { exact: true }).waitFor();
    const id = await page.getByLabel('Saved workflow', { exact: true }).inputValue();
    assert(id);
    await page.getByLabel('Connect from', { exact: true }).selectOption({ label: 'End' });
    await page.getByLabel('Connect to', { exact: true }).selectOption({ label: 'Manual start' });
    await page.getByRole('button', { name: 'Connect nodes', exact: true }).click();
    await page.getByText('That connection would create a cycle. Choose a later node.', { exact: true }).waitFor();
    await page.getByText('More planning nodes · execution unavailable', { exact: true }).click();
    await page.getByRole('button', { name: 'Add publish (save only)', exact: true }).click();
    await page.getByRole('button', { name: 'Save workflow', exact: true }).click();
    await page.getByText('Saved revision 2', { exact: true }).waitFor();
    assert(await page.getByRole('button', { name: 'Review manual run', exact: true }).isDisabled());
    await page.getByLabel('Revision to restore', { exact: true }).selectOption('1');
    await page.getByRole('button', { name: 'Restore revision', exact: true }).click();
    await page.getByRole('button', { name: 'Confirm change', exact: true }).click();
    await page.getByText('Saved revision 3', { exact: true }).waitFor();
    await page.getByLabel('Workflow name', { exact: true }).fill('Accidental unsaved name');
    await page.getByRole('button', { name: 'Goals', exact: true }).click();
    await page.getByRole('heading', { name: 'Unsaved workflow edits', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Stay and keep editing', exact: true }).click();
    assert.equal(await page.getByLabel('Workflow name', { exact: true }).inputValue(), 'Accidental unsaved name');
    await page.getByRole('button', { name: 'Reload saved version', exact: true }).click();
    await page.getByRole('button', { name: 'Confirm change', exact: true }).click();
    await page.getByText('Saved revision 3', { exact: true }).waitFor();
    // Preserve a user's pending edit when a second session saves a newer revision.
    const base = new URL(process.env.JAVO_SMOKE_URL).origin;
    const headers = { Authorization: 'Bearer '+process.env.JAVO_OWNER_ACCESS_TOKEN };
    const remote = await (await page.request.get(base+'/api/workflows/'+id, { headers })).json();
    const { name, description, status, trigger_config, viewport, nodes, edges } = remote;
    const changed = await page.request.put(base+'/api/workflows/'+id, { headers, data: { name: 'Second session saved name', description, status, trigger_config, viewport, nodes, edges, expected_revision: remote.revision } });
    assert.equal(changed.status(), 200);
    await page.getByLabel('Workflow name', { exact: true }).fill('My unsaved local edit');
    await page.getByRole('button', { name: 'Save workflow', exact: true }).click();
    await page.getByText('This workflow changed elsewhere. Reload the saved version before overwriting it.', { exact: true }).waitFor();
    assert.equal(await page.getByLabel('Workflow name', { exact: true }).inputValue(), 'My unsaved local edit');
    await page.getByRole('button', { name: 'Save as new copy', exact: true }).click();
    await page.getByText('Saved revision 1', { exact: true }).waitFor();
    const copyId = await page.getByLabel('Saved workflow', { exact: true }).inputValue();
    assert.notEqual(copyId, id);
    const preserved = await (await page.request.get(base+'/api/workflows/'+id, { headers })).json();
    assert.equal(preserved.name, 'Second session saved name');
    await page.getByLabel('Saved workflow', { exact: true }).selectOption(id);
    await page.getByRole('button', { name: 'Open saved workflow', exact: true }).click();
    await page.getByText('Saved revision 4', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Review manual run', exact: true }).click();
    await page.getByRole('button', { name: 'Confirm manual run', exact: true }).click();
    await page.getByText('Run: queued · revision 4', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Cancel run', exact: true }).click();
    await page.getByText('Run: cancelled · revision 4', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Autopilot: OFF', exact: true }).click();
    await page.getByRole('button', { name: 'Autopilot: ON', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Review manual run', exact: true }).click();
    await page.getByRole('button', { name: 'Confirm manual run', exact: true }).click();
    await page.getByText('Run: completed · revision 4', { exact: true }).waitFor();
    await page.getByText('Synthetic saved workflow draft.', { exact: true }).waitFor();
    await page.reload();
    await authenticate();
    await page.getByLabel('Saved workflow', { exact: true }).selectOption(id);
    await page.getByRole('button', { name: 'Open saved workflow', exact: true }).click();
    await page.getByText('Run: completed · revision 4', { exact: true }).waitFor();
    await page.getByText('Synthetic saved workflow draft.', { exact: true }).waitFor();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForFunction(() => {
      const canvas = document.querySelector('.react-flow')?.getBoundingClientRect();
      const nodes = [...document.querySelectorAll('.react-flow__node')];
      return canvas && nodes.length === 3 && nodes.every(node => {
        const rect = node.getBoundingClientRect();
        return rect.left >= canvas.left && rect.right <= canvas.right && rect.top >= canvas.top && rect.bottom <= canvas.bottom;
      });
    });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'Workflow editor must fit a mobile viewport');
    if (process.env.JAVO_WORKFLOWS_SCREENSHOT) await page.screenshot({ path: process.env.JAVO_WORKFLOWS_SCREENSHOT, fullPage: true });
    assert.deepEqual(errors, []);
    console.log('WORKFLOW_SAVE_RELOAD_REVISION_CONFLICT_RESTORE_CYCLE_GUARD_QUEUE_CANCEL_LOCAL_RUN_OK');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
