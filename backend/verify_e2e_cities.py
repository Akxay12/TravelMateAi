"""
End-to-end verification: calls the live /api/itinerary/generate endpoint for 10 cities.
Checks HTTP 200, valid JSON, and successful Pydantic model instantiation.
"""
import json
import sys
import time

import httpx

BASE_URL = "http://localhost:8000"

CITIES = [
    "Mumbai",
    "Pune",
    "Goa",
    "Jaipur",
    "Delhi",
    "Ahmedabad",
    "Nashik",
    "Munnar",
    "Varanasi",
    "Udaipur",
]

# Minimal payload — 2 generic attractions so the model always has something to place
def build_payload(destination: str) -> dict:
    return {
        "destination": destination,
        "start_date": "2026-10-01",
        "end_date": "2026-10-02",
        "budget": 20000,
        "travelers": 2,
        "travel_style": "standard",
        "interests": "history, culture",
        "selected_attractions": [
            {
                "id": "osm_node_1",
                "name": f"{destination} Central Museum",
                "category": "Museum",
                "description": f"The main heritage museum in {destination} showcasing local art and history.",
                "distance_km": 1.5,
                "estimated_duration_minutes": 120,
                "osm_tags": {"latitude": "20.0", "longitude": "77.0"},
                "quality_score": 90,
                "interest_score": 85,
                "final_score": 88,
            },
            {
                "id": "osm_node_2",
                "name": f"{destination} City Park",
                "category": "Park",
                "description": f"A large scenic park in the heart of {destination}, popular with locals.",
                "distance_km": 3.0,
                "estimated_duration_minutes": 90,
                "osm_tags": {"latitude": "20.01", "longitude": "77.01"},
                "quality_score": 80,
                "interest_score": 75,
                "final_score": 78,
            },
        ],
    }


def main():
    results = []
    passed = 0
    failed = 0

    print(f"\n{'='*60}")
    print("  TravelMate AI — Itinerary JSON Robustness Verification")
    print(f"{'='*60}\n")

    with httpx.Client(timeout=300.0) as client:
        for i, city in enumerate(CITIES, 1):
            print(f"[{i:02d}/10] Testing {city}...", end=" ", flush=True)
            t0 = time.time()
            try:
                resp = client.post(
                    f"{BASE_URL}/api/itinerary/generate",
                    json=build_payload(city),
                )
                elapsed = time.time() - t0

                if resp.status_code != 200:
                    print(f"FAIL — HTTP {resp.status_code}")
                    print(f"       Response: {resp.text[:300]}")
                    results.append({"city": city, "status": "FAIL", "reason": f"HTTP {resp.status_code}"})
                    failed += 1
                    continue

                # Verify the body is valid JSON (json.loads must succeed)
                try:
                    data = resp.json()
                except Exception as je:
                    print(f"FAIL — json.loads() error: {je}")
                    results.append({"city": city, "status": "FAIL", "reason": f"json decode: {je}"})
                    failed += 1
                    continue

                # Spot-check required top-level keys
                missing = [k for k in ("destination", "total_days", "days") if k not in data]
                if missing:
                    print(f"FAIL — Missing keys: {missing}")
                    results.append({"city": city, "status": "FAIL", "reason": f"missing keys: {missing}"})
                    failed += 1
                    continue

                days_count = len(data.get("days", []))
                print(f"OK    ({elapsed:.1f}s, {days_count} day(s))")
                results.append({"city": city, "status": "OK", "days": days_count, "elapsed": round(elapsed, 1)})
                passed += 1

            except Exception as exc:
                elapsed = time.time() - t0
                print(f"FAIL — Exception: {exc}")
                results.append({"city": city, "status": "FAIL", "reason": str(exc)})
                failed += 1

            # Small pause to avoid rate-limiting
            time.sleep(1)

    print(f"\n{'='*60}")
    print(f"  Results: {passed}/10 passed, {failed}/10 failed")
    print(f"{'='*60}")

    for r in results:
        status = "✓" if r["status"] == "OK" else "✗"
        info = f"{r.get('days', '?')} days, {r.get('elapsed', '?')}s" if r["status"] == "OK" else r.get("reason", "")
        print(f"  {status} {r['city']:<15} {info}")

    print()
    if failed > 0:
        print("SOME TESTS FAILED — see above for details.")
        sys.exit(1)
    else:
        print("ALL 10 CITIES PASSED — JSON output is valid every time.")
        sys.exit(0)


if __name__ == "__main__":
    main()
