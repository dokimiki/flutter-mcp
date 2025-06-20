# Flutter MCP Server Development Guide

## Quick Start

1. **Install Redis** (required for caching):
   ```bash
   # macOS
   brew install redis && brew services start redis
   
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # Docker (alternative)
   docker run -d -p 6379:6379 --name flutter-mcp-redis redis:alpine
   ```

2. **Run the test script**:
   ```bash
   ./test-server.sh
   ```

   This will:
   - Check if Redis is running
   - Start the MCP Inspector
   - Open a web interface at http://localhost:5173

3. **Test the tools** in MCP Inspector:
   
   **Get Flutter documentation:**
   ```json
   {
     "class_name": "Container",
     "library": "widgets"
   }
   ```
   
   **Search Flutter docs:**
   ```json
   {
     "query": "material.AppBar"
   }
   ```
   
   **Get pub.dev package info:**
   ```json
   {
     "package_name": "provider"
   }
   ```

## Development Commands

```bash
# Install dependencies
uv sync

# Run server directly
uv run server.py

# Run with MCP Inspector (recommended)
uv run mcp dev server.py

# Run without uv
python server.py
```

## Testing with Claude Desktop

1. Add to Claude Desktop config:
   ```json
   {
     "mcpServers": {
       "flutter-mcp": {
         "command": "uv",
         "args": ["--directory", "/path/to/flutter-docs-mcp", "run", "server.py"]
       }
     }
   }
   ```

2. Restart Claude Desktop

3. Test with queries like:
   - "How do I use the Container widget in Flutter?"
   - "Show me the documentation for material.Scaffold"
   - "What's the latest version of the provider package?"

## Architecture

- **FastMCP**: Handles MCP protocol and tool registration
- **Redis**: Caches processed documentation (24h for APIs, 12h for packages)
- **Rate Limiter**: Ensures respectful scraping (2 requests/second)
- **HTML Parser**: Converts Flutter docs to clean Markdown
- **Structured Logging**: Track performance and debug issues

## Common Issues

1. **Redis not running**: Server works but responses are slower
2. **Rate limiting**: First requests take 1-2 seconds
3. **404 errors**: Check class name and library spelling

## Next Steps

- [ ] Add pub.dev README parsing
- [ ] Implement @flutter_mcp activation
- [ ] Add Flutter cookbook integration
- [ ] Support version-specific docs