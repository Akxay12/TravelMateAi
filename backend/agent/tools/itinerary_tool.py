import json
import logging
import os
import re
from datetime import date, timedelta

import google.generativeai as genai

from config import settings
from models.schemas import AttractionItem, DayPlan, ItineraryResponse, TimeSlotItem
from agent.tools.budget_tool import BudgetEstimateResult
from agent.tools.travel_safety_tool import TravelSafetyResult

logger = logging.getLogger(__name__)

# Directory where invalid Gemini responses are persisted for debugging
_LOGS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))


class ItineraryGenerationError(Exception):
    """Raised when itinerary generation fails."""


def _date_range(start: str, end: str) -> list[str]:
    """Return list of date strings between start and end inclusive."""
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    days: list[str] = []
    current = s
    while current <= e:
        days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def _log_invalid_response(raw_text: str, error: Exception) -> None:
    """Persist the full raw Gemini response and error to the logs directory."""
    try:
        os.makedirs(_LOGS_DIR, exist_ok=True)
        log_path = os.path.join(_LOGS_DIR, "gemini_invalid_response.json")
        payload = {
            "error": str(error),
            "raw_response_length": len(raw_text),
            "raw_response": raw_text,
        }
        with open(log_path, "w", encoding="utf-8") as f:
            # Use ensure_ascii=False so non-ASCII attraction names are readable
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.error("Invalid Gemini response logged to: %s", log_path)
    except Exception as log_exc:  # pragma: no cover
        logger.error("Failed to write invalid-response log: %s", log_exc)


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that Gemini sometimes wraps JSON in."""
    # Remove opening fences: ```json or ```
    cleaned = re.sub(r"```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    # Remove closing fences
    cleaned = re.sub(r"```\s*", "", cleaned)
    return cleaned.strip()


def _extract_json_object(text: str) -> str:
    """
    Locate and return the outermost JSON object substring from *text*.
    Raises ItineraryGenerationError if no braces are found.
    """
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ItineraryGenerationError(
            f"No JSON object found in Gemini response. "
            f"First 200 chars: {text[:200]!r}"
        )
    return text[start:end]


def _try_repair_json(raw_json_str: str) -> dict:
    """
    Attempt a lightweight JSON repair using the json-repair library.
    Returns the parsed dict on success.
    Raises json.JSONDecodeError or ValueError if repair also fails.
    """
    try:
        from json_repair import repair_json  # type: ignore[import]
        repaired = repair_json(raw_json_str, return_objects=True)
        if isinstance(repaired, dict):
            return repaired
        # repair_json may return a string if return_objects=True isn't available
        if isinstance(repaired, str):
            return json.loads(repaired)
        raise ValueError(f"json_repair returned unexpected type: {type(repaired)}")
    except ImportError:
        # json-repair not installed — re-raise the original decode error
        raise


class ItineraryTool:
    """
    ItineraryTool organizes selected attractions into a structured day-by-day plan.
    It builds the Gemini prompt, invokes Gemini, validates the response schema,
    and returns ItineraryResponse.
    """

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def run(
        self,
        selected_attractions: list[AttractionItem],
        budget_result: BudgetEstimateResult,
        travel_safety_result: TravelSafetyResult,
        destination: str,
        start_date: str,
        end_date: str,
        travelers: int,
        travel_style: str,
        interests: str | None = None,
    ) -> ItineraryResponse:
        """
        Generates the itinerary plan.
        1. Formulate Gemini prompt using the provided pre-computed budget and safety results.
        2. Query Gemini exactly ONE time.
        3. Parse, validate, and serialize output.
        """
        # Ensure API key is configured
        if not settings.gemini_api_key:
            raise ItineraryGenerationError("Gemini API key is not configured.")

        # Calculate days
        dates = _date_range(start_date, end_date)
        total_days = len(dates)

        # Build prompt
        prompt = self._build_prompt(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            travelers=travelers,
            travel_style=travel_style,
            interests=interests,
            dates=dates,
            selected_attractions=selected_attractions,
            budget_result=budget_result,
            travel_safety_result=travel_safety_result,
        )

        # Query Gemini API — exactly ONE call, no retries
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)

        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    # Use the SDK maximum to avoid mid-JSON truncation.
                    # gemini-2.5-flash supports up to 65 536 output tokens.
                    max_output_tokens=65536,
                    response_mime_type="application/json",
                ),
            )
            raw_text = response.text
        except Exception as exc:
            raise ItineraryGenerationError(f"Gemini API call failed: {exc}") from exc

        if not raw_text or not raw_text.strip():
            raise ItineraryGenerationError("Gemini returned an empty response.")

        # ------------------------------------------------------------------
        # Parse the JSON response robustly
        # ------------------------------------------------------------------
        parsed = self._parse_gemini_response(raw_text)

        # ------------------------------------------------------------------
        # Structural validation
        # ------------------------------------------------------------------
        valid_ids = {a.id for a in selected_attractions}

        raw_days = parsed.get("days", [])
        if not isinstance(raw_days, list):
            raise ItineraryGenerationError("Invalid JSON structure: 'days' must be a list.")

        # Validate day count matches requested trip duration
        if len(raw_days) != total_days:
            raise ItineraryGenerationError(
                f"Generated itinerary has {len(raw_days)} days, "
                f"but the requested trip duration is {total_days} days."
            )

        # Parse and validate day plans
        days = [self._parse_day(day, valid_ids, dates, selected_attractions) for day in raw_days]

        # Parse budget_summary
        from models.schemas import BudgetSummarySchema
        raw_budget = parsed.get("budget_summary")
        if raw_budget and isinstance(raw_budget, dict):
            budget_sum = BudgetSummarySchema(
                accommodation=float(raw_budget.get("accommodation", budget_result.accommodation_cost)),
                food=float(raw_budget.get("food", budget_result.food_cost)),
                transport=float(raw_budget.get("transport", budget_result.transportation_cost)),
                tickets=float(raw_budget.get("tickets", budget_result.attraction_fees)),
                miscellaneous=float(raw_budget.get("miscellaneous", budget_result.miscellaneous_cost)),
                total=float(raw_budget.get("total", budget_result.total_cost)),
                remaining=float(raw_budget.get("remaining", budget_result.remaining_budget)),
                status=str(raw_budget.get("status", budget_result.budget_status))
            )
        else:
            budget_sum = BudgetSummarySchema(
                accommodation=budget_result.accommodation_cost,
                food=budget_result.food_cost,
                transport=budget_result.transportation_cost,
                tickets=budget_result.attraction_fees,
                miscellaneous=budget_result.miscellaneous_cost,
                total=budget_result.total_cost,
                remaining=budget_result.remaining_budget,
                status=budget_result.budget_status
            )

        # Parse weather_summary
        from models.schemas import WeatherSummarySchema
        ws = travel_safety_result.weather_summary
        raw_weather = parsed.get("weather_summary")
        if raw_weather and isinstance(raw_weather, dict):
            weather_sum = WeatherSummarySchema(
                condition=str(raw_weather.get("condition", ws.weather_condition)),
                temperature_range=str(raw_weather.get("temperature_range", f"{ws.temperature_min}°C - {ws.temperature_max}°C")),
                rain_probability=str(raw_weather.get("rain_probability", f"{ws.rain_probability}%")),
                wind_speed=str(raw_weather.get("wind_speed", f"{ws.wind_speed} km/h")),
                humidity=str(raw_weather.get("humidity", f"{ws.humidity}%")),
                risk_level=str(raw_weather.get("risk_level", travel_safety_result.risk_level)),
                advisories=list(raw_weather.get("advisories", travel_safety_result.travel_advisories)),
                packing_checklist=list(raw_weather.get("packing_checklist", travel_safety_result.packing_suggestions))
            )
        else:
            weather_sum = WeatherSummarySchema(
                condition=ws.weather_condition,
                temperature_range=f"{ws.temperature_min}°C - {ws.temperature_max}°C",
                rain_probability=f"{ws.rain_probability}%",
                wind_speed=f"{ws.wind_speed} km/h",
                humidity=f"{ws.humidity}%",
                risk_level=travel_safety_result.risk_level,
                advisories=travel_safety_result.travel_advisories,
                packing_checklist=travel_safety_result.packing_suggestions
            )

        from pydantic import ValidationError
        try:
            return ItineraryResponse(
                destination=destination,
                total_days=total_days,
                days=days,
                trip_title=parsed.get("trip_title"),
                overview=parsed.get("overview"),
                final_summary=parsed.get("final_summary"),
                budget_notes=parsed.get("budget_notes"),
                weather_notes=parsed.get("weather_notes"),
                packing_reminder=parsed.get("packing_reminder"),
                budget_summary=budget_sum,
                weather_summary=weather_sum,
                important_travel_advice=list(parsed.get("important_travel_advice", [])),
                emergency_tips=list(parsed.get("emergency_tips", [])),
            )
        except ValidationError as val_err:
            raise val_err

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_gemini_response(self, raw_text: str) -> dict:
        """
        Parse the raw Gemini text into a Python dict.

        Strategy (NO additional Gemini calls):
        1. Strip markdown fences (defensive — response_mime_type should prevent them).
        2. Locate the outermost JSON object boundaries.
        3. Try direct json.loads().
        4. On failure, attempt ONE lightweight repair with json-repair.
        5. If repair also fails, log the full response and raise ItineraryGenerationError.
        """
        # Step 1 — strip fences
        cleaned = _strip_fences(raw_text)

        # Step 2 — extract outermost JSON object
        json_str = _extract_json_object(cleaned)

        # Step 3 — direct parse
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as first_exc:
            logger.warning(
                "Direct JSON parse failed (line %d col %d: %s). "
                "Attempting json-repair...",
                first_exc.lineno,
                first_exc.colno,
                first_exc.msg,
            )

        # Step 4 — single repair attempt
        try:
            repaired = _try_repair_json(json_str)
            logger.info("json-repair succeeded — using repaired JSON.")
            return repaired
        except Exception as repair_exc:
            logger.error("json-repair also failed: %s", repair_exc)
            combined_err = ItineraryGenerationError(
                f"Failed to parse JSON response from Gemini even after repair attempt. "
                f"Repair error: {repair_exc}"
            )

        # Step 5 — log the full raw response and surface a clean error
        _log_invalid_response(raw_text, combined_err)
        raise combined_err

    def _build_prompt(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        travelers: int,
        travel_style: str,
        interests: str | None,
        dates: list[str],
        selected_attractions: list[AttractionItem],
        budget_result: BudgetEstimateResult,
        travel_safety_result: TravelSafetyResult,
    ) -> str:
        # Format attraction details for token optimization
        lines = []
        for a in selected_attractions:
            coords = "N/A"
            if a.osm_tags:
                lat_val = a.osm_tags.get("latitude")
                lon_val = a.osm_tags.get("longitude")
                if lat_val and lon_val:
                    coords = f"({lat_val}, {lon_val})"
            # Limit description to 120 chars for token efficiency
            desc = a.description[:120] + "..." if len(a.description) > 120 else a.description
            lines.append(
                f"- ID: {a.id} | Name: {a.name} | Category: {a.category} | "
                f"Coordinates: {coords} | Distance: {a.distance_km} km | Description: {desc}"
            )
        attraction_list = "\n".join(lines)
        valid_ids_str = ", ".join(sorted({a.id for a in selected_attractions}))

        ws = travel_safety_result.weather_summary

        # Formulate instructions based on weather and budget
        weather_instructions = ""
        if "heavy rain" in ws.weather_condition.lower() or ws.rain_probability > 70.0:
            weather_instructions += "- Heavy rain is in the forecast. You MUST schedule indoor attractions earlier in the day/trip when possible.\n"
        if ws.temperature_max > 38.0:
            weather_instructions += (
                f"- Extreme heat expected (Max Temp: {ws.temperature_max}°C). "
                "You MUST avoid scheduling outdoor attractions during the afternoon "
                "(keep afternoon visits indoors or suggest resting/comfortable pacing).\n"
            )

        budget_instructions = ""
        if budget_result.budget_status == "OVER_BUDGET":
            budget_instructions += (
                "- The current estimated cost exceeds the user's budget. "
                "You MUST recommend cost-saving suggestions in the `budget_notes` "
                "(e.g., choices of transport, local eating options), but you MUST NEVER "
                "remove or replace any of the selected attractions.\n"
            )

        prompt = f"""You are an expert travel itinerary generator. Your task is to organize the supplied attractions into a structured day-by-day itinerary.

