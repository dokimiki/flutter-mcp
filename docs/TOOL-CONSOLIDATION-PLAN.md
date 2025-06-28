# Tool Consolidation Implementation Plan

## Overview

This document outlines the plan to consolidate Flutter MCP's 5 tools into 2-3 simplified tools, following Context7's successful pattern. This will make the server easier to use for AI assistants while maintaining all functionality.

## Goals

1. **Simplify from 5 tools to 2-3 tools**
2. **Match Context7's UX patterns**
3. **Add token limiting (10,000 default)**
4. **Maintain backwards compatibility**
5. **Improve discoverability**

## Current State (5 Tools)

```python
1. get_flutter_docs(class_name, library, max_tokens)
2. search_flutter_docs(query)
3. get_pub_package_info(package_name)
4. process_flutter_mentions(text)
5. health_check()
```

## Target State (2 Primary Tools + 1 Optional)

```python
1. flutter_search(query, limit=10)
2. flutter_docs(identifier, topic=None, max_tokens=10000)
3. flutter_status() [optional]
```

## Implementation Timeline

### Phase 1: Core Implementation (Current)

- [x] Create unified `flutter_search` tool
- [x] Create unified `flutter_docs` tool  
- [x] Add backwards compatibility layer
- [ ] Update tests
- [ ] Fix duplicate implementations
- [ ] Handle process_flutter_mentions

### Phase 2: Polish & Documentation

- [ ] Update README and examples
- [ ] Add deprecation warnings
- [ ] Update npm wrapper
- [ ] Create migration guide

### Phase 3: Cleanup (Future)

- [ ] Remove deprecated tools
- [ ] Optimize performance
- [ ] Add natural language activation

## Tool Specifications

### 1. flutter_search

**Purpose**: Universal search across Flutter/Dart ecosystem

**Input**:
```python
query: str          # Natural language or identifier
limit: int = 10     # Max results to return
```

**Output**:
```json
{
    "query": "state management",
    "results": [
        {
            "id": "pub:provider",
            "type": "package",
            "title": "provider",
            "description": "State management library",
            "relevance": 0.95,
            "doc_size": "large"
        },
        {
            "id": "flutter:widgets.StatefulWidget",
            "type": "class",
            "title": "StatefulWidget",
            "description": "Widget with mutable state",
            "relevance": 0.87,
            "doc_size": "medium"
        }
    ],
    "metadata": {
        "total_results": 25,
        "search_time_ms": 145
    }
}
```

### 2. flutter_docs

**Purpose**: Fetch documentation with smart resolution and filtering

**Input**:
```python
identifier: str             # "Container", "pub:dio", "dart:async.Future"
topic: Optional[str]        # "examples", "constructors", "getting-started"
max_tokens: int = 10000     # Token limit for response
```

**Output**:
```json
{
    "identifier": "provider",
    "type": "package",
    "content": "# provider\n\n...",
    "metadata": {
        "source": "live",
        "tokens": 8234,
        "truncated": false,
        "version": "6.1.2"
    }
}
```

### 3. flutter_status

**Purpose**: Health check and cache statistics

**Output**:
```json
{
    "status": "healthy",
    "cache": {
        "entries": 42,
        "size_mb": 12.3,
        "hit_rate": 0.87
    },
    "scrapers": {
        "flutter_docs": "operational",
        "pub_dev": "operational"
    }
}
```

## Implementation Details

### Identifier Resolution

```python
# Unified identifier format:
"Container"                  # Flutter widget (auto-detect)
"material.AppBar"           # Library-qualified
"pub:provider"              # Explicit package
"dart:async.Future"         # Dart core library
"provider"                  # Auto-detect as package
```

### Topic Filtering

```python
# Class topics:
"constructors", "properties", "methods", "examples", "summary"

# Package topics:
"getting-started", "examples", "api", "changelog", "installation"
```

### Smart Truncation

