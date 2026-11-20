"""Real persistence/control/artifact paths behind explicitly synthetic service replies."""
import base64
import json

import pytest

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jBHoAAAAASUVORK5CYII=')


@pytest.fixture
def generation_service(monkeypatch):
    from app.services import studio
    calls, jobs = [], {}
    state = {'mode': 'queued', 'unsafe': False}
    async def request(cfg, method, route, *, payload=None, params=None, limit=1024*1024):
        calls.append((method, route, payload, params))
        if route.startswith('/object_info/'):
            name = route.split('/')[-1]
            required = {'ckpt_name': [['synthetic.safetensors']], 'unet_name': [['synthetic.safetensors']],
                        'clip_name': [['synthetic.safetensors']], 'vae_name': [['synthetic.safetensors']]}
            return json.dumps({name: {'input': {'required': required}}}).encode()
        if route == '/prompt':
            jobs[payload['prompt_id']] = payload['prompt']
            return json.dumps({'prompt_id': payload['prompt_id'], 'node_errors': {}}).encode()
        if route.startswith('/history/'):
            key = route.split('/')[-1]
            if state['mode'] == 'error':
                value = {key: {'status': {'status_str': 'error', 'completed': False}}}
            elif state['mode'] == 'completed':
                value = {key: {'status': {'status_str': 'success', 'completed': True}, 'outputs': {'7': {'images': [
                    {'filename': 'fixture.png', 'subfolder': '../escape' if state['unsafe'] else '', 'type': 'output'}]}}}}
            else:
                value = {}
            return json.dumps(value).encode()
        if route == '/queue':
            if method == 'POST':
                return b'{}'
            return json.dumps({'queue_pending': [[0, key] for key in jobs], 'queue_running': []}).encode()
        if route == '/view':
            return PNG
        raise AssertionError('Unexpected service request')
    monkeypatch.setattr(studio, 'request', request)
    return state, calls, jobs


def configure(client):
    result = client.put('/api/studio/configuration', json={'enabled': True,
        'image_checkpoint': 'synthetic.safetensors', 'video_unet': 'synthetic.safetensors',
        'video_clip': 'synthetic.safetensors', 'video_vae': 'synthetic.safetensors'})
    assert result.status_code == 200, result.text
    return result.json()


def inputs(cfg, kind='image'):
    return {'kind': kind, 'prompt': 'Synthetic test scene, not a real model-quality test.', 'reviewed': True,
            'configuration_fingerprint': cfg['fingerprint'], 'request_key': 'test-'+kind}


def test_reviewed_image_job_artifact_integrity_and_idempotent_restart(owner_runtime, generation_service):
    from app.services import studio
    create, _ = owner_runtime
    state, calls, _ = generation_service
    with create() as client:
        assert client.put('/api/studio/configuration', json={'base_url': 'https://remote.example'}).status_code == 422
        cfg = configure(client)
        data = inputs(cfg)
        assert client.post('/api/studio/jobs', json=data).status_code == 409
        client.post('/api/security/resume')
        assert client.post('/api/studio/jobs', json={**data, 'reviewed': 1}).status_code == 422
        result = client.post('/api/studio/jobs', json=data)
        assert result.status_code == 202, result.text
        row = result.json()
        assert row['status'] == 'queued' and not row['artifact_ready']
        assert not row['actions_executed']
        assert len([call for call in calls if call[1] == '/prompt']) == 1
        assert client.post('/api/studio/jobs', json=data).json()['id'] == row['id']
        assert len([call for call in calls if call[1] == '/prompt']) == 1
        assert client.post('/api/studio/jobs', json={**data, 'request_key': 'new'}).status_code == 409
        state['mode'] = 'completed'
        response = client.post('/api/studio/jobs/'+row['id']+'/refresh')
        assert response.status_code == 200, response.text
        assert response.json()['status'] == 'completed'
        artifact = client.get('/api/studio/jobs/'+row['id']+'/artifact')
        assert artifact.status_code == 200 and artifact.content == PNG
        assert artifact.headers['content-type'] == 'image/png'
        assert client.post('/api/studio/jobs', json=data).json()['status'] == 'completed'
    with create() as client:
        assert client.get('/api/studio/jobs').json()[0]['status'] == 'completed'
        assert client.get('/api/studio/jobs/'+row['id']+'/artifact').content == PNG
        (studio.artifact_root()/(row['id']+'.png')).write_bytes(b'corrupt')
        assert client.get('/api/studio/jobs/'+row['id']+'/artifact').status_code == 503


