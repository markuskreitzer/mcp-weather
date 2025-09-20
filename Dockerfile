FROM python:3.11-slim as builder

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies in a virtual environment
RUN uv sync --frozen --no-cache

FROM python:3.11-slim as runtime

# Install uv for runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY mcp_weather/ ./mcp_weather/
COPY pyproject.toml ./

# Create cache directory for weather data
RUN mkdir -p /app/.cache/weather

# Set environment variables for HTTP streaming mode
ENV MCP_TRANSPORT=http
ENV HOST=0.0.0.0
ENV PORT=8080
ENV WEATHER_SOURCE=weathergov
ENV LOG_LEVEL=INFO

# Make sure we use venv
ENV PATH="/app/.venv/bin:$PATH"

# Expose port for HTTP transport
EXPOSE 8080

# Health check to ensure the server is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the MCP server
CMD ["uvicorn", "mcp_weather.weather:mcp.run_server", "--host", "0.0.0.0", "--port", "8080"]