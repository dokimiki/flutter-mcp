#!/bin/bash
# Script to publish Flutter MCP Server to PyPI

set -e  # Exit on error

echo "🚀 Publishing Flutter MCP Server to PyPI..."

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PYTHON_VERSION"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info src/*.egg-info

# Install build tools
echo "📦 Installing build tools..."
pip install --upgrade pip setuptools wheel twine build

# Build the package
echo "🔨 Building package..."
python -m build

# Check the package
echo "✅ Checking package with twine..."
twine check dist/*

# Show what will be uploaded
echo ""
echo "📦 Package contents:"
ls -la dist/

echo ""
echo "⚠️  Ready to upload to PyPI!"
echo "To upload to TestPyPI first (recommended):"
echo "  twine upload --repository testpypi dist/*"
echo ""
echo "To upload to PyPI:"
echo "  twine upload dist/*"
echo ""
echo "Note: You'll need PyPI credentials configured in ~/.pypirc or use:"
echo "  export TWINE_USERNAME=__token__"
echo "  export TWINE_PASSWORD=<your-pypi-token>"