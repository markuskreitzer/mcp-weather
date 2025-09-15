#!/usr/bin/env python3
"""
Test client for the mcp-weather HTTP transport.
Run this while the server is running with --http flag.
"""

import asyncio
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

async def test_http_client():
    """Test the HTTP transport client connection."""
    # Create HTTP transport
    transport = StreamableHttpTransport(url="http://localhost:8080/mcp")
    client = Client(transport)
    
    try:
        async with client:
            print("Connected to mcp-weather HTTP server!")
            
            # Test the tools
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")
            
            # Test weather lookup
            result = await client.call_tool("get_hourly_weather", {
                "location": "San Francisco, CA",
                "units": "imperial"
            })
            print(f"Weather result: {result}")
            
    except Exception as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    asyncio.run(test_http_client())