#!/bin/bash
# Build standalone executables for Flutter MCP Server

set -e

echo "🔨 Building Flutter MCP Server executables..."

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Install PyInstaller if not already installed
pip install pyinstaller

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Build the executable
echo "🏗️ Building executable..."
pyinstaller build.spec

# Create release directory
mkdir -p releases

# Get the platform
PLATFORM=$(python -c "import platform; print(platform.system().lower())")
ARCH=$(python -c "import platform; print(platform.machine())")

# Move and rename based on platform
if [ "$PLATFORM" = "darwin" ]; then
    if [ "$ARCH" = "arm64" ]; then
        BINARY_NAME="flutter-mcp-macos-arm64"
    else
        BINARY_NAME="flutter-mcp-macos-x64"
    fi
elif [ "$PLATFORM" = "linux" ]; then
    BINARY_NAME="flutter-mcp-linux-x64"
elif [ "$PLATFORM" = "windows" ]; then
    BINARY_NAME="flutter-mcp-windows-x64.exe"
else
    BINARY_NAME="flutter-mcp-$PLATFORM-$ARCH"
fi

# Move the binary
mv "dist/flutter-mcp" "releases/$BINARY_NAME" 2>/dev/null || \
mv "dist/flutter-mcp.exe" "releases/$BINARY_NAME" 2>/dev/null

echo "✅ Build complete! Binary available at: releases/$BINARY_NAME"

# Test the binary
echo "🧪 Testing the binary..."
"./releases/$BINARY_NAME" --version

echo "
📦 Binary details:"
ls -lh "releases/$BINARY_NAME"
file "releases/$BINARY_NAME"

echo "
🚀 To distribute, upload releases/$BINARY_NAME to GitHub Releases"