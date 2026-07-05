from models.schemas import AttractionItem
from services.attractions_service import fetch_attractions

class AttractionTool:
    """Wrapper tool for Overpass OSM attraction service."""
    
    async def run(
        self,
        lat: float,
        lon: float,
        destination: str,
        interests: str | None = None,
        location_type: str | None = None,
        area_id: int | None = None,
    ) -> list[AttractionItem]:
        """Fetches attractions near coordinates or within boundary from OpenStreetMap."""
        return await fetch_attractions(
            lat, lon, destination, interests=interests, location_type=location_type, area_id=area_id
        )
