# Flutter MCP Server API Reference

## Overview

The Flutter MCP (Model Context Protocol) server provides AI assistants with seamless access to Flutter, Dart, and pub.dev documentation through on-demand web scraping with Redis caching. This ensures you always get the most current documentation while maintaining fast response times.

## Activation

To use the Flutter MCP tools, mention `@flutter_mcp` in your prompt. This activates the Flutter documentation context and makes the following tools available.

## Rate Limiting

All tools respect a rate limit of **2 requests per second** to ensure responsible use of documentation servers. Requests exceeding this limit will be queued automatically.

## Caching Behavior

- **Flutter/Dart API Documentation**: Cached for 24 hours
- **Pub.dev Package Documentation**: Cached for 12 hours
- **Search Results**: Cached for 1 hour

Cached responses are stored in Redis with appropriate TTLs to balance freshness with performance.

## Available Tools

### 1. get_flutter_docs

Retrieves documentation for Flutter and Dart classes, methods, properties, and constructors.

#### Description
Fetches and processes documentation from api.flutter.dev and api.dart.dev, providing clean, well-formatted documentation with examples and usage information.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | The Flutter/Dart API element to search for (e.g., "Container", "setState", "Future.wait") |

#### Return Format

```json
{
  "content": "string",      // Formatted documentation content
  "source_url": "string",   // URL of the documentation page
  "cached": "boolean"       // Whether response was served from cache
}
```

#### Example Requests

**Basic Widget Documentation:**
```json
{
  "query": "Container"
}
```

**Method Documentation:**
```json
{
  "query": "setState"
}
```

**Dart Core Library:**
```json
{
  "query": "Future.wait"
}
```

#### Example Responses

**Success Response:**
```json
{
  "content": "# Container class\n\nA convenience widget that combines common painting, positioning, and sizing widgets.\n\n## Description\n\nA container first surrounds the child with padding (inflated by any borders present in the decoration) and then applies additional constraints to the padded extent...\n\n## Example\n\n```dart\nContainer(\n  margin: const EdgeInsets.all(10.0),\n  color: Colors.amber[600],\n  width: 48.0,\n  height: 48.0,\n)\n```",
  "source_url": "https://api.flutter.dev/flutter/widgets/Container-class.html",
  "cached": false
}
```

**Error Response:**
```json
{
  "error": "Documentation not found for 'NonExistentWidget'. Try searching for a valid Flutter/Dart API element."
}
```

#### Common Use Cases

1. **Widget Documentation**: Get detailed information about Flutter widgets
   - `Container`, `Column`, `Row`, `Scaffold`, `AppBar`

2. **State Management**: Understanding Flutter's state management APIs
   - `setState`, `StatefulWidget`, `State`, `InheritedWidget`

3. **Dart Core Libraries**: Access Dart language features
   - `Future`, `Stream`, `List`, `Map`, `String`

4. **Material Design Components**: Material Design widgets
   - `MaterialApp`, `ThemeData`, `IconButton`, `TextField`

### 2. get_pub_package_docs

Retrieves documentation for packages published on pub.dev.

#### Description
Fetches package information, README content, and metadata from pub.dev using the official API, providing comprehensive package documentation.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `package_name` | string | Yes | The exact name of the package on pub.dev |

#### Return Format

```json
{
  "content": "string",      // Formatted package documentation
  "metadata": {
    "name": "string",
    "version": "string",
    "description": "string",
    "homepage": "string",
    "repository": "string",
    "documentation": "string",
    "pub_url": "string"
  },
  "cached": "boolean"
}
```

#### Example Requests

**Popular Package:**
```json
{
  "package_name": "provider"
}
```

**HTTP Client Package:**
```json
{
  "package_name": "dio"
}
```

#### Example Responses

**Success Response:**
```json
{
  "content": "# provider\n\nA wrapper around InheritedWidget to make them easier to use and more reusable.\n\n## Features\n\n- Simplifies InheritedWidget usage\n- Supports multiple providers\n- Lazy loading of values...\n\n## Getting started\n\n```yaml\ndependencies:\n  provider: ^6.1.0\n```\n\n## Usage\n\n```dart\nimport 'package:provider/provider.dart';\n\nvoid main() {\n  runApp(\n    ChangeNotifierProvider(\n      create: (context) => Counter(),\n      child: MyApp(),\n    ),\n  );\n}\n```",
  "metadata": {
    "name": "provider",
    "version": "6.1.0",
    "description": "A wrapper around InheritedWidget to make them easier to use and more reusable.",
    "homepage": "https://github.com/rrousselGit/provider",
    "repository": "https://github.com/rrousselGit/provider",
    "documentation": "https://pub.dev/documentation/provider/latest/",
    "pub_url": "https://pub.dev/packages/provider"
  },
  "cached": false
}
```

**Package Not Found:**
```json
{
  "error": "Package 'non-existent-package' not found on pub.dev"
}
```

#### Common Use Cases

1. **State Management Packages**: 
   - `provider`, `riverpod`, `bloc`, `getx`, `mobx`

2. **HTTP/Networking**:
   - `dio`, `http`, `retrofit`, `chopper`

3. **Database/Storage**:
   - `sqflite`, `hive`, `shared_preferences`, `path_provider`

4. **UI/Animation**:
   - `animations`, `lottie`, `shimmer`, `cached_network_image`

### 3. search_pub_packages

Searches for packages on pub.dev based on keywords or functionality.

