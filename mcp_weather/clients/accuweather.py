
import json
from pathlib import Path

from aiohttp import ClientSession

from ..utils import (
    format_relative_time,
    format_temperature,
    handle_api_error,
    safe_print_warning,
    validate_weather_params,
)
from .base import WeatherClient


class AccuWeatherClient(WeatherClient):
    """Weather client for AccuWeather API."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("ACCUWEATHER_API_KEY is required.")
        self.api_key = api_key
        self.base_url = "http://dataservice.accuweather.com"
        self._cache_dir = Path.home() / ".cache" / "weather"
        self._location_cache_file = self._cache_dir / "location_cache.json"

    def _get_cached_location_key(self, location: str) -> str | None:
        """Get location key from cache."""
        if not self._location_cache_file.exists():
            return None

        try:
            with open(self._location_cache_file) as f:
                cache = json.load(f)
                normalized_location = location.lower().strip()
                return cache.get(normalized_location)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def _cache_location_key(self, location: str, location_key: str):
        """Cache location key for future use."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            if self._location_cache_file.exists():
                with open(self._location_cache_file) as f:
                    cache = json.load(f)
            else:
                cache = {}

            normalized_location = location.lower().strip()
            cache[normalized_location] = location_key

            with open(self._location_cache_file, "w") as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            safe_print_warning(f"Failed to cache location key: {e}")

    async def _search_location(self, session: ClientSession, location: str) -> dict:
        """Search for location and return location info.

        Args:
            session: HTTP session
            location: Location to search for

        Returns:
            Dictionary with location information
        """
        location_search_url = f"{self.base_url}/locations/v1/cities/search"
        params = {"apikey": self.api_key, "q": location}
        async with session.get(location_search_url, params=params) as response:
            locations = await response.json()
            if response.status != 200:
                handle_api_error(response.status, locations, "AccuWeather")
            if not locations or len(locations) == 0:
                raise Exception(f"Location '{location}' not found. Please check the spelling and try again.")
            return locations[0]

    async def _get_current_conditions(self, session: ClientSession, location_key: str) -> list:
        """Get current weather conditions.

        Args:
            session: HTTP session
            location_key: AccuWeather location key

        Returns:
            List of current conditions
        """
        current_conditions_url = f"{self.base_url}/currentconditions/v1/{location_key}"
        params = {"apikey": self.api_key}
        async with session.get(current_conditions_url, params=params) as response:
            current_conditions = await response.json()
            if response.status != 200:
                handle_api_error(response.status, current_conditions, "AccuWeather")
            return current_conditions

    async def _get_hourly_forecast(self, session: ClientSession, location_key: str, use_metric: bool) -> list:
        """Get hourly forecast data.

        Args:
            session: HTTP session
            location_key: AccuWeather location key
            use_metric: Whether to use metric units

        Returns:
            List of hourly forecast data
        """
        forecast_url = f"{self.base_url}/forecasts/v1/hourly/12hour/{location_key}"
        params = {"apikey": self.api_key}
        if use_metric:
            params["metric"] = "true"
        async with session.get(forecast_url, params=params) as response:
            forecast = await response.json()
            if response.status != 200:
                handle_api_error(response.status, forecast, "AccuWeather")
            return forecast

    def _format_current_conditions(self, current_conditions: list, use_metric: bool) -> dict | str:
        """Format current conditions data.

        Args:
            current_conditions: Raw current conditions data
            use_metric: Whether to use metric units

        Returns:
            Formatted current conditions
        """
        if current_conditions and len(current_conditions) > 0:
            current = current_conditions[0]
            temp_key = "Metric" if use_metric else "Imperial"
            temp_value = current["Temperature"][temp_key]["Value"]
            units_str = "metric" if use_metric else "imperial"
            return {
                "temperature": format_temperature(temp_value, units_str),
                "weather_text": current["WeatherText"],
                "relative_humidity": current.get("RelativeHumidity"),
                "precipitation": current.get("HasPrecipitation", False),
                "observation_time": current["LocalObservationDateTime"]
            }
        else:
            return "No current conditions available"

    def _format_hourly_forecast(self, forecast: list) -> list:
        """Format hourly forecast data.

        Args:
            forecast: Raw forecast data

        Returns:
            Formatted hourly forecast data
        """
        hourly_data = []
        for i, hour in enumerate(forecast, 1):
            # Determine units from the temperature data
            temp_value = hour["Temperature"]["Value"]
            temp_unit = hour["Temperature"]["Unit"]
            units_str = "metric" if temp_unit.upper() == "C" else "imperial"

            hourly_data.append({
                "relative_time": format_relative_time(i),
                "temperature": format_temperature(temp_value, units_str),
                "weather_text": hour["IconPhrase"],
                "precipitation_probability": hour["PrecipitationProbability"],
                "precipitation_type": hour.get("PrecipitationType"),
                "precipitation_intensity": hour.get("PrecipitationIntensity"),
            })
        return hourly_data

    async def get_hourly_weather(self, location: str, units: str = "imperial") -> dict:
        """Get current weather conditions and 12-hour forecast for a location."""
        validate_weather_params(location, units)
        use_metric = units == "metric"

        location_key = self._get_cached_location_key(location)

        async with ClientSession() as session:
            # Get location info (from cache or fresh lookup)
            if not location_key:
                location_info = await self._search_location(session, location)
                location_key = location_info["Key"]
                self._cache_location_key(location, location_key)
            else:
                # Try to get fresh location info, fall back to cached location name
                try:
                    location_info = await self._search_location(session, location)
                except Exception:
                    location_info = {"LocalizedName": location, "Country": {"LocalizedName": "Unknown"}}

            # Get weather data
            current_conditions = await self._get_current_conditions(session, location_key)
            forecast = await self._get_hourly_forecast(session, location_key, use_metric)

            # Format response
            current_data = self._format_current_conditions(current_conditions, use_metric)
            hourly_data = self._format_hourly_forecast(forecast)

            return {
                "location": location_info["LocalizedName"],
                "location_key": location_key,
                "country": location_info.get("Country", {}).get("LocalizedName", "Unknown"),
                "current_conditions": current_data,
                "hourly_forecast": hourly_data
            }

    def clear_cache(self) -> str:
        """Clear the location cache to force fresh API lookups."""
        try:
            if self._location_cache_file.exists():
                self._location_cache_file.unlink()
                return "Weather location cache cleared successfully"
            else:
                return "No cache file found - cache is already empty"
        except Exception as e:
            return f"Error clearing cache: {e}"
