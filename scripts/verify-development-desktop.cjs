// Actual development Electron plus venv runtime, using only a generated profile.
const { _electron } = require(process.env.JAVO_PLAYWRIGHT_MODULE || 'playwright-core');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

(async () => {
  const root = path.resolve(__dirname, '..');
  const tempRoot = fs.realpathSync(os.tmpdir());
  const profile = fs.mkdtempSync(path.join(tempRoot, 'javo-development-'));
  const inherited = Object.fromEntries(Object.entries(process.env).filter(([name]) => !name.startsWith('JAVO_') && name !== 'ELECTRON_RUN_AS_NODE'));
  const env = {...inherited, JAVO_USER_DATA_DIR: profile};
  let app;
  let base;
  try {
    app = await _electron.launch({
      executablePath: require(path.join(root, 'apps/windows/node_modules/electron')),
      args: [path.join(root, 'apps/windows')], env, timeout: 60000,
    });
    const page = await app.firstWindow({timeout: 60000});
    await page.getByRole('heading', {name:'Local runtime',exact:true}).waitFor({timeout:30000});
    const state = await page.evaluate(() => window.javoDesktop.getRuntimeStatus());
    assert.equal(state.running, true, state.lastError || 'Runtime was not ready');
    assert.equal(state.paused, true);
    base = state.baseUrl;
    await page.getByRole('button',{name:'AI Team',exact:true}).click();
    await page.getByRole('button',{name:'Inspect Budget Guardian',exact:true}).waitFor();
    await page.getByRole('button',{name:'Goals',exact:true}).click();
    await page.getByText('No saved goals on this page. Create a goal to begin tracking.').waitFor();
    await page.getByRole('button',{name:'Accounts',exact:true}).click();
    await page.getByText('No saved accounts on this page. Add a record to save your brand rules.').waitFor();
    await page.getByRole('button',{name:'Workflows',exact:true}).click();
    await page.getByRole('heading',{name:'Workflows',exact:true}).waitFor();
    await page.getByRole('button',{name:'Use caption draft template',exact:true}).waitFor();
    await page.getByRole('button',{name:'Settings',exact:true}).click();
    await page.getByText('Completed AI requests: 0',{exact:true}).waitFor();
    await app.close();
    app = null;
    await assert.rejects(fetch(base+'/auth/status', {signal:AbortSignal.timeout(1000)}));
    console.log('DEVELOPMENT_ELECTRON_VENV_START_PAGES_QUIT_NO_ORPHAN_OK');
  } finally {
    if (app) await app.close();
    // Never recurse into a supplied/owner profile or a symlink.
    assert.equal(path.dirname(path.resolve(profile)), tempRoot);
    assert(/^javo-development-/.test(path.basename(profile)));
    assert.equal(fs.lstatSync(profile).isSymbolicLink(), false);
    fs.rmSync(profile,{recursive:true,force:true});
  }
})().catch(error=>{ console.error(error); process.exit(1); });
