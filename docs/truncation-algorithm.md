# Smart Truncation Algorithm for Flutter/Dart Documentation

## Overview

The smart truncation algorithm is designed to intelligently reduce Flutter and Dart documentation to fit within token limits while preserving the most critical information for developers. This algorithm uses a priority-based system to ensure that essential information is retained even under severe token constraints.

## Key Features

### 1. Priority-Based Content Classification

The algorithm classifies documentation content into five priority levels:

- **CRITICAL (1)**: Must always be retained
  - Class descriptions
  - Constructor signatures
  
- **HIGH (2)**: Retained whenever possible
  - Primary method signatures (build, createState, initState, dispose)
  - Common properties (child, children, padding, margin, etc.)
  - Constructor descriptions

- **MEDIUM (3)**: Retained if space allows
  - Secondary methods
  - Less common properties
  - First 2 code examples
  
- **LOW (4)**: First to be removed
  - Private methods
  - Verbose method descriptions
  - Additional code examples (3+)
  
- **MINIMAL (5)**: Removed first
  - Inherited members
  - See also sections
  - Related classes

### 2. Intelligent Section Parsing

The algorithm parses Flutter documentation into semantic sections:

```python
sections = [
    "description",      # Class overview
    "constructors",     # Constructor signatures and docs
    "properties",       # Widget properties
    "methods",          # Class methods
    "examples"          # Code examples
]
```

Each section is further broken down into sub-components with individual priorities.

### 3. Flutter-Aware Prioritization

The algorithm has built-in knowledge of Flutter's widget hierarchy and common patterns:

#### High-Priority Widgets
```python
HIGH_PRIORITY_WIDGETS = {
    "Container", "Row", "Column", "Text", "Image", "Scaffold",
    "AppBar", "ListView", "GridView", "Stack", "Positioned",
    "Center", "Padding", "SizedBox", "Expanded", "Flexible",
    # ... and more
}
```

#### High-Priority Methods
```python
HIGH_PRIORITY_METHODS = {
    "build", "createState", "initState", "dispose", "setState",
    "didChangeDependencies", "didUpdateWidget", "deactivate"
}
```

#### High-Priority Properties
```python
HIGH_PRIORITY_PROPERTIES = {
    "child", "children", "width", "height", "color", "padding",
    "margin", "alignment", "decoration", "style", "onPressed",
    "onTap", "controller", "value", "enabled", "visible"
}
```

### 4. Truncation Strategies

The algorithm supports multiple truncation strategies:

#### Balanced (Default)
Maintains a good mix of all documentation types:
- Keeps description, main constructors, key properties, and primary methods
- Includes 1-2 code examples if space allows
- Best for general-purpose documentation

#### Signatures
Prioritizes method and constructor signatures:
- Maximizes retention of code signatures
- Reduces or removes descriptions
- Ideal when the user needs API reference information

#### Examples
Prioritizes code examples:
- Keeps more code examples than other strategies
- Useful for learning and implementation guidance

#### Minimal
Keeps only the most essential information:
- Class description
- Primary constructor
- build() method for widgets
- child/children properties

### 5. Smart Code Truncation

When truncating code blocks, the algorithm:
- Preserves syntactic validity when possible
- Balances braces and brackets
- Truncates at line boundaries
- Adds ellipsis comments to indicate truncation

Example:
```dart
Container(
  width: 200,
  height: 200,
  child: Column(
    children: [
      Text('Line 1'),
      // ...
    ],
  ),
)
```

### 6. Progressive Truncation

The algorithm applies truncation progressively:

1. Calculate total token count
2. If under limit, return unchanged
3. Remove MINIMAL priority content
4. Remove LOW priority content
5. Reduce MEDIUM priority content
6. Trim HIGH priority content (descriptions only)
7. CRITICAL content is never removed

## Usage Examples

### Basic Usage

```python
from flutter_mcp.truncation import truncate_flutter_docs

# Truncate to 4000 tokens with balanced strategy
truncated_doc = truncate_flutter_docs(
    content=original_documentation,
    class_name="Container",
    max_tokens=4000,
    strategy="balanced"
)
```

### Advanced Usage with Metadata

```python
from flutter_mcp.truncation import AdaptiveTruncator

truncator = AdaptiveTruncator(max_tokens=2000)
truncated_doc, metadata = truncator.truncate_with_strategy(
    doc_content=original_documentation,
    class_name="ListView",
    library="widgets",
    strategy="signatures"
)

print(f"Compression ratio: {metadata['compression_ratio']:.1%}")
print(f"Was truncated: {metadata['was_truncated']}")
```

### Integration with MCP Server

```python
# In the MCP tool
@mcp.tool()
async def get_flutter_docs(
    class_name: str, 
    library: str = "widgets",
    max_tokens: int = None  # Optional truncation
) -> Dict[str, Any]:
    # Fetch documentation...
    
    # Apply smart truncation if requested
    if max_tokens:
        content = truncate_flutter_docs(
            content,
            class_name,
            max_tokens=max_tokens,
            strategy="balanced"
        )
```

## Token Limits and Recommendations

| Use Case | Recommended Token Limit | Strategy |
|----------|------------------------|----------|
| Quick reference | 500-1000 | minimal |
| API overview | 2000-4000 | signatures |
| Learning/Tutorial | 4000-8000 | examples |
| Full documentation | 8000+ | balanced |

## Implementation Details

### Token Estimation

The algorithm uses a simple but effective token estimation:
- English text: ~4 characters per token
- Code: ~3 characters per token

This provides a good approximation for planning truncation without requiring actual tokenization.

### Section Preservation

When a section must be truncated:
1. Code sections are truncated at line boundaries
2. Text sections are truncated at sentence boundaries
3. Lists are truncated at item boundaries
4. A truncation notice is always added

### Example Output

Original documentation: 15,000 characters (~3,750 tokens)
Truncated to 1,000 tokens:

```markdown
# Container (Truncated Documentation)

## Description
A convenience widget that combines common painting, positioning, and sizing widgets.

## Constructors
### Container({Key? key, AlignmentGeometry? alignment, ...})
```dart
Container({
  Key? key,
  this.alignment,
  this.padding,
  this.color,
  this.decoration,
  double? width,
  double? height,
  this.child,
})
```

## Properties
- **child**: The child contained by the container
- **padding**: Empty space to inscribe inside the decoration
- **color**: The color to paint behind the child
- **width**: Container width constraint
- **height**: Container height constraint

## Methods
### build(BuildContext context)
```dart
@override
Widget build(BuildContext context) {
  // ... (truncated)
}
```

---
*Note: This documentation has been intelligently truncated to fit within token limits. Some sections may have been removed or shortened.*
```

## Performance Considerations

The truncation algorithm is designed to be efficient:
- O(n) parsing of documentation
- O(n log n) sorting of sections by priority
- O(n) reconstruction of truncated documentation

Typical truncation takes <50ms for large documents.

## Future Enhancements

Potential improvements to the algorithm:

1. **ML-based importance scoring**: Use machine learning to determine section importance based on usage patterns
2. **Context-aware truncation**: Adjust priorities based on the user's query context
3. **Cross-reference preservation**: Maintain links between related classes when truncating
4. **Incremental loading**: Support progressive disclosure of truncated content
5. **Custom priority profiles**: Allow users to define their own priority preferences

## Conclusion

The smart truncation algorithm ensures that Flutter/Dart documentation remains useful even under severe token constraints. By understanding the structure and importance of different documentation sections, it preserves the most critical information while gracefully degrading less essential content.