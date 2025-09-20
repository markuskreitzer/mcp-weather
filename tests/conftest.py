"""Shared pytest fixtures for all tests."""
from pathlib import Path

import pytest

from mcp_weather.clients.accuweather import AccuWeatherClient
from mcp_weather.clients.weathergov import WeatherGovClient


@pytest.fixture
def weathergov_client():
    """Create a WeatherGov client instance."""
    return WeatherGovClient()


@pytest.fixture
def accuweather_client(tmp_path):
    """Create an AccuWeather client instance with temporary cache directory."""
    client = AccuWeatherClient("test_api_key")
    # Use temporary directory for cache tests
    client._cache_dir = tmp_path / ".cache" / "weather"
    client._location_cache_file = client._cache_dir / "location_cache.json"
    return client


@pytest.fixture(params=["", "  ", None])
def invalid_location(request):
    """Parametrized fixture for invalid location values."""
    return request.param


@pytest.fixture(params=["kelvin", "fahrenheit", "celsius", "invalid"])
def invalid_units(request):
    """Parametrized fixture for invalid units values."""
    return request.param


@pytest.fixture(params=["imperial", "metric"])
def valid_units(request):
    """Parametrized fixture for valid units values."""
    return request.param


@pytest.fixture
def sample_location():
    """Sample location for testing."""
    return "Huntsville, AL"


@pytest.fixture
def sample_location_key():
    """Sample AccuWeather location key for testing."""
    return "331435"


@pytest.fixture
def mock_accuweather_location_response():
    """Mock AccuWeather location search response."""
    return [
        {
            "Key": "331435",
            "LocalizedName": "Huntsville",
            "Country": {"LocalizedName": "United States"},
            "AdministrativeArea": {"LocalizedName": "Alabama"},
        }
    ]


@pytest.fixture
def mock_accuweather_current_conditions():
    """Mock AccuWeather current conditions response."""
    return [
        {
            "Temperature": {
                "Imperial": {"Value": 75, "Unit": "F"},
                "Metric": {"Value": 24, "Unit": "C"},
            },
            "WeatherText": "Partly cloudy",
            "RelativeHumidity": 45,
            "HasPrecipitation": False,
            "LocalObservationDateTime": "2023-01-01T12:00:00-06:00",
        }
    ]


@pytest.fixture
def mock_accuweather_forecast():
    """Mock AccuWeather hourly forecast response."""
    return [
        {
            "Temperature": {"Value": 75, "Unit": "F"},
            "IconPhrase": "Partly cloudy",
            "PrecipitationProbability": 20,
            "PrecipitationType": None,
            "PrecipitationIntensity": None,
        },
        {
            "Temperature": {"Value": 73, "Unit": "F"},
            "IconPhrase": "Mostly cloudy",
            "PrecipitationProbability": 30,
            "PrecipitationType": None,
            "PrecipitationIntensity": None,
        },
    ]