"""Optional real LangGraph + MCP SDK read path. No LLM or cloud account used."""
from __future__ import annotations

import asyncio
import json
import os
import time
from typing import TypedDict
from urllib.parse import urlsplit

import httpx2
from langgraph.graph import StateGraph, START, END
from langsmith import tracing_context
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


class State(TypedDict):
    runtime: dict


async def main():
    base = os.environ.get('JAVO_INTEGRATION_BASE', 'http://127.0.0.1:8000')
    url = urlsplit(base)
    if url.scheme != 'http' or url.hostname not in {'127.0.0.1', 'localhost'} or url.path not in {'', '/'} or url.query or url.fragment or url.username or url.password:
        raise ValueError('This example accepts an explicit local loopback Javo endpoint only')
    token = os.environ.get('JAVO_INTEGRATION_TOKEN', '')
    if not token.startswith('javo_client_'):
        raise ValueError('Provide a separate read_status client grant, never the owner token')
    began = time.monotonic()
    async with httpx2.AsyncClient(headers={'Authorization': 'Bearer '+token}, trust_env=False, follow_redirects=False, timeout=20) as client:
        async with streamable_http_client(base.rstrip('/')+'/api/integrations/mcp', http_client=client) as streams:
            read, write = streams[:2]
            async with ClientSession(read, write) as session:
                await session.initialize()
                available = await session.list_tools()
                if 'javo_runtime_status' not in {tool.name for tool in available.tools}:
                    raise ValueError('This client needs read_status scope')
                async def read_runtime(state: State):
                    result = await session.call_tool('javo_runtime_status', {})
                    if result.is_error:
                        raise ValueError('Javo refused the status read')
                    return {'runtime': json.loads(result.content[0].text)}
                graph = StateGraph(State)
                graph.add_node('read_permitted_status', read_runtime)
                graph.add_edge(START, 'read_permitted_status')
                graph.add_edge('read_permitted_status', END)
                # Never inherit optional cloud tracing for owner runtime data.
                with tracing_context(enabled=False):
                    result = await graph.compile().ainvoke({'runtime': {}}, config={'recursion_limit': 3})
                print(json.dumps({'marker': 'REAL_LANGGRAPH_MCP_SCOPED_STATUS_OK',
                    'seconds': round(time.monotonic()-began, 3), 'runtime': result['runtime'],
                    'cloud_execution': False, 'actions_executed': False}))


if __name__ == '__main__':
    asyncio.run(main())
