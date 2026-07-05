"""TravelMate AI 2.0 — FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.connection import create_tables
from routes.attractions import router as attractions_router
from routes.itinerary import router as itinerary_router
from routes.trips import router as trips_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables on startup and validate Gemini API Key."""
    await create_tables()
    # Validate Gemini API key presence
    import logging
    logger = logging.getLogger("uvicorn")
    if settings.gemini_api_key and settings.gemini_api_key.strip():
        print("Gemini API Key Loaded", flush=True)
        logger.info("Gemini API Key Loaded")
    else:
        print("Gemini API Key Missing", flush=True)
        logger.warning("Gemini API Key Missing")
    yield


app = FastAPI(
    title="TravelMate AI",
    version="2.0.0",
    description="AI-powered travel itinerary planner using real OpenStreetMap attractions.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(trips_router)
app.include_router(attractions_router)
app.include_router(itinerary_router)


@app.get("/api/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}
