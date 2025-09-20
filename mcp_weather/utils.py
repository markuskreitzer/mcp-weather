"""Shared utilities for weather clients."""
import logging
from typing import Any


def validate_weather_params(location: str, units: str) -> None:
    """Validate common weather request parameters.

    Args:
        location: The location to get weather for
        units: Temperature units ("imperial" or "metric")

    Raises:
        ValueError: If parameters are invalid
    """
    if not location or not location.strip():
        raise ValueError("Location parameter is required and cannot be empty")

    if units not in ["imperial", "metric"]:
        raise ValueError("Units must be 'imperial' (Fahrenheit) or 'metric' (Celsius)")


def handle_api_error(response_status: int, error_data: Any, service_name: str) -> None:
    """Handle common API error responses.

    Args:
        response_status: HTTP status code
        error_data: Response data (for error context)
        service_name: Name of the weather service

    Raises:
        Exception: Appropriate exception based on status code
    """
    if response_status == 401:
        raise Exception(f"Invalid API key. Please check your {service_name.upper()}_API_KEY")
    elif response_status == 503:
        raise Exception(f"{service_name} API is temporarily unavailable. Please try again later.")
    else:
        raise Exception(f"Error from {service_name}: {response_status}, {error_data}")


def fahrenheit_to_celsius(temp_f: float) -> float:
    """Convert temperature from Fahrenheit to Celsius.

    Args:
        temp_f: Temperature in Fahrenheit

    Returns:
        Temperature in Celsius
    """
    return (temp_f - 32) * 5/9


def get_temperature_unit(units: str) -> str:
    """Get temperature unit symbol for the given unit system.

    Args:
        units: Unit system ("imperial" or "metric")

    Returns:
        Temperature unit symbol ("F" or "C")
    """
    return "F" if units == "imperial" else "C"


def safe_print_warning(message: str) -> None:
    """Safely print warning message using logging if available, otherwise print.

    Args:
        message: Warning message to output
    """
    try:
        logging.warning(message)
    except Exception:
        # Fallback to print if logging is not configured
        print(f"Warning: {message}")


def format_temperature(value: float | None, units: str) -> dict:
    """Format temperature with value and unit.

    Args:
        value: Temperature value
        units: Unit system ("imperial" or "metric")

    Returns:
        Dictionary with value and unit
    """
    return {
        "value": round(value) if value is not None else None,
        "unit": get_temperature_unit(units)
    }


def format_relative_time(hour_offset: int) -> str:
    """Format relative time for hourly forecast.

    Args:
        hour_offset: Number of hours from now (1, 2, 3, etc.)

    Returns:
        Formatted relative time string ("+1 hour", "+2 hours", etc.)
    """
    return f"+{hour_offset} hour{'s' if hour_offset > 1 else ''}"


# Constants
USER_AGENT = "MCP-Weather-Client"
DEFAULT_FORECAST_HOURS = 12
