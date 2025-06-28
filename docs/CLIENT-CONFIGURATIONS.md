# MCP Client Configurations

This document provides configuration examples for various MCP clients to connect to Flutter MCP Server.

## Transport Modes Overview

Flutter MCP Server supports three transport modes:
- **STDIO** (default): Standard input/output communication
- **HTTP**: REST-like HTTP transport
- **SSE**: Server-Sent Events for streaming

## Claude Desktop

**Transport**: STDIO

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "flutter-mcp": {
      "command": "flutter-mcp",
      "args": ["start"],
      "env": {}
    }
  }
}
```

Or using npx:
```json
{
  "mcpServers": {
    "flutter-mcp": {
      "command": "npx",
      "args": ["@flutter-mcp/server", "start"],
      "env": {}
    }
  }
}
```

## MCP SuperAssistant

**Transport**: HTTP

1. Start the server:
   ```bash
   flutter-mcp start --transport http --port 8000
   ```

2. In MCP SuperAssistant:
   - Click "Add Server"
   - Name: `Flutter MCP`
   - URL: `http://localhost:8000`
   - Type: `HTTP MCP Server`

## Claude Code (claude.ai/code)

**Transport**: STDIO

### Global Configuration

Install globally and Claude Code will auto-detect:
```bash
pip install flutter-mcp-server
```

### Per-Project Configuration

Create `.mcp.json` in your project root:
```json
{
  "mcpServers": {
    "flutter-mcp": {
      "command": "/path/to/flutter-mcp/venv/bin/flutter-mcp",
      "args": ["start"]
    }
  }
}
```

## VS Code + Continue

**Transport**: STDIO

In `.continuerc.json`:
```json
{
  "models": [
    {
      "provider": "claude",
      "mcp_servers": {
        "flutter-mcp": {
          "command": "flutter-mcp",
          "args": ["start"]
        }
      }
    }
  ]
}
```

## Custom HTTP Client

**Transport**: HTTP

```python
import httpx

# Start server: flutter-mcp start --transport http --port 8000

client = httpx.Client(base_url="http://localhost:8000")

# Make MCP requests
response = client.post("/mcp/v1/tools/list")
tools = response.json()

# Call a tool
response = client.post("/mcp/v1/tools/call", json={
    "name": "get_flutter_docs",
    "arguments": {
        "query": "StatefulWidget"
    }
})
```

## Custom SSE Client

**Transport**: SSE

```javascript
// Start server: flutter-mcp start --transport sse --port 8080

const eventSource = new EventSource('http://localhost:8080/sse');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Send requests via POST to the same server
fetch('http://localhost:8080/mcp/v1/tools/list', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' }
})
.then(res => res.json())
.then(console.log);
```

## Docker Configurations

### Claude Desktop with Docker

```json
{
  "mcpServers": {
    "flutter-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "ghcr.io/flutter-mcp/flutter-mcp:latest"
      ]
    }
  }
}
```

### HTTP Server with Docker

```bash
# Run with HTTP transport exposed
docker run -p 8000:8000 ghcr.io/flutter-mcp/flutter-mcp:latest \
  flutter-mcp start --transport http --host 0.0.0.0 --port 8000
```

## Environment Variables

All transport modes support these environment variables:

```bash
# Cache directory
export CACHE_DIR=/path/to/cache

# Debug logging
export DEBUG=1

# Transport settings (when not using CLI args)
export MCP_TRANSPORT=http
export MCP_PORT=8000
export MCP_HOST=0.0.0.0
```

## Troubleshooting Connection Issues

### STDIO Transport
- Ensure the command path is correct
- Check Python is installed: `python3 --version`
- Verify installation: `flutter-mcp --version`

### HTTP/SSE Transport
- Check port availability: `lsof -i :8000`
- Try different port: `--port 8080`
- Bind to all interfaces: `--host 0.0.0.0`
- Check firewall settings

### Common Issues

1. **"Connection refused"**
   - Server not running
   - Wrong port
   - Firewall blocking connection

2. **"Command not found"**
   - Package not installed
   - Wrong path in configuration
   - Virtual environment not activated

3. **"Transport mismatch"**
   - Client expects different transport
   - Check client documentation
   - Use correct transport flag

## Testing Connection

### Test STDIO
```bash
echo '{"method": "mcp/v1/tools/list"}' | flutter-mcp start
```

### Test HTTP
```bash
# Start server
flutter-mcp start --transport http --port 8000

# Test with curl
curl -X POST http://localhost:8000/mcp/v1/tools/list
```

### Test SSE
```bash
# Start server
flutter-mcp start --transport sse --port 8080

# Test with curl
curl http://localhost:8080/sse
```