#!/bin/bash
# Test script for Flutter MCP Server

echo "🚀 Flutter MCP Server Test Script"
echo "================================"

# Check if Redis is running
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "❌ Redis is not running. Starting Redis..."
        if command -v redis-server &> /dev/null; then
            redis-server --daemonize yes
            echo "✅ Redis started"
        else
            echo "❌ Redis is not installed. Please install Redis first:"
            echo "   macOS: brew install redis"
            echo "   Ubuntu: sudo apt-get install redis-server"
            echo ""
            echo "The server will run without caching (slower responses)"
        fi
    fi
else
    echo "⚠️  Redis CLI not found. The server will run without caching."
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    # Source uv if installed locally
    if [ -f "$HOME/.local/bin/env" ]; then
        source "$HOME/.local/bin/env"
    fi
fi

echo ""
echo "Starting MCP Inspector..."
echo "========================="

# Run with MCP Inspector
if command -v uv &> /dev/null; then
    uv run mcp dev server.py
else
    echo "❌ uv not found. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Or run directly with Python:"
    echo "   python server.py"
fi