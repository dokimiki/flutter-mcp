# Version Specification System

The Flutter MCP server now supports advanced version specifications for pub.dev packages, allowing AI assistants to fetch documentation for specific package versions based on various constraint formats.

## Overview

When referencing packages with `@flutter_mcp`, you can now specify version constraints similar to how they work in `pubspec.yaml` files. This ensures AI assistants get documentation that matches the exact version requirements of a project.

## Supported Formats

### 1. Exact Versions

Specify an exact version to fetch documentation for that specific release:

```
@flutter_mcp riverpod:2.5.1
@flutter_mcp provider:6.0.5
@flutter_mcp dio:5.3.2
```

### 2. Caret Syntax (^)

The caret syntax allows compatible updates according to semantic versioning:

```
@flutter_mcp provider:^6.0.0    # Allows >=6.0.0 <7.0.0
@flutter_mcp bloc:^8.1.0        # Allows >=8.1.0 <9.0.0
@flutter_mcp get:^4.6.5         # Allows >=4.6.5 <5.0.0
```

For packages with 0.x.x versions, the caret is more restrictive:
- `^0.2.3` allows `>=0.2.3 <0.3.0`
- `^0.0.3` allows `>=0.0.3 <0.0.4`

### 3. Version Ranges

Specify explicit version ranges using comparison operators:

```
@flutter_mcp dio:>=5.0.0 <6.0.0    # Any 5.x version
@flutter_mcp http:>0.13.0 <=1.0.0  # Greater than 0.13.0, up to and including 1.0.0
@flutter_mcp provider:>=6.0.0       # 6.0.0 or higher
@flutter_mcp bloc:<9.0.0            # Any version below 9.0.0
```

### 4. Special Keywords

Use keywords to fetch specific version types:

```
@flutter_mcp provider:latest   # Absolute latest version (including pre-releases)
@flutter_mcp riverpod:stable   # Latest stable version (no pre-releases)
@flutter_mcp bloc:dev          # Latest dev version
@flutter_mcp get:beta          # Latest beta version
@flutter_mcp dio:alpha         # Latest alpha version
```

### 5. No Version (Current Behavior)

When no version is specified, the system fetches the latest stable version:

```
@flutter_mcp provider          # Latest stable version
@flutter_mcp riverpod          # Latest stable version
```

## Examples in Context

### Example 1: Upgrading Dependencies

```
I'm upgrading from @flutter_mcp provider:^5.0.0 to @flutter_mcp provider:^6.0.0.
What are the breaking changes I need to be aware of?
```

### Example 2: Testing Pre-release Features

```
I want to try the new features in @flutter_mcp riverpod:beta.
Can you show me what's new compared to @flutter_mcp riverpod:stable?
```

### Example 3: Version Compatibility

```
My project uses @flutter_mcp dio:>=5.0.0 <6.0.0 for networking.
Is this compatible with @flutter_mcp retrofit:^4.0.0?
```

### Example 4: Legacy Code

```
I'm maintaining legacy code that uses @flutter_mcp provider:5.0.0.
Can you help me understand the API from that specific version?
```

## How It Works

### Version Resolution

1. **Parsing**: The system parses the version specification to understand the constraint type
2. **Resolution**: For constraints (not exact versions), the system queries pub.dev to find all available versions
3. **Selection**: The highest version that satisfies the constraint is selected
4. **Fetching**: Documentation for the selected version is retrieved and cached

### Caching

Version-specific documentation is cached separately:
- Cache key includes the package name and resolved version
- Different version constraints that resolve to the same version share the cache
- Cache duration: 12 hours for package documentation

### Error Handling

The system provides helpful error messages:
- If a version doesn't exist: Lists available versions
- If constraint can't be resolved: Explains why
- If package doesn't exist: Standard package not found error

## Implementation Details

### Version Parser

The `VersionParser` class handles parsing of version specifications:
- Regex patterns for different constraint formats
- Semantic version comparison logic
- Support for pre-release versions

### Version Resolver

The `VersionResolver` class interfaces with pub.dev API:
- Fetches available versions from pub.dev
- Applies constraint logic to find best match
- Handles special keywords (latest, stable, etc.)

### Integration

The version system is fully integrated with:
- `process_flutter_mentions`: Parses mentions with version specs
- `get_pub_package_info`: Fetches version-specific documentation
- Cache system: Version-aware cache keys

## Best Practices

1. **Use Caret for Flexibility**: `^` allows compatible updates
   ```
   @flutter_mcp provider:^6.0.0
   ```

2. **Exact Versions for Reproducibility**: When you need specific behavior
   ```
   @flutter_mcp riverpod:2.5.1
   ```

3. **Ranges for Compatibility**: When working with multiple packages
   ```
   @flutter_mcp dio:>=5.0.0 <6.0.0
   ```

4. **Keywords for Exploration**: Testing new features
   ```
   @flutter_mcp bloc:beta
   ```

## Limitations

1. **Flutter/Dart Classes**: Version specifications only work with pub.dev packages, not Flutter framework classes
   - ✅ `@flutter_mcp provider:^6.0.0`
   - ❌ `@flutter_mcp material.AppBar:^3.0.0`

2. **Version Availability**: Only versions published on pub.dev are accessible

3. **Rate Limiting**: Version resolution requires additional API calls, subject to rate limits

## Future Enhancements

Potential future improvements:
1. Flutter SDK version-specific documentation
2. Git commit/branch references for packages
3. Local path references for development
4. Version comparison tools
5. Migration guide generation between versions