"""Dependency-free MCP stdio adapter to Javo's scoped local HTTP bridge."""
from __future__ import annotations

import json
import os
import sys
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def main():
    base = os.environ.get('JAVO_INTEGRATION_BASE', 'http://127.0.0.1:8000')
    url = urlsplit(base)
    token = os.environ.get('JAVO_INTEGRATION_TOKEN', '')
    if url.scheme != 'http' or url.hostname not in {'127.0.0.1', 'localhost'} or url.path not in {'', '/'} or url.query or url.fragment or url.username or url.password:
        raise ValueError('Only a local Javo endpoint is accepted')
    if not token.startswith('javo_client_'):
        raise ValueError('A separate scoped client grant is required')
    opener = build_opener(ProxyHandler({}), NoRedirect())
    while line := sys.stdin.buffer.readline(32770):
        if len(line) > 32768 or not line.endswith(b'\n'):
            raise ValueError('MCP message limit exceeded')
        message = json.loads(line)
        if not isinstance(message, dict):
            raise ValueError('MCP request must be an object')
        try:
            request = Request(base.rstrip('/')+'/api/integrations/mcp', data=line, method='POST',
                headers={'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Bearer '+token})
            with opener.open(request, timeout=20) as response:
                result = response.read(1024*1024+1)
            if len(result) > 1024*1024:
                raise ValueError('MCP response limit exceeded')
            if 'id' in message:
                print(json.dumps(json.loads(result)), flush=True)
        except Exception:
            if 'id' in message:
                print(json.dumps({'jsonrpc': '2.0', 'id': message['id'], 'error': {'code': -32000,
                    'message': 'Local bridge unavailable or request refused; check grant, scope and runtime.'}}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Javo scoped MCP proxy stopped; check local configuration.', file=sys.stderr)
        sys.exit(1)
