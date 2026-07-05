import asyncio
import os
import sys
import json
import logging
import nest_asyncio
from typing import Any
from pydantic import BaseModel

# Enable nest_asyncio to allow running synchronous tool wrappers with async loops
nest_asyncio.apply()

# Ensure we import config
from config import settings

# Setup environment variable for Google ADK
os.environ["GEMINI_API_KEY"] = settings.gemini_api_key

from google.adk import Workflow, Context
from google.adk.runners import InMemoryRunner
from google.genai import types

from models.schemas import AttractionItem, ItineraryRequest, ItineraryResponse
from agent.tools.budget_tool import BudgetEstimateResult
from agent.tools.travel_safety_tool import TravelSafetyResult

logger = logging.getLogger(__name__)

# Lazy import of TravelPlannerAgent to avoid circular import issues
def get_legacy_agent() -> Any:
    from agent.travel_planner_agent import TravelPlannerAgent
    return TravelPlannerAgent(bypass_adk=True)


# ==========================================
# WORKFLOW STATE SCHEMAS
# ==========================================

class DiscoveryWorkflowState(BaseModel):
    destination: str
    interests: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    
    # Coordinates & Results
    lat: float = 0.0
    lon: float = 0.0
    attractions: list[dict] | None = None


class ItineraryWorkflowState(BaseModel):
    destination: str
    start_date: str
    end_date: str
    budget: float
    travelers: int
    travel_style: str
    selected_attractions: list[dict]
    interests: str | None = None
    
    # Intermediate / Output fields
    lat: float = 0.0
    lon: float = 0.0
    budget_result: dict | None = None
    travel_safety_result: dict | None = None
    itinerary_result: dict | None = None


# ==========================================
# WORKFLOW NODE STEPS
# ==========================================

def geocode_step(ctx: Context) -> dict:
    destination = ctx.state["destination"]
    loop = asyncio.get_event_loop()
    lat, lon = loop.run_until_complete(get_legacy_agent().discover_destination(destination))
    ctx.state["lat"] = lat
    ctx.state["lon"] = lon
    return {"lat": lat, "lon": lon}

def discover_attractions_step(ctx: Context) -> dict:
    loop = asyncio.get_event_loop()
    items = loop.run_until_complete(get_legacy_agent().discover_attractions(
        lat=ctx.state["lat"],
        lon=ctx.state["lon"],
        destination=ctx.state["destination"],
        interests=ctx.state["interests"],
        start_date=ctx.state["start_date"],
        end_date=ctx.state["end_date"]
    ))
    ctx.state["attractions"] = [item.model_dump() for item in items]
    return {"attractions": ctx.state["attractions"]}

def rank_attractions_step(ctx: Context) -> dict:
    attractions = ctx.state["attractions"] or []
    attr_items = [AttractionItem(**a) for a in attractions]
    ranked = get_legacy_agent().rank_attractions(attr_items)
    ctx.state["attractions"] = [r.model_dump() for r in ranked]
    return {"attractions": ctx.state["attractions"]}

def budget_step(ctx: Context) -> dict:
    from datetime import date
    try:
        s = date.fromisoformat(ctx.state["start_date"])
        e = date.fromisoformat(ctx.state["end_date"])
        total_days = (e - s).days + 1
    except Exception:
        total_days = 1
        
    attr_items = [AttractionItem(**a) for a in ctx.state["selected_attractions"]]
    res = get_legacy_agent().estimate_budget(
        selected_attractions=attr_items,
        total_days=total_days,
        travelers=ctx.state["travelers"],
        budget=ctx.state["budget"],
        travel_style=ctx.state["travel_style"]
    )
    ctx.state["budget_result"] = res.model_dump()
    return {"budget_result": ctx.state["budget_result"]}

def safety_step(ctx: Context) -> dict:
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(get_legacy_agent().analyze_travel_safety(
        lat=ctx.state["lat"],
        lon=ctx.state["lon"],
        start_date=ctx.state["start_date"],
        end_date=ctx.state["end_date"]
    ))
    ctx.state["travel_safety_result"] = res.model_dump()
    return {"travel_safety_result": ctx.state["travel_safety_result"]}

