# flutter-mcp

Stop hallucinated Flutter code. Get real docs, instantly.

Flutter MCP provides AI coding assistants with real-time access to Flutter/Dart documentation, eliminating outdated or incorrect API suggestions.

## Quick Start

```bash
# One-time usage (no installation)
npx flutter-mcp

# Or install globally
npm install -g flutter-mcp
flutter-mcp
```

## Claude Desktop Setup

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "flutter-docs": {
      "command": "npx",
      "args": ["flutter-mcp"]
    }
  }
}
```

That's it! No configuration needed.

## Features

✅ **Real-time documentation** - Always up-to-date Flutter/Dart APIs  
✅ **500+ pre-indexed widgets** - Instant access to common Flutter components  
✅ **Smart search** - Fuzzy matching finds what you need  
✅ **Pub.dev integration** - Package docs and examples included  
✅ **Zero config** - Works out of the box  

## Advanced Usage

```bash
# HTTP mode for web clients
flutter-mcp --http --port 3000

# SSE mode for streaming
flutter-mcp --sse --port 3000

# Update Python backend
flutter-mcp --install
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