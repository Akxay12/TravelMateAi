"""Route: POST /api/attractions/search — geocode + fetch real OSM & Wikivoyage attractions."""

from fastapi import APIRouter, HTTPException

from models.schemas import AttractionSearchRequest, AttractionSearchResponse, Coordinates
from services.geocoding_service import GeocodingError
from agent.travel_planner_agent import TravelPlannerAgent

router = APIRouter(prefix="/api/attractions", tags=["attractions"])


@router.post("/search", response_model=AttractionSearchResponse)
async def search_attractions(payload: AttractionSearchRequest) -> AttractionSearchResponse:
    """
    1. Resolve destination to coordinates (Nominatim) using TravelPlannerAgent.
    2. Fetch and merge attractions from OpenStreetMap & Wikivoyage using Discovery Tool.
    3. Rank attractions by distance using Ranking Tool.
    4. Return cards.
    """
    agent = TravelPlannerAgent()
    try:
        lat, lon = await agent.discover_destination(payload.destination)
    except GeocodingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Geocoding service unavailable: {exc}") from exc

    try:
        attractions = await agent.discover_attractions(
            lat, lon, payload.destination,
            interests=payload.interests,
            start_date=payload.start_date,
            end_date=payload.end_date
        )
        ranked = agent.rank_attractions(attractions)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Attractions service unavailable: {exc}") from exc

    if not ranked:
        raise HTTPException(
            status_code=404,
            detail=f"No attractions found for '{payload.destination}'. Try a more specific city name.",
        )

    return AttractionSearchResponse(
        destination=payload.destination,
        coordinates=Coordinates(lat=lat, lon=lon),
        attractions=ranked,
    )

