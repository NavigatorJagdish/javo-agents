// electron-builder beforePack hook. A source-only package is not installable.
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');

function verifyPackage(projectDir) {
  const root = path.resolve(projectDir, '../..');
  const runtime = path.join(projectDir, 'build/runtime/javo-runtime');
  const requireFile = filename => {
    if (!fs.statSync(filename, { throwIfNoEntry: false })?.isFile()) {
      throw new Error(`Missing desktop payload: ${filename}. See docs/WINDOWS_PACKAGING.md.`);
    }
  };
  requireFile(path.join(root, 'apps/dashboard/dist/index.html'));
  requireFile(path.join(root, 'packages/brand-assets/icons/dist/javo-app.ico'));
  requireFile(path.join(runtime, 'javo-runtime.exe'));
  const manifestPath = path.join(runtime, 'runtime-manifest.json');
  requireFile(manifestPath);
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  if (manifest.schema !== 1 || manifest.platform !== 'win32' || manifest.arch !== 'x64'
      || manifest.self_test?.result !== 'RUNTIME_IMPORTS_OK'
      || manifest.self_test?.agents !== 30 || !manifest.files
      || !Object.hasOwn(manifest.files, 'javo-runtime.exe')
      || !Object.keys(manifest.files).some(name => /^_internal\/python3\d+\.dll$/.test(name))) {
    throw new Error('Bundled Python runtime manifest is incomplete or unverified.');
  }
  for (const [name, expected] of Object.entries(manifest.files)) {
    const filename = path.resolve(runtime, name);
    const relative = path.relative(runtime, filename);
    if (relative.startsWith('..') || path.isAbsolute(relative) || relative === 'runtime-manifest.json') {
      throw new Error('Unsafe path in runtime manifest.');
    }
    requireFile(filename);
    if (fs.lstatSync(filename).isSymbolicLink()
        || createHash('sha256').update(fs.readFileSync(filename)).digest('hex') !== expected) {
      throw new Error(`Runtime payload checksum mismatch: ${name}`);
    }
  }
}

module.exports = async context => verifyPackage(context.packager.projectDir);
module.exports.verifyPackage = verifyPackage;
if (require.main === module) verifyPackage(path.resolve(__dirname, '..'));
