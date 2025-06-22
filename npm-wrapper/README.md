# @flutter-mcp/server

NPM wrapper for Flutter MCP Server - Real-time Flutter/Dart documentation for AI assistants.

This package provides an easy way to install and run the Flutter MCP Server without needing to manage Python dependencies directly.

## Installation

You don't need to install this package globally. Just use npx:

```bash
npx @flutter-mcp/server
```

## Usage

### Run the server
```bash
npx @flutter-mcp/server start
```

### Use with different transports
```bash
# STDIO transport (default - for Claude Desktop)
npx @flutter-mcp/server start

# HTTP transport (for MCP SuperAssistant)
npx @flutter-mcp/server start --transport http --port 8000

# SSE transport
npx @flutter-mcp/server start --transport sse --port 8080
```

Then add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "flutter-mcp": {
      "command": "npx",
      "args": ["@flutter-mcp/server", "start"]
    }
  }
}
```

### Install Python package only
```bash
npx @flutter-mcp/server --install
```

## Requirements

- Node.js 16+
- Python 3.8+
- pip (Python package manager)

## What it does

This wrapper:
1. Checks for Python 3.8+ installation
2. Installs the `flutter-mcp-server` Python package if needed
3. Runs the Flutter MCP Server

## Documentation

For full documentation, visit: https://github.com/flutter-mcp/flutter-mcp

## License

MIT