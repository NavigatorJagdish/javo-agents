"""Bound uploads before multipart parsing and reject untrusted host names."""
from __future__ import annotations

import tempfile

from starlette.responses import JSONResponse

from app.core.local_auth import is_valid_owner_token
from app.config import get_settings


class LocalHttpBoundary:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        path = scope.get('path', '/')
        headers = {k.decode('latin-1').lower(): v.decode('latin-1') for k, v in scope.get('headers', [])}
        method = scope.get('method', 'GET')
        # Keep auth ahead of body parsing. Static dashboard and public status
        # need no bearer token; the MCP bridge uses its own scoped validator.
        public = path in {'/', '/auth/status', '/docs', '/redoc', '/openapi.json', '/docs/oauth2-redirect'} or path.startswith('/dashboard/')
        mcp = path.rstrip('/') == '/api/integrations/mcp'
        if not public and not mcp and method != 'OPTIONS' and not is_valid_owner_token(headers.get('authorization')):
            configured = get_settings().owner_access_token
            code = 503 if not configured or len(configured.get_secret_value()) < 32 else 401
            return await JSONResponse({'detail': 'Local authorization required' if code == 401 else 'Local access is not configured. Start with the secure launcher.'}, status_code=code)(scope, receive, send)
        limit = 64 * 1024 * 1024 if path.rstrip('/') in {'/content/upload', '/api/content/upload'} else 4 * 1024 * 1024 if path.rstrip('/') in {'/voice/transcribe', '/api/voice/transcribe'} else 1024 * 1024
        if mcp:
            limit = 32768
        try:
            size = int(headers.get('content-length', '0'))
            if size < 0:
                raise ValueError('Negative length')
        except ValueError:
            return await JSONResponse({'detail': 'Invalid request length'}, status_code=400)(scope, receive, send)
        if size > limit:
            return await JSONResponse({'detail': 'Request exceeds its supported size limit'}, status_code=413)(scope, receive, send)

        async def private_send(message):
            if message['type'] == 'http.response.start':
                extra = {b'x-content-type-options': b'nosniff', b'referrer-policy': b'no-referrer', b'x-frame-options': b'DENY'}
                if not path.startswith('/dashboard/'):
                    extra[b'cache-control'] = b'no-store'
                message['headers'] = [(key, value) for key, value in message.get('headers', []) if key.lower() not in extra] + list(extra.items())
            await send(message)

        # Spooled storage caps memory even for valid content uploads. Reading
        # the bounded body first avoids parsers masking an over-limit exception.
        with tempfile.SpooledTemporaryFile(max_size=1024*1024) as spool:
            total = 0
            while True:
                message = await receive()
                if message['type'] == 'http.disconnect':
                    return
                chunk = message.get('body', b'')
                total += len(chunk)
                if total > limit:
                    return await JSONResponse({'detail': 'Request exceeds its supported size limit'}, status_code=413)(scope, receive, send)
                spool.write(chunk)
                if not message.get('more_body', False):
                    break
            spool.seek(0)
            delivered = False
            async def replay():
                nonlocal delivered
                if delivered:
                    return await receive()
                chunk = spool.read(65536)
                more = spool.tell() < total
                if not more:
                    delivered = True
                return {'type': 'http.request', 'body': chunk, 'more_body': more}
            await self.app(scope, replay, private_send)
