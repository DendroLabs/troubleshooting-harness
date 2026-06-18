#!/usr/bin/env python3
import asyncio
import json
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from harness.src.tools.base import build_context
from harness.interfaces.mcp.tool_registry import TOOL_DEFINITIONS
from harness.interfaces.mcp.tool_dispatch import build_dispatch

server = Server("tsh-harness")
ctx = build_context(REPO_ROOT)
dispatch = build_dispatch(ctx)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOL_DEFINITIONS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    handler = dispatch.get(name)
    if handler is None:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"})
        )]
    try:
        result = handler(**arguments)
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "tool": name})
        )]


async def main():
    async with stdio_server() as streams:
        await server.run(
            streams[0], streams[1],
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
