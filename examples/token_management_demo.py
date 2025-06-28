#!/usr/bin/env python3
"""
Token Management Demo for Flutter MCP

This example demonstrates how token management works in Flutter MCP,
showing both approximation and truncation features.
"""

import asyncio
import json
from flutter_mcp.token_manager import TokenManager, count_tokens, get_mode
from flutter_mcp.truncation import DocumentTruncator


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


async def demo_token_counting():
    """Demonstrate token counting functionality."""
    print_section("Token Counting Demo")
    
    # Sample Flutter documentation
    sample_doc = """# Container

A convenience widget that combines common painting, positioning, and sizing widgets.

## Description

A container first surrounds the child with padding (inflated by any borders present in the decoration) and then applies additional constraints to the padded extent (incorporating the width and height as constraints, if either is non-null). The container is then surrounded by additional empty space described from the margin.

## Constructors

### Container({Key? key, AlignmentGeometry? alignment, EdgeInsetsGeometry? padding, Color? color, Decoration? decoration, Decoration? foregroundDecoration, double? width, double? height, BoxConstraints? constraints, EdgeInsetsGeometry? margin, Matrix4? transform, AlignmentGeometry? transformAlignment, Widget? child, Clip clipBehavior = Clip.none})

Creates a widget that combines common painting, positioning, and sizing widgets.

## Properties

- alignment → AlignmentGeometry?
  Align the child within the container.
  
- child → Widget?
  The child contained by the container.
  
- clipBehavior → Clip
  The clip behavior when Container.decoration is not null.
  
- color → Color?
  The color to paint behind the child.
  
- constraints → BoxConstraints?
  Additional constraints to apply to the child.

## Methods

- build(BuildContext context) → Widget
  Describes the part of the user interface represented by this widget.
  
- createElement() → StatelessElement
  Creates a StatelessElement to manage this widget's location in the tree.
  
- debugDescribeChildren() → List<DiagnosticsNode>
  Returns a list of DiagnosticsNode objects describing this node's children.

## Examples

```dart
Container(
  width: 200,
  height: 200,
  color: Colors.blue,
  child: Center(
    child: Text('Hello Flutter!'),
  ),
)
```

## See Also

- Padding, which adds padding to a child widget.
- DecoratedBox, which applies a decoration to a child widget.
- Transform, which applies a transformation to a child widget.
"""
    
    # Count tokens using approximation
    print(f"\nCurrent mode: {get_mode()}")
    approx_tokens = count_tokens(sample_doc)
    print(f"Approximate token count: {approx_tokens}")
    print(f"Character count: {len(sample_doc)}")
    print(f"Word count: {len(sample_doc.split())}")
    print(f"Ratio (tokens/words): {approx_tokens / len(sample_doc.split()):.2f}")


