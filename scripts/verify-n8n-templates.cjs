// Contract harness for original Code/expression logic, not an n8n engine test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const flow = JSON.parse(fs.readFileSync(path.join(__dirname, '../integrations/n8n-reviewed-drafting.json'), 'utf8'));
const byName = new Map(flow.nodes.map(node => [node.name, node]));
assert.equal(flow.active, false);
assert.equal(byName.size, 17);
assert.equal(byName.get('Optional scheduled start').disabled, true);
for (const [source, outputs] of Object.entries(flow.connections)) {
  assert(byName.has(source));
  for (const group of outputs.main) for (const edge of group) assert(byName.has(edge.node));
}
const values = {};
function run(name, input, index = 0) {
  const source = byName.get(name).parameters.jsCode;
  const output = new Function('$input', '$', '$runIndex', source)(
    {first: () => ({json: input})}, ref => ({first: () => ({json: values[ref]})}), index);
  values[name] = output[0].json;
  return output[0].json;
}
// Compile every prepared Code node and expression before evaluating contracts.
for (const node of flow.nodes) {
  if (node.type.endsWith('.code')) new Function('$input', '$', '$runIndex', node.parameters.jsCode);
  if (node.type.endsWith('.httpRequest')) {
    assert.equal(node.parameters.authentication, 'genericCredentialType');
    assert.equal(node.credentials, undefined);
    assert(!node.parameters.jsonBody.slice(3,-2).includes('}}'), 'Nested JavaScript object closes must not terminate an n8n expression early');
    new Function('$', '$json', '$execution', 'return '+node.parameters.jsonBody.slice(3,-2));
  }
}
const brief = {...run('Set brief', {}), workflow_id: '12345678-1234-1234-1234-123456789abc'};
run('Validate input', brief);
for (const base_url of ['https://evil.invalid', 'http://localhost.evil.invalid', 'http://127.0.0.1@evil.invalid']) {
  assert.throws(() => run('Validate input', {...brief, base_url}));
}
assert.throws(() => run('Validate input', {...brief, brief:'x'.repeat(2001)}));
const rpc = obj => ({result:{content:[{text:JSON.stringify(obj)}]}});
assert.equal(run('Inspect actual status', rpc({status:'pending'}),29).continue_wait, false);
assert.equal(run('Inspect actual status', rpc({status:'pending'}),0).continue_wait, true);
assert.equal(run('Inspect actual status', rpc({status:'rejected'}),0).terminal, true);
assert.equal(run('Inspect actual status', rpc({status:'approved', execution_status:'failed'})).terminal, true);
assert.throws(() => run('Report verified local result', rpc({execution:{status:'queued'}})));
assert.equal(run('Report verified local result',rpc({id:'p',execution_id:'e',execution:{status:'completed',execution_verified:true,execution_log:[]}})).status,'completed');
assert.equal(flow.connections['Still eligible to wait?'].main[1][0].node, 'Stop without replay');
assert.equal(flow.connections['Completed actual run?'].main[1][0].node, 'Still eligible to wait?');
console.log('N8N_TEMPLATE_STRUCTURE_INPUT_FAILURE_BOUNDED_WAIT_RESULT_CONTRACTS_OK; external engine acceptance still required.');
