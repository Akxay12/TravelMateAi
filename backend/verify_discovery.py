import asyncio
import sys
import os

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.travel_planner_agent import TravelPlannerAgent
from models.schemas import AttractionItem

def test_deterministic_scoring_rules(agent: TravelPlannerAgent):
    print("\n==========================================")
    print("TESTING DETERMINISTIC QUALITY FILTER SCORING")
    print("==========================================")
    
    # Construct mock items matching the prompt's examples exactly
    items = [
        AttractionItem(id="1", name="Gandhi Ashram", category="Attraction", description="Historic ashram", distance_km=2.5, estimated_duration_minutes=60),
        AttractionItem(id="2", name="Science City", category="Attraction", description="Interactive science museum", distance_km=5.0, estimated_duration_minutes=60),
        AttractionItem(id="3", name="Sabarmati Riverfront", category="Attraction", description="Beautiful river promenade", distance_km=1.2, estimated_duration_minutes=60),
        AttractionItem(id="4", name="Bhadra Fort", category="Fort", description="Historic fort", distance_km=0.8, estimated_duration_minutes=60),
        AttractionItem(id="5", name="Kankaria Lake", category="Attraction", description="Huge lake and entertainment zone", distance_km=3.1, estimated_duration_minutes=60),
        AttractionItem(id="6", name="Bird Feeder", category="Amenity", description="A bird feeding pole", distance_km=0.5, estimated_duration_minutes=60),
        AttractionItem(id="7", name="Logo Wall", category="Artwork", description="A wall with a painted logo", distance_km=1.5, estimated_duration_minutes=60),
        AttractionItem(id="8", name="Random Statue", category="Artwork", description="Generic statue", distance_km=0.2, estimated_duration_minutes=60),
        AttractionItem(id="9", name="Residential Park", category="Park", description="Small neighborhood park", distance_km=0.4, estimated_duration_minutes=60),
    ]
    
    # Calculate scores using the agent's discovery_tool
    scored_items = []
    for item in items:
        item.quality_score = agent.discovery_tool.compute_quality_score(item)
        print(f"  - {item.name}: Score = {item.quality_score}")
        scored_items.append(item)
        
    # Sort them using the agent's rank_attractions logic (stable sort)
    ranked = agent.rank_attractions(scored_items)
    
    print("\nSorted mock attractions:")
    for idx, r in enumerate(ranked):
        print(f"  {idx+1}. {r.name} (Score: {r.quality_score}, Distance: {r.distance_km} km)")
        
    # Assert specific scores
    assert scored_items[0].quality_score == 98, "Gandhi Ashram score should be 98"
    assert scored_items[1].quality_score == 96, "Science City score should be 96"
    assert scored_items[2].quality_score == 95, "Sabarmati Riverfront score should be 95"
    assert scored_items[3].quality_score == 94, "Bhadra Fort score should be 94"
    assert scored_items[4].quality_score == 94, "Kankaria Lake score should be 94"
    assert scored_items[5].quality_score == 10, "Bird Feeder score should be 10"
    assert scored_items[6].quality_score == 5, "Logo Wall score should be 5"
    assert scored_items[7].quality_score == 3, "Random Statue score should be 3"
    assert scored_items[8].quality_score == 2, "Residential Park score should be 2"
    
    # Assert correct priority ranking
    names_ranked = [r.name for r in ranked]
    assert names_ranked.index("Gandhi Ashram") < names_ranked.index("Bird Feeder"), "Gandhi Ashram must appear before Bird Feeder"
    assert names_ranked.index("Science City") < names_ranked.index("Residential Park"), "Science City must appear before Residential Park"
    assert names_ranked.index("Kankaria Lake") < names_ranked.index("Logo Wall"), "Kankaria Lake must appear before Logo Wall"
    assert names_ranked.index("Bhadra Fort") < names_ranked.index("Random Statue"), "Bhadra Fort must appear before Random Statue"
    
    print("  [OK] Mock deterministic scoring test passed successfully.")

