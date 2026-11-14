const { test, mock } = require('node:test');
const assert = require('node:assert/strict');
const childProcess = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const net = require('node:net');
const { LocalRuntimeManager } = require('../dist/backendManager');

// A real child process with an HTTP fixture, not the Python application.
// This isolates desktop process/port/auth/storage/shutdown contracts from Python.
const fixture = `
const http = require('node:http'), fs = require('node:fs');
const stateFile = process.env.JAVO_CONTROL_STATE_PATH;
let state = fs.existsSync(stateFile) ? JSON.parse(fs.readFileSync(stateFile))
  : {paused:true, emergency_stopped:false};
http.createServer((req, res) => {
  if (req.headers.authorization !== 'Bearer ' + process.env.JAVO_OWNER_ACCESS_TOKEN) {
    res.writeHead(401).end(); return;
  }
  if (req.url === '/health/') { res.end(JSON.stringify({status:'healthy'})); return; }
  if (req.url === '/security/resume') state = {paused:false, emergency_stopped:false};
  if (req.url === '/security/pause') state.paused = true;
  if (req.url === '/security/emergency-stop') state = {paused:true, emergency_stopped:true};
  fs.writeFileSync(stateFile, JSON.stringify(state));
  res.end(JSON.stringify(state));
}).listen(Number(process.env.JAVO_PORT), '127.0.0.1');
`;

test('desktop manager lifecycle, occupied port, auth and persisted controls', { timeout: 30000 }, async () => {
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'javo-desktop-test-'));
  const runtime = path.join(folder, 'read-only-source');
  const data = path.join(folder, 'owner-data');
  fs.mkdirSync(runtime);
  const blocker = net.createServer();
  await new Promise(resolve => blocker.listen(0, '127.0.0.1', resolve));
  const occupiedPort = blocker.address().port;
  const realSpawn = childProcess.spawn;
  let spawns = 0;
  const spawnMock = mock.method(childProcess, 'spawn', (_python, _args, options) => {
    spawns++;
    assert.equal(options.cwd, data);
    assert.equal(options.windowsHide, true);
    assert(options.env.PYTHONPATH.split(path.delimiter).includes(runtime));
    assert(options.env.JAVO_DATABASE_URL.includes(data.replaceAll('\\', '/')));
    return realSpawn(process.execPath, ['-e', fixture], options);
  });
  const manager = new LocalRuntimeManager(runtime, data);
  try {
    assert.equal(manager.getStatus().running, false);
    const [status, concurrentStatus] = await Promise.all([manager.start(occupiedPort), manager.start(occupiedPort)]);
    assert.equal(spawns, 1, 'Concurrent start must not create two backends');
    assert.equal(status.running, true);
    assert.equal(concurrentStatus.pid, status.pid);
    assert.notEqual(status.port, occupiedPort);
    assert.equal((await fetch(status.baseUrl + '/health/')).status, 401);
    assert.deepEqual(await manager.getControlState(), { paused: true, emergency_stopped: false });
    assert.equal(await manager.callControlEndpoint('/security/resume'), true);
    assert.equal((await manager.getControlState()).paused, false);
    assert.equal(await manager.callControlEndpoint('/security/emergency-stop'), true);
    await Promise.all([manager.stop(), manager.stop()]);
    assert.equal(manager.getStatus().running, false);
    assert.equal(manager.getStatus().pid, null);
    assert.equal(await manager.getControlState(), null);
    assert.deepEqual(fs.readdirSync(runtime), [], 'Runtime source must not hold user data');
    await assert.rejects(fetch(status.baseUrl + '/health/', { signal: AbortSignal.timeout(500) }));
    const restarted = new LocalRuntimeManager(runtime, data);
    try {
      assert.equal((await restarted.start(occupiedPort)).running, true);
      assert.deepEqual(await restarted.getControlState(), { paused: true, emergency_stopped: true });
    } finally { await restarted.stop(); }
  } finally {
    await manager.stop();
    spawnMock.restore();
    await new Promise(resolve => blocker.close(resolve));
    fs.rmSync(folder, { recursive: true, force: true });
  }
});

test('missing Python reports failure without an unhandled spawn error', { timeout: 10000 }, async () => {
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'javo-missing-python-'));
  const oldPython = process.env.JAVO_PYTHON_PATH;
  process.env.JAVO_PYTHON_PATH = path.join(folder, 'not-installed.exe');
  const manager = new LocalRuntimeManager(folder, path.join(folder, 'data'));
  try {
    const status = await manager.start(0);
    assert.equal(status.running, false);
    assert.equal(status.pid, null);
    assert.match(status.lastError, /Could not start local runtime/);
  } finally {
    await manager.stop();
    if (oldPython === undefined) delete process.env.JAVO_PYTHON_PATH;
    else process.env.JAVO_PYTHON_PATH = oldPython;
    fs.rmSync(folder, { recursive: true, force: true });
  }
});
