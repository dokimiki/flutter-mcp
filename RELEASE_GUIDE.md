# Release Guide for Flutter MCP Server

## ✅ Package Status

The package has been successfully built and is ready for publication:
- **PyPI Package**: `flutter_mcp_server-0.1.0` 
- **npm Package**: `@flutter-mcp/server@0.1.0`

## 🚀 Publishing to PyPI

### 1. Create PyPI Account
- Main PyPI: https://pypi.org/account/register/
- Test PyPI: https://test.pypi.org/account/register/

### 2. Get API Token
- Go to https://pypi.org/manage/account/token/
- Create a new API token with scope "Entire account"
- Save the token securely (starts with `pypi-`)

### 3. Publish to TestPyPI (Recommended First)
```bash
# Set your TestPyPI token
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<your-test-pypi-token>

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation
pip install -i https://test.pypi.org/simple/ flutter-mcp-server
```

### 4. Publish to PyPI
```bash
# Set your PyPI token
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<your-pypi-token>

# Upload to PyPI
twine upload dist/*
```

### 5. Verify Installation
```bash
pip install flutter-mcp-server
flutter-mcp --version
```

## 📦 Publishing npm Package

### 1. Login to npm
```bash
npm login
```

### 2. Publish the Package
```bash
cd npm-wrapper
./publish.sh
```

### 3. Verify Installation
```bash
npx @flutter-mcp/server --version
```

## 🎉 What's New in This Release

### Transport Support (v0.1.0)
- **STDIO Transport** (default) - For Claude Desktop and most MCP clients
- **HTTP Transport** - For MCP SuperAssistant and HTTP-based clients  
- **SSE Transport** - For Server-Sent Events based clients

### Usage Examples

#### HTTP Transport (for MCP SuperAssistant)
```bash
flutter-mcp start --transport http --port 8000
```

#### SSE Transport
```bash
flutter-mcp start --transport sse --port 8080
```

#### Custom Host Binding
```bash
flutter-mcp start --transport http --host 0.0.0.0 --port 3000
```

## 📝 Post-Release Checklist

- [ ] Upload to TestPyPI and test
- [ ] Upload to PyPI
- [ ] Publish npm package
- [ ] Create GitHub release with tag `v0.1.0`
- [ ] Update the main README if needed
- [ ] Announce in relevant communities

## 🔧 Troubleshooting

### "Package already exists"
The package name might be taken. Check:
- PyPI: https://pypi.org/project/flutter-mcp-server/
- npm: https://www.npmjs.com/package/@flutter-mcp/server

### Build Issues
```bash
# Clean and rebuild
rm -rf dist/ build/ *.egg-info src/*.egg-info
python -m build
```

### npm Login Issues
```bash
npm whoami  # Check if logged in
npm login   # Login again if needed
```