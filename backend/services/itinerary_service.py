"""Itinerary service — delegates to TravelPlannerAgent."""

from datetime import date

from models.schemas import ItineraryRequest, ItineraryResponse
from agent.travel_planner_agent import TravelPlannerAgent
from agent.tools.itinerary_tool import ItineraryGenerationError


async def generate_itinerary(request: ItineraryRequest) -> ItineraryResponse:
    """
    Send selected attractions to TravelPlannerAgent and return the generated itinerary.
    Validates that selected_attractions count is within [1, trip_days * places_per_day].
    """
    # Compute trip duration
    try:
        s = date.fromisoformat(request.start_date)
        e = date.fromisoformat(request.end_date)
        total_days = (e - s).days + 1
    except ValueError:
        total_days = 1

    # Backend max-attraction guard (only when places_per_day is provided)
    if request.places_per_day and request.places_per_day > 0:
        max_allowed = total_days * request.places_per_day
        if len(request.selected_attractions) > max_allowed:
            raise ItineraryGenerationError(
                f"You selected {len(request.selected_attractions)} attractions, but the maximum allowed for a "
                f"{total_days}-day trip at {request.places_per_day} places/day is {max_allowed}. "
                f"Please deselect {len(request.selected_attractions) - max_allowed} attraction(s)."
            )

    agent = TravelPlannerAgent()
    return await agent.generate_itinerary(request)