async def demo_truncation():
    """Demonstrate document truncation."""
    print_section("Document Truncation Demo")
    
    # Create a longer document
    long_doc = """# ListView

A scrollable list of widgets arranged linearly.

## Description

ListView is the most commonly used scrolling widget. It displays its children one after another in the scroll direction. In the cross axis, the children are required to fill the ListView.

If non-null, the itemExtent forces the children to have the given extent in the scroll direction. If non-null, the prototypeItem forces the children to have the same extent as the given widget in the scroll direction.

Specifying an itemExtent or an prototypeItem is more efficient than letting the children determine their own extent because the scrolling machinery can make use of the foreknowledge of the children's extent to save work, for example when the scroll position changes drastically.

## Constructors

### ListView({Key? key, Axis scrollDirection = Axis.vertical, bool reverse = false, ScrollController? controller, bool? primary, ScrollPhysics? physics, bool shrinkWrap = false, EdgeInsetsGeometry? padding, double? itemExtent, Widget? prototypeItem, bool addAutomaticKeepAlives = true, bool addRepaintBoundaries = true, bool addSemanticIndexes = true, double? cacheExtent, List<Widget> children = const <Widget>[], int? semanticChildCount, DragStartBehavior dragStartBehavior = DragStartBehavior.start, ScrollViewKeyboardDismissBehavior keyboardDismissBehavior = ScrollViewKeyboardDismissBehavior.manual, String? restorationId, Clip clipBehavior = Clip.hardEdge})

Creates a scrollable, linear array of widgets from an explicit List.

### ListView.builder({Key? key, Axis scrollDirection = Axis.vertical, bool reverse = false, ScrollController? controller, bool? primary, ScrollPhysics? physics, bool shrinkWrap = false, EdgeInsetsGeometry? padding, double? itemExtent, Widget? prototypeItem, required NullableIndexedWidgetBuilder itemBuilder, ChildIndexGetter? findChildIndexCallback, int? itemCount, bool addAutomaticKeepAlives = true, bool addRepaintBoundaries = true, bool addSemanticIndexes = true, double? cacheExtent, int? semanticChildCount, DragStartBehavior dragStartBehavior = DragStartBehavior.start, ScrollViewKeyboardDismissBehavior keyboardDismissBehavior = ScrollViewKeyboardDismissBehavior.manual, String? restorationId, Clip clipBehavior = Clip.hardEdge})

Creates a scrollable, linear array of widgets that are created on demand.

### ListView.separated({Key? key, Axis scrollDirection = Axis.vertical, bool reverse = false, ScrollController? controller, bool? primary, ScrollPhysics? physics, bool shrinkWrap = false, EdgeInsetsGeometry? padding, required NullableIndexedWidgetBuilder itemBuilder, ChildIndexGetter? findChildIndexCallback, required IndexedWidgetBuilder separatorBuilder, required int itemCount, bool addAutomaticKeepAlives = true, bool addRepaintBoundaries = true, bool addSemanticIndexes = true, double? cacheExtent, DragStartBehavior dragStartBehavior = DragStartBehavior.start, ScrollViewKeyboardDismissBehavior keyboardDismissBehavior = ScrollViewKeyboardDismissBehavior.manual, String? restorationId, Clip clipBehavior = Clip.hardEdge})

Creates a scrollable, linear array of widgets with a custom separator.

## Properties

### Essential Properties

- children → List<Widget>
  The widgets to display in the list.
  
- controller → ScrollController?
  An object that can be used to control the position to which this scroll view is scrolled.
  
- itemBuilder → NullableIndexedWidgetBuilder
  Called to build children for the list with a builder.
  
- itemCount → int?
  The number of items to build when using ListView.builder.
  
- scrollDirection → Axis
  The axis along which the scroll view scrolls.

### Performance Properties

- cacheExtent → double?
  The viewport has an area before and after the visible area to cache items that are about to become visible when the user scrolls.
  
- itemExtent → double?
  If non-null, forces the children to have the given extent in the scroll direction.
  
- prototypeItem → Widget?
  If non-null, forces the children to have the same extent as the given widget in the scroll direction.
  
- shrinkWrap → bool
  Whether the extent of the scroll view in the scrollDirection should be determined by the contents being viewed.

### Behavior Properties

- physics → ScrollPhysics?
  How the scroll view should respond to user input.
  
- primary → bool?
  Whether this is the primary scroll view associated with the parent PrimaryScrollController.
  
- reverse → bool
  Whether the scroll view scrolls in the reading direction.

## Methods

### Core Methods

- build(BuildContext context) → Widget
  Describes the part of the user interface represented by this widget.
  
- buildChildLayout(BuildContext context) → Widget
  Subclasses should override this method to build the layout model.
  
- buildSlivers(BuildContext context) → List<Widget>
  Build the list of widgets to place inside the viewport.
  
- buildViewport(BuildContext context, ViewportOffset offset, AxisDirection axisDirection, List<Widget> slivers) → Widget
  Build the viewport.

### Utility Methods

- debugFillProperties(DiagnosticPropertiesBuilder properties) → void
  Add additional properties associated with the node.
  
- getDirection(BuildContext context) → AxisDirection
  Returns the AxisDirection in which the scroll view scrolls.

## Examples

### Basic ListView

```dart
ListView(
  children: <Widget>[
    ListTile(
      leading: Icon(Icons.map),
      title: Text('Map'),
    ),
    ListTile(
      leading: Icon(Icons.photo_album),
      title: Text('Album'),
    ),
    ListTile(
      leading: Icon(Icons.phone),
      title: Text('Phone'),
    ),
  ],
)
```

### ListView.builder Example

```dart
ListView.builder(
  itemCount: 100,
  itemBuilder: (BuildContext context, int index) {
    return ListTile(
      title: Text('Item $index'),
      subtitle: Text('Subtitle for item $index'),
      leading: CircleAvatar(
        child: Text('$index'),
      ),
    );
  },
)
```

### ListView.separated Example

```dart
ListView.separated(
  itemCount: 50,
  itemBuilder: (BuildContext context, int index) {
    return Container(
      height: 50,
      color: Colors.amber[colorCodes[index]],
      child: Center(child: Text('Entry $index')),
    );
  },
  separatorBuilder: (BuildContext context, int index) => const Divider(),
)
```

### Performance Optimized ListView

```dart
ListView.builder(
  itemExtent: 60.0, // Fixed height for performance
  cacheExtent: 250.0, // Cache more items
  itemCount: items.length,
  itemBuilder: (context, index) {
    return ListTile(
      title: Text(items[index].title),
      subtitle: Text(items[index].subtitle),
    );
  },
)
```

## Common Issues and Solutions

### Performance Issues

1. **Use ListView.builder for long lists**: Don't use the default constructor with many children.
2. **Set itemExtent when possible**: Improves scrolling performance significantly.
3. **Use const constructors**: For static content, use const widgets.

### Layout Issues

1. **Unbounded height error**: Wrap in Expanded or give explicit height.
2. **Horizontal ListView**: Set scrollDirection and wrap in Container with height.

## See Also

- SingleChildScrollView, which is a scrollable widget that has a single child.
- PageView, which is a scrolling list that works page by page.
- GridView, which is a scrollable, 2D array of widgets.
- CustomScrollView, which is a scrollable widget that creates custom scroll effects using slivers.
- ListBody, which arranges its children in a similar manner, but without scrolling.
- ScrollNotification and NotificationListener, which can be used to watch the scroll position without using a ScrollController.
"""
    
    truncator = DocumentTruncator()
    token_manager = TokenManager()
    
    # Test different token limits
    limits = [1000, 2000, 5000]
    
    for limit in limits:
        print(f"\n{'─' * 40}")
        print(f"Truncating to {limit} tokens:")
        print('─' * 40)
        
        truncated = truncator.truncate_to_limit(long_doc, limit)
        actual_tokens = token_manager.count_tokens(truncated)
        
        print(f"Original length: {len(long_doc)} characters")
        print(f"Truncated length: {len(truncated)} characters")
        print(f"Target tokens: {limit}")
        print(f"Actual tokens: {actual_tokens}")
        
        # Show which sections were kept
        sections_kept = []
        for section in ["Description", "Constructors", "Properties", "Methods", "Examples", "Common Issues", "See Also"]:
            if f"## {section}" in truncated:
                sections_kept.append(section)
        
        print(f"Sections kept: {', '.join(sections_kept)}")
        
        # Show if truncation notice was added
        if "*Note: Documentation has been truncated" in truncated:
            print("✓ Truncation notice added")