def test_video_graph_failure_and_unsafe_output_never_certify_success(owner_runtime, generation_service):
    create, _ = owner_runtime
    state, calls, _ = generation_service
    with create() as client:
        cfg = configure(client)
        client.post('/api/security/resume')
        response = client.post('/api/studio/jobs', json=inputs(cfg, 'video'))
        assert response.status_code == 202, response.text
        key = response.json()['id']
        graph = next(call[2]['prompt'] for call in calls if call[1] == '/prompt')
        assert graph['6']['class_type'] == 'EmptyHunyuanLatentVideo' and graph['11']['class_type'] == 'SaveVideo'
        assert all('API' not in node['class_type'] for node in graph.values())
        state['mode'] = 'error'
        assert client.post('/api/studio/jobs/'+key+'/refresh').json()['status'] == 'failed'
        assert client.get('/api/studio/jobs/'+key+'/artifact').status_code == 409
        state['mode'] = 'queued'
        image = client.post('/api/studio/jobs', json=inputs(cfg)).json()
        state.update(mode='completed', unsafe=True)
        assert client.post('/api/studio/jobs/'+image['id']+'/refresh').status_code == 503
        assert client.get('/api/studio/jobs').json()[0]['status'] != 'completed'


def test_queued_removal_is_not_running_interrupt_or_fake_completion(owner_runtime, generation_service):
    create, _ = owner_runtime
    _, calls, _ = generation_service
    with create() as client:
        cfg = configure(client)
        client.post('/api/security/resume')
        key = client.post('/api/studio/jobs', json=inputs(cfg)).json()['id']
        result = client.post('/api/studio/jobs/'+key+'/remove-queued')
        assert result.status_code == 200 and result.json()['status'] == 'cancel_requested'
        assert not any(call[1] == '/interrupt' for call in calls)
        assert client.post('/api/studio/jobs/'+key+'/abandon').status_code == 422
        assert client.post('/api/studio/jobs/'+key+'/abandon?confirmed=true').json()['status'] == 'abandoned'


def test_trend_refresh_parses_source_times_retains_snapshot_and_blocks_entities(owner_runtime, monkeypatch):
    import httpx
    import app.api.routes.studio as routes
    create, _ = owner_runtime
    real_client = httpx.AsyncClient
    payload = {'data': b'''<rss xmlns:ht="https://trends.google.com/trending/rss"><channel><item><title>Synthetic search trend</title><pubDate>Wed, 18 Nov 2026 10:00:00 GMT</pubDate><ht:approx_traffic>1000+</ht:approx_traffic></item></channel></rss>'''}
    def responder(request):
        assert request.url.host == 'trends.google.com' and request.url.params['geo'] in {'IN', 'US'}
        assert 'authorization' not in request.headers
        return httpx.Response(200, content=payload['data'])
    monkeypatch.setattr(routes.httpx, 'AsyncClient', lambda **kwargs: real_client(transport=httpx.MockTransport(responder), **kwargs))
    with create() as client:
        assert client.get('/api/studio/trends').json() is None
        result = client.post('/api/studio/trends/refresh')
        assert result.status_code == 200, result.text
        assert result.json()['items'][0]['approximate_traffic_label'] == '1000+'
        assert result.json()['items'][0]['published_at'].endswith('+00:00')
        assert client.post('/api/studio/trends/refresh').status_code == 429
        payload['data'] = b'<!DOCTYPE x [<!ENTITY example "untrusted">]><rss><channel><item><title>&example;</title></item></channel></rss>'
        assert client.post('/api/studio/trends/refresh?country=US').status_code == 503
        assert client.get('/api/studio/trends').json()['items'][0]['title'] == 'Synthetic search trend'
