// Real packaged Electron/backend smoke. Requires Windows and an unpacked build.
const { _electron } = require(process.env.JAVO_PLAYWRIGHT_MODULE || 'playwright-core');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

(async () => {
  const exe = path.resolve(process.argv[2] || 'apps/windows/release/win-unpacked/Javo Agents.exe');
  assert(fs.existsSync(exe), 'Packaged desktop executable is missing');
  const suppliedProfile = process.env.JAVO_SMOKE_PROFILE;
  const profile = suppliedProfile ? path.resolve(suppliedProfile)
    : fs.mkdtempSync(path.join(os.tmpdir(), 'javo-packaged-'));
  if (suppliedProfile) {
    assert(process.env.RUNNER_TEMP, 'Persistent QA profiles require the isolated CI runner');
    assert.equal(path.basename(profile), 'qa-profile');
    assert(/^javo-installer-[a-f0-9]{32}$/i.test(path.basename(path.dirname(profile))));
    assert.equal(path.relative(path.resolve(process.env.RUNNER_TEMP), path.dirname(path.dirname(profile))), '');
  }
  fs.mkdirSync(profile, { recursive: true });
  assert.equal(fs.lstatSync(profile).isSymbolicLink(), false, 'QA profiles must not link to owner data');
  const inherited = Object.fromEntries(Object.entries(process.env).filter(([name]) => !name.startsWith('JAVO_')));
  const env = { ...inherited, JAVO_USER_DATA_DIR: profile,
    PATH: path.join(process.env.SystemRoot || 'C:/Windows', 'System32') };
  delete env.JAVO_DASHBOARD_URL;
  delete env.JAVO_PYTHON_PATH;
  let app;
  try {
    for (const restart of [false, true]) {
      app = await _electron.launch({ executablePath: exe, env, timeout: 60000 });
      const page = await app.firstWindow({ timeout: 60000 });
      await page.getByRole('heading', { name: 'Local runtime', exact: true }).waitFor({ timeout: 30000 });
      const state = await page.evaluate(() => window.javoDesktop.getRuntimeStatus());
      assert.equal(state.running, true, state.lastError || 'Backend is not ready');
      await page.evaluate(() => { location.hash = '/settings'; });
      await page.getByLabel('gemini model', { exact: true }).waitFor();
      await page.getByText('Storage protection: windows-user', { exact: true }).waitFor();
      if (restart) {
        assert.equal(state.paused, true);
        assert.equal(state.emergencyStopped, true, 'Restart lost emergency-stop state');
        assert.equal(await page.getByLabel('gemini model', { exact: true }).inputValue(), 'packaged-owner-model');
        assert.equal(await page.getByLabel('gemini replacement API key', { exact: true }).inputValue(), '');
        if (!(suppliedProfile && process.env.JAVO_SMOKE_PRESERVE_PROVIDER === '1')) {
          await page.getByRole('button', { name: 'Remove gemini credentials', exact: true }).click();
          await page.getByRole('status').filter({ hasText: 'Saved credentials removed' }).waitFor();
        }
      } else {
        if (suppliedProfile && process.env.JAVO_SMOKE_EXPECT_PROVIDER === '1') {
          assert.equal(await page.getByLabel('gemini model', { exact: true }).inputValue(), 'packaged-owner-model');
          await page.getByRole('button', { name: 'Remove gemini credentials', exact: true }).waitFor();
          console.log('REINSTALLED_PROVIDER_DECRYPTION_OK');
        }
        await page.getByLabel('gemini model', { exact: true }).fill('packaged-owner-model');
        const fakeKey = 'synthetic-packaged-value-not-a-live-key';
        await page.getByLabel('gemini replacement API key', { exact: true }).fill(fakeKey);
        await page.getByRole('button', { name: 'Save gemini', exact: true }).click();
        await page.getByRole('status').filter({ hasText: 'Saved encrypted provider configuration' }).waitFor();
        assert(!fs.readFileSync(path.join(profile, 'runtime/provider-config.enc')).includes(Buffer.from(fakeKey)));
        assert(fs.existsSync(path.join(profile, 'runtime/provider-config.key.dpapi')));
        assert.equal(await page.evaluate(() => window.javoDesktop.resumeAgents()), true);
        assert.equal((await page.evaluate(() => window.javoDesktop.getRuntimeStatus())).paused, false);
        assert.equal(await page.evaluate(() => window.javoDesktop.pauseAgents()), true);
        assert.equal((await page.evaluate(() => window.javoDesktop.getRuntimeStatus())).paused, true);
        assert.equal(await page.evaluate(() => window.javoDesktop.emergencyStop()), true);
      }
      await app.close();
      app = null;
      // The app's awaited quit handler must not leave the backend behind.
      const deadline = Date.now() + 5000;
      let alive = true;
      while (alive && Date.now() < deadline) {
        try { process.kill(state.pid, 0); await new Promise(r => setTimeout(r, 100)); }
        catch (error) { if (error.code === 'ESRCH') alive = false; else throw error; }
      }
      assert.equal(alive, false, 'Packaged quit left an orphan runtime');
    }
    console.log('PACKAGED_DESKTOP_START_CONTROLS_RESTART_QUIT_OK (Python absent from child PATH)');
    console.log('PACKAGED_PROVIDER_WINDOWS_USER_PROTECTION_RESTART_OK');
  } finally {
    if (app) await app.close();
    // Only this script's fresh temporary profile is eligible for cleanup.
    if (!suppliedProfile) {
      const resolved = path.resolve(profile);
      assert.equal(path.dirname(resolved), path.resolve(os.tmpdir()));
      assert(path.basename(resolved).startsWith('javo-packaged-'));
      fs.rmSync(resolved, { recursive: true, force: true });
    }
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
