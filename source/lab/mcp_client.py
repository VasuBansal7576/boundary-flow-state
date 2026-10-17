"""A short-lived real MCP client, with identity passed only by trusted code."""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .state import ROOT

async def invoke(arm, peer, action, request_id, port=None):
    env = {**os.environ, 'BOUNDARY_MCP_ARM': arm, 'BOUNDARY_MCP_AGENT': peer}
    if port is not None:
        env['BOUNDARY_MCP_PORT'] = str(port)
    params = StdioServerParameters(command=sys.executable, args=['-m', 'lab.mcp_server'], cwd=ROOT, env=env)
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as session:
            initialization = await session.initialize()
            tools = await session.list_tools()
            assert 'site_http' in {tool.name for tool in tools.tools}
            result = await session.call_tool('site_http', arguments={'method': action['method'], 'resource_path': action['path'], 'payload': action.get('payload', ''), 'request_id': request_id})
            if result.is_error:
                raise RuntimeError('MCP tool failed: ' + ' '.join(getattr(c, 'text', '') for c in result.content))
            body = result.structured_content
            if body is None:
                body = json.loads(next(c.text for c in result.content if getattr(c, 'text', None)))
            return body, {'protocol_version': initialization.protocol_version, 'server': initialization.server_info.model_dump(), 'discovered_tools': [tool.name for tool in tools.tools]}

def call(arm, peer, action, request_id, port=None):
    return asyncio.run(invoke(arm, peer, action, request_id, port))
