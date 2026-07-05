import httpx
import json

payload = {
    "destination": "Mumbai",
    "start_date": "2026-10-01",
    "end_date": "2026-10-02",
    "budget": 5000.0,
    "travelers": 2,
    "travel_style": "standard",
    "selected_attractions": [
        {
            "id": "osm_node_1",
            "name": "Historic Fort",
            "category": "Fort",
            "description": "A magnificent ancient fort.",
            "distance_km": 1.2,
            "estimated_duration_minutes": 120,
            "osm_tags": {"latitude": "18.92", "longitude": "72.82"}
        },
        {
            "id": "osm_node_2",
            "name": "Nehru Museum",
            "category": "Museum",
            "description": "Interactive science exhibits.",
            "distance_km": 4.5,
            "estimated_duration_minutes": 90,
            "osm_tags": {"latitude": "18.98", "longitude": "72.81"}
        }
    ],
    "interests": "history, museum"
}

url = "http://127.0.0.1:8000/api/itinerary/generate"
print(f"Sending real POST request to {url}...")
try:
    with httpx.Client(timeout=120.0) as client:
        response = client.post(url, json=payload)
        print("Response Status Code:", response.status_code)
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
except Exception as e:
    print("Error contacting local server:", e)