#### Description
Searches pub.dev for packages matching your query, returning a list of relevant packages with their descriptions and metadata. Useful for discovering packages for specific functionality.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search terms to find packages (e.g., "state management", "http client", "animations") |
| `max_results` | integer | No | Maximum number of results to return (default: 10, max: 30) |

#### Return Format

```json
{
  "results": [
    {
      "name": "string",
      "description": "string",
      "version": "string",
      "publisher": "string",
      "score": "number",
      "url": "string"
    }
  ],
  "total_found": "integer",
  "cached": "boolean"
}
```

#### Example Requests

**Search for State Management:**
```json
{
  "query": "state management",
  "max_results": 5
}
```

**Search for HTTP Packages:**
```json
{
  "query": "http client"
}
```

#### Example Responses

**Success Response:**
```json
{
  "results": [
    {
      "name": "provider",
      "description": "A wrapper around InheritedWidget to make them easier to use and more reusable.",
      "version": "6.1.0",
      "publisher": "flutter.dev",
      "score": 99,
      "url": "https://pub.dev/packages/provider"
    },
    {
      "name": "riverpod",
      "description": "A simple way to access state while robust and testable.",
      "version": "2.4.0",
      "publisher": null,
      "score": 96,
      "url": "https://pub.dev/packages/riverpod"
    }
  ],
  "total_found": 156,
  "cached": false
}
```

**No Results:**
```json
{
  "results": [],
  "total_found": 0,
  "cached": false,
  "message": "No packages found matching 'very-specific-nonexistent-query'"
}
```

#### Common Use Cases

1. **Finding Alternatives**: Search for packages providing similar functionality
   - "state management" → provider, bloc, riverpod, getx
   - "navigation" → go_router, auto_route, beamer

2. **Specific Features**: Search for packages implementing specific features
   - "camera", "barcode scanner", "pdf viewer", "charts"

3. **Platform Integration**: Find packages for platform-specific features
   - "firebase", "google maps", "notifications", "biometric"

## Error Handling

All tools implement consistent error handling:

### Common Error Scenarios

1. **Network Errors**
```json
{
  "error": "Failed to fetch documentation: Network timeout"
}
```

2. **Not Found Errors**
```json
{
  "error": "Documentation not found for 'InvalidQuery'. Please check the spelling and try again."
}
```

3. **Rate Limit Errors**
```json
{
  "error": "Rate limit exceeded. Please wait before making another request."
}
```

4. **Invalid Parameters**
```json
{
  "error": "Invalid parameter: max_results must be between 1 and 30"
}
```

## Best Practices

### 1. Efficient Querying
- Use specific class/method names for `get_flutter_docs`
- Use exact package names for `get_pub_package_docs`
- Use descriptive keywords for `search_pub_packages`

### 2. Cache Utilization
- Repeated requests for the same documentation will be served from cache
- Cache TTLs ensure documentation stays relatively fresh
- No need to manually refresh unless you suspect documentation has just been updated

### 3. Error Recovery
- If a query fails, check spelling and formatting
- For Flutter/Dart docs, try both class name and full method signature
- For packages, ensure the exact package name from pub.dev

### 4. Rate Limit Compliance
- The server automatically queues requests to respect rate limits
- Avoid making rapid successive requests for different items
- Batch related queries when possible

## Integration Examples

### Example 1: Getting Widget Documentation
```python
# User prompt: "@flutter_mcp Show me how to use Container widget"

# MCP tool call
{
  "tool": "get_flutter_docs",
  "parameters": {
    "query": "Container"
  }
}

# Returns comprehensive Container documentation with examples
```

### Example 2: Finding and Learning About Packages
```python
# User prompt: "@flutter_mcp I need a good HTTP client package"

# First, search for packages
{
  "tool": "search_pub_packages",
  "parameters": {
    "query": "http client",
    "max_results": 5
  }
}

# Then get detailed docs for a specific package
{
  "tool": "get_pub_package_docs",
  "parameters": {
    "package_name": "dio"
  }
}
```

### Example 3: Learning Flutter Concepts
```python
# User prompt: "@flutter_mcp Explain setState and state management"

# Get setState documentation
{
  "tool": "get_flutter_docs",
  "parameters": {
    "query": "setState"
  }
}

# Search for state management packages
{
  "tool": "search_pub_packages",
  "parameters": {
    "query": "state management"
  }
}
```

## Troubleshooting

### Documentation Not Found
- Verify the exact class/method name from Flutter documentation
- Try variations (e.g., "setState" vs "State.setState")
- Check if it's a Dart core library element (e.g., "Future" instead of "flutter.Future")

### Package Not Found
- Ensure exact package name as it appears on pub.dev
- Use search_pub_packages first to find the correct name
- Package names are case-sensitive

### Slow Responses
- First request for documentation may take longer (not cached)
- Subsequent requests should be faster (served from cache)
- Check Redis connection if consistently slow

### Incomplete Documentation
- Some newer APIs may have limited documentation
- Third-party package docs depend on package author's README
- Consider checking the source repository for more details

## Version Information

- **API Version**: 1.0.0
- **Supported Flutter Docs**: Latest stable version
- **Supported Dart Docs**: Latest stable version
- **Pub.dev API**: v2

## Support

For issues, feature requests, or contributions:
- GitHub: [flutter-docs-mcp](https://github.com/yourusername/flutter-docs-mcp)
- Issues: Report bugs or request features via GitHub Issues
- PRs: Contributions welcome following the project guidelines