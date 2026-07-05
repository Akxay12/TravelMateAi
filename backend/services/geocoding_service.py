"""Geocoding service — resolves a destination name to lat/lon using Nominatim."""

import re
import httpx

from config import settings


class GeocodingError(Exception):
    """Raised when a destination cannot be resolved to coordinates."""


# In-memory cache to store full Nominatim place results: query_string -> place_dict
_geocoding_cache: dict[str, dict] = {}


async def _query_nominatim(query: str) -> dict:
    """Helper to query Nominatim for a specific string query."""
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "extratags": 1,
        "limit": 1,
    }
    headers = {
        "User-Agent": "TravelMateAI/2.0 (travel-planner-app)",
        "Accept-Language": "en",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(settings.nominatim_url, params=params, headers=headers)
        response.raise_for_status()

    results = response.json()
    if not results:
        raise GeocodingError(f"Destination not found: '{query}'")

    return results[0]


async def resolve_coordinates(destination: str) -> tuple[float, float]:
    """
    Query Nominatim to get (lat, lon) for the given destination.
    Uses query relaxation fallbacks if the initial lookup fails.
    Caches full geocoding details to support boundary detection.

    Raises:
        GeocodingError: if the destination is not found or the API fails.
    """
    dest_key = destination.strip().lower()
    if dest_key in _geocoding_cache:
        place = _geocoding_cache[dest_key]
        return float(place["lat"]), float(place["lon"])

    # 1. Try the original query first
    try:
        place = await _query_nominatim(destination)
        _geocoding_cache[dest_key] = place
        return float(place["lat"]), float(place["lon"])
    except GeocodingError:
        pass

    # 2. Relax the query by removing common helper/descriptive words
    relaxed = destination.lower()
    descriptors = [
        "hill station", "national park", "heritage site", "unesco",
        "wildlife sanctuary", "sanctuary", "temple", "beach", "beaches",
        "lake", "river", "mountain", "tourist", "attractions", "places",
        "sightseeing", "visit", "trip", "city", "town", "village"
    ]
    
    has_descriptor = False
    for desc in descriptors:
        if desc in relaxed:
            # Replace case-insensitively using regex boundary check
            relaxed = re.sub(rf"\b{desc}\b", "", relaxed)
            has_descriptor = True
            
    # Clean up excess spacing & punctuation
    relaxed = re.sub(r"[^\w\s-]", " ", relaxed)
    relaxed = re.sub(r"\s+", " ", relaxed).strip()

    if has_descriptor and len(relaxed) >= 2:
        try:
            place = await _query_nominatim(relaxed)
            _geocoding_cache[dest_key] = place
            _geocoding_cache[relaxed.strip().lower()] = place
            return float(place["lat"]), float(place["lon"])
        except GeocodingError:
            pass

    # 3. Fallback to the first part of a comma, semicolon or slash separated string
    parts = [p.strip() for p in re.split(r"[,|;/]", destination) if p.strip()]
    if len(parts) > 1 and len(parts[0]) >= 2:
        try:
            place = await _query_nominatim(parts[0])
            _geocoding_cache[dest_key] = place
            _geocoding_cache[parts[0].strip().lower()] = place
            return float(place["lat"]), float(place["lon"])
        except GeocodingError:
            pass

    # Re-raise for the original destination to display the correct error details
    raise GeocodingError(f"Destination not found: '{destination}'")


def get_cached_geocoding_result(destination: str) -> dict | None:
    """Retrieve full cached place metadata dictionary for the given destination query."""
    return _geocoding_cache.get(destination.strip().lower())


def detect_location_type(destination: str, place: dict) -> str:
    """
    Determine geographical entity type: 'city', 'district', 'state', or 'country'.
    Respects explicit user query hints first.
    """
    dest_lower = destination.lower()
    
    # 1. Check explicit indicators first
    if "district" in dest_lower:
        return "district"
    if "city" in dest_lower:
        return "city"
    if "state" in dest_lower:
        return "state"
    if "country" in dest_lower:
        return "country"

    # 2. Extract OSM metadata
    extratags = place.get("extratags") or {}
    address = place.get("address") or {}
    place_class = place.get("class")
    place_type = place.get("type")

    # Use admin_level if available (OSM standard)
    admin_level = extratags.get("admin_level") or address.get("admin_level")
    if admin_level:
        try:
            al = int(admin_level)
            if al == 2:
                return "country"
            elif al in (3, 4):
                return "state"
            elif al in (5, 6):
                return "district"
            elif al >= 8:
                return "city"
        except ValueError:
            pass

    # Inspect linked place and border type
    if extratags.get("linked_place") == "country" or extratags.get("border_type") in ("nation", "country"):
        return "country"
    if extratags.get("linked_place") == "state" or extratags.get("place") == "state":
        return "state"

    # Check boundaries and administration
    if place_class == "boundary" and place_type == "administrative":
        if "country" in address and len(address) <= 2:
            return "country"
        if "state" in address and not any(k in address for k in ("state_district", "county", "city")):
            return "state"
        if "state_district" in address or "county" in address:
            return "district"

    if place_class == "place" and place_type in ("city", "town", "village", "municipality", "suburb", "hamlet", "city_district"):
        return "city"

    # Fallback to address key checking
    if "city" in address or "town" in address or "village" in address or "municipality" in address:
        return "city"
    if "state_district" in address or "county" in address or "district" in address:
        return "district"
    if "state" in address:
        return "state"
    if "country" in address:
        return "country"

    return "city"


