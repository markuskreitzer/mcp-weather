import logging
import os

from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_weather.clients.accuweather import AccuWeatherClient
from mcp_weather.clients.base import WeatherClient
from mcp_weather.clients.weathergov import WeatherGovClient

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastMCP
mcp = FastMCP("mcp-weather")

def get_weather_client() -> WeatherClient:
    """Factory function to get the weather client based on the environment variable."""
    source = os.getenv("WEATHER_SOURCE", "weathergov").lower()
    logging.info(f"Using weather source: {source}")
    if source == "accuweather":
        api_key = os.getenv("ACCUWEATHER_API_KEY")
        if not api_key:
            raise ValueError("ACCUWEATHER_API_KEY is required for AccuWeather client.")
        return AccuWeatherClient(api_key)
    elif source == "weathergov":
        return WeatherGovClient()
    else:
        raise ValueError(f"Invalid weather source: {source}")

@mcp.tool()
async def get_hourly_weather(location: str, units: str = "imperial") -> dict:
    """Get current weather conditions and 12-hour forecast for a location."""
    client = get_weather_client()
    return await client.get_hourly_weather(location, units)

@mcp.tool()
async def clear_weather_cache(source: str = "accuweather") -> str:
    """Clear the location cache to force fresh API lookups."""
    source = source.lower()
    if source == "accuweather":
        api_key = os.getenv("ACCUWEATHER_API_KEY")
        if not api_key:
            return "Cannot clear cache: ACCUWEATHER_API_KEY is not set."
        client = AccuWeatherClient(api_key)
        return client.clear_cache()
    else:
        return f"Cache clearing not supported for source: {source}"

# Add health endpoint for Docker health checks
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Simple health check endpoint for Docker containers."""
    return JSONResponse({"status": "healthy", "service": "mcp-weather"})

# Support for running with HTTP transport
if __name__ == "__main__":
    import sys

    # Check for HTTP transport via command line flag or environment variable
    use_http = (len(sys.argv) > 1 and sys.argv[1] == "--http") or os.getenv("MCP_TRANSPORT", "").lower() == "http"

    if use_http:
        # Run with HTTP transport (Streamable HTTP)
        port = int(os.getenv("PORT", "8080"))
        host = os.getenv("HOST", "0.0.0.0")

        logging.info(f"Starting mcp-weather server with HTTP transport on {host}:{port}")
        mcp.run(transport="http", host=host, port=port)
    else:
        # Default STDIO transport
        mcp.run()
