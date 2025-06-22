#!/bin/bash
# Script to publish the npm wrapper package

echo "Publishing @flutter-mcp/server to npm..."

# Check if logged in to npm
if ! npm whoami &> /dev/null; then
    echo "Error: Not logged in to npm. Please run 'npm login' first."
    exit 1
fi

# Clean any previous builds
rm -rf node_modules package-lock.json

# Install dependencies
echo "Installing dependencies..."
npm install

# Run prepublish script
npm run prepublishOnly

# Publish to npm
echo "Publishing to npm..."
npm publish --access public

echo "✅ Published successfully!"
echo ""
echo "Users can now install with:"
echo "  npx @flutter-mcp/server"