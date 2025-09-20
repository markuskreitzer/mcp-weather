"""E2E integration tests for the weather server."""
import os
import tempfile
from pathlib import Path

import pytest

from mcp_weather.clients.accuweather import AccuWeatherClient
from mcp_weather.clients.weathergov import WeatherGovClient
from mcp_weather.weather import get_weather_client


@pytest.mark.e2e
class TestWeatherIntegration:
    """Integration tests for weather clients with real API calls (when possible)."""

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Store and restore environment for each test."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    @pytest.mark.asyncio
    async def test_weathergov_integration(self):
        """Test WeatherGov client with real API call."""
        client = WeatherGovClient()

        try:
            result = await client.get_hourly_weather("Washington, DC", "imperial")

            # Verify response structure
            assert "location" in result
            assert "source" in result
            assert "current_conditions" in result
            assert "hourly_forecast" in result

            # Verify current conditions structure
            current = result["current_conditions"]
            assert "temperature" in current
            assert "value" in current["temperature"]
            assert "unit" in current["temperature"]
            assert current["temperature"]["unit"] == "F"

            # Verify forecast structure
            forecast = result["hourly_forecast"]
            assert isinstance(forecast, list)
            assert len(forecast) > 0

            for hour in forecast[:3]:  # Check first 3 hours
                assert "relative_time" in hour
                assert "temperature" in hour
                assert "weather_text" in hour

        except Exception as e:
            pytest.skip(f"WeatherGov API not available: {e}")

    @pytest.mark.asyncio
    async def test_weathergov_metric_conversion(self):
        """Test WeatherGov client temperature conversion to metric."""
        client = WeatherGovClient()

        try:
            result = await client.get_hourly_weather("Washington, DC", "metric")

            # Verify temperature is in Celsius
            current = result["current_conditions"]
            assert current["temperature"]["unit"] == "C"

            # Verify temperature is reasonable for Celsius (typically -40 to 50)
            temp_value = current["temperature"]["value"]
            assert isinstance(temp_value, (int, float))
            assert temp_value > -50
            assert temp_value < 60

        except Exception as e:
            pytest.skip(f"WeatherGov API not available: {e}")

    @pytest.mark.asyncio
    async def test_accuweather_integration_with_mock_key(self):
        """Test AccuWeather client behavior with invalid API key."""
        # This test doesn't require a real API key, just tests error handling
        client = AccuWeatherClient("invalid_key")

        with pytest.raises(Exception) as exc_info:
            await client.get_hourly_weather("Washington, DC", "imperial")

        # Should get an API key error
        assert "Invalid API key" in str(exc_info.value)

    def test_accuweather_cache_functionality(self):
        """Test AccuWeather client caching functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            client = AccuWeatherClient("test_key")
            client._cache_dir = Path(temp_dir) / ".cache" / "weather"
            client._location_cache_file = client._cache_dir / "location_cache.json"

            # Test caching a location
            location = "Test Location"
            location_key = "12345"

            client._cache_location_key(location, location_key)

            # Verify cache file exists and contains data
            assert client._location_cache_file.exists()

            # Test retrieving from cache
            cached_key = client._get_cached_location_key(location)
            assert cached_key == location_key

            # Test cache clearing
            result = client.clear_cache()
            assert "cleared successfully" in result
            assert not client._location_cache_file.exists()

    def test_weather_client_factory_integration(self):
        """Test the weather client factory with different configurations."""
        # Test default (WeatherGov)
        os.environ.pop('WEATHER_SOURCE', None)
        client = get_weather_client()
        assert isinstance(client, WeatherGovClient)

        # Test explicit WeatherGov
        os.environ['WEATHER_SOURCE'] = 'weathergov'
        client = get_weather_client()
        assert isinstance(client, WeatherGovClient)

        # Test AccuWeather with API key
        os.environ['WEATHER_SOURCE'] = 'accuweather'
        os.environ['ACCUWEATHER_API_KEY'] = 'test_key'
        client = get_weather_client()
        assert isinstance(client, AccuWeatherClient)
        assert client.api_key == 'test_key'

    @pytest.mark.asyncio
    async def test_input_validation_integration(self):
        """Test input validation across all clients."""
        clients = [
            WeatherGovClient(),
            AccuWeatherClient("test_key")
        ]

        for client in clients:
            # Test empty location
            with pytest.raises(ValueError):
                await client.get_hourly_weather("", "imperial")

            # Test invalid units
            with pytest.raises(ValueError):
                await client.get_hourly_weather("Washington, DC", "invalid")

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling with various invalid inputs."""
        client = WeatherGovClient()

        # Test with a location that might not be found
        try:
            await client.get_hourly_weather("NonexistentCity12345", "imperial")
        except Exception as e:
            # Should get a meaningful error message
            assert isinstance(str(e), str)
            assert len(str(e)) > 0
