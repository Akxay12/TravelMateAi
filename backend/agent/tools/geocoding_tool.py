from services.geocoding_service import resolve_coordinates

class GeocodingTool:
    """Wrapper tool for geocoding service using Nominatim."""
    
    async def run(self, destination: str) -> tuple[float, float]:
        """Resolves destination query into lat, lon coordinates."""
        return await resolve_coordinates(destination)
