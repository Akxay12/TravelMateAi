"""Attractions service — fetches real places from OpenStreetMap via Overpass API."""

import math
import re
from typing import Any

import httpx

from config import settings
from models.schemas import AttractionItem

# ---------------------------------------------------------------------------
# OSM tag → human-readable category mapping
# ---------------------------------------------------------------------------

CATEGORY_MAP: dict[str, str] = {
    "tourism=museum": "Museum",
    "tourism=attraction": "Attraction",
    "tourism=viewpoint": "Viewpoint",
    "tourism=artwork": "Artwork",
    "tourism=gallery": "Art Gallery",
    "tourism=theme_park": "Theme Park",
    "tourism=zoo": "Zoo",
    "tourism=aquarium": "Aquarium",
    "historic=monument": "Monument",
    "historic=castle": "Castle",
    "historic=ruins": "Historic Ruins",
    "historic=memorial": "Memorial",
    "historic=archaeological_site": "Archaeological Site",
    "historic=building": "Historic Building",
    "historic=fort": "Fort",
    "historic=tomb": "Tomb",
    "leisure=park": "Park",
    "leisure=garden": "Garden",
    "leisure=nature_reserve": "Nature Reserve",
    "boundary=national_park": "National Park",
    "amenity=place_of_worship": "Place of Worship",
    "amenity=theatre": "Theatre",
    "amenity=cinema": "Cinema",
    "natural=beach": "Beach",
    "natural=peak": "Mountain Peak",
    "natural=waterfall": "Waterfall",
}

# Default visit duration (minutes) per category
DURATION_MAP: dict[str, int] = {
    "Museum": 120,
    "Attraction": 60,
    "Viewpoint": 30,
    "Artwork": 20,
    "Art Gallery": 90,
    "Theme Park": 240,
    "Zoo": 180,
    "Aquarium": 120,
    "Monument": 30,
    "Castle": 90,
    "Historic Ruins": 60,
    "Memorial": 30,
    "Archaeological Site": 90,
    "Historic Building": 45,
    "Fort": 120,
    "Tomb": 60,
    "Park": 60,
    "Garden": 45,
    "Nature Reserve": 90,
    "National Park": 180,
    "Place of Worship": 30,
    "Theatre": 30,
    "Cinema": 30,
    "Beach": 120,
    "Mountain Peak": 180,
    "Waterfall": 60,
}

# ---------------------------------------------------------------------------
# Overpass query builder
# ---------------------------------------------------------------------------

def _get_query_clauses(interests_str: str | None) -> list[str]:
    """Map user interest keywords to specific OSM tag queries to optimize search."""
    if not interests_str:
        return []
    
    parts = []
    if "," in interests_str or ";" in interests_str:
        parts = [p.strip().lower() for p in re.split(r"[;,]", interests_str) if p.strip()]
    else:
        parts = [p.strip().lower() for p in interests_str.split() if p.strip()]
        
    clauses = []
    
    for interest in parts:
        if "fort" in interest:
            clauses.extend([
                'node["historic"~"fort|castle|ruins"]',
                'way["historic"~"fort|castle|ruins"]',
                'relation["historic"~"fort|castle|ruins"]',
                'node["tourism"~"attraction|viewpoint"]',
                'way["tourism"~"attraction|viewpoint"]',
                'relation["tourism"~"attraction|viewpoint"]'
            ])
        if "temple" in interest or "worship" in interest or "church" in interest or "mosque" in interest:
            clauses.extend([
                'node["amenity"="place_of_worship"]',
                'way["amenity"="place_of_worship"]',
                'node["historic"="tomb"]',
                'way["historic"="tomb"]',
                'relation["historic"="tomb"]'
            ])
        if "adventure" in interest:
            clauses.extend([
                'node["leisure"="nature_reserve"]',
                'way["leisure"="nature_reserve"]',
                'relation["leisure"="nature_reserve"]',
                'node["boundary"="national_park"]',
                'way["boundary"="national_park"]',
                'relation["boundary"="national_park"]',
                'node["natural"~"peak|waterfall"]',
                'way["natural"~"peak|waterfall"]'
            ])
        if "nature" in interest:
            clauses.extend([
                'node["leisure"~"park|garden|nature_reserve"]',
                'way["leisure"~"park|garden|nature_reserve"]',
                'relation["leisure"~"park|garden|nature_reserve"]',
                'node["boundary"="national_park"]',
                'way["boundary"="national_park"]',
                'relation["boundary"="national_park"]',
                'node["natural"="waterfall"]',
                'way["natural"="waterfall"]'
            ])
        if "beach" in interest:
            clauses.extend([
                'node["natural"="beach"]',
                'way["natural"="beach"]',
                'node["tourism"~"attraction|aquarium"]',
                'way["tourism"~"attraction|aquarium"]'
            ])
        if "museum" in interest:
            clauses.extend([
                'node["tourism"~"museum|gallery"]',
                'way["tourism"~"museum|gallery"]',
                'relation["tourism"~"museum|gallery"]'
            ])
        if "history" in interest or "historic" in interest:
            clauses.extend([
                'node["historic"~"monument|castle|ruins|memorial|archaeological_site|building|fort|tomb"]',
                'way["historic"~"monument|castle|ruins|memorial|archaeological_site|building|fort|tomb"]',
                'relation["historic"~"monument|castle|ruins|memorial|archaeological_site|building|fort|tomb"]',
                'node["tourism"~"museum|attraction|viewpoint"]',
                'way["tourism"~"museum|attraction|viewpoint"]',
                'relation["tourism"~"museum|attraction|viewpoint"]'
            ])
        if "park" in interest or "garden" in interest:
            clauses.extend([
                'node["leisure"~"park|garden"]',
                'way["leisure"~"park|garden"]',
                'relation["leisure"~"park|garden"]'
            ])
        if "lake" in interest or "river" in interest or "water" in interest:
            clauses.extend([
                'node["natural"~"water|lake"]',
                'way["natural"~"water|lake"]',
                'relation["natural"~"water|lake"]'
            ])
        if "waterfall" in interest:
            clauses.extend([
                'node["natural"="waterfall"]',
                'way["natural"="waterfall"]'
            ])
        if "palace" in interest or "castle" in interest or "monument" in interest:
            clauses.extend([
                'node["historic"~"castle|palace|monument"]',
                'way["historic"~"castle|palace|monument"]',
                'relation["historic"~"castle|palace|monument"]'
            ])
            
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for c in clauses:
        if c not in seen:
            seen.add(c)
            deduped.append(c)
    return deduped