async def demo_real_usage():
    """Demonstrate real-world usage with Flutter MCP."""
    print_section("Real Usage Example")
    
    print("\nExample 1: Default usage (no token limit)")
    print("─" * 40)
    print("await get_flutter_docs('Container')")
    print("→ Returns full documentation (8000 token default)")
    
    print("\nExample 2: Limited tokens for constrained context")
    print("─" * 40)
    print("await get_flutter_docs('Container', tokens=2000)")
    print("→ Returns essential information only")
    
    print("\nExample 3: Search with token limit")
    print("─" * 40)
    print("await search_flutter_docs('navigation', tokens=3000)")
    print("→ Each result gets proportional share of tokens")
    
    print("\nExample 4: Processing mentions with limits")
    print("─" * 40)
    print("await process_flutter_mentions('@flutter_mcp ListView @flutter_mcp GridView', tokens=2000)")
    print("→ Each mention gets ~1000 tokens")
    
    print("\nResponse format with token info:")
    print("─" * 40)
    response = {
        "content": "# Container\n\n## Description\n...",
        "source": "live",
        "class": "Container",
        "library": "widgets",
        "token_count": 1998,
        "original_tokens": 5234,
        "truncated": True,
        "truncation_note": "Documentation limited to 2000 tokens. Some sections omitted for brevity."
    }
    print(json.dumps(response, indent=2))


async def main():
    """Run all demos."""
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║          Flutter MCP Token Management Demo                ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    await demo_token_counting()
    await demo_truncation()
    await demo_real_usage()
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())