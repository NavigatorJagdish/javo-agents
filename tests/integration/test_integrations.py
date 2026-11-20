"""Actual scoped MCP, SQL review/dispatch and request-boundary contracts."""
import json
import sqlite3
from uuid import uuid4

import pytest


def graph(client):
    start, end = str(uuid4()), str(uuid4())
    result = client.post('/api/workflows/', json={'name': 'Reviewed integration graph', 'nodes': [
        {'id': start, 'node_type': 'trigger', 'label': 'Start', 'is_entry_point': True},
        {'id': end, 'node_type': 'end', 'label': 'End'}], 'edges': [{'source_node_id': start, 'target_node_id': end}]})
    assert result.status_code == 201, result.text
    return result.json()


def grant(client, scopes):
    response = client.post('/api/integrations/grants', json={'client': 'langgraph', 'label': 'Synthetic SDK client', 'scopes': scopes})
    assert response.status_code == 201, response.text
    return response.json()


def call(client, token, method, params=None, **kwargs):
    return client.post('/api/integrations/mcp', headers={'Authorization': 'Bearer '+token, **kwargs},
        json={'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})


def proposal(client, token, saved, key='first'):
    return call(client, token, 'tools/call', {'name': 'javo_propose_workflow', 'arguments': {
        'request_key': key, 'title': 'Reviewed local request', 'workflow_id': saved['id'],
        'expected_revision': saved['revision'], 'fingerprint': saved['fingerprint'], 'trigger_data': {'brief': 'Synthetic brief'}}})


def test_scoped_bridge_no_owner_privilege_or_secret_replay(owner_runtime):
    create, db = owner_runtime
    with create() as client:
        created = grant(client, ['read_status'])
        token = created['token']
        assert token not in client.get('/api/integrations/grants').text
        assert token.encode() not in db.read_bytes()
        assert call(client, token, 'initialize').json()['result']['protocolVersion'] == '2025-06-18'
        tools = call(client, token, 'tools/list').json()['result']['tools']
        assert [t['name'] for t in tools] == ['javo_runtime_status']
        status = call(client, token, 'tools/call', {'name': 'javo_runtime_status'}).json()
        assert json.loads(status['result']['content'][0]['text'])['paused'] is True
        assert 'error' in call(client, token, 'tools/call', {'name': 'javo_list_goals'}).json()
        assert client.post('/api/security/resume', headers={'Authorization': 'Bearer '+token}).status_code == 401
        assert call(client, token, 'initialize', origin='https://untrusted.invalid').status_code == 403
        assert client.post('/api/integrations/grants/'+created['id']+'/revoke').status_code == 200
        assert call(client, token, 'tools/list').status_code == 401
        catalog = client.get('/api/integrations/catalog').json()
        assert len(catalog['items']) == 11 and catalog['external_runtimes_verified'] is False
        assert next(i for i in catalog['items'] if i['id'] == 'agent-inbox')['archived']


def test_proposal_idempotency_owner_review_atomic_queue_and_repeat_refusal(owner_runtime):
    create, _ = owner_runtime
    with create() as client:
        saved = graph(client)
        key = grant(client, ['propose_workflow', 'read_workflows', 'read_goals'])['token']
        assert call(client, key, 'tools/call', {'name': 'javo_list_workflows'}).json()['result']
        assert call(client, key, 'tools/call', {'name': 'javo_list_goals'}).json()['result']
        response = proposal(client, key, saved)
        assert response.status_code == 200, response.text
        assert 'error' not in response.json(), response.text
        first = json.loads(response.json()['result']['content'][0]['text'])
        assert not first['actions_executed'] and first['requires_owner_review']
        preview = client.get('/api/integrations/proposals/'+first['id']+'/preview')
        assert preview.status_code == 200 and preview.json()['matches_reviewed_snapshot']
        assert preview.json()['definition']['name'] == saved['name']
        assert client.get('/api/integrations/proposals/'+first['id']+'/preview', headers={'Authorization': 'Bearer '+key}).status_code == 401
        second = json.loads(proposal(client, key, saved).json()['result']['content'][0]['text'])
        assert first['id'] == second['id']
        assert client.get('/api/workflows/'+saved['id']+'/executions').json() == []
        path = '/api/integrations/proposals/'+first['id']+'/review'
        assert client.post(path, headers={'Authorization': 'Bearer '+key}, json={'expected_revision': 1, 'decision': 'approve'}).status_code == 401
        result = client.post(path, json={'expected_revision': 1, 'decision': 'approve'})
        assert result.status_code == 200, result.text
        assert result.json()['status'] == 'approved' and result.json()['execution_id']
        runs = client.get('/api/workflows/'+saved['id']+'/executions').json()
        assert len(runs) == 1 and runs[0]['status'] == 'queued'
        assert client.post(path, json={'expected_revision': 1, 'decision': 'approve'}).status_code == 409
        exported = client.get('/api/integrations/exports/task-master').json()['master']['tasks']
        assert exported[0]['status'] == 'pending'  # Approved is never completed.
        assert key not in json.dumps(exported)


@pytest.mark.parametrize('invalid', ['changed_graph', 'revoked', 'expired'])
def test_stale_or_unauthorized_proposal_cannot_dispatch(owner_runtime, invalid):
    create, db = owner_runtime
    with create() as client:
        saved = graph(client)
        created = grant(client, ['propose_workflow'])
        response = proposal(client, created['token'], saved).json()
        item = json.loads(response['result']['content'][0]['text'])
        if invalid == 'revoked':
            client.post('/api/integrations/grants/'+created['id']+'/revoke')
        elif invalid == 'expired':
            with sqlite3.connect(db) as sql:
                sql.execute("UPDATE integration_proposals SET expires_at='2000-01-01' WHERE id=?", (item['id'],))
        else:
            body = {k: saved[k] for k in ['name', 'description', 'status', 'trigger_config', 'viewport', 'nodes', 'edges']}
            body.update(name='Changed graph', expected_revision=saved['revision'])
            assert client.put('/api/workflows/'+saved['id'], json=body).status_code == 200
        path = '/api/integrations/proposals/'+item['id']+'/review'
        assert client.post(path, json={'expected_revision': 1, 'decision': 'approve'}).status_code == 409
        assert client.get('/api/workflows/'+saved['id']+'/executions').json() == []
        assert client.post(path, json={'expected_revision': 1, 'decision': 'reject'}).status_code == 200


def test_host_upload_size_and_private_response_headers(owner_runtime):
    create, _ = owner_runtime
    with create() as client:
        assert client.get('/api/health/', headers={'Host': 'untrusted.invalid'}).status_code == 400
        assert client.post('/api/content/upload', headers={'Authorization': '', 'Content-Length': str(100*1024*1024)}, content=b'').status_code == 401
        assert client.post('/api/voice/tts', headers={'Content-Length': str(2*1024*1024)}, content=b'').status_code == 413
        result = client.get('/api/integrations/grants')
        assert result.headers['cache-control'] == 'no-store'
        assert result.headers['x-content-type-options'] == 'nosniff'
        assert result.headers['referrer-policy'] == 'no-referrer'


def test_own_result_scope_cannot_read_other_clients_proposals(owner_runtime):
    create, _ = owner_runtime
    with create() as client:
        saved = graph(client)
        first = grant(client, ['propose_workflow', 'read_own_results'])
        other = grant(client, ['propose_workflow', 'read_own_results'])
        response = proposal(client, first['token'], saved).json()
        item = json.loads(response['result']['content'][0]['text'])
        params = {'name': 'javo_get_my_proposal', 'arguments': {'proposal_id': item['id']}}
        assert 'result' in call(client, first['token'], 'tools/call', params).json()
        assert 'error' in call(client, other['token'], 'tools/call', params).json()
        no_results = grant(client, ['propose_workflow'])
        params['name'] = 'javo_get_my_workflow_result'
        assert 'error' in call(client, no_results['token'], 'tools/call', params).json()
        client.post('/api/integrations/proposals/'+item['id']+'/review', json={'expected_revision': 1, 'decision': 'approve'})
        own = json.loads(call(client, first['token'], 'tools/call', params).json()['result']['content'][0]['text'])
        assert own['execution']['execution_verified'] and own['execution']['status'] == 'queued'


def test_all_native_node_definitions_and_templates_are_truthful(owner_runtime):
    create, _ = owner_runtime
    with create() as client:
        nodes = client.get('/api/workflows/node-types').json()
        assert len(nodes) == 16
        assert {n['node_type'] for n in nodes if n['execution_available']} == {'trigger', 'ai_prompt', 'delay', 'end'}
        for template in client.get('/api/workflows/templates').json():
            created = client.post('/api/workflows/', json=template)
            assert created.status_code == 201, created.text
            assert created.json()['execution_available'] and created.json()['revision'] == 1
