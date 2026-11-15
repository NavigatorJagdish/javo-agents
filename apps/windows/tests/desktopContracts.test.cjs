const { test, mock } = require('node:test');
const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const childProcess = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { LocalRuntimeManager } = require('../dist/backendManager');
const { verifyPackage } = require('../scripts/verify-package.cjs');

async function withManager(run, packaged = false) {
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'javo-contract-'));
  const exe = packaged ? path.join(folder, 'javo-runtime.exe') : undefined;
  if (exe) fs.writeFileSync(exe, 'fixture');
  const manager = new LocalRuntimeManager(folder, path.join(folder, 'data'), exe);
  manager.findAvailablePort = async () => 54321;
  const child = new EventEmitter();
  Object.assign(child, { pid: 101, exitCode: null, stdout: { resume() {} }, stderr: new EventEmitter(),
    kill() { child.exitCode = 0; child.emit('exit', 0); return true; } });
  const spawned = mock.method(childProcess, 'spawn', () => child);
  // Never send OS process-control commands to a fixture PID.
  const stopped = mock.method(childProcess, 'execFile', (command, args, options, callback) => {
    assert.equal(command, 'taskkill');
    assert.deepEqual(args, ['/PID', '101', '/T', '/F']);
    child.kill();
    callback(null, '', '');
    return new EventEmitter();
  });
  const fetched = mock.method(global, 'fetch', async () => new Response(JSON.stringify({
    status: 'healthy', database: 'connected'
  })));
  try { await run({ manager, child, spawned, fetched, exe }); }
  finally {
    await manager.stop();
    spawned.mock.restore(); fetched.mock.restore(); stopped.mock.restore();
    fs.rmSync(folder, { recursive: true, force: true });
  }
}

test('packaged launch uses bundled executable without python or module arguments', async () => {
  await withManager(async ({ manager, spawned, exe }) => {
    assert.equal((await manager.start()).running, true);
    const [command, args, options] = spawned.mock.calls[0].arguments;
    assert.equal(command, exe);
    assert.deepEqual(args, ['--port', '54321']);
    assert.equal(options.windowsHide, true);
  }, true);
});

test('missing packaged runtime fails closed without falling back to system Python', async () => {
  await withManager(async ({ manager, spawned, exe }) => {
    fs.unlinkSync(exe);
    const status = await manager.start();
    assert.equal(status.running, false);
    assert.match(status.lastError, /Bundled runtime is missing/);
    assert.equal(spawned.mock.callCount(), 0);
  }, true);
});

test('stop during port allocation cancels startup before a child can spawn', async () => {
  await withManager(async ({ manager, spawned }) => {
    let resolvePort;
    manager.findAvailablePort = () => new Promise(resolve => { resolvePort = resolve; });
    const start = manager.start();
    await manager.stop();
    resolvePort(54321);
    assert.equal((await start).running, false);
    assert.equal(spawned.mock.callCount(), 0);
  });
});

test('delayed health response cannot resurrect a child after stop', async () => {
  await withManager(async ({ manager, fetched }) => {
    let resolveHealth;
    fetched.mock.mockImplementation(() => new Promise(resolve => { resolveHealth = resolve; }));
    const start = manager.start();
    await new Promise(resolve => setImmediate(resolve));
    await manager.stop();
    resolveHealth(new Response(JSON.stringify({ status: 'healthy', database: 'connected' })));
    assert.equal((await start).running, false);
    assert.equal(manager.getStatus().pid, null);
  });
});

test('degraded HTTP 200 never marks desktop backend ready', async () => {
  await withManager(async ({ manager, child, fetched }) => {
    fetched.mock.mockImplementation(async () => {
      setImmediate(() => { child.exitCode = 1; child.emit('exit', 1); });
      return new Response(JSON.stringify({ status: 'degraded', database: 'unavailable' }));
    });
    assert.equal((await manager.start()).running, false);
  });
});

