from typing import Dict
from aiohttp import ClientSession
from .base import WeatherClient

class WeatherGovClient(WeatherClient):
    """Weather client for Weather.gov API."""

    def __init__(self):
        self.base_url = "https://api.weather.gov"

    async def _get_lat_lon(self, location: str, session: ClientSession) -> Dict[str, float]:
        """Get latitude and longitude for a location using Nominatim."""
        url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
        headers = {"User-Agent": "MCP-Weather-Client"} # Nominatim requires a User-Agent
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Error geocoding location '{location}': {response.status}")
            data = await response.json()
            if not data:
                raise Exception(f"Location '{location}' not found.")
            return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}

    async def get_hourly_weather(self, location: str, units: str = "imperial") -> Dict:
        """Get current weather conditions and 12-hour forecast for a location."""
        if not location or not location.strip():
            raise ValueError("Location parameter is required and cannot be empty")

        if units not in ["imperial", "metric"]:
            raise ValueError("Units must be 'imperial' (Fahrenheit) or 'metric' (Celsius)")

        async with ClientSession() as session:
            # Get lat/lon from location string
            lat_lon = await self._get_lat_lon(location, session)

            # Get gridpoint data from weather.gov
            points_url = f"{self.base_url}/points/{lat_lon['lat']:.4f},{lat_lon['lon']:.4f}"
            headers = {"User-Agent": "MCP-Weather-Client"}
            async with session.get(points_url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Error getting gridpoint data: {response.status}")
                points_data = await response.json()
                forecast_url = points_data.get("properties", {}).get("forecastHourly")
                if not forecast_url:
                    raise Exception("Could not retrieve hourly forecast URL.")

            # Get hourly forecast
            async with session.get(forecast_url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Error getting hourly forecast: {response.status}")
                forecast_data = await response.json()

        # Process forecast data
        properties = forecast_data.get("properties", {})
        periods = properties.get("periods", [])
        if not periods:
            return {"message": "No hourly forecast data available."}

        # Get current conditions from the first period
        current = periods[0]
        current_temp = current.get("temperature")
        if units == "imperial":
            current_temp = (current_temp * 9/5) + 32 if current_temp is not None else None

        current_data = {
            "temperature": {
                "value": round(current_temp) if current_temp is not None else None,
                "unit": "F" if units == "imperial" else "C"
            },
            "weather_text": current.get("shortForecast"),
            "relative_humidity": current.get("relativeHumidity"),
            "wind_speed": current.get("windSpeed"),
            "wind_direction": current.get("windDirection")
        }

        # Get hourly forecast for the next 12 hours
        hourly_data = []
        for i, period in enumerate(periods[1:13], 1):
            temp = period.get("temperature")
            if units == "imperial":
                temp = (temp * 9/5) + 32 if temp is not None else None

            hourly_data.append({
                "relative_time": f"+{i} hour{'s' if i > 1 else ''}",
                "temperature": {
                    "value": round(temp) if temp is not None else None,
                    "unit": "F" if units == "imperial" else "C"
                },
                "weather_text": period.get("shortForecast"),
                "precipitation_probability": period.get("probabilityOfPrecipitation", {}).get("value", 0),
                "wind_speed": period.get("windSpeed"),
                "wind_direction": period.get("windDirection")
            })

        return {
            "location": location,
            "source": "Weather.gov",
            "current_conditions": current_data,
            "hourly_forecast": hourly_data
        }