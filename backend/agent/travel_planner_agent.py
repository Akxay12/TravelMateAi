from models.schemas import AttractionItem, ItineraryRequest, ItineraryResponse
from agent.tools.geocoding_tool import GeocodingTool
from agent.tools.attraction_tool import AttractionTool
from agent.tools.ranking_tool import RankingTool
from agent.tools.budget_tool import BudgetTool, BudgetEstimateResult
from agent.tools.travel_safety_tool import TravelSafetyTool, TravelSafetyResult
from agent.tools.discovery_tool import DiscoveryTool
from agent.tools.itinerary_tool import ItineraryTool

class TravelPlannerAgent:
    """
    Coordinates geocoding, attraction fetching, ranking, budget estimation, and travel safety.
    Prepares the application for future Google ADK integration.
    """
    
    def __init__(
        self,
        geocoding_tool: GeocodingTool | None = None,
        attraction_tool: AttractionTool | None = None,
        ranking_tool: RankingTool | None = None,
        budget_tool: BudgetTool | None = None,
        travel_safety_tool: TravelSafetyTool | None = None,
        discovery_tool: DiscoveryTool | None = None,
        itinerary_tool: ItineraryTool | None = None,
        bypass_adk: bool = False,
    ) -> None:
        self.bypass_adk = bypass_adk
        self.geocoding_tool = geocoding_tool or GeocodingTool()
        self.attraction_tool = attraction_tool or AttractionTool()
        self.ranking_tool = ranking_tool or RankingTool()
        self.budget_tool = budget_tool or BudgetTool()
        self.travel_safety_tool = travel_safety_tool or TravelSafetyTool()
        self.discovery_tool = discovery_tool or DiscoveryTool(attraction_tool=self.attraction_tool)
        self.itinerary_tool = itinerary_tool or ItineraryTool(
            budget_tool=self.budget_tool,
            travel_safety_tool=self.travel_safety_tool,
        )

    async def discover_destination(self, destination: str) -> tuple[float, float]:
        """Discover destination coordinates using Geocoding Tool."""
        return await self.geocoding_tool.run(destination)

    async def fetch_attractions(
        self, lat: float, lon: float, destination: str
    ) -> list[AttractionItem]:
        """Fetch attractions using OSM Attraction Tool directly (legacy)."""
        return await self.attraction_tool.run(lat, lon, destination)

    async def discover_attractions(
        self,
        lat: float,
        lon: float,
        destination: str,
        interests: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[AttractionItem]:
        """Fetch and merge attractions from OSM and Wikivoyage using Discovery Tool via Discovery MCP Server, falling back to local run if unavailable."""
        if not self.bypass_adk:
            try:
                from agent.adk_agent import run_discovery_adk
                return await run_discovery_adk(
                    destination=destination,
                    interests=interests,
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Google ADK attraction discovery failed: {e}. Falling back to legacy orchestration.")
        try:
            import os
            import sys
            import json
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
            
            # Determine path to discovery_server.py
            agent_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(agent_dir)
            server_path = os.path.join(backend_dir, "mcp_servers", "discovery_server.py")
            
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[server_path],
                env=os.environ.copy()
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    result = await session.call_tool(
                        "discover_places",
                        arguments={
                            "lat": lat,
                            "lon": lon,
                            "destination": destination,
                            "interests": interests,
                            "start_date": start_date,
                            "end_date": end_date
                        }
                    )
                    
                    text_blocks = [block.text for block in result.content if hasattr(block, "text")]
                    if not text_blocks:
                        raise ValueError("No text content returned from Discovery MCP Tool")
                    
                    raw_json = "".join(text_blocks)
                    items_data = json.loads(raw_json)
                    return [AttractionItem(**item) for item in items_data]
                    
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"MCP Discovery Tool failed or unavailable (falling back to local): {e}")
            
            return await self.discovery_tool.run(
                lat,
                lon,
                destination,
                interests=interests,
                start_date=start_date,
                end_date=end_date,
            )

    def rank_attractions(self, attractions: list[AttractionItem]) -> list[AttractionItem]:
        """
        Rank attractions using Ranking Tool (distance) first,
        then stable-sort by final_score descending (prioritizing interest_score, falling back to quality_score).
        """
        distance_ranked = self.ranking_tool.run(attractions)
        return sorted(
            distance_ranked,
            key=lambda a: a.final_score if a.final_score > 0 else a.quality_score,
            reverse=True,
        )

    def estimate_budget(
        self,
        selected_attractions: list[AttractionItem],
        total_days: int,
        travelers: int,
        budget: float,
        travel_style: str,
    ) -> BudgetEstimateResult:
        """Estimate trip budget expenses using Budget Tool."""
        return self.budget_tool.run(
            selected_attractions=selected_attractions,
            total_days=total_days,
            travelers=travelers,
            budget=budget,
            travel_style=travel_style,
        )

    async def analyze_travel_safety(
        self, lat: float, lon: float, start_date: str, end_date: str
    ) -> TravelSafetyResult:
        """Analyze weather and travel risk using Travel Safety Tool via Weather MCP Server, falling back to local run if unavailable."""
        try:
            import os
            import sys
            import json
            import asyncio
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
            
            # Determine path to weather_server.py
            agent_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(agent_dir)
            server_path = os.path.join(backend_dir, "mcp_servers", "weather_server.py")
            
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[server_path],
                env=os.environ.copy()
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    args = {
                        "lat": lat,
                        "lon": lon,
                        "start_date": start_date,
                        "end_date": end_date
                    }
                    
                    # Call endpoints concurrently
                    weather_task = session.call_tool("get_weather", arguments=args)
                    safety_task = session.call_tool("get_travel_safety", arguments=args)
                    packing_task = session.call_tool("packing_recommendations", arguments=args)
                    
                    weather_res, safety_res, packing_res = await asyncio.gather(
                        weather_task, safety_task, packing_task
                    )
                    
                    weather_text = "".join([block.text for block in weather_res.content if hasattr(block, "text")])
                    safety_text = "".join([block.text for block in safety_res.content if hasattr(block, "text")])
                    packing_text = "".join([block.text for block in packing_res.content if hasattr(block, "text")])
                    
                    weather_data = json.loads(weather_text)
                    safety_data = json.loads(safety_text)
                    packing_data = json.loads(packing_text)
                    
                    from agent.tools.travel_safety_tool import WeatherSummary, TravelSafetyResult
                    
                    return TravelSafetyResult(
                        weather_summary=WeatherSummary(**weather_data),
                        risk_level=safety_data["risk_level"],
                        travel_advisories=safety_data["travel_advisories"],
                        packing_suggestions=packing_data
                    )
                    
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"MCP Weather Tool failed or unavailable (falling back to local): {e}")
            
            return await self.travel_safety_tool.run(
                lat=lat, lon=lon, start_date=start_date, end_date=end_date
            )

    async def run(self, destination: str) -> list[AttractionItem]:
        """
        Execute the agent pipeline:
        discover_destination -> discover_attractions -> rank_attractions
        """
        lat, lon = await self.discover_destination(destination)
        attractions = await self.discover_attractions(lat, lon, destination)
        ranked = self.rank_attractions(attractions)
        return ranked

    async def generate_itinerary(self, request: ItineraryRequest) -> ItineraryResponse:
        """
        Generates the itinerary plan.
        1. Resolve coordinates for travel safety analysis.
        2. Conduct budget analysis using BudgetTool.
        3. Conduct safety and weather analysis using TravelSafetyTool.
        4. Organize selections via Google Gemini and parse response.
        """
        if not self.bypass_adk:
            try:
                from agent.adk_agent import run_itinerary_adk
                return await run_itinerary_adk(request)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Google ADK itinerary generation failed: {e}. Fallback is disabled for itinerary generation.")
                raise e
        # 1. Resolve coordinates
        try:
            lat, lon = await self.discover_destination(request.destination)
        except Exception:
            lat, lon = 0.0, 0.0

        # Calculate days
        from datetime import date, timedelta
        dates = []
        try:
            s = date.fromisoformat(request.start_date)
            e = date.fromisoformat(request.end_date)
            current = s
            while current <= e:
                dates.append(current.isoformat())
                current += timedelta(days=1)
        except Exception as exc:
            raise ValueError(f"Invalid date format: {exc}")

        total_days = len(dates)

        # 2. Run Budget Tool
        budget_res = self.estimate_budget(
            selected_attractions=request.selected_attractions,
            total_days=total_days,
            travelers=request.travelers,
            budget=request.budget,
            travel_style=request.travel_style,
        )

        # 3. Run Travel Safety Tool
        safety_res = await self.analyze_travel_safety(
            lat=lat,
            lon=lon,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        # 4. Generate itinerary using Itinerary Tool
        interests = getattr(request, "interests", None)
        return await self.itinerary_tool.run(
            selected_attractions=request.selected_attractions,
            budget_result=budget_res,
            travel_safety_result=safety_res,
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            travelers=request.travelers,
            travel_style=request.travel_style,
            interests=interests,
        )

