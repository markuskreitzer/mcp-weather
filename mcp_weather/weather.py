import os
import json
from pathlib import Path
from typing import Dict, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv
from aiohttp import ClientSession

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("mcp-weather")

# Cache configuration
CACHE_DIR = Path.home() / ".cache" / "weather"
LOCATION_CACHE_FILE = CACHE_DIR / "location_cache.json"

def get_cached_location_key(location: str) -> Optional[str]:
    """Get location key from cache."""
    if not LOCATION_CACHE_FILE.exists():
        return None
    
    try:
        with open(LOCATION_CACHE_FILE, "r") as f:
            cache = json.load(f)
            # Normalize location for consistent lookup
            normalized_location = location.lower().strip()
            return cache.get(normalized_location)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def cache_location_key(location: str, location_key: str):
    """Cache location key for future use."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        if LOCATION_CACHE_FILE.exists():
            with open(LOCATION_CACHE_FILE, "r") as f:
                cache = json.load(f)
        else:
            cache = {}
        
        # Normalize location for consistent caching
        normalized_location = location.lower().strip()
        cache[normalized_location] = location_key
        
        with open(LOCATION_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to cache location key: {e}")

@mcp.tool()
async def get_hourly_weather(location: str, units: str = "imperial") -> Dict:
    """Get current weather conditions and 12-hour forecast for a location.
    
    Args:
        location: Name of the city or location (e.g., "New York", "London", "Tokyo")
        units: Temperature units - "imperial" for Fahrenheit (default) or "metric" for Celsius
    
    Returns:
        Dict containing current conditions and hourly forecast data
    
    Raises:
        Exception: If API key is missing, location not found, or API request fails
    """
    api_key = os.getenv("ACCUWEATHER_API_KEY")
    if not api_key:
        raise Exception("ACCUWEATHER_API_KEY environment variable is required. Get a free API key at https://developer.accuweather.com/")
    
    if not location or not location.strip():
        raise Exception("Location parameter is required and cannot be empty")
    
    # Validate units parameter
    if units not in ["imperial", "metric"]:
        raise Exception("Units must be 'imperial' (Fahrenheit) or 'metric' (Celsius)")
    
    use_metric = units == "metric"
    
    base_url = "http://dataservice.accuweather.com"
    
    # Try to get location key from cache first
    location_key = get_cached_location_key(location)
    
    async with ClientSession() as session:
        if not location_key:
            location_search_url = f"{base_url}/locations/v1/cities/search"
            params = {
                "apikey": api_key,
                "q": location,
            }
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
            # Cache the location key for future use
            cache_location_key(location, location_key)
        else:
            # If we have cached location key, we need to get location info for response
            location_search_url = f"{base_url}/locations/v1/cities/search"
            params = {
                "apikey": api_key,
                "q": location,
            }
            async with session.get(location_search_url, params=params) as response:
                locations = await response.json()
                if response.status != 200 or not locations:
                    # Fallback location info if search fails
                    location_info = {"LocalizedName": location, "Country": {"LocalizedName": "Unknown"}}
                else:
                    location_info = locations[0]
        
        # Get current conditions
        current_conditions_url = f"{base_url}/currentconditions/v1/{location_key}"
        params = {
            "apikey": api_key,
        }
        async with session.get(current_conditions_url, params=params) as response:
            current_conditions = await response.json()
            if response.status != 200:
                if response.status == 401:
                    raise Exception("Invalid API key. Please check your ACCUWEATHER_API_KEY")
                elif response.status == 503:
                    raise Exception("AccuWeather API is temporarily unavailable. Please try again later.")
                else:
                    raise Exception(f"Error fetching current conditions: {response.status}, {current_conditions}")
            
        # Get hourly forecast
        forecast_url = f"{base_url}/forecasts/v1/hourly/12hour/{location_key}"
        params = {
            "apikey": api_key,
        }
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
        
        # Format response
        hourly_data = []
        for i, hour in enumerate(forecast, 1):
            hourly_data.append({
                "relative_time": f"+{i} hour{'s' if i > 1 else ''}",
                "temperature": {
                    "value": hour["Temperature"]["Value"],
                    "unit": hour["Temperature"]["Unit"]
                },
                "weather_text": hour["IconPhrase"],
                "precipitation_probability": hour["PrecipitationProbability"],
                "precipitation_type": hour.get("PrecipitationType"),
                "precipitation_intensity": hour.get("PrecipitationIntensity"),
            })
        
        # Format current conditions
        if current_conditions and len(current_conditions) > 0:
            current = current_conditions[0]
            temp_key = "Metric" if use_metric else "Imperial"
            current_data = {
                "temperature": {
                    "value": current["Temperature"][temp_key]["Value"],
                    "unit": current["Temperature"][temp_key]["Unit"]
                },
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

@mcp.tool()
async def clear_weather_cache() -> str:
    """Clear the location cache to force fresh API lookups.
    
    Returns:
        str: Confirmation message
    """
    try:
        if LOCATION_CACHE_FILE.exists():
            LOCATION_CACHE_FILE.unlink()
            return "Weather location cache cleared successfully"
        else:
            return "No cache file found - cache is already empty"
    except Exception as e:
        return f"Error clearing cache: {e}" 
