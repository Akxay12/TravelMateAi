"""Pydantic schemas for request validation and response serialization."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared enums / literals
# ---------------------------------------------------------------------------

TravelStyle = Literal["budget", "standard", "luxury"]


# ---------------------------------------------------------------------------
# Trip schemas
# ---------------------------------------------------------------------------

class TripCreate(BaseModel):
    destination: str = Field(..., min_length=2, max_length=200)
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    budget: float = Field(..., gt=0)
    travelers: int = Field(..., ge=1, le=50)
    travel_style: TravelStyle


class TripResponse(TripCreate):
    id: int
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Attraction schemas
# ---------------------------------------------------------------------------

class AttractionSearchRequest(TripCreate):
    """Same fields as trip creation — used to fetch attractions."""
    interests: str | None = None


class Coordinates(BaseModel):
    lat: float
    lon: float


class AttractionItem(BaseModel):
    id: str                          # e.g. "osm_node_123456"
    name: str
    category: str
    description: str
    distance_km: float
    estimated_duration_minutes: int
    osm_tags: dict[str, str] = Field(default_factory=dict)
    quality_score: int = 0
    interest_score: int = 0
    final_score: int = 0


class AttractionSearchResponse(BaseModel):
    destination: str
    coordinates: Coordinates
    attractions: list[AttractionItem]


# ---------------------------------------------------------------------------
# Itinerary schemas
# ---------------------------------------------------------------------------

class ItineraryRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    budget: float
    travelers: int
    travel_style: TravelStyle
    selected_attractions: list[AttractionItem] = Field(..., min_length=1)
    interests: str | None = None
    places_per_day: int | None = None  # Used for max-attraction validation (trip_days * places_per_day)


class TimeSlotItem(BaseModel):
    attraction_id: str
    name: str
    suggested_time: str              # "09:00"
    duration_minutes: int
    notes: str = ""


class DailyBudgetSchema(BaseModel):
    food: float = 0.0
    transport: float = 0.0
    tickets: float = 0.0
    total: float = 0.0


class DayPlan(BaseModel):
    day_number: int
    date: str
    summary: str
    morning: list[TimeSlotItem] = Field(default_factory=list)
    afternoon: list[TimeSlotItem] = Field(default_factory=list)
    evening: list[TimeSlotItem] = Field(default_factory=list)
    lunch_suggestion: str = ""
    dinner_suggestion: str = ""
    estimated_travel_time_minutes: int = 0
    estimated_walking_time_minutes: int = 0
    transportation: str | None = None
    daily_budget: DailyBudgetSchema | None = None
    travel_tip: str | None = None
    notes: str | None = None


class BudgetSummarySchema(BaseModel):
    accommodation: float = 0.0
    food: float = 0.0
    transport: float = 0.0
    tickets: float = 0.0
    miscellaneous: float = 0.0
    total: float = 0.0
    remaining: float = 0.0
    status: str = ""


class WeatherSummarySchema(BaseModel):
    condition: str = ""
    temperature_range: str = ""
    rain_probability: str = ""
    wind_speed: str = ""
    humidity: str = ""
    risk_level: str = ""
    advisories: list[str] = Field(default_factory=list)
    packing_checklist: list[str] = Field(default_factory=list)


class ItineraryResponse(BaseModel):
    destination: str
    total_days: int
    days: list[DayPlan]
    trip_title: str | None = None
    overview: str | None = None
    final_summary: str | None = None
    budget_notes: str | None = None
    weather_notes: str | None = None
    packing_reminder: str | None = None
    budget_summary: BudgetSummarySchema | None = None
    weather_summary: WeatherSummarySchema | None = None
    important_travel_advice: list[str] = Field(default_factory=list)
    emergency_tips: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Generic error
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    detail: str