TRIP DETAILS:
- Destination: {destination}
- Dates: {start_date} to {end_date} ({len(dates)} days)
- Travelers: {travelers}
- Travel Style: {travel_style}
- User Interests: {interests or 'None'}

PRE-COMPUTED BUDGET TOOL OUTPUTS:
- Accommodation Cost: ₹{budget_result.accommodation_cost:.2f}
- Food Cost: ₹{budget_result.food_cost:.2f}
- Transportation Cost: ₹{budget_result.transportation_cost:.2f}
- Attraction Fees: ₹{budget_result.attraction_fees:.2f}
- Miscellaneous Cost: ₹{budget_result.miscellaneous_cost:.2f}
- Total Estimated Cost: ₹{budget_result.total_cost:.2f}
- Remaining Budget: ₹{budget_result.remaining_budget:.2f}
- Budget Status: {budget_result.budget_status}

PRE-COMPUTED TRAVEL SAFETY & WEATHER TOOL OUTPUTS:
- Weather Condition: {ws.weather_condition}
- Temperature Min: {ws.temperature_min}°C
- Temperature Max: {ws.temperature_max}°C
- Rain Probability: {ws.rain_probability}%
- Wind Speed: {ws.wind_speed} km/h
- Humidity: {ws.humidity}%
- Risk Level: {travel_safety_result.risk_level}
- Travel Advisories: {travel_safety_result.travel_advisories}
- Packing Suggestions: {travel_safety_result.packing_suggestions}

