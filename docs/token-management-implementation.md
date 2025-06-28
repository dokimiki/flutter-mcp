# Token Management Implementation Plan

## Overview

This document outlines the implementation of token management for Flutter MCP, inspired by Context7's simple approach but adapted for our client-side architecture.

## Goals

1. **Simple API**: Add optional `tokens` parameter to all documentation tools
2. **Smart Truncation**: Preserve most important content when limits are reached
3. **Performance**: Fast token counting without impacting response times
4. **Transparency**: Clear indication when content is truncated
5. **Context7-like UX**: Sensible defaults, no required parameters

## Implementation Phases

### Phase 1: Basic Token Management (Status: In Progress)
- [ ] Add `tokens` parameter to all documentation tools
- [ ] Implement basic token counting (word-based approximation)
- [ ] Simple truncation at section boundaries
- [ ] Update response format with token metadata

### Phase 2: Smart Truncation (Status: Pending)
- [ ] Create priority-based content classification
- [ ] Implement Flutter-aware section detection
- [ ] Add intelligent truncation algorithm
- [ ] Preserve markdown formatting during truncation

### Phase 3: Cache Integration (Status: Pending)
- [ ] Update cache schema to store token counts
- [ ] Modify cache read/write operations
- [ ] Ensure backward compatibility with existing cache

### Phase 4: Testing & Documentation (Status: Pending)
- [ ] Unit tests for token counting
- [ ] Integration tests for truncation
- [ ] Update API documentation
- [ ] Add usage examples

## Technical Design

### Token Counting Strategy

**Approximation Method** (Default):
```python
def approximate_tokens(text: str) -> int:
    """Fast token approximation: ~1.3 tokens per word"""
    return int(len(text.split()) * 1.3)
```

**Accurate Counting** (Optional):
- Use tiktoken for GPT models
- Lazy-loaded to avoid startup overhead
- Configurable via environment variable

### Default Token Limits

| Tool | Default | Minimum | Rationale |
|------|---------|---------|-----------|
| get_flutter_docs | 8,000 | 1,000 | Single class documentation |
| search_flutter_docs | 5,000 | 1,000 | Multiple search results |
| get_pub_package_info | 6,000 | 1,000 | Package info + README |
| process_flutter_mentions | 4,000 | 500 | Per mention |

### Truncation Priority

1. **CRITICAL**: Class description, constructor signatures
2. **HIGH**: Common methods (build, setState), essential properties
3. **MEDIUM**: Secondary methods, code examples
4. **LOW**: Inherited members, see also sections
5. **MINIMAL**: Related classes, external links

### Response Format

```json
{
  "content": "# Widget Name\n...",
  "source": "live|cache",
  "truncated": true,
  "token_count": 2000,
  "original_tokens": 5234,
  "sections_included": ["description", "constructors"],
  "sections_truncated": ["methods", "examples"],
  "truncation_note": "Documentation limited to 2000 tokens."
}
```

## Implementation Progress

### ✅ Completed
- Created implementation plan document
- Added `tokens` parameter to all documentation tools
- Implemented `TokenManager` class with approximation and accurate counting
- Created `DocumentTruncator` class with section detection
- Updated tool signatures with validation
- Integrated token management into server processing pipeline
- Updated cache to store and retrieve token counts
- Added schema migration for existing cache databases
- Updated response format to include token metadata
- Created comprehensive test suite
- Added usage examples and demo script

### 🎉 All phases complete!

## Implementation Summary

### What Was Built

1. **TokenManager** (`src/flutter_mcp/token_manager.py`)
   - Fast word-based approximation (default)
   - Optional accurate counting with tiktoken
   - Environment variable configuration
   - ~1.3 tokens per word ratio

2. **DocumentTruncator** (`src/flutter_mcp/truncation.py`)
   - Smart section detection for Flutter docs
   - Priority-based content preservation
   - Maintains markdown formatting
   - Graceful degradation for edge cases

3. **Server Integration**
   - All tools now accept optional `tokens` parameter
   - Automatic truncation when limits exceeded
   - Token metadata in all responses
   - Transparent to existing users (backward compatible)

4. **Cache Enhancement**
   - Stores token counts with content
   - Avoids re-counting for cached docs
   - Schema migration for existing databases
   - Statistics tracking for cached tokens

5. **Testing & Documentation**
   - Comprehensive test suite
   - Interactive demo script
   - Usage examples

### Key Features

- **Simple like Context7**: Optional parameter, sensible defaults
- **Fast**: Approximation takes <1ms for typical docs
- **Smart**: Preserves most important content when truncating
- **Transparent**: Users see token counts and truncation status
- **Cached**: Token counts stored to avoid recalculation

### Usage

```python
# Default usage - no change needed
docs = await get_flutter_docs("Container")

# With token limit
docs = await get_flutter_docs("Container", tokens=2000)

# Response includes token info
{
  "content": "...",
  "token_count": 1998,
  "truncated": true,
  "truncation_note": "Documentation limited to 2000 tokens."
}
```

## Notes

- Using word-based approximation for performance (1.3 tokens/word)
- Optional tiktoken integration for accuracy
- Cache stores both content and token count
- Backward compatible with existing cache entries