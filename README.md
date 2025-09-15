
# MCP Weather Server

A simple MCP server that provides hourly weather forecasts from either Weather.gov (default) or AccuWeather.

## Setup

1.  Install dependencies using `uv`:

    ```bash
    uv venv
    uv sync
    ```

2.  Create a `.env` file to configure the weather source and API keys. See the **Configuration** section below for details.

## Configuration

### Environment Variables

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `WEATHER_SOURCE` | Weather data provider | `weathergov` | `weathergov`, `accuweather` |
| `ACCUWEATHER_API_KEY` | Required for AccuWeather | - | Your API key |
| `MCP_TRANSPORT` | Transport protocol | `stdio` | `stdio`, `http` |
| `HOST` | HTTP server host | `0.0.0.0` | Any valid host |
| `PORT` | HTTP server port | `8080` | Any valid port |
| `LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Weather Sources

#### Weather.gov (Default)

No API key is required for the Weather.gov API.

```bash
# .env
WEATHER_SOURCE=weathergov
```

#### AccuWeather

To use AccuWeather, you need an API key.

1.  Get a free API key by registering at [AccuWeather API](https://developer.accuweather.com/).
2.  Add the following to your `.env` file:

    ```bash
    # .env
    WEATHER_SOURCE=accuweather
    ACCUWEATHER_API_KEY=your_api_key_here
    ```

### Transport Configuration

#### STDIO Transport (Default)
For use with MCP clients like Claude Desktop:

```bash
# .env
MCP_TRANSPORT=stdio
```

#### HTTP Transport
For remote access and web integration:

```bash
# .env
MCP_TRANSPORT=http
HOST=0.0.0.0
PORT=8080
```

## Running the Server

The server supports two transport modes:

### STDIO Transport (Default)
For use with MCP clients like Claude Desktop:

```bash
mcp-weather
```

Or with environment variable:

```bash
MCP_TRANSPORT=stdio mcp-weather
```

### HTTP Transport (Streamable HTTP)
For remote access and web integration:

```bash
# Using command line flag
uv run python -m mcp_weather.weather --http

# Using environment variable
MCP_TRANSPORT=http uv run python -m mcp_weather.weather
```

This starts the server on `http://localhost:8080/mcp` with FastMCP's Streamable HTTP transport.

### Testing HTTP Transport

You can test the HTTP transport with the included test client:

```bash
# Start the server in HTTP mode (in one terminal)
MCP_TRANSPORT=http uv run python -m mcp_weather.weather

# Test the client connection (in another terminal)
uv run python test_http_client.py
```

## AI Assistant Integration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": ["run", "mcp-weather"],
      "env": {
        "WEATHER_SOURCE": "weathergov"
      }
    }
  }
}
```

### Claude Code

Claude Code can connect to MCP servers via HTTP transport:

```bash
# Start the server
MCP_TRANSPORT=http uv run python -m mcp_weather.weather

# In Claude Code, connect to: http://localhost:8080/mcp
```

### OpenCode (opencode)

OpenCode supports MCP servers through its tool integration:

```bash
# Start the server in HTTP mode
MCP_TRANSPORT=http uv run python -m mcp_weather.weather

# OpenCode will automatically discover and connect to MCP servers
# running on standard ports
```

### GitHub Copilot

For Copilot integration, use the HTTP transport:

```bash
# Start the server
MCP_TRANSPORT=http uv run python -m mcp_weather.weather

# Configure Copilot to connect to http://localhost:8080/mcp
```

### Cursor

Add to your Cursor MCP configuration:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": ["run", "mcp-weather"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "WEATHER_SOURCE": "weathergov"
      }
    }
  }
}
```

## API Usage

The `get_hourly_weather` tool provides current weather conditions and a 12-hour forecast.

**Example Response (Weather.gov):**

```json
{
    "location": "Washington, DC",
    "source": "Weather.gov",
    "current_conditions": {
        "temperature": {
            "value": 75,
            "unit": "F"
        },
        "weather_text": "Sunny",
        "relative_humidity": {
            "value": 50,
            "unit": "%"
        },
        "wind_speed": "10 mph",
        "wind_direction": "NW"
    },
    "hourly_forecast": [
        {
            "relative_time": "+1 hour",
            "temperature": {
                "value": 76,
                "unit": "F"
            },
            "weather_text": "Sunny",
            "precipitation_probability": 0,
            "wind_speed": "10 mph",
            "wind_direction": "NW"
        }
    ]
}
```

**Example Response (AccuWeather):**

```json
{
    "location": "Jakarta",
    "location_key": "208971",
    "country": "Indonesia",
    "current_conditions": {
        "temperature": {
            "value": 32.2,
            "unit": "C"
        },
        "weather_text": "Partly sunny",
        "relative_humidity": 75,
        "precipitation": false,
        "observation_time": "2024-01-01T12:00:00+07:00"
    },
    "hourly_forecast": [
        {
            "relative_time": "+1 hour",
            "temperature": {
                "value": 32.2,
                "unit": "C"
            },
            "weather_text": "Partly sunny",
            "precipitation_probability": 40,
            "precipitation_type": "Rain",
            "precipitation_intensity": "Light"
        }
    ]
}
```
