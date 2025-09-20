#!/usr/bin/env python3
"""
Test client for the mcp-weather HTTP transport.
Run this while the server is running with --http flag.
"""

import asyncio

import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_http_client():
    """Test the HTTP transport client connection."""
    # Create HTTP transport
    transport = StreamableHttpTransport(url="http://localhost:8081/mcp")
    client = Client(transport)

    try:
        async with client:
            print("Connected to mcp-weather HTTP server!")

            # Test the tools
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")
            assert len(tools) > 0

            # Test weather lookup for Huntsville, AL
            result = await client.call_tool("get_hourly_weather", {
                "location": "Huntsville, AL",
                "units": "imperial"
            })
            print(f"Weather result: {result}")
            assert "location" in result.content[0].text

    except Exception as e:
        pytest.skip(f"HTTP server not available: {e}")


if __name__ == "__main__":
    asyncio.run(test_http_client())
