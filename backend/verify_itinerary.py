import asyncio
import json
import sys
import unittest
from unittest.mock import MagicMock, patch

from agent.travel_planner_agent import TravelPlannerAgent
from agent.tools.itinerary_tool import ItineraryTool, ItineraryGenerationError
from models.schemas import AttractionItem, ItineraryRequest, ItineraryResponse
from agent.tools.budget_tool import BudgetEstimateResult
from agent.tools.travel_safety_tool import TravelSafetyResult, WeatherSummary


class TestItineraryToolAndAgent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.selected_attractions = [
            AttractionItem(
                id="osm_node_1",
                name="Historic Fort",
                category="Fort",
                description="A magnificent ancient fort.",
                distance_km=1.2,
                estimated_duration_minutes=120,
                osm_tags={"latitude": "18.92", "longitude": "72.82"}
            ),
            AttractionItem(
                id="osm_node_2",
                name="Nehru Museum",
                category="Museum",
                description="Interactive science exhibits.",
                distance_km=4.5,
                estimated_duration_minutes=90,
                osm_tags={"latitude": "18.98", "longitude": "72.81"}
            )
        ]
        self.request = ItineraryRequest(
            destination="Mumbai",
            start_date="2026-10-01",
            end_date="2026-10-02",  # 2 days
            budget=5000.0,
            travelers=2,
            travel_style="standard",
            selected_attractions=self.selected_attractions,
            interests="history, museum"
        )
        self.budget_result = BudgetEstimateResult(
            accommodation_cost=3500.0,
            food_cost=3000.0,
            transportation_cost=1600.0,
            attraction_fees=400.0,
            miscellaneous_cost=1000.0,
            total_cost=9500.0,
            remaining_budget=-4500.0,
            budget_status="OVER_BUDGET"
        )
        self.safety_result = TravelSafetyResult(
            weather_summary=WeatherSummary(
                temperature_min=24.0,
                temperature_max=39.0,  # Extreme heat
                weather_condition="Pleasant Weather",
                rain_probability=85.0,  # Heavy rain probability
                wind_speed=15.0,
                humidity=75.0
            ),
            risk_level="MODERATE",
            travel_advisories=["Roads may become slippery"],
            packing_suggestions=["Umbrella", "Sunscreen"]
        )

    @patch("agent.tools.itinerary_tool.settings")
    @patch("google.generativeai.GenerativeModel")
    async def test_itinerary_tool_success(self, mock_model_class, mock_settings):
        mock_settings.gemini_api_key = "fake-key"
        mock_settings.gemini_model = "fake-model"

        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "trip_title": "Mumbai Adventure",
            "overview": "A 2-day historical and museum tour in Mumbai.",
            "days": [
                {
                    "day_number": 1,
                    "date": "2026-10-01",
                    "summary": "Historic monuments",
                    "morning": [
                        {
                            "attraction_id": "osm_node_1",
                            "name": "Historic Fort",
                            "suggested_time": "09:00",
                            "duration_minutes": 120,
                            "notes": "Go early"
                        }
                    ],
                    "afternoon": [],
                    "evening": [],
                    "lunch_suggestion": "Cafe Mondegar (₹400 per person)",
                    "dinner_suggestion": "Bademiya (₹600 per person)",
                    "estimated_travel_time_minutes": 30,
                    "estimated_walking_time_minutes": 45,
                    "transportation": "Taxi",
                    "daily_budget": {
                        "food": 1000.0,
                        "transport": 500.0,
                        "tickets": 200.0,
                        "total": 1700.0
                    },
                    "travel_tip": "Drink lots of water",
                    "notes": "Drink lots of water"
                },
                {
                    "day_number": 2,
                    "date": "2026-10-02",
                    "summary": "Museum visit",
                    "morning": [],
                    "afternoon": [
                        {
                            "attraction_id": "osm_node_2",
                            "name": "Nehru Museum",
                            "suggested_time": "14:00",
                            "duration_minutes": 90,
                            "notes": "Air conditioned"
                        }
                    ],
                    "evening": [],
                    "lunch_suggestion": "Cheaper option (₹200 per person)",
                    "dinner_suggestion": "Comfort food (₹300 per person)",
                    "estimated_travel_time_minutes": 20,
                    "estimated_walking_time_minutes": 60,
                    "transportation": "Local train",
                    "daily_budget": {
                        "food": 1000.0,
                        "transport": 500.0,
                        "tickets": 200.0,
                        "total": 1700.0
                    },
                    "travel_tip": "Raincoats recommended",
                    "notes": "Raincoats recommended"
                }
            ],
            "packing_reminder": "Bring umbrella and sunscreen",
            "final_summary": "An exciting short trip",
            "budget_notes": "Remaining budget: -₹4500. Save by eating street food.",
            "weather_notes": "Heavy rain and extreme heat. Afternoon visits are indoors.",
            "budget_summary": {
                "accommodation": 3500.0,
                "food": 3000.0,
                "transport": 1600.0,
                "tickets": 400.0,
                "miscellaneous": 1000.0,
                "total": 9500.0,
                "remaining": -4500.0,
                "status": "OVER_BUDGET"
            },
            "weather_summary": {
                "condition": "Pleasant Weather",
                "temperature_range": "24.0°C - 39.0°C",
                "rain_probability": "85.0%",
                "wind_speed": "15.0 km/h",
                "humidity": "75.0%",
                "risk_level": "MODERATE",
                "advisories": ["Roads may become slippery"],
                "packing_checklist": ["Umbrella", "Sunscreen"]
            },
            "important_travel_advice": ["Advice 1", "Advice 2"],
            "emergency_tips": ["Tip 1"]
        })

        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_instance

        tool = ItineraryTool()
        result = await tool.run(
            selected_attractions=self.selected_attractions,
            budget_result=self.budget_result,
            travel_safety_result=self.safety_result,
            destination="Mumbai",
            start_date="2026-10-01",
            end_date="2026-10-02",
            travelers=2,
            travel_style="standard",
            interests="history, museum"
        )

        self.assertIsInstance(result, ItineraryResponse)
        self.assertEqual(result.trip_title, "Mumbai Adventure")
        self.assertEqual(len(result.days), 2)
        self.assertEqual(result.days[0].morning[0].attraction_id, "osm_node_1")
        self.assertEqual(result.days[1].afternoon[0].attraction_id, "osm_node_2")
        self.assertEqual(result.days[0].estimated_walking_time_minutes, 45)
        self.assertEqual(result.days[0].daily_budget.food, 1000.0)
        self.assertEqual(result.budget_summary.total, 9500.0)
        self.assertEqual(result.weather_summary.condition, "Pleasant Weather")

        # Verify build_prompt contains our optimizations
        called_prompt = mock_instance.generate_content.call_args[0][0]
        self.assertIn("Heavy rain is in the forecast", called_prompt)
        self.assertIn("Extreme heat expected", called_prompt)
        self.assertIn("The current estimated cost exceeds the user's budget", called_prompt)
        self.assertIn("NEVER invent, add, or substitute", called_prompt)

    @patch("agent.tools.itinerary_tool.settings")
    @patch("google.generativeai.GenerativeModel")
    async def test_itinerary_tool_rejects_invented_attractions(self, mock_model_class, mock_settings):
        mock_settings.gemini_api_key = "fake-key"
        mock_settings.gemini_model = "fake-model"

        # Mock Gemini response returning an invented attraction id "osm_node_999"
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "trip_title": "Invalid Trip",
            "overview": "Should fail",
            "days": [
                {
                    "day_number": 1,
                    "date": "2026-10-01",
                    "summary": "Invented attraction in day",
                    "morning": [
                        {
                            "attraction_id": "osm_node_999",  # NOT SUPPLIED
                            "name": "Invented Spot",
                            "suggested_time": "09:00",
                            "duration_minutes": 60,
                            "notes": "Fake place"
                        }
                    ],
                    "afternoon": [],
                    "evening": []
                },
                {
                    "day_number": 2,
                    "date": "2026-10-02",
                    "summary": "Valid attraction",
                    "morning": [],
                    "afternoon": [],
                    "evening": []
                }
            ],
            "packing_reminder": "Bring umbrella",
            "final_summary": "Bad trip",
            "budget_notes": "",
            "weather_notes": "",
        })

        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_instance

        tool = ItineraryTool()
        with self.assertRaises(ItineraryGenerationError) as ctx:
            await tool.run(
                selected_attractions=self.selected_attractions,
                budget_result=self.budget_result,
                travel_safety_result=self.safety_result,
                destination="Mumbai",
                start_date="2026-10-01",
                end_date="2026-10-02",
                travelers=2,
                travel_style="standard",
                interests="history"
            )
        self.assertIn("not present in the selected attractions list", str(ctx.exception))

    @patch("agent.tools.itinerary_tool.settings")
    @patch("google.generativeai.GenerativeModel")
    async def test_itinerary_tool_rejects_invalid_day_count(self, mock_model_class, mock_settings):
        mock_settings.gemini_api_key = "fake-key"
        mock_settings.gemini_model = "fake-model"

        # Mock Gemini response returning only 1 day when 2 were requested
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "trip_title": "Invalid Day Count",
            "overview": "Should fail",
            "days": [
                {
                    "day_number": 1,
                    "date": "2026-10-01",
                    "summary": "Only one day",
                    "morning": [],
                    "afternoon": [],
                    "evening": []
                }
            ]
        })

        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_instance

        tool = ItineraryTool()
        with self.assertRaises(ItineraryGenerationError) as ctx:
            await tool.run(
                selected_attractions=self.selected_attractions,
                budget_result=self.budget_result,
                travel_safety_result=self.safety_result,
                destination="Mumbai",
                start_date="2026-10-01",
                end_date="2026-10-02",  # 2 days requested
                travelers=2,
                travel_style="standard",
                interests="history"
            )
        self.assertIn("requested trip duration is 2 days", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
