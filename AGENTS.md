# Agent Guidelines for mcp-weather

## Build Commands
- **Setup**: `uv venv && uv sync`
- **Run server (STDIO)**: `uv run mcp-weather`
- **Run server (HTTP)**: `MCP_TRANSPORT=http uv run python -m mcp_weather.weather`
- **Run server (HTTP flag)**: `uv run python -m mcp_weather.weather --http`
- **Test HTTP client**: `uv run python test_http_client.py`
- **Run single test**: `uv run python -m pytest path/to/test_file.py::test_function`
- **Test functions**: Use commands from CLAUDE.md for testing individual MCP tools

## Environment Variables
- **MCP_TRANSPORT**: Set to "http" to enable HTTP transport, "stdio" for STDIO (default: stdio)
- **HOST**: HTTP server host (default: 0.0.0.0)
- **PORT**: HTTP server port (default: 8080)
- **WEATHER_SOURCE**: Weather provider - "weathergov" or "accuweather" (default: weathergov)
- **ACCUWEATHER_API_KEY**: Required when using AccuWeather
- **LOG_LEVEL**: Logging level - DEBUG, INFO, WARNING, ERROR (default: INFO)

## Code Style
- **Imports**: Standard library first, third-party, then local imports with blank lines between groups
- **Types**: Use typing module annotations (Dict, Optional, etc.) and ABC for abstract classes
- **Naming**: snake_case for functions/variables, PascalCase for classes, descriptive names preferred
- **Error handling**: Raise ValueError for input validation, catch specific exceptions, use logging module
- **Async**: Use async/await patterns with aiohttp ClientSession for HTTP requests
- **Documentation**: Docstrings for public methods explaining purpose and parameters
- **Environment**: Use python-dotenv for config, Path objects for file operations
- **Caching**: Store user data in `~/.cache/weather/` directory structure
- **Constants**: Use environment variables with sensible defaults

## Architecture
- Follow abstract base class pattern (WeatherClient) for multiple API providers
- Factory pattern for client selection based on environment variables
- FastMCP framework for MCP tool declarations with @mcp.tool() decorator
- never add Claude as a co-author to commits. Do not mention AI or Claude at all in commits.