test('concurrent startup is coalesced and stop waits for child exit', async () => {
  await withManager(async ({ manager, spawned }) => {
    const [a, b] = await Promise.all([manager.start(), manager.start()]);
    assert.equal(a.running, true);
    assert.equal(a.pid, b.pid);
    assert.equal(spawned.mock.callCount(), 1);
    await Promise.all([manager.stop(), manager.stop()]);
    assert.equal(manager.getStatus().pid, null);
  });
});

function payloadFixture(run) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'javo-package-'));
  const project = path.join(root, 'apps/windows');
  const runtime = path.join(project, 'build/runtime/javo-runtime');
  for (const name of ['apps/dashboard/dist/index.html', 'packages/brand-assets/icons/dist/javo-app.ico',
                      'services/local-runtime/app/main.py', 'services/local-runtime/desktop_entry.py',
                      'services/local-runtime/pyproject.toml', 'services/local-runtime/requirements.txt',
                      'apps/windows/build/runtime/javo-runtime/javo-runtime.exe',
                      'apps/windows/build/runtime/javo-runtime/_internal/python311.dll']) {
    const filename = path.join(root, name);
    fs.mkdirSync(path.dirname(filename), { recursive: true }); fs.writeFileSync(filename, 'fixture');
  }
  const digest = createHash('sha256').update('fixture').digest('hex');
  const manifest = { schema: 1, platform: 'win32', arch: 'x64',
    self_test: { result: 'RUNTIME_IMPORTS_OK', agents: 30 },
    files: { 'javo-runtime.exe': digest, '_internal/python311.dll': digest },
    source_files: { 'app/main.py': digest, 'desktop_entry.py': digest,
                    'pyproject.toml': digest, 'requirements.txt': digest } };
  const write = () => fs.writeFileSync(path.join(runtime, 'runtime-manifest.json'), JSON.stringify(manifest));
  write();
  try { run({ project, runtime, manifest, write }); }
  finally { fs.rmSync(root, { recursive: true, force: true }); }
}

test('package preflight accepts complete checksum-verified payload fixture', () => {
  payloadFixture(({ project }) => assert.doesNotThrow(() => verifyPackage(project)));
});
test('package preflight rejects missing Python payload', () => {
  payloadFixture(({ project, runtime }) => {
    fs.unlinkSync(path.join(runtime, '_internal/python311.dll'));
    assert.throws(() => verifyPackage(project), /Missing desktop payload/);
  });
});
test('package preflight rejects tampered runtime', () => {
  payloadFixture(({ project, runtime }) => {
    fs.writeFileSync(path.join(runtime, 'javo-runtime.exe'), 'changed');
    assert.throws(() => verifyPackage(project), /checksum mismatch/);
  });
});
test('package preflight rejects paths outside the payload', () => {
  payloadFixture(({ project, manifest, write }) => {
    manifest.files['../../outside'] = 'x'; write();
    assert.throws(() => verifyPackage(project), /Unsafe path/);
  });
});
test('package preflight rejects unverified import checks', () => {
  payloadFixture(({ project, manifest, write }) => {
    manifest.self_test.result = 'failed'; write();
    assert.throws(() => verifyPackage(project), /incomplete or unverified/);
  });
});

test('package preflight rejects extra files absent from runtime manifest', () => {
  payloadFixture(({ project, runtime }) => {
    fs.writeFileSync(path.join(runtime, 'unexpected.env'), 'unverified');
    assert.throws(() => verifyPackage(project), /unverified payload/);
  });
});
test('package preflight rejects backend source changes after bundling', () => {
  payloadFixture(({ project }) => {
    fs.writeFileSync(path.resolve(project, '../../services/local-runtime/app/main.py'), 'changed');
    assert.throws(() => verifyPackage(project), /source changed/);
  });
});
test('package preflight rejects newly added backend modules absent from bundle', () => {
  payloadFixture(({ project }) => {
    fs.writeFileSync(path.resolve(project, '../../services/local-runtime/app/new.py'), 'new');
    assert.throws(() => verifyPackage(project), /source manifest is outdated/);
  });
});
test('package preflight rejects bundles with no source provenance', () => {
  payloadFixture(({ project, manifest, write }) => {
    delete manifest.source_files; write();
    assert.throws(() => verifyPackage(project), /source manifest is outdated/);
  });
});
