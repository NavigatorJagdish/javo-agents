// Original build-time mitigation for GHSA-fc5q-39xc-vjpf while no patched
// release exists. Upstream MIT notices stay intact. No runtime app code copied.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = fs.realpathSync(path.resolve(process.cwd(), 'node_modules'));
const seen = new Set();
const packages = [];
const guard = `
  // JAVO_BUILD_GLOB_GUARD_V1: refuse repeated extglobs before regex creation.
  if (typeof input === 'string' && (input.length > 4096 || /[+*]\\(/.test(input))) {
    const unsafe = new SyntaxError('Javo build refuses repeated extglobs or oversized patterns');
    unsafe.code = 'JAVO_UNSAFE_BUILD_GLOB';
    throw unsafe;
  }
`;
function inspectPackage(directory) {
  const resolved = fs.realpathSync(directory);
  if (resolved !== root && !resolved.startsWith(root + path.sep)) return;
  const manifest = path.join(directory, 'package.json');
  if (fs.existsSync(manifest)) {
    const info = JSON.parse(fs.readFileSync(manifest, 'utf8'));
    if (info.name === 'picomatch') {
      assert.equal(info.license, 'MIT', 'Review changed dependency licensing before applying a patch');
      packages.push({directory, version: info.version});
      const targets = [['lib/parse.js', 'const parse = (input, options) => {'],
        ['lib/picomatch.js', 'picomatch.makeRe = (input, options = {}, returnOutput = false, returnState = false) => {']];
      for (const [relative, anchor] of targets) {
        const target = path.join(directory, relative);
        const text = fs.readFileSync(target, 'utf8');
        assert.equal(text.split(anchor).length, 2, 'Unsupported dependency shape; review before building');
        if (!text.includes('JAVO_BUILD_GLOB_GUARD_V1')) fs.writeFileSync(target, text.replace(anchor, anchor+guard));
        else assert(text.includes(anchor+guard), 'Existing dependency guard differs from the reviewed patch');
      }
    }
  }
  const nested = path.join(directory, 'node_modules');
  if (fs.existsSync(nested)) scan(nested);
}
function scan(directory) {
  const resolved = fs.realpathSync(directory);
  if (seen.has(resolved)) return;
  seen.add(resolved);
  for (const entry of fs.readdirSync(directory, {withFileTypes: true})) {
    if (!entry.isDirectory() || entry.name.startsWith('.')) continue;
    const target = path.join(directory, entry.name);
    if (entry.name.startsWith('@')) {
      for (const child of fs.readdirSync(target, {withFileTypes: true})) if (child.isDirectory()) inspectPackage(path.join(target, child.name));
    } else inspectPackage(target);
  }
}
scan(root);
assert(packages.length > 0, 'No expected build matcher found; review dependency changes');
for (const item of packages) {
  const matcher = require(item.directory);
  for (const pattern of ['+(*)', '+(*a)', '*(a*)', '**/'+ '*'.repeat(4100)]) {
    assert.throws(() => matcher.makeRe(pattern), error => error.code === 'JAVO_UNSAFE_BUILD_GLOB');
    assert.throws(() => matcher.parse(pattern), error => error.code === 'JAVO_UNSAFE_BUILD_GLOB');
  }
  assert(matcher('**/*.ts')('src/voice.ts'));
  assert(!matcher('**/*.ts')('src/image.png'));
}
console.log('BUILD_GLOB_REDOS_GUARD_OK: '+packages.length+' installed matchers checked; upstream advisory remains recorded.');
