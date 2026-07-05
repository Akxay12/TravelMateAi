import sys
import os
import json
import asyncio
from mcp.server.fastmcp import FastMCP

# Ensure the backend directory is in the import path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from agent.tools.discovery_tool import DiscoveryTool
from services.geocoding_service import resolve_coordinates

mcp = FastMCP("Discovery MCP Server")
discovery_tool = DiscoveryTool()

async def safe_resolve(destination: str):
    try:
        await resolve_coordinates(destination)
    except Exception:
        pass

@mcp.tool()
async def discover_places(
    lat: float,
    lon: float,
    destination: str,
    interests: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None
) -> str:
    """
    Discover local attractions and places using the OSM and Wikivoyage APIs.
    Delegates to the DiscoveryTool.
    """
    await safe_resolve(destination)
    results = await discovery_tool.run(
        lat=lat,
        lon=lon,
        destination=destination,
        interests=interests,
        start_date=start_date,
        end_date=end_date
    )
    # Serialize to JSON string for transmission over MCP stdio
    return json.dumps([item.model_dump() for item in results])

@mcp.tool()
async def search_destination(lat: float, lon: float, destination: str) -> str:
    """
    Search for attractions in a destination using OSM and Wikivoyage.
    Delegates to the DiscoveryTool.
    """
    await safe_resolve(destination)
    results = await discovery_tool.run(lat=lat, lon=lon, destination=destination)
    return json.dumps([item.model_dump() for item in results])

@mcp.tool()
async def search_by_interest(lat: float, lon: float, destination: str, interests: str) -> str:
    """
    Search for attractions in a destination filtered by specific interests.
    Delegates to the DiscoveryTool.
    """
    await safe_resolve(destination)
    results = await discovery_tool.run(lat=lat, lon=lon, destination=destination, interests=interests)
    return json.dumps([item.model_dump() for item in results])

if __name__ == "__main__":
    mcp.run()

