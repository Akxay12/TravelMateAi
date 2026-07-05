"""Route: POST /api/itinerary/generate — call Gemini with selected attractions only."""

from fastapi import APIRouter, HTTPException

from models.schemas import ItineraryRequest, ItineraryResponse
from services.itinerary_service import ItineraryGenerationError, generate_itinerary

router = APIRouter(prefix="/api/itinerary", tags=["itinerary"])


@router.post("/generate", response_model=ItineraryResponse)
async def generate(payload: ItineraryRequest) -> ItineraryResponse:
    """
    Receive the user's selected attractions and trip details,
    then ask Gemini to organize them into a day-by-day plan.
    Gemini is NOT called at any earlier step.
    """
    try:
        result = await generate_itinerary(payload)
    except ItineraryGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI service error: {exc}") from exc

    return result