- Default: 10,000 tokens
- Preserves section structure
- Prioritizes important content
- Indicates truncation in response

## Backwards Compatibility

Existing tools will be maintained but marked as deprecated:

```python
@mcp.tool()
async def get_flutter_docs(class_name, library="widgets", max_tokens=None):
    """[Deprecated] Use flutter_docs instead."""
    # Internally calls flutter_docs
```

## Migration Guide for Users

### Before:
```python
# Searching
results = await search_flutter_docs("state management")

# Getting docs
doc = await get_flutter_docs("Container", "widgets")
```

### After:
```python
# Searching
results = await flutter_search("state management")

# Getting docs
doc = await flutter_docs("Container")
doc = await flutter_docs("widgets.Container", topic="examples")
```

## Success Metrics

1. **Reduced complexity**: 5 tools → 2 tools (60% reduction)
2. **Improved discoverability**: Natural language queries
3. **Better token management**: Default limits prevent overflow
4. **Backwards compatible**: No breaking changes

## Status Updates

### 2025-06-27 - Started Implementation
- Created implementation plan
- Beginning tool development

### 2025-06-28 - Implementation Progress

#### What's Been Implemented

1. **New Unified Tools Created**:
   - ✅ `flutter_docs()` - Unified documentation fetching tool (lines 571-683 and 1460+)
   - ✅ `flutter_search()` - Enhanced search tool (lines 802-836 and 2342+) 
   - ✅ `flutter_status()` - Health check tool (line 2773+)

2. **Backwards Compatibility Layer**:
   - ✅ Deprecated tools now call new implementations internally
   - ✅ `get_flutter_docs()` wrapper implemented (lines 686-727)
   - ✅ `search_flutter_docs()` wrapper implemented (lines 840-869)
   - ✅ Deprecation warnings added via logger

3. **Helper Functions Added**:
   - ✅ `resolve_identifier()` - Smart identifier type detection (lines 100-150)
   - ✅ `filter_by_topic()` - Topic-based content filtering (lines 153-236)
   - ✅ `to_unified_id()` - Convert to unified ID format (lines 239-265)
   - ✅ `from_unified_id()` - Parse unified ID format (lines 267-296)
   - ✅ `estimate_doc_size()` - Document size estimation (lines 298-320)
   - ✅ `rank_results()` - Result relevance ranking (lines 322-370)

#### Current Issues Found

1. **Duplicate Implementations**:
   - ⚠️ `flutter_docs()` defined twice (lines 571 and 1460)
   - ⚠️ `flutter_search()` defined twice (lines 802 and 2342)
   - Need to remove duplicate definitions and consolidate

2. **Missing Implementations**:
   - ❌ `process_flutter_mentions()` not yet integrated into new tools
   - ❌ Topic filtering not fully integrated into `flutter_docs()`
   - ❌ Version-specific queries not fully implemented

3. **Test Coverage**:
   - ❌ Tests still use old tool names (test_tools.py)
   - ❌ No tests for new unified tools yet
   - ❌ No migration examples in tests

#### Examples of New Tool Usage

##### 1. flutter_docs - Unified Documentation

```python
# Old way (deprecated)
doc = await get_flutter_docs("Container", "widgets")

# New way - auto-detection
doc = await flutter_docs("Container")

# New way - with library
doc = await flutter_docs("material.AppBar")

# New way - Dart core library
doc = await flutter_docs("dart:async.Future")

# New way - Pub package
doc = await flutter_docs("pub:provider")

# New way - with topic filtering (when implemented)
doc = await flutter_docs("Container", topic="constructors")
doc = await flutter_docs("pub:dio", topic="examples")
```

##### 2. flutter_search - Enhanced Search

```python
# Old way (deprecated)
results = await search_flutter_docs("state management")

# New way - basic search
results = await flutter_search("state management")

# New way - with limit
results = await flutter_search("navigation", limit=5)

# New way - with type filtering (when implemented)
results = await flutter_search("http", types=["package"])
results = await flutter_search("widget", types=["flutter", "dart"])
```

