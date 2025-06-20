# Flutter MCP Server Docker Image
# Build from project root: docker build -f docker/Dockerfile -t flutter-mcp .
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml setup.py ./
COPY src ./src
COPY docs/README.md LICENSE ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose MCP default port (optional, MCP uses stdio by default)
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CACHE_DIR=/app/.cache

# Health check using our health_check tool
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; import sys; sys.path.insert(0, '/app/src'); from flutter_mcp.server import health_check; print(asyncio.run(health_check()))"

# Run the MCP server
CMD ["python", "-m", "flutter_mcp.server"]