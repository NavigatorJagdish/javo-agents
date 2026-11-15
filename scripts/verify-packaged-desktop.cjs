// Real packaged Electron/backend smoke. Requires Windows and an unpacked build.
const { _electron } = require(process.env.JAVO_PLAYWRIGHT_MODULE || 'playwright-core');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

(async () => {
  const exe = path.resolve(process.argv[2] || 'apps/windows/release/win-unpacked/Javo Agents.exe');
  assert(fs.existsSync(exe), 'Packaged desktop executable is missing');
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'javo-packaged-'));
  const env = { ...process.env, JAVO_USER_DATA_DIR: profile,
    PATH: path.join(process.env.SystemRoot || 'C:/Windows', 'System32') };
  delete env.JAVO_DASHBOARD_URL;
  delete env.JAVO_PYTHON_PATH;
  let app;
  const backendPids = [];
  try {
    for (const restart of [false, true]) {
      app = await _electron.launch({ executablePath: exe, env, timeout: 60000 });
      const page = await app.firstWindow({ timeout: 60000 });
      await page.getByRole('heading', { name: 'Local runtime', exact: true }).waitFor({ timeout: 30000 });
      const state = await page.evaluate(() => window.javoDesktop.getRuntimeStatus());
      assert.equal(state.running, true, state.lastError || 'Backend is not ready');
      backendPids.push(state.pid);
      if (restart) {
        assert.equal(state.paused, true);
        assert.equal(state.emergencyStopped, true, 'Restart lost emergency-stop state');
      } else {
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
  } finally {
    if (app) await app.close();
    // Only this script's fresh temporary profile is eligible for cleanup.
    const resolved = path.resolve(profile);
    assert.equal(path.dirname(resolved), path.resolve(os.tmpdir()));
    assert(path.basename(resolved).startsWith('javo-packaged-'));
    fs.rmSync(resolved, { recursive: true, force: true });
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
