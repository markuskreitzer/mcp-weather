"""Unit tests for weather clients."""
import json

import pytest

from mcp_weather.clients.base import WeatherClient


class TestWeatherClient:
    """Test the abstract base WeatherClient class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that WeatherClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            WeatherClient()


@pytest.mark.unit
class TestWeatherGovClient:
    """Test the WeatherGov client implementation."""

    def test_initialization(self, weathergov_client):
        """Test WeatherGovClient initialization."""
        assert weathergov_client.base_url == "https://api.weather.gov"

    @pytest.mark.asyncio
    async def test_invalid_location_parameter(self, weathergov_client, invalid_location):
        """Test handling of invalid location parameters."""
        if invalid_location is None:
            pytest.skip("None is not a valid test case for location string")

        with pytest.raises(ValueError) as exc_info:
            await weathergov_client.get_hourly_weather(invalid_location, "imperial")
        assert "Location parameter is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_units_parameter(self, weathergov_client, invalid_units, sample_location):
        """Test handling of invalid units parameters."""
        with pytest.raises(ValueError) as exc_info:
            await weathergov_client.get_hourly_weather(sample_location, invalid_units)
        assert "Units must be" in str(exc_info.value)


@pytest.mark.unit
class TestAccuWeatherClient:
    """Test the AccuWeather client implementation."""

    def test_initialization(self, accuweather_client):
        """Test AccuWeatherClient initialization."""
        assert accuweather_client.api_key == "test_api_key"
        assert accuweather_client.base_url == "http://dataservice.accuweather.com"

    def test_initialization_without_api_key(self):
        """Test AccuWeatherClient initialization fails without API key."""
        from mcp_weather.clients.accuweather import AccuWeatherClient

        with pytest.raises(ValueError) as exc_info:
            AccuWeatherClient("")
        assert "ACCUWEATHER_API_KEY is required" in str(exc_info.value)

    def test_cache_location_key(self, accuweather_client, sample_location, sample_location_key):
        """Test caching location keys."""
        accuweather_client._cache_location_key(sample_location, sample_location_key)

        # Check that cache file was created and contains correct data
        assert accuweather_client._location_cache_file.exists()

        with open(accuweather_client._location_cache_file) as f:
            cache = json.load(f)

        assert cache[sample_location.lower().strip()] == sample_location_key

    def test_get_cached_location_key(self, accuweather_client, sample_location, sample_location_key):
        """Test retrieving cached location keys."""
        # First cache a location
        accuweather_client._cache_location_key(sample_location, sample_location_key)

        # Then retrieve it
        cached_key = accuweather_client._get_cached_location_key(sample_location)
        assert cached_key == sample_location_key

        # Test case insensitive lookup
        cached_key = accuweather_client._get_cached_location_key("huntsville, al")
        assert cached_key == sample_location_key

        # Test non-existent location
        cached_key = accuweather_client._get_cached_location_key("NonExistent")
        assert cached_key is None

    def test_get_cached_location_key_no_cache_file(self, accuweather_client, sample_location):
        """Test retrieving from cache when no cache file exists."""
        cached_key = accuweather_client._get_cached_location_key(sample_location)
        assert cached_key is None

    def test_clear_cache(self, accuweather_client, sample_location, sample_location_key):
        """Test clearing the location cache."""
        # Create cache file
        accuweather_client._cache_location_key(sample_location, sample_location_key)

        # Verify cache exists
        assert accuweather_client._location_cache_file.exists()

        # Clear cache
        result = accuweather_client.clear_cache()

        # Verify cache is cleared
        assert not accuweather_client._location_cache_file.exists()
        assert "cleared successfully" in result

    def test_clear_cache_no_file(self, accuweather_client):
        """Test clearing cache when no cache file exists."""
        result = accuweather_client.clear_cache()
        assert "already empty" in result

    @pytest.mark.asyncio
    async def test_invalid_location_parameter(self, accuweather_client, invalid_location):
        """Test handling of invalid location parameters."""
        if invalid_location is None:
            pytest.skip("None is not a valid test case for location string")

        with pytest.raises(ValueError) as exc_info:
            await accuweather_client.get_hourly_weather(invalid_location, "imperial")
        assert "Location parameter is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_units_parameter(self, accuweather_client, invalid_units, sample_location):
        """Test handling of invalid units parameters."""
        with pytest.raises(ValueError) as exc_info:
            await accuweather_client.get_hourly_weather(sample_location, invalid_units)
        assert "Units must be" in str(exc_info.value)
