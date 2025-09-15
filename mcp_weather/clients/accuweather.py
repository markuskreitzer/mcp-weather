
import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from aiohttp import ClientSession
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

    def _get_cached_location_key(self, location: str) -> Optional[str]:
        """Get location key from cache."""
        if not self._location_cache_file.exists():
            return None
        
        try:
            with open(self._location_cache_file, "r") as f:
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
                with open(self._location_cache_file, "r") as f:
                    cache = json.load(f)
            else:
                cache = {}
            
            normalized_location = location.lower().strip()
            cache[normalized_location] = location_key
            
            with open(self._location_cache_file, "w") as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to cache location key: {e}")

    async def get_hourly_weather(self, location: str, units: str = "imperial") -> Dict:
        """Get current weather conditions and 12-hour forecast for a location."""
        if not location or not location.strip():
            raise ValueError("Location parameter is required and cannot be empty")
        
        if units not in ["imperial", "metric"]:
            raise ValueError("Units must be 'imperial' (Fahrenheit) or 'metric' (Celsius)")
        
        use_metric = units == "metric"
        
        location_key = self._get_cached_location_key(location)
        
        async with ClientSession() as session:
            if not location_key:
                location_search_url = f"{self.base_url}/locations/v1/cities/search"
                params = {"apikey": self.api_key, "q": location}
                async with session.get(location_search_url, params=params) as response:
                    locations = await response.json()
                    if response.status != 200:
                        if response.status == 401:
                            raise Exception("Invalid API key. Please check your ACCUWEATHER_API_KEY")
                        elif response.status == 503:
                            raise Exception("AccuWeather API is temporarily unavailable. Please try again later.")
                        else:
                            raise Exception(f"Error fetching location data: {response.status}, {locations}")
                    if not locations or len(locations) == 0:
                        raise Exception(f"Location '{location}' not found. Please check the spelling and try again.")
                
                location_info = locations[0]
                location_key = location_info["Key"]
                self._cache_location_key(location, location_key)
            else:
                location_search_url = f"{self.base_url}/locations/v1/cities/search"
                params = {"apikey": self.api_key, "q": location}
                async with session.get(location_search_url, params=params) as response:
                    locations = await response.json()
                    if response.status != 200 or not locations:
                        location_info = {"LocalizedName": location, "Country": {"LocalizedName": "Unknown"}}
                    else:
                        location_info = locations[0]
            
            current_conditions_url = f"{self.base_url}/currentconditions/v1/{location_key}"
            params = {"apikey": self.api_key}
            async with session.get(current_conditions_url, params=params) as response:
                current_conditions = await response.json()
                if response.status != 200:
                    if response.status == 401:
                        raise Exception("Invalid API key. Please check your ACCUWEATHER_API_KEY")
                    elif response.status == 503:
                        raise Exception("AccuWeather API is temporarily unavailable. Please try again later.")
                    else:
                        raise Exception(f"Error fetching current conditions: {response.status}, {current_conditions}")
            
            forecast_url = f"{self.base_url}/forecasts/v1/hourly/12hour/{location_key}"
            params = {"apikey": self.api_key}
            if use_metric:
                params["metric"] = "true"
            async with session.get(forecast_url, params=params) as response:
                forecast = await response.json()
                if response.status != 200:
                    if response.status == 401:
                        raise Exception("Invalid API key. Please check your ACCUWEATHER_API_KEY")
                    elif response.status == 503:
                        raise Exception("AccuWeather API is temporarily unavailable. Please try again later.")
                    else:
                        raise Exception(f"Error fetching forecast data: {response.status}, {forecast}")
            
            hourly_data = []
            for i, hour in enumerate(forecast, 1):
                hourly_data.append({
                    "relative_time": f"+{i} hour{'s' if i > 1 else ''}",
                    "temperature": {"value": hour["Temperature"]["Value"], "unit": hour["Temperature"]["Unit"]},
                    "weather_text": hour["IconPhrase"],
                    "precipitation_probability": hour["PrecipitationProbability"],
                    "precipitation_type": hour.get("PrecipitationType"),
                    "precipitation_intensity": hour.get("PrecipitationIntensity"),
                })
            
            if current_conditions and len(current_conditions) > 0:
                current = current_conditions[0]
                temp_key = "Metric" if use_metric else "Imperial"
                current_data = {
                    "temperature": {"value": current["Temperature"][temp_key]["Value"], "unit": current["Temperature"][temp_key]["Unit"]},
                    "weather_text": current["WeatherText"],
                    "relative_humidity": current.get("RelativeHumidity"),
                    "precipitation": current.get("HasPrecipitation", False),
                    "observation_time": current["LocalObservationDateTime"]
                }
            else:
                current_data = "No current conditions available"
            
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
