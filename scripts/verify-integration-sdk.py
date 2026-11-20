"""Run optional official LangGraph/MCP clients against an isolated actual server."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from verification_runtime import ROOT, clean_environment, isolated_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-python', required=True, type=Path)
    args = parser.parse_args()
    with isolated_runtime() as (base, request):
        grant = request('/api/integrations/grants', {'client': 'langgraph', 'label': 'Isolated SDK verification', 'scopes': ['read_status']})
        env = clean_environment()
        env.update(JAVO_INTEGRATION_BASE=base, JAVO_INTEGRATION_TOKEN=grant['token'])
        result = subprocess.run([str(args.sdk_python.resolve()), str(ROOT/'integrations/clients/langgraph_bridge.py')], env=env, cwd=ROOT, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            # This harness contains synthetic data only; redact its disposable
            # grant even if an SDK error embeds request headers.
            print((result.stderr+result.stdout)[-7000:].replace(grant['token'], '[redacted disposable grant]'), file=sys.stderr)
            raise RuntimeError('Official SDK integration failed; inspect protocol compatibility using the isolated profile')
        evidence = json.loads(result.stdout.strip().splitlines()[-1])
        assert evidence['marker'] == 'REAL_LANGGRAPH_MCP_SCOPED_STATUS_OK'
        assert evidence['runtime']['paused'] is True and evidence['actions_executed'] is False
        messages = [{'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list', 'params': {}}]
        proxy = subprocess.run([str(args.sdk_python.resolve()), str(ROOT/'integrations/clients/mcp_stdio_proxy.py')],
            input=''.join(json.dumps(v)+'\n' for v in messages), env=env, capture_output=True, text=True, timeout=30)
        assert proxy.returncode == 0
        tools = json.loads(proxy.stdout)['result']['tools']
        assert [tool['name'] for tool in tools] == ['javo_runtime_status']
        request('/api/integrations/grants/'+grant['id']+'/revoke', {}, method='POST')
        print(json.dumps({**evidence, 'stdio_marker': 'SCOPED_STDIO_PROXY_PROTOCOL_OK'}))


if __name__ == '__main__':
    main()