async def verify_city(agent: TravelPlannerAgent, city: str):
    print(f"\n==========================================")
    print(f"VERIFYING CITY: {city}")
    print(f"==========================================")
    
    # 1. Geocode
    print(f"Step 1: Geocoding '{city}'...")
    try:
        lat, lon = await agent.discover_destination(city)
        print(f"Coordinates: lat={lat}, lon={lon}")
    except Exception as e:
        print(f"[FAIL] Geocoding failed: {e}")
        return False
        
    # 2. Discover attractions
    print(f"Step 2: Running Discovery Tool (OSM + Wikivoyage)...")
    
    attractions = []
    max_retries = 5
    for attempt in range(max_retries):
        try:
            attractions = await agent.discover_attractions(lat, lon, city)
            
            # Check if we got OSM attractions
            osm_count = sum(1 for item in attractions if item.osm_tags.get("source", "osm") in ("osm", "osm_and_wikivoyage"))
            if osm_count > 0:
                break
            else:
                if attempt < max_retries - 1:
                    sleep_time = (attempt + 1) * 8.0
                    print(f"[WARNING] Attempt {attempt+1}/{max_retries}: No OSM attractions returned (possibly rate limited). Retrying in {sleep_time} seconds...")
                    await asyncio.sleep(sleep_time)
        except Exception as e:
            if attempt < max_retries - 1:
                sleep_time = (attempt + 1) * 8.0
                print(f"[WARNING] Attempt {attempt+1}/{max_retries} failed: {e}. Retrying in {sleep_time} seconds...")
                await asyncio.sleep(sleep_time)
            
    print(f"Total attractions returned: {len(attractions)}")
    if not attractions:
        print(f"[FAIL] No attractions returned for {city}")
        return False
        
    # Apply stable double sort to verify agent output
    ranked = agent.rank_attractions(attractions)
    
    # Verify sorted ordering: Quality Score (descending)
    # Check if there is any item with a lower quality score placed before a higher quality score
    out_of_order = 0
    for i in range(len(ranked) - 1):
        if ranked[i].quality_score < ranked[i+1].quality_score:
            out_of_order += 1
            
    print(f"  Quality ordering check: {out_of_order} out-of-order pairs (0 is perfect)")
    assert out_of_order == 0, f"Attractions are not correctly sorted by quality score descending!"
    
    # 3. Categorize sources
    osm_only = 0
    wv_only = 0
    merged = 0
    
    for item in ranked:
        src = item.osm_tags.get("source", "osm")
        if src == "osm_and_wikivoyage":
            merged += 1
        elif src == "wikivoyage":
            wv_only += 1
        else:
            osm_only += 1
            
    print(f"Results breakdown for {city}:")
    print(f"  OSM-only: {osm_only}, Wikivoyage-only: {wv_only}, Merged: {merged}")
    
    # Print top 5 attractions (first page quality)
    print(f"\nTop 5 Attractions (First Page):")
    for attr in ranked[:5]:
        src = attr.osm_tags.get("source", "osm")
        safe_name = attr.name.encode('ascii', 'ignore').decode('ascii')
        safe_desc = attr.description.encode('ascii', 'ignore').decode('ascii')
        print(f"  - [{attr.category}] {safe_name} (Score: {attr.quality_score}, Dist: {attr.distance_km} km) [Src: {src}]")
        print(f"    Desc: {safe_desc[:120]}...")
        
    # Print bottom 3 attractions (Low Value)
    if len(ranked) > 5:
        print(f"\nBottom 3 Attractions (Low Value/Infrastructure):")
        for attr in ranked[-3:]:
            src = attr.osm_tags.get("source", "osm")
            safe_name = attr.name.encode('ascii', 'ignore').decode('ascii')
            print(f"  - [{attr.category}] {safe_name} (Score: {attr.quality_score}, Dist: {attr.distance_km} km) [Src: {src}]")
            
    return True