def _get_default_clauses() -> list[str]:
    """Default fallback OSM clauses when no specific interests match."""
    return [
        'node["tourism"~"museum|attraction|viewpoint|artwork|gallery|theme_park|zoo|aquarium"]',
        'way["tourism"~"museum|attraction|viewpoint|artwork|gallery|theme_park|zoo|aquarium"]',
        'relation["tourism"~"museum|attraction|viewpoint|artwork|gallery|theme_park|zoo|aquarium"]',
        'node["historic"~"monument|castle|ruins|memorial|archaeological_site|building|fort|tomb"]',
        'way["historic"~"monument|castle|ruins|memorial|archaeological_site|building|fort|tomb"]',
        'relation["historic"~"monument|castle|ruins|memorial|archaeological_site|building|fort|tomb"]',
        'node["leisure"~"park|garden|nature_reserve"]',
        'way["leisure"~"park|garden|nature_reserve"]',
        'relation["leisure"~"park|garden|nature_reserve"]',
        'node["boundary"="national_park"]',
        'way["boundary"="national_park"]',
        'relation["boundary"="national_park"]',
        'node["amenity"~"place_of_worship|theatre"]["name"]',
        'way["amenity"~"place_of_worship|theatre"]["name"]',
        'node["natural"~"beach|peak|waterfall"]',
        'way["natural"~"beach|peak|waterfall"]'
    ]


def _build_overpass_query_with_clauses(clauses: list[str], lat: float, lon: float, radius_m: int) -> str:
    """Build Overpass query using a bounding radius filter."""
    query_parts = []
    for c in clauses:
        if c.startswith("node"):
            part = c.replace("node", f"node(around:{radius_m},{lat},{lon})", 1)
        elif c.startswith("way"):
            part = c.replace("way", f"way(around:{radius_m},{lat},{lon})", 1)
        elif c.startswith("relation"):
            part = c.replace("relation", f"relation(around:{radius_m},{lat},{lon})", 1)
        else:
            part = c
        query_parts.append(part)
        
    joined = ";\n  ".join(query_parts) + ";"
    return f"""
[out:json][timeout:30];
(
  {joined}
);
out center tags;
""".strip()


def _build_overpass_area_query_with_clauses(clauses: list[str], area_id: int) -> str:
    """Build Overpass query using an area boundary filter."""
    query_parts = []
    for c in clauses:
        if c.startswith("node"):
            part = c.replace("node", "node(area.searchArea)", 1)
        elif c.startswith("way"):
            part = c.replace("way", "way(area.searchArea)", 1)
        elif c.startswith("relation"):
            part = c.replace("relation", "relation(area.searchArea)", 1)
        else:
            part = c
        query_parts.append(part)
        
    joined = ";\n  ".join(query_parts) + ";"
    return f"""
[out:json][timeout:60];
area({area_id})->.searchArea;
(
  {joined}
);
out center tags;
""".strip()