def itinerary_step(ctx: Context) -> dict:
    attr_items = [AttractionItem(**a) for a in ctx.state["selected_attractions"]]
    b_res = BudgetEstimateResult(**ctx.state["budget_result"])
    s_res = TravelSafetyResult(**ctx.state["travel_safety_result"])
    
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(get_legacy_agent().itinerary_tool.run(
        selected_attractions=attr_items,
        budget_result=b_res,
        travel_safety_result=s_res,
        destination=ctx.state["destination"],
        start_date=ctx.state["start_date"],
        end_date=ctx.state["end_date"],
        travelers=ctx.state["travelers"],
        travel_style=ctx.state["travel_style"],
        interests=ctx.state["interests"]
    ))
    ctx.state["itinerary_result"] = res.model_dump()
    return {"itinerary_result": ctx.state["itinerary_result"]}


# ==========================================
# AGENT PIPELINE EXECUTION ENTRYPOINTS
# ==========================================

async def run_discovery_adk(
    destination: str,
    interests: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None
) -> list[AttractionItem]:
    """Execute the attraction search pipeline via Google ADK Workflow orchestration."""
    logger.info(f"Orchestrating attraction discovery via Google ADK Workflow for '{destination}'...")
    
    workflow = Workflow(
        name="discovery_workflow",
        state_schema=DiscoveryWorkflowState,
        edges=[
            ("START", geocode_step),
            (geocode_step, discover_attractions_step),
            (discover_attractions_step, rank_attractions_step)
        ]
    )
    
    runner = InMemoryRunner(node=workflow)
    runner.auto_create_session = True
    
    initial_state = {
        "destination": destination,
        "interests": interests,
        "start_date": start_date,
        "end_date": end_date
    }
    
    msg = types.Content(parts=[types.Part.from_text(text="start")])
    
    async for _ in runner.run_async(
        user_id="default_user",
        session_id=f"session_discovery_{destination}",
        new_message=msg,
        state_delta=initial_state
    ):
        pass
        
    sessions_model = await runner.session_service.list_sessions(user_id="default_user", app_name="InMemoryRunner")
    if not sessions_model or not sessions_model.sessions:
        raise RuntimeError("No session found after ADK discovery workflow run")
        
    session = sessions_model.sessions[0]
    data = session.state.get("attractions") or []
    return [AttractionItem(**item) for item in data]


async def run_itinerary_adk(request: ItineraryRequest) -> ItineraryResponse:
    """Execute the itinerary generation pipeline via Google ADK Workflow orchestration."""
    logger.info(f"Orchestrating itinerary generation via Google ADK Workflow for '{request.destination}'...")
    
    workflow = Workflow(
        name="itinerary_workflow",
        state_schema=ItineraryWorkflowState,
        edges=[
            ("START", geocode_step),
            (geocode_step, budget_step),
            (budget_step, safety_step),
            (safety_step, itinerary_step)
        ]
    )
    
    runner = InMemoryRunner(node=workflow)
    runner.auto_create_session = True
    
    initial_state = {
        "destination": request.destination,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "budget": request.budget,
        "travelers": request.travelers,
        "travel_style": request.travel_style,
        "selected_attractions": [a.model_dump() for a in request.selected_attractions],
        "interests": request.interests
    }
    
    msg = types.Content(parts=[types.Part.from_text(text="start")])
    
    async for _ in runner.run_async(
        user_id="default_user",
        session_id=f"session_itinerary_{request.destination}",
        new_message=msg,
        state_delta=initial_state
    ):
        pass
        
    sessions_model = await runner.session_service.list_sessions(user_id="default_user", app_name="InMemoryRunner")
    if not sessions_model or not sessions_model.sessions:
        raise RuntimeError("No session found after ADK itinerary workflow run")
        
    session = sessions_model.sessions[0]
    result_dict = session.state.get("itinerary_result")
    if not result_dict:
        raise RuntimeError("Itinerary workflow completed but no itinerary_result was generated")
        
    return ItineraryResponse(**result_dict)