async def discover_attractions_with_retry(agent, lat, lon, city, interests=None, start_date=None, end_date=None):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            attractions = await agent.discover_attractions(
                lat, lon, city, interests=interests, start_date=start_date, end_date=end_date
            )
            if len(attractions) > 0:
                return attractions
        except Exception as e:
            print(f"[WARNING] Attempt {attempt+1}/{max_retries} for {city} failed: {e}")
        
        if attempt < max_retries - 1:
            print(f"Sleeping for 6 seconds before retry...")
            await asyncio.sleep(6.0)
    return []

async def test_interest_matching_rules(agent: TravelPlannerAgent):
    print("\n==========================================")
    print("TESTING INTEREST MATCHING SCORING & FILTERING (PHASE 7)")
    print("==========================================")
    
    # 1. Nashik City with Fort
    print("\nTesting 1: Nashik (City) with interest='Fort'...")
    lat, lon = await agent.discover_destination("Nashik")
    attractions_city = await discover_attractions_with_retry(
        agent, lat, lon, "Nashik", interests="Fort", start_date="2026-07-02", end_date="2026-07-04"
    )
    ranked_city = agent.rank_attractions(attractions_city)
    print(f"Total Nashik City attractions returned: {len(ranked_city)}")
    
    # Verify that all attractions are strictly within Nashik city limits (<= 10km)
    for a in ranked_city:
        assert a.distance_km <= 10.0, f"Attraction {a.name} is {a.distance_km}km away, which is outside city limits (10km)!"
        
    # Verify that famous outer forts are NOT in the list
    outer_forts = ["ramshej", "harihar", "tringalwadi", "anjaneri", "salher", "mulher", "bahula"]
    for a in ranked_city:
        for of in outer_forts:
            assert of not in a.name.lower(), f"Nashik City search must not include outer fort: {a.name}!"
    print("  [OK] Nashik City search successfully excluded outer forts.")

    # 2. Nashik District with Fort
    print("\nTesting 2: Nashik District with interest='Fort'...")
    lat, lon = await agent.discover_destination("Nashik District")
    attractions_dist = await discover_attractions_with_retry(
        agent, lat, lon, "Nashik District", interests="Fort", start_date="2026-07-02", end_date="2026-07-04"
    )
    ranked_dist = agent.rank_attractions(attractions_dist)
    print(f"Total Nashik District attractions returned: {len(ranked_dist)}")
    
    # Verify that we got forts from across the district (including those further than 10km)
    top_5_names = [a.name.lower() for a in ranked_dist[:5]]
    fort_count = sum(1 for name in top_5_names if any(kw in name for kw in ["fort", "castle", "citadel", "trek"]))
    print(f"Fort-related count in top 5: {fort_count}")
    assert fort_count >= 2, "Nashik District with 'Fort' interest must return at least 2 fort-related attractions in top 5!"
    
    # Verify some outer forts are present in district results
    district_forts_found = [a.name.lower() for a in ranked_dist]
    found_any_outer = False
    for of in outer_forts:
        if any(of in name for name in district_forts_found):
            found_any_outer = True
            print(f"  Found district fort: {of}")
    assert found_any_outer, "Nashik District search must return district forts outside Nashik City!"
    print("  [OK] Nashik District search successfully retrieved district-wide forts.")

    # 3. Pune City with Park
    print("\nTesting 3: Pune (City) with interest='Park'...")
    lat, lon = await agent.discover_destination("Pune")
    attractions_pune_city = await discover_attractions_with_retry(
        agent, lat, lon, "Pune", interests="Park", start_date="2026-07-02", end_date="2026-07-04"
    )
    ranked_pune_city = agent.rank_attractions(attractions_pune_city)
    print(f"Total Pune City attractions returned: {len(ranked_pune_city)}")
    for a in ranked_pune_city:
        assert a.distance_km <= 10.0, f"Attraction {a.name} is {a.distance_km}km away, which is outside city limits!"
    print("  [OK] Pune City search successfully restricted to city limits.")

    # 4. Pune District with Fort, Park
    print("\nTesting 4: Pune District with interest='Fort, Park'...")
    lat, lon = await agent.discover_destination("Pune District")
    attractions_pune_dist = await discover_attractions_with_retry(
        agent, lat, lon, "Pune District", interests="Fort, Park", start_date="2026-07-02", end_date="2026-07-04"
    )
    ranked_pune_dist = agent.rank_attractions(attractions_pune_dist)
    print(f"Total Pune District attractions returned: {len(ranked_pune_dist)}")
    
    # Verify both forts and parks are returned across Pune District (including > 10km)
    has_parks = any("park" in a.name.lower() or "garden" in a.name.lower() for a in ranked_pune_dist)
    has_forts = any("fort" in a.name.lower() or "castle" in a.name.lower() for a in ranked_pune_dist)
    has_far_items = any(a.distance_km > 10.0 for a in ranked_pune_dist)
    assert has_parks, "Pune District must return parks."
    assert has_forts, "Pune District must return forts."
    assert has_far_items, "Pune District search must return district-wide attractions (> 10km)."
    print("  [OK] Pune District search returned forts and parks across the entire district.")

    # 5. Goa State with Beach
    print("\nTesting 5: Goa with interest='Beach'...")
    lat, lon = await agent.discover_destination("Goa")
    attractions_goa = await discover_attractions_with_retry(
        agent, lat, lon, "Goa", interests="Beach", start_date="2026-07-02", end_date="2026-07-04"
    )
    ranked_goa = agent.rank_attractions(attractions_goa)
    print(f"Total Goa attractions returned: {len(ranked_goa)}")
    has_beaches = any("beach" in a.name.lower() for a in ranked_goa)
    assert has_beaches, "Goa search with 'Beach' interest must return beaches."
    print("  [OK] Goa search successfully retrieved beaches.")

    # 6. Maharashtra State with Fort
    print("\nTesting 6: Maharashtra with interest='Fort'...")
    lat, lon = await agent.discover_destination("Maharashtra")
    attractions_mh = await discover_attractions_with_retry(
        agent, lat, lon, "Maharashtra", interests="Fort", start_date="2026-07-02", end_date="2026-07-04"
    )
    ranked_mh = agent.rank_attractions(attractions_mh)
    print(f"Total Maharashtra attractions returned: {len(ranked_mh)}")
    has_mh_forts = any("fort" in a.name.lower() or "castle" in a.name.lower() for a in ranked_mh)
    assert has_mh_forts, "Maharashtra search with 'Fort' interest must return forts."
    print("  [OK] Maharashtra search successfully retrieved forts.")

    print("\n  [OK] Interest matching and boundary discovery tests passed successfully.")

async def main():
    agent = TravelPlannerAgent()
    
    # Run deterministic scoring tests
    test_deterministic_scoring_rules(agent)
    
    # Run new interest matching tests
    await test_interest_matching_rules(agent)
    
    cities = ["Ahmedabad", "Pune", "Delhi", "Jaipur", "Goa", "Munnar"]
    success = True
    
    for city in cities:
        try:
            city_success = await verify_city(agent, city)
            if not city_success:
                success = False
        except Exception as e:
            print(f"[ERROR] Verification for {city} raised exception: {e}")
            success = False
        # Add politeness sleep between cities to prevent rate limits
        print(f"Sleeping for 8 seconds between city tests...")
        await asyncio.sleep(8.0)
            
    if success:
        print("\n==========================================")
        print("SUCCESS: ALL VERIFICATIONS COMPLETED!")
        print("==========================================")
        sys.exit(0)
    else:
        print("\n==========================================")
        print("FAILED: SOME VERIFICATIONS ENCOUNTERED ERRORS!")
        print("==========================================")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
