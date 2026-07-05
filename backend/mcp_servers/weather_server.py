import sys
import os
import json
import asyncio
from mcp.server.fastmcp import FastMCP

# Ensure the backend directory is in the import path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from agent.tools.travel_safety_tool import TravelSafetyTool

mcp = FastMCP("Weather MCP Server")
travel_safety_tool = TravelSafetyTool()

@mcp.tool()
async def get_weather(lat: float, lon: float, start_date: str, end_date: str) -> str:
    """
    Get weather summary for a destination and date range.
    Delegates to TravelSafetyTool.
    """
    res = await travel_safety_tool.run(lat=lat, lon=lon, start_date=start_date, end_date=end_date)
    return json.dumps(res.weather_summary.model_dump())

@mcp.tool()
async def get_travel_safety(lat: float, lon: float, start_date: str, end_date: str) -> str:
    """
    Get travel safety assessment and risk level.
    Delegates to TravelSafetyTool.
    """
    res = await travel_safety_tool.run(lat=lat, lon=lon, start_date=start_date, end_date=end_date)
    return json.dumps({
        "risk_level": res.risk_level,
        "travel_advisories": res.travel_advisories
    })

@mcp.tool()
async def packing_recommendations(lat: float, lon: float, start_date: str, end_date: str) -> str:
    """
    Get packing recommendations based on weather forecast.
    Delegates to TravelSafetyTool.
    """
    res = await travel_safety_tool.run(lat=lat, lon=lon, start_date=start_date, end_date=end_date)
    return json.dumps(res.packing_suggestions)

if __name__ == "__main__":
    mcp.run()
