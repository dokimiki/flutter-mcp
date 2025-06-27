# Quick Fix for MCP SuperAssistant Users

## For Users Who Already Installed from Source

1. **Pull the latest changes**:
```bash
cd flutter-mcp  # or wherever you cloned it
git pull
```

2. **Reinstall with new features**:
```bash
pip install -e .
```

3. **Start with HTTP transport**:
```bash
flutter-mcp start --transport http --port 8000
```

4. **Configure MCP SuperAssistant**:
- URL: `http://localhost:8000`
- Type: HTTP MCP Server

That's it! The HTTP transport support is now available.

## Alternative: Direct GitHub Install

If you haven't cloned the repo:
```bash
pip install git+https://github.com/flutter-mcp/flutter-mcp.git
flutter-mcp start --transport http --port 8000
```

## Troubleshooting

If `flutter-mcp` command not found:
```bash
python -m flutter_mcp.cli start --transport http --port 8000
```

Or from the source directory:
```bash
cd src
python -m flutter_mcp start --transport http --port 8000
```