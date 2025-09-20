
from abc import ABC, abstractmethod


class WeatherClient(ABC):
    """Abstract base class for weather clients."""

    @abstractmethod
    async def get_hourly_weather(self, location: str, units: str = "imperial") -> dict:
        """Get current weather conditions and 12-hour forecast for a location."""
        pass
