# Publishing Flutter MCP Server

This document explains how to publish Flutter MCP Server to PyPI and npm.

## PyPI Publication

### Prerequisites

1. PyPI account: https://pypi.org/account/register/
2. PyPI API token: https://pypi.org/manage/account/token/
3. TestPyPI account (optional but recommended): https://test.pypi.org/account/register/

### Setup

1. Configure PyPI credentials:
   ```bash
   cp .pypirc.template ~/.pypirc
   # Edit ~/.pypirc with your API tokens
   ```

   Or use environment variables:
   ```bash
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=pypi-your-token-here
   ```

2. Install build tools:
   ```bash
   pip install --upgrade pip setuptools wheel twine build
   ```

### Publishing Process

1. Update version in:
   - `pyproject.toml`
   - `setup.py`
   - `src/flutter_mcp/cli.py` (__version__)

2. Run the publish script:
   ```bash
   ./scripts/publish-pypi.sh
   ```

3. Test on TestPyPI first (recommended):
   ```bash
   twine upload --repository testpypi dist/*
   
   # Test installation
   pip install -i https://test.pypi.org/simple/ flutter-mcp-server
   ```

4. Publish to PyPI:
   ```bash
   twine upload dist/*
   ```

5. Verify installation:
   ```bash
   pip install flutter-mcp-server
   flutter-mcp --version
   ```

## NPM Publication

### Prerequisites

1. npm account: https://www.npmjs.com/signup
2. Login to npm: `npm login`

### Publishing Process

1. Update version in `npm-wrapper/package.json`

2. Navigate to npm wrapper directory:
   ```bash
   cd npm-wrapper
   ```

3. Run the publish script:
   ```bash
   ./publish.sh
   ```

4. Verify installation:
   ```bash
   npx @flutter-mcp/server --version
   ```

## Version Synchronization

Keep versions synchronized across:
- `pyproject.toml`
- `setup.py`
- `src/flutter_mcp/cli.py`
- `npm-wrapper/package.json`

## Release Checklist

- [ ] Update version numbers
- [ ] Update CHANGELOG
- [ ] Run tests: `pytest`
- [ ] Test locally: `flutter-mcp start`
- [ ] Build and check package: `./scripts/publish-pypi.sh`
- [ ] Publish to TestPyPI
- [ ] Test installation from TestPyPI
- [ ] Publish to PyPI
- [ ] Publish npm wrapper
- [ ] Create GitHub release
- [ ] Update documentation

## Troubleshooting

### "Invalid distribution file"
- Ensure README.md exists in docs/
- Check MANIFEST.in includes all necessary files

### "Version already exists"
- Increment version number
- Delete old builds: `rm -rf dist/ build/`

### npm publish fails
- Ensure you're logged in: `npm whoami`
- Check package name availability
- Verify package.json is valid: `npm pack --dry-run`