# ---------------------------------------------------------------------------
# Distance helper
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two lat/lon points."""
    r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return r * 2 * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# OSM element → AttractionItem converter
# ---------------------------------------------------------------------------

def _resolve_category(tags: dict[str, str]) -> str:
    for key, value in tags.items():
        combo = f"{key}={value}"
        if combo in CATEGORY_MAP:
            return CATEGORY_MAP[combo]
    return "Attraction"


def _is_valid_attraction_name(name: str) -> bool:
    """Validate attraction name to filter out generic or invalid placeholders."""
    name_lower = name.lower().strip()
    if len(name_lower) < 3:
        return False
    # Avoid purely numeric names (e.g. "1234")
    if name_lower.isdigit():
        return False
    # Avoid generic placeholder words or words matching category names exactly
    generic_names = {
        "temple", "church", "mosque", "masjid", "park", "playground", "waterfall", 
        "beach", "mountain peak", "peak", "monument", "ruins", "tomb", "museum", 
        "attraction", "tourist attraction", "untitled", "unknown", "test", "todo",
        "place of worship", "art gallery", "theatre", "cinema", "zoo", "aquarium", "hotel"
    }
    if name_lower in generic_names:
        return False
    return True


def _element_to_attraction(
    element: dict[str, Any], city_lat: float, city_lon: float
) -> AttractionItem | None:
    tags = element.get("tags", {})
    name = tags.get("name", "").strip()
    if not name:
        return None

    # Determine coordinates
    if element["type"] == "node":
        el_lat, el_lon = element["lat"], element["lon"]
    else:
        center = element.get("center", {})
        el_lat = center.get("lat", city_lat)
        el_lon = center.get("lon", city_lon)

    category = _resolve_category(tags)
    distance_km = _haversine_km(city_lat, city_lon, el_lat, el_lon)
    duration = DURATION_MAP.get(category, 60)

    # Build a short description from OSM tags
    description_parts: list[str] = []
    if tags.get("description"):
        description_parts.append(tags["description"])
    if tags.get("wikipedia"):
        description_parts.append(f"Referenced on Wikipedia: {tags['wikipedia']}")
    if not description_parts:
        description_parts.append(f"A {category.lower()} located in the area.")

    osm_id = f"osm_{element['type']}_{element['id']}"

    return AttractionItem(
        id=osm_id,
        name=name,
        category=category,
        description=" ".join(description_parts),
        distance_km=round(distance_km, 2),
        estimated_duration_minutes=duration,
        osm_tags={k: v for k, v in tags.items() if k in ("name", "tourism", "historic", "leisure", "natural", "amenity", "boundary", "wikipedia", "wikidata")},
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def fetch_attractions(
    lat: float,
    lon: float,
    destination: str,
    interests: str | None = None,
    location_type: str | None = None,
    area_id: int | None = None,
) -> list[AttractionItem]:
    """
    Query Overpass API for real attractions near (lat, lon) or inside the administrative boundary.
    Returns a deduplicated, sorted list of AttractionItem objects.
    """
    clauses = _get_query_clauses(interests)
    if not clauses:
        clauses = _get_default_clauses()

    async def get_elements_by_query(query: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                settings.overpass_url,
                data={"data": query},
                headers={
                    "User-Agent": "TravelMateAI/2.0 (travel-planner)",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            return response.json().get("elements", [])

    # Limit setup
    limit = 250 if interests else 60

    if area_id:
        # Area search - search the entire administrative boundary
        query = _build_overpass_area_query_with_clauses(clauses, area_id)
        try:
            elements = await get_elements_by_query(query)
        except Exception:
            raise
    else:
        # Radius search (fallback)
        if location_type == "city":
            initial_radius = 10000
        elif interests:
            initial_radius = 50000
        else:
            initial_radius = 10000

        query = _build_overpass_query_with_clauses(clauses, lat, lon, initial_radius)
        try:
            elements = await get_elements_by_query(query)
        except Exception:
            raise

        # Apply dynamic scaling only for non-city radius searches when interests are not specified
        if location_type != "city" and not interests:
            # Dynamic scaling for small towns: if < 15 elements, scale up search radius to 25 km
            if len(elements) < 15:
                try:
                    scaled_query = _build_overpass_query_with_clauses(clauses, lat, lon, 25000)
                    larger_elements = await get_elements_by_query(scaled_query)
                    if len(larger_elements) > len(elements):
                        elements = larger_elements
                except Exception:
                    pass

            # Dynamic scaling for remote or very small towns: if < 10 elements, scale up to 50 km
            if len(elements) < 10:
                try:
                    scaled_query = _build_overpass_query_with_clauses(clauses, lat, lon, 50000)
                    even_larger_elements = await get_elements_by_query(scaled_query)
                    if len(even_larger_elements) > len(elements):
                        elements = even_larger_elements
                except Exception:
                    pass

    seen_names: set[str] = set()
    attractions: list[AttractionItem] = []

    for element in elements:
        item = _element_to_attraction(element, lat, lon)
        if item is None:
            continue
        # Filter out invalid or generic names
        if not _is_valid_attraction_name(item.name):
            continue
        # Deduplicate by name (case-insensitive)
        key = item.name.lower()
        if key in seen_names:
            continue
        seen_names.add(key)
        attractions.append(item)

    # Sort by distance from city centre
    attractions.sort(key=lambda a: a.distance_km)

    return attractions[:limit]  # Cap at 60 results for UI performance
