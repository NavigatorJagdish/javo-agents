"""Create Javo-authored inactive n8n workflows; does not install or run n8n."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    nodes, connections = [], {}
    def node(name, kind, parameters, version=2, *, disabled=False):
        index = len(nodes)
        value = {'id': 'javo-'+str(index+1), 'name': name, 'type': 'n8n-nodes-base.'+kind,
            'typeVersion': version, 'position': [240+(index%5)*260, 260+(index//5)*220], 'parameters': parameters}
        if disabled:
            value['disabled'] = True
        if kind not in {'manualTrigger', 'scheduleTrigger', 'stopAndError'}:
            value['onError'] = 'continueErrorOutput'
        nodes.append(value)
        return name
    def connect(source, target, output=0):
        outputs = connections.setdefault(source, {'main': []})['main']
        while len(outputs) <= output:
            outputs.append([])
        outputs[output].append({'node': target, 'type': 'main', 'index': 0})
    def code(name, source):
        return node(name, 'code', {'jsCode': source, 'mode': 'runOnceForAllItems'})
    def http(name, body):
        return node(name, 'httpRequest', {'method': 'POST', 'url': "={{ $('Validate input').first().json.base_url + '/api/integrations/mcp' }}",
            'authentication': 'genericCredentialType', 'genericAuthType': 'httpHeaderAuth', 'sendBody': True,
            'specifyBody': 'json', 'jsonBody': body, 'options': {'timeout': 15000}}, 4.2)
    def condition(name, expression):
        return node(name, 'if', {'conditions': {'options': {'caseSensitive': True, 'leftValue': '', 'typeValidation': 'strict', 'version': 2},
            'conditions': [{'id': 'condition', 'leftValue': expression, 'rightValue': True, 'operator': {'type': 'boolean', 'operation': 'true', 'singleValue': True}}], 'combinator': 'and'}}, 2.2)
    node('Manual start', 'manualTrigger', {}, 1)
    node('Optional scheduled start', 'scheduleTrigger', {'rule': {'interval': [{'field': 'cronExpression', 'expression': '0 9 * * *'}]}}, 1.2, disabled=True)
    code('Set brief', "return [{json:{base_url:'http://127.0.0.1:8000',workflow_id:'REPLACE_WITH_SAVED_JAVO_WORKFLOW_ID',brief:'Write a short original caption from these verified facts.',max_polls:30}}];")
    code('Validate input', "const v=$input.first().json;if(!/^http:\\/\\/(127\\.0\\.0\\.1|localhost)(:\\d+)?$/.test(v.base_url)||! /^[a-f0-9-]{36}$/.test(v.workflow_id)||typeof v.brief!=='string'||!v.brief.trim()||v.brief.length>2000)throw new Error('Set a local endpoint, saved workflow UUID and bounded brief.');return [{json:{...v,max_polls:Math.max(1,Math.min(30,Number(v.max_polls)||30))}}];")
    http('Read saved workflows', "={{ JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'javo_list_workflows',arguments:{}}}) }}")
    code('Select exact saved revision', "const r=$input.first().json;if(r.error||r.result?.isError)throw new Error('Workflow read refused');const rows=JSON.parse(r.result.content[0].text);const id=$('Validate input').first().json.workflow_id;const v=rows.find(x=>x.id===id&&x.execution_available);if(!v)throw new Error('Choose an executable workflow from the first20 saved entries.');return [{json:v}];")
    http('Submit owner review proposal', "={{ JSON.stringify({jsonrpc:'2.0',id:2,method:'tools/call',params:{name:'javo_propose_workflow',arguments:{request_key:'n8n_'+$execution.id,title:'Reviewed draft from n8n',workflow_id:$json.id,expected_revision:$json.revision,fingerprint:$json.fingerprint,trigger_data:{brief:$('Validate input').first().json.brief}}}}) }}")
    code('Keep proposal reference', "const r=$input.first().json;if(r.error||r.result?.isError)throw new Error('Proposal refused');const p=JSON.parse(r.result.content[0].text);if(!p.id||p.actions_executed!==false)throw new Error('Missing truthful proposal receipt');return [{json:{proposal_id:p.id,attempts:0}}];")
    node('Wait for review or execution', 'wait', {'resume': 'timeInterval', 'amount': 10, 'unit': 'seconds'}, 1.1)
    http('Read own proposal status', "={{ JSON.stringify({jsonrpc:'2.0',id:3,method:'tools/call',params:{name:'javo_get_my_proposal',arguments:{proposal_id:$('Keep proposal reference').first().json.proposal_id}}}) }}")
    code('Inspect actual status', "const r=$input.first().json;if(r.error||r.result?.isError)throw new Error('Status read refused');const p=JSON.parse(r.result.content[0].text);const n=$runIndex+1;return [{json:{...p,attempts:n,done:p.execution_status==='completed',terminal:p.status==='rejected'||['failed','cancelled'].includes(p.execution_status),continue_wait:n<$('Validate input').first().json.max_polls}}];")
    condition('Completed actual run?', '={{ $json.done }}')
    condition('Still eligible to wait?', '={{ !$json.terminal && $json.continue_wait }}')
    http('Fetch own reviewed result', "={{ JSON.stringify({jsonrpc:'2.0',id:4,method:'tools/call',params:{name:'javo_get_my_workflow_result',arguments:{proposal_id:$('Keep proposal reference').first().json.proposal_id}}}) }}")
    code('Report verified local result', "const r=$input.first().json;if(r.error||r.result?.isError)throw new Error('Result read refused');const p=JSON.parse(r.result.content[0].text);if(p.execution?.status!=='completed'||p.execution?.execution_verified!==true)throw new Error('No completed verified receipt');return [{json:{proposal_id:p.id,execution_id:p.execution_id,status:'completed',outputs:p.execution.execution_log,actions_executed:false,source:'Actual reviewed Javo local workflow'}}];")
    node('Stop without replay', 'stopAndError', {'errorMessage': 'Review rejected, execution failed or bounded wait expired. Inspect the existing Javo receipt; never resubmit automatically.'}, 1)
    code('Safe error report', "return [{json:{status:'failed_or_unconfirmed',message:'Inspect the existing Javo proposal/run receipt. No automatic approval, retry, publication or completed action is inferred.'}}];")
    names = [n['name'] for n in nodes]
    for source, target in [('Manual start','Set brief'),('Optional scheduled start','Set brief'),('Set brief','Validate input'),('Validate input','Read saved workflows'),('Read saved workflows','Select exact saved revision'),('Select exact saved revision','Submit owner review proposal'),('Submit owner review proposal','Keep proposal reference'),('Keep proposal reference','Wait for review or execution'),('Wait for review or execution','Read own proposal status'),('Read own proposal status','Inspect actual status'),('Inspect actual status','Completed actual run?'),('Completed actual run?','Fetch own reviewed result'),('Fetch own reviewed result','Report verified local result'),('Still eligible to wait?','Wait for review or execution')]:
        connect(source, target)
    connect('Completed actual run?', 'Still eligible to wait?', 1)
    connect('Still eligible to wait?', 'Stop without replay', 1)
    for item in nodes:
        if item.get('onError') == 'continueErrorOutput' and item['name'] != 'Safe error report':
            # Code/HTTP nodes expose an error output; IF's second output is its
            # false branch, so retain the explicit condition paths instead.
            if item['type'].endswith('.if'):
                item.pop('onError', None)
            else:
                connect(item['name'], 'Safe error report', 1)
    assert len(names) == len(set(names))
    workflow = {'name': 'Javo reviewed local drafting — complete manual bridge', 'nodes': nodes, 'connections': connections,
        'active': False, 'settings': {'executionOrder': 'v1', 'timezone': 'Asia/Kolkata'}}
    target = ROOT/'integrations/n8n-reviewed-drafting.json'
    target.write_text(json.dumps(workflow, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print('N8N_REVIEWED_TEMPLATE_PREPARED: '+str(len(nodes))+' nodes; inactive; external engine acceptance required.')


if __name__ == '__main__':
    main()
