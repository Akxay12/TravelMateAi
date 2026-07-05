import httpx
from datetime import date, timedelta
from typing import Literal
from pydantic import BaseModel

RiskLevel = Literal["LOW", "MODERATE", "HIGH"]

class WeatherSummary(BaseModel):
    temperature_min: float
    temperature_max: float
    weather_condition: str
    rain_probability: float
    wind_speed: float
    humidity: float

class TravelSafetyResult(BaseModel):
    weather_summary: WeatherSummary
    risk_level: RiskLevel
    travel_advisories: list[str]
    packing_suggestions: list[str]

class TravelSafetyTool:
    """
    TravelSafetyTool fetches weather forecast data from Open-Meteo
    and conducts rule-based risk analysis, travel advisories, and packing tips.
    """

    # WMO Weather interpretation codes (WW) mapped to (Friendly Condition Name, Severity Score)
    WMO_CODES: dict[int, tuple[str, int]] = {
        0: ("Pleasant Weather", 0),       # Clear sky
        1: ("Pleasant Weather", 0),       # Mainly clear
        2: ("Cloudy", 1),                 # Partly cloudy
        3: ("Cloudy", 1),                 # Overcast
        45: ("Foggy", 2),                 # Fog
        48: ("Foggy", 2),                 # Depositing rime fog
        51: ("Light Rain", 4),            # Drizzle: Light
        53: ("Light Rain", 4),            # Drizzle: Moderate
        55: ("Light Rain", 5),            # Drizzle: Dense
        56: ("Light Rain", 5),            # Freezing Drizzle: Light
        57: ("Light Rain", 5),            # Freezing Drizzle: Dense
        61: ("Light Rain", 4),            # Rain: Slight
        63: ("Moderate Rain", 5),         # Rain: Moderate
        65: ("Heavy Rain", 7),            # Rain: Heavy
        66: ("Freezing Rain", 6),         # Freezing Rain: Light
        67: ("Freezing Rain", 7),         # Freezing Rain: Heavy
        71: ("Snowy", 5),                 # Snow fall: Slight
        73: ("Snowy", 6),                 # Snow fall: Moderate
        75: ("Snowy", 7),                 # Snow fall: Heavy
        77: ("Snowy", 6),                 # Snow grains
        80: ("Rain Showers", 4),          # Rain showers: Slight
        81: ("Rain Showers", 5),          # Rain showers: Moderate
        82: ("Heavy Rain Showers", 7),    # Rain showers: Violent
        85: ("Snow Showers", 5),          # Snow showers: Slight
        86: ("Snow Showers", 6),          # Snow showers: Heavy
        95: ("Thunderstorm", 8),          # Thunderstorm: Slight/moderate
        96: ("Thunderstorm with Hail", 9),# Thunderstorm with slight hail
        99: ("Storm", 10),                # Thunderstorm with heavy hail
    }

    # Default fallback weather summary when API fails or dates are out of range
    FALLBACK_WEATHER = {
        "temperature_min": 15.0,
        "temperature_max": 25.0,
        "weather_condition": "Pleasant Weather",
        "rain_probability": 10.0,
        "wind_speed": 12.0,
        "humidity": 60.0
    }

    async def _fetch_weather(self, lat: float, lon: float, start_date: str, end_date: str) -> dict:
        """Fetch weather data from Open-Meteo for the coordinate and date range."""
        today = date.today()
        try:
            s_date = date.fromisoformat(start_date)
            e_date = date.fromisoformat(end_date)
        except ValueError:
            s_date = today
            e_date = today

        days_to_start = (s_date - today).days
        days_to_end = (e_date - today).days

        # Open-Meteo forecast only goes 14 days out. If dates are beyond, clamp to relative window
        if days_to_start < 0 or days_to_start > 14 or days_to_end < 0 or days_to_end > 14:
            # Out of forecast window, query the next 7 days instead
            s_str = today.isoformat()
            e_str = (today + timedelta(days=6)).isoformat()
        else:
            s_str = start_date
            e_str = end_date

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
            "hourly": "relative_humidity_2m",
            "start_date": s_str,
            "end_date": e_str,
            "timezone": "auto",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def run(self, lat: float, lon: float, start_date: str, end_date: str) -> TravelSafetyResult:
        """
        Runs weather retrieval and analyzes travel risk, advisories, and packing list.
        """
        try:
            raw_data = await self._fetch_weather(lat, lon, start_date, end_date)
            
            daily = raw_data.get("daily", {})
            hourly = raw_data.get("hourly", {})
            
            # Minimum temperature of the trip
            temp_min = min(daily.get("temperature_2m_min", [self.FALLBACK_WEATHER["temperature_min"]]))
            # Maximum temperature of the trip
            temp_max = max(daily.get("temperature_2m_max", [self.FALLBACK_WEATHER["temperature_max"]]))
            # Maximum rain probability during the trip
            rain_prob = max(daily.get("precipitation_probability_max", [self.FALLBACK_WEATHER["rain_probability"]]))
            # Maximum wind speed of the trip
            wind_sp = max(daily.get("wind_speed_10m_max", [self.FALLBACK_WEATHER["wind_speed"]]))
            
            # Average relative humidity during the trip
            humidities = hourly.get("relative_humidity_2m", [])
            avg_humidity = sum(humidities) / len(humidities) if humidities else self.FALLBACK_WEATHER["humidity"]

            # Weather Condition: choose the condition with the highest severity score to be cautious
            weather_codes = daily.get("weather_code", [])
            resolved_conditions = [self.WMO_CODES.get(code, ("Pleasant Weather", 0)) for code in weather_codes]
            if resolved_conditions:
                # Sort by severity score descending, pick the most severe
                resolved_conditions.sort(key=lambda x: x[1], reverse=True)
                weather_cond = resolved_conditions[0][0]
            else:
                weather_cond = self.FALLBACK_WEATHER["weather_condition"]
            
        except Exception:
            # Graceful fallback in case of API failure, offline mode, or timeout
            temp_min = self.FALLBACK_WEATHER["temperature_min"]
            temp_max = self.FALLBACK_WEATHER["temperature_max"]
            rain_prob = self.FALLBACK_WEATHER["rain_probability"]
            wind_sp = self.FALLBACK_WEATHER["wind_speed"]
            avg_humidity = self.FALLBACK_WEATHER["humidity"]
            weather_cond = self.FALLBACK_WEATHER["weather_condition"]

        # 1. Travel Risk Analysis Classification
        # High Risk Conditions
        high_risk_conditions = {"Heavy Rain", "Storm", "Thunderstorm", "Thunderstorm with Hail", "Freezing Rain"}
        # Moderate Risk Conditions
        mod_risk_conditions = {"Foggy", "Rain Showers", "Snowy", "Snow Showers", "Light Rain", "Moderate Rain"}

        if (weather_cond in high_risk_conditions 
            or wind_sp > 40.0 
            or rain_prob > 80.0 
            or temp_max > 42.0 
            or temp_min < -10.0):
            risk_level: RiskLevel = "HIGH"
        elif (weather_cond in mod_risk_conditions 
              or wind_sp > 25.0 
              or rain_prob > 50.0 
              or temp_max > 38.0 
              or temp_min < 0.0):
            risk_level: RiskLevel = "MODERATE"
        else:
            risk_level: RiskLevel = "LOW"

        # 2. Travel Advisories
        advisories: list[str] = []
        if rain_prob > 70.0 or weather_cond in high_risk_conditions:
            advisories.append("Heavy rain expected")
        if rain_prob > 50.0 or any(kw in weather_cond for kw in ["Rain", "Snow", "Storm"]):
            advisories.append("Roads may become slippery")
        if wind_sp > 30.0:
            advisories.append("Strong winds expected")
        if temp_max > 28.0 and weather_cond in {"Pleasant Weather", "Cloudy"}:
            advisories.append("High UV exposure")
        if temp_max > 40.0:
            advisories.append("Extreme heat expected")
        if temp_min < 5.0:
            advisories.append("Extreme cold expected")
        if "Foggy" in weather_cond or wind_sp > 40.0:
            advisories.append("Visibility may be reduced")

        # 3. Packing Suggestions
        packing: list[str] = ["Comfortable Walking Shoes"] # Standard suggestion
        
        rain_keywords = ["Rain", "Showers", "Storm", "Drizzle"]
        if rain_prob > 40.0 or any(kw in weather_cond for kw in rain_keywords):
            packing.extend(["Umbrella", "Raincoat", "Waterproof Shoes"])
        
        if temp_max > 25.0 or weather_cond == "Pleasant Weather":
            packing.extend(["Cap", "Sunscreen", "Water Bottle"])
        
        if 12.0 <= temp_min < 20.0:
            packing.append("Light Jacket")
        elif temp_min < 12.0:
            packing.extend(["Thermal Clothing", "Heavy Jacket"])
            
        if temp_min < 5.0:
            packing.extend(["Gloves & Beanie"])

        # Deduplicate packing suggestions preserving order
        deduped_packing = []
        for item in packing:
            if item not in deduped_packing:
                deduped_packing.append(item)

        return TravelSafetyResult(
            weather_summary=WeatherSummary(
                temperature_min=round(temp_min, 1),
                temperature_max=round(temp_max, 1),
                weather_condition=weather_cond,
                rain_probability=round(rain_prob, 1),
                wind_speed=round(wind_sp, 1),
                humidity=round(avg_humidity, 1)
            ),
            risk_level=risk_level,
            travel_advisories=advisories,
            packing_suggestions=deduped_packing
        )
