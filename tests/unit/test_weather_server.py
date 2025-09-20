"""Unit tests for weather server functionality."""
import os

import pytest

from mcp_weather.clients.accuweather import AccuWeatherClient
from mcp_weather.clients.weathergov import WeatherGovClient
from mcp_weather.weather import get_weather_client


@pytest.mark.unit
class TestWeatherServer:
    """Test the main weather server functionality."""

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Store and restore environment for each test."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_get_weather_client_default(self):
        """Test get_weather_client returns WeatherGovClient by default."""
        # Clear WEATHER_SOURCE to test default
        os.environ.pop('WEATHER_SOURCE', None)

        client = get_weather_client()
        assert isinstance(client, WeatherGovClient)

    def test_get_weather_client_weathergov(self):
        """Test get_weather_client returns WeatherGovClient when specified."""
        os.environ['WEATHER_SOURCE'] = 'weathergov'

        client = get_weather_client()
        assert isinstance(client, WeatherGovClient)

    def test_get_weather_client_accuweather_with_key(self):
        """Test get_weather_client returns AccuWeatherClient when API key provided."""
        os.environ['WEATHER_SOURCE'] = 'accuweather'
        os.environ['ACCUWEATHER_API_KEY'] = 'test_key'

        client = get_weather_client()
        assert isinstance(client, AccuWeatherClient)
        assert client.api_key == 'test_key'

    def test_get_weather_client_accuweather_no_key(self):
        """Test get_weather_client raises error when AccuWeather selected but no API key."""
        os.environ['WEATHER_SOURCE'] = 'accuweather'
        os.environ.pop('ACCUWEATHER_API_KEY', None)

        with pytest.raises(ValueError) as exc_info:
            get_weather_client()

        assert "ACCUWEATHER_API_KEY is required" in str(exc_info.value)

    def test_get_weather_client_invalid_source(self):
        """Test get_weather_client raises error for invalid weather source."""
        os.environ['WEATHER_SOURCE'] = 'invalid_source'

        with pytest.raises(ValueError) as exc_info:
            get_weather_client()

        assert "Invalid weather source" in str(exc_info.value)

    def test_mcp_server_exists(self):
        """Test that MCP server is properly configured."""
        from mcp_weather.weather import mcp

        assert mcp is not None
        assert mcp.name == "mcp-weather"

        # Test that the tools are registered (they exist as FastMCP tools)
        from mcp_weather.weather import clear_weather_cache, get_hourly_weather
        assert get_hourly_weather is not None
        assert clear_weather_cache is not None