##### 3. flutter_status - Health Check

```python
# New tool (no old equivalent)
status = await flutter_status()
# Returns:
# {
#   "status": "healthy",
#   "cache": {
#     "entries": 42,
#     "size_mb": 12.3,
#     "hit_rate": 0.87
#   },
#   "scrapers": {
#     "flutter_docs": "operational",
#     "pub_dev": "operational"
#   }
# }
```

#### Migration Examples for Users

##### Basic Migration

```python
# Before: Multiple tools with different interfaces
doc1 = await get_flutter_docs("Container", "widgets")
doc2 = await get_pub_package_info("provider")
search = await search_flutter_docs("navigation")

# After: Unified interface
doc1 = await flutter_docs("Container")
doc2 = await flutter_docs("pub:provider")
search = await flutter_search("navigation")
```

##### Advanced Migration

```python
# Before: Manual library specification
material_doc = await get_flutter_docs("AppBar", "material")
dart_doc = await get_flutter_docs("Future", "dart:async")  # Didn't work well

# After: Smart resolution
material_doc = await flutter_docs("material.AppBar")
dart_doc = await flutter_docs("dart:async.Future")

# Before: Limited search
results = await search_flutter_docs("state")  # Only 5-10 results

# After: Configurable search
results = await flutter_search("state", limit=20)
# Future: Type filtering
results = await flutter_search("state", types=["package", "concept"])
```

#### Challenges and Decisions Made

1. **Identifier Resolution**:
   - Decision: Use prefixes for explicit types (`pub:`, `dart:`)
   - Challenge: Auto-detecting Flutter vs Dart classes
   - Solution: Common widget list + library patterns

2. **Backwards Compatibility**:
   - Decision: Keep old tools as wrappers
   - Challenge: Transforming response formats
   - Solution: Internal `_impl` functions + format converters

3. **Topic Filtering**:
   - Decision: Optional `topic` parameter
   - Challenge: Different topics for classes vs packages
   - Solution: Type-aware topic extraction

4. **Duplicate Code**:
   - Issue: Functions defined multiple times
   - Cause: Possibly from incremental development
   - Action Needed: Clean up and consolidate

#### Next Steps

1. **Immediate Actions**:
   - Remove duplicate function definitions
   - Implement topic filtering in `flutter_docs()`
   - Update tests to use new tools
   - Fix `process_flutter_mentions` integration

2. **Documentation Updates**:
   - Update README with new tool examples
   - Create migration guide
   - Update npm wrapper documentation

3. **Future Enhancements**:
   - Natural language activation patterns
   - Version-specific documentation
   - Cookbook recipe integration
   - Stack Overflow integration

### 2025-06-28 - Implementation Complete! 🎉

#### Final Status:

1. **All Duplicate Implementations Fixed**:
   - Removed duplicate `flutter_docs` (kept the more complete one)
   - Removed duplicate `flutter_search` (kept the one with parallel search)
   - Cleaned up code structure

2. **Tool Consolidation Complete**:
   - **2 Primary Tools**: `flutter_search` and `flutter_docs`
   - **1 Optional Tool**: `flutter_status`
   - **All 5 original tools** maintained with deprecation notices
   - `process_flutter_mentions` updated to use new tools internally

3. **Key Features Implemented**:
   - ✅ Smart identifier resolution (auto-detects type)
   - ✅ Topic filtering for focused documentation
   - ✅ Token limiting with default 10,000
   - ✅ Parallel search across multiple sources
   - ✅ Unified ID format (flutter:, dart:, pub:, concept:)
   - ✅ Backwards compatibility maintained

4. **Next Steps**:
   - Update tests for new tool signatures
   - Update main README with examples
   - Monitor usage and gather feedback
   - Consider removing deprecated tools in v2.0

---

*Implementation completed on 2025-06-28. This document serves as the record of the tool consolidation effort.*