INVENTORY:
You MUST ONLY schedule attractions from this list (using their exact IDs and names):
{attraction_list}

VALID ATTRACTION IDs: {valid_ids_str}

CRITICAL RULES:
1. You MUST ONLY use the supplied attractions. NEVER invent, add, or substitute any other attractions.
2. You MUST NOT rename, duplicate, or replace the supplied attractions.
3. You MUST use every supplied attraction exactly ONCE across the entire itinerary.
4. Do NOT fill empty time slots with fake or invented places. Leave slots empty if no supplied attraction fits.
5. Spread attractions NATURALLY across the days.
6. Minimize travel time by grouping nearby attractions (close coordinates) on the same day.
7. Provide dining recommendations (lunch_suggestion and dinner_suggestion) for each day in Indian Rupees (₹) using Indian number formatting (e.g., ₹200, ₹1,500 per person). These must be restaurant dining suggestions, NOT attraction spots.
8. Provide transportation suggestions (e.g. Walk, Metro, Auto Rickshaw, Taxi, Local Bus, Rental Bike) for each day under the `transportation` field, choosing the most suitable transport using nearby attractions.
9. CRITICAL OUTPUT RULE: Your ENTIRE response MUST be a single, valid JSON object — nothing else. Do NOT include markdown code fences (```), do NOT include any explanation, commentary, or text before or after the JSON. Start your response with {{ and end it with }}. Any deviation will cause a system failure.
10. CRITICAL JSON RULE: Every string value must be properly terminated with a closing double-quote. Every object must be closed with }}. Every array must be closed with ]. Never truncate the output mid-string or mid-object — if you are running low on space, shorten the text values of notes/tips/summaries but always complete the JSON structure.

WEATHER & SAFETY INSTRUCTIONS:
{weather_instructions or "- Optimize pacing and schedules for comfort and safety."}
- In `weather_summary`, populate the fields exactly using the PRE-COMPUTED TRAVEL SAFETY & WEATHER TOOL OUTPUTS above. Do NOT modify or recalculate them.
- Format `temperature_range` as "{ws.temperature_min}°C - {ws.temperature_max}°C".
- Format `rain_probability` as "{ws.rain_probability}%".
- Format `wind_speed` as "{ws.wind_speed} km/h".
- Format `humidity` as "{ws.humidity}%".
- For `packing_checklist`, copy the pre-computed packing suggestions exactly.
- If Risk Level is HIGH, populate the `emergency_tips` list with relevant safety actions. Otherwise, leave it empty or list standard safety precautions.

BUDGET INSTRUCTIONS:
{budget_instructions or "- Keep budget status and remaining budget in mind."}
- In `budget_summary`, populate the fields exactly using the PRE-COMPUTED BUDGET TOOL OUTPUTS above. Do NOT modify or recalculate them.
- For the day-wise `daily_budget` in each day: estimate/allocate approximate daily costs for food, transport, and tickets such that the sum of daily costs across all days roughly matches the total estimated costs from the Budget Tool. Food and transport are daily costs, while tickets correspond to the admission fees for the attractions visited on that day. Sum them up in the daily `total`.

DAY SUMMARY STATS:
For each day in `days`, you must include:
- `estimated_travel_time_minutes`: estimate the travel time in minutes based on coordinate distances.
- `estimated_walking_time_minutes`: estimate the total walking time in minutes at the attractions for that day (e.g., 30, 60, 90 minutes).
- `travel_tip`: a helpful daily travel tip for the user.

You MUST return a JSON object with this exact schema:
{{
  "trip_title": "A catchy title for the trip",
  "overview": "Brief overview of the trip",
  "days": [
    {{
      "day_number": 1,
      "date": "YYYY-MM-DD",
      "summary": "Brief summary of the day",
      "morning": [
        {{
          "attraction_id": "ID of selected attraction",
          "name": "Name of selected attraction",
          "suggested_time": "HH:MM",
          "duration_minutes": 90,
          "notes": "Visiting tips"
        }}
      ],
      "afternoon": [],
      "evening": [],
      "lunch_suggestion": "Lunch restaurant and cost per person (e.g., ₹200 per person)",
      "dinner_suggestion": "Dinner restaurant and cost per person (e.g., ₹600 per person)",
      "estimated_travel_time_minutes": 45,
      "estimated_walking_time_minutes": 60,
      "transportation": "Walk",
      "daily_budget": {{
        "food": 900.0,
        "transport": 350.0,
        "tickets": 500.0,
        "total": 1750.0
      }},
      "travel_tip": "Daily travel tip here",
      "notes": "Daily notes/warnings"
    }}
  ],
  "packing_reminder": "Brief packing reminder text",
  "final_summary": "Final wrap-up summary",
  "budget_notes": "Budget status, remaining budget, and cost-saving tips if applicable",
  "weather_notes": "Weather conditions, risk levels, and weather adjustments made",
  "budget_summary": {{
    "accommodation": 8000.0,
    "food": 4500.0,
    "transport": 2000.0,
    "tickets": 1200.0,
    "miscellaneous": 1000.0,
    "total": 16700.0,
    "remaining": 3300.0,
    "status": "WITHIN BUDGET"
  }},
  "weather_summary": {{
    "condition": "Partly Cloudy",
    "temperature_range": "22°C - 31°C",
    "rain_probability": "20%",
    "wind_speed": "14 km/h",
    "humidity": "60%",
    "risk_level": "LOW",
    "advisories": ["Carry sunscreen", "Drink enough water"],
    "packing_checklist": ["Comfortable Shoes", "Cap", "Sunscreen", "Umbrella", "Water Bottle"]
  }},
  "important_travel_advice": ["Advice 1", "Advice 2"],
  "emergency_tips": ["Tip 1"]
}}

Generate exactly {len(dates)} day(s) in the "days" array. Use only IDs from: {valid_ids_str}"""
        return prompt

    def _parse_time_slot(self, raw: dict, valid_ids: set[str], selected_attractions: list[AttractionItem]) -> TimeSlotItem:
        """Parse raw slot into TimeSlotItem, raising an error if the attraction ID is invalid."""
        attraction_id = raw.get("attraction_id", "")
        if attraction_id not in valid_ids:
            raise ItineraryGenerationError(
                f"Generated itinerary contains an attraction ID '{attraction_id}' "
                "not present in the selected attractions list."
            )
        from pydantic import ValidationError
        try:
            return TimeSlotItem(
                attraction_id=attraction_id,
                name=raw.get("name", ""),
                suggested_time=raw.get("suggested_time", "09:00"),
                duration_minutes=int(raw.get("duration_minutes", 60)),
                notes=raw.get("notes", ""),
            )
        except ValidationError as val_err:
            raise val_err

    def _parse_day(self, raw: dict, valid_ids: set[str], dates: list[str], selected_attractions: list[AttractionItem]) -> DayPlan:
        day_num = int(raw.get("day_number", 1))
        date_str = raw.get("date") or (dates[day_num - 1] if day_num <= len(dates) else dates[-1])

        def parse_slots(key: str) -> list[TimeSlotItem]:
            items = []
            for slot in raw.get(key, []):
                parsed = self._parse_time_slot(slot, valid_ids, selected_attractions)
                items.append(parsed)
            return items

        from pydantic import ValidationError
        try:
            # Construct DailyBudgetSchema if daily_budget is in raw
            raw_budget = raw.get("daily_budget")
            daily_budget = None
            if raw_budget and isinstance(raw_budget, dict):
                from models.schemas import DailyBudgetSchema
                daily_budget = DailyBudgetSchema(
                    food=float(raw_budget.get("food", 0.0)),
                    transport=float(raw_budget.get("transport", 0.0)),
                    tickets=float(raw_budget.get("tickets", 0.0)),
                    total=float(raw_budget.get("total", 0.0)),
                )

            return DayPlan(
                day_number=day_num,
                date=date_str,
                summary=raw.get("summary", ""),
                morning=parse_slots("morning"),
                afternoon=parse_slots("afternoon"),
                evening=parse_slots("evening"),
                lunch_suggestion=raw.get("lunch_suggestion", ""),
                dinner_suggestion=raw.get("dinner_suggestion", ""),
                estimated_travel_time_minutes=int(raw.get("estimated_travel_time_minutes", 0)),
                estimated_walking_time_minutes=int(raw.get("estimated_walking_time_minutes", 0)),
                transportation=raw.get("transportation"),
                daily_budget=daily_budget,
                travel_tip=raw.get("travel_tip"),
                notes=raw.get("notes"),
            )
        except ValidationError as val_err:
            raise val_err
