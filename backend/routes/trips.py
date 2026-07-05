"""Route: POST /api/trips — save a trip to the database."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from models.schemas import TripCreate, TripResponse
from models.trip import Trip

router = APIRouter(prefix="/api/trips", tags=["trips"])


@router.post("", response_model=TripResponse, status_code=201)
async def create_trip(payload: TripCreate, db: AsyncSession = Depends(get_db)) -> TripResponse:
    """Save a new trip and return its ID."""
    trip = Trip(
        destination=payload.destination,
        start_date=payload.start_date,
        end_date=payload.end_date,
        budget=payload.budget,
        travelers=payload.travelers,
        travel_style=payload.travel_style,
    )
    db.add(trip)
    await db.commit()
    await db.refresh(trip)
    return TripResponse(
        id=trip.id,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        budget=trip.budget,
        travelers=trip.travelers,
        travel_style=trip.travel_style,  # type: ignore[arg-type]
        created_at=str(trip.created_at),
    )
