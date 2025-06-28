#!/usr/bin/env python3
"""
Demonstration of the smart truncation algorithm for Flutter documentation.

This script shows how the truncation algorithm preserves the most important
information when dealing with token limits.
"""

import asyncio
from src.flutter_mcp.truncation import AdaptiveTruncator, ContentPriority


def create_mock_flutter_doc():
    """Create a mock Flutter documentation that simulates a real large doc."""
    return """# ListView

## Description
A scrollable list of widgets arranged linearly. ListView is the most commonly used 
scrolling widget. It displays its children one after another in the scroll direction. 
In the cross axis, the children are required to fill the ListView.

There are four options for constructing a ListView:

1. The default constructor takes an explicit List<Widget> of children. This constructor 
   is appropriate for list views with a small number of children because constructing 
   the List requires doing work for every child that could possibly be displayed in 
   the list view instead of just those children that are actually visible.

2. The ListView.builder constructor takes an IndexedWidgetBuilder, which builds the 
   children on demand. This constructor is appropriate for list views with a large 
   (or infinite) number of children because the builder is called only for those 
   children that are actually visible.

3. The ListView.separated constructor takes two IndexedWidgetBuilders: itemBuilder 
   builds child items on demand, and separatorBuilder similarly builds separator 
   children which appear in between the child items. This constructor is appropriate 
   for list views with a fixed number of children.

4. The ListView.custom constructor takes a SliverChildDelegate, which provides the 
   ability to customize additional aspects of the child model.

## Constructors

### ListView({Key? key, Axis scrollDirection = Axis.vertical, bool reverse = false, ScrollController? controller, bool? primary, ScrollPhysics? physics, bool shrinkWrap = false, EdgeInsetsGeometry? padding, double? itemExtent, Widget? prototypeItem, bool addAutomaticKeepAlives = true, bool addRepaintBoundaries = true, bool addSemanticIndexes = true, double? cacheExtent, List<Widget> children = const <Widget>[], int? semanticChildCount, DragStartBehavior dragStartBehavior = DragStartBehavior.start, ScrollViewKeyboardDismissBehavior keyboardDismissBehavior = ScrollViewKeyboardDismissBehavior.manual, String? restorationId, Clip clipBehavior = Clip.hardEdge})
```dart
ListView({
  Key? key,
  Axis scrollDirection = Axis.vertical,
  bool reverse = false,
  ScrollController? controller,
  bool? primary,
  ScrollPhysics? physics,
  bool shrinkWrap = false,
  EdgeInsetsGeometry? padding,
  this.itemExtent,
  this.prototypeItem,
  bool addAutomaticKeepAlives = true,
  bool addRepaintBoundaries = true,
  bool addSemanticIndexes = true,
  double? cacheExtent,
  List<Widget> children = const <Widget>[],
  int? semanticChildCount,
  DragStartBehavior dragStartBehavior = DragStartBehavior.start,
  ScrollViewKeyboardDismissBehavior keyboardDismissBehavior = ScrollViewKeyboardDismissBehavior.manual,
  String? restorationId,
  Clip clipBehavior = Clip.hardEdge,
})
```
Creates a scrollable, linear array of widgets from an explicit List.

### ListView.builder({Key? key, Axis scrollDirection = Axis.vertical, bool reverse = false, ScrollController? controller, bool? primary, ScrollPhysics? physics, bool shrinkWrap = false, EdgeInsetsGeometry? padding, double? itemExtent, Widget? prototypeItem, required IndexedWidgetBuilder itemBuilder, int? itemCount, bool addAutomaticKeepAlives = true, bool addRepaintBoundaries = true, bool addSemanticIndexes = true, double? cacheExtent, int? semanticChildCount, DragStartBehavior dragStartBehavior = DragStartBehavior.start, ScrollViewKeyboardDismissBehavior keyboardDismissBehavior = ScrollViewKeyboardDismissBehavior.manual, String? restorationId, Clip clipBehavior = Clip.hardEdge})
```dart
ListView.builder({
  Key? key,
  Axis scrollDirection = Axis.vertical,
  bool reverse = false,
  ScrollController? controller,
  bool? primary,
  ScrollPhysics? physics,
  bool shrinkWrap = false,
  EdgeInsetsGeometry? padding,
  this.itemExtent,
  this.prototypeItem,
  required IndexedWidgetBuilder itemBuilder,
  int? itemCount,
  bool addAutomaticKeepAlives = true,
  bool addRepaintBoundaries = true,
  bool addSemanticIndexes = true,
  double? cacheExtent,
  int? semanticChildCount,
  DragStartBehavior dragStartBehavior = DragStartBehavior.start,
  ScrollViewKeyboardDismissBehavior keyboardDismissBehavior = ScrollViewKeyboardDismissBehavior.manual,
  String? restorationId,
  Clip clipBehavior = Clip.hardEdge,
})
```
Creates a scrollable, linear array of widgets that are created on demand.

### ListView.separated({Key? key, Axis scrollDirection = Axis.vertical, bool reverse = false, ScrollController? controller, bool? primary, ScrollPhysics? physics, bool shrinkWrap = false, EdgeInsetsGeometry? padding, required IndexedWidgetBuilder itemBuilder, required IndexedWidgetBuilder separatorBuilder, required int itemCount, bool addAutomaticKeepAlives = true, bool addRepaintBoundaries = true, bool addSemanticIndexes = true, double? cacheExtent, DragStartBehavior dragStartBehavior = DragStartBehavior.start, ScrollViewKeyboardDismissBehavior keyboardDismissBehavior = ScrollViewKeyboardDismissBehavior.manual, String? restorationId, Clip clipBehavior = Clip.hardEdge})
```dart
ListView.separated({
  Key? key,
  Axis scrollDirection = Axis.vertical,
  bool reverse = false,
  ScrollController? controller,
  bool? primary,
  ScrollPhysics? physics,
  bool shrinkWrap = false,
  EdgeInsetsGeometry? padding,
  required IndexedWidgetBuilder itemBuilder,
  required IndexedWidgetBuilder separatorBuilder,
  required int itemCount,
  bool addAutomaticKeepAlives = true,
  bool addRepaintBoundaries = true,
  bool addSemanticIndexes = true,
  double? cacheExtent,
  DragStartBehavior dragStartBehavior = DragStartBehavior.start,
  ScrollViewKeyboardDismissBehavior keyboardDismissBehavior = ScrollViewKeyboardDismissBehavior.manual,
  String? restorationId,
  Clip clipBehavior = Clip.hardEdge,
})
```
Creates a scrollable, linear array of widgets with a custom separator.

## Properties

- **scrollDirection**: The axis along which the scroll view scrolls
- **reverse**: Whether the scroll view scrolls in the reading direction
- **controller**: An object that can be used to control the position to which this scroll view is scrolled
- **primary**: Whether this is the primary scroll view associated with the parent
- **physics**: How the scroll view should respond to user input
- **shrinkWrap**: Whether the extent of the scroll view should be determined by the contents
- **padding**: The amount of space by which to inset the children
- **itemExtent**: The extent of each item in the scroll direction
- **prototypeItem**: A prototype item to use for measuring item extent
- **addAutomaticKeepAlives**: Whether to wrap each child in an AutomaticKeepAlive
- **addRepaintBoundaries**: Whether to wrap each child in a RepaintBoundary
- **addSemanticIndexes**: Whether to wrap each child in an IndexedSemantics
- **cacheExtent**: The viewport has an area before and after the visible area to cache items
- **semanticChildCount**: The number of children that will contribute semantic information
- **dragStartBehavior**: Determines the way that drag start behavior is handled
- **keyboardDismissBehavior**: Defines how the scroll view dismisses the keyboard
- **restorationId**: Restoration ID to save and restore the scroll offset
- **clipBehavior**: The content will be clipped (or not) according to this option

## Methods

### build(BuildContext context)
```dart
@override
Widget build(BuildContext context) {
  final List<Widget> slivers = buildSlivers(context);
  final AxisDirection axisDirection = getDirection(context);

  final ScrollController? scrollController = primary
    ? PrimaryScrollController.of(context)
    : controller;
  final Scrollable scrollable = Scrollable(
    dragStartBehavior: dragStartBehavior,
    axisDirection: axisDirection,
    controller: scrollController,
    physics: physics,
    scrollBehavior: scrollBehavior,
    semanticChildCount: semanticChildCount,
    restorationId: restorationId,
    viewportBuilder: (BuildContext context, ViewportOffset offset) {
      return buildViewport(context, offset, axisDirection, slivers);
    },
  );
  final Widget scrollableResult = primary && scrollController != null
    ? PrimaryScrollController.none(child: scrollable)
    : scrollable;

  if (keyboardDismissBehavior == ScrollViewKeyboardDismissBehavior.onDrag) {
    return NotificationListener<ScrollUpdateNotification>(
      child: scrollableResult,
      onNotification: (ScrollUpdateNotification notification) {
        final FocusScopeNode focusScope = FocusScope.of(context);
        if (notification.dragDetails != null && focusScope.hasFocus) {
          focusScope.unfocus();
        }
        return false;
      },
    );
  } else {
    return scrollableResult;
  }
}
```
Describes the part of the user interface represented by this widget.

### buildSlivers(BuildContext context)
```dart
@override
List<Widget> buildSlivers(BuildContext context) {
  Widget sliver = childrenDelegate.build(context);
  EdgeInsetsGeometry? effectivePadding = padding;
  if (padding == null) {
    final MediaQueryData? mediaQuery = MediaQuery.maybeOf(context);
    if (mediaQuery != null) {
      final EdgeInsets mediaQueryHorizontalPadding =
          mediaQuery.padding.copyWith(top: 0.0, bottom: 0.0);
      final EdgeInsets mediaQueryVerticalPadding =
          mediaQuery.padding.copyWith(left: 0.0, right: 0.0);
      effectivePadding = scrollDirection == Axis.vertical
          ? mediaQueryVerticalPadding
          : mediaQueryHorizontalPadding;
      sliver = MediaQuery(
        data: mediaQuery.copyWith(
          padding: scrollDirection == Axis.vertical
              ? mediaQueryHorizontalPadding
              : mediaQueryVerticalPadding,
        ),
        child: sliver,
      );
    }
  }

  if (effectivePadding != null)
    sliver = SliverPadding(padding: effectivePadding, sliver: sliver);
  return <Widget>[ sliver ];
}
```
Build the list of widgets to place inside the viewport.

### buildViewport(BuildContext context, ViewportOffset offset, AxisDirection axisDirection, List<Widget> slivers)
```dart
@override
Widget buildViewport(
  BuildContext context,
  ViewportOffset offset,
  AxisDirection axisDirection,
  List<Widget> slivers,
) {
  if (shrinkWrap) {
    return ShrinkWrappingViewport(
      axisDirection: axisDirection,
      offset: offset,
      slivers: slivers,
      clipBehavior: clipBehavior,
    );
  }
  return Viewport(
    axisDirection: axisDirection,
    offset: offset,
    slivers: slivers,
    cacheExtent: cacheExtent,
    center: center,
    anchor: anchor,
    clipBehavior: clipBehavior,
  );
}
```
Build the viewport.

### debugFillProperties(DiagnosticPropertiesBuilder properties)
```dart
@override
void debugFillProperties(DiagnosticPropertiesBuilder properties) {
  super.debugFillProperties(properties);
  properties.add(EnumProperty<Axis>('scrollDirection', scrollDirection));
  properties.add(FlagProperty('reverse', value: reverse, ifTrue: 'reversed', showName: true));
  properties.add(DiagnosticsProperty<ScrollController>('controller', controller, showName: false, defaultValue: null));
  properties.add(FlagProperty('primary', value: primary, ifTrue: 'using primary controller', showName: true));
  properties.add(DiagnosticsProperty<ScrollPhysics>('physics', physics, showName: false, defaultValue: null));
  properties.add(FlagProperty('shrinkWrap', value: shrinkWrap, ifTrue: 'shrink-wrapping', showName: true));
}
```
Add additional properties associated with the node.

## Code Examples

#### Example 1:
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

#### Example 2:
```dart
ListView.builder(
  itemCount: items.length,
  itemBuilder: (BuildContext context, int index) {
    return ListTile(
      title: Text('Item ${items[index]}'),
      onTap: () {
        print('Tapped on item $index');
      },
    );
  },
)
```

#### Example 3:
```dart
ListView.separated(
  itemCount: items.length,
  itemBuilder: (BuildContext context, int index) {
    return Container(
      height: 50,
      color: Colors.amber[colorCodes[index]],
      child: Center(child: Text('Entry ${items[index]}')),
    );
  },
  separatorBuilder: (BuildContext context, int index) => const Divider(),
)
```

#### Example 4:
```dart
ListView(
  scrollDirection: Axis.horizontal,
  children: <Widget>[
    Container(
      width: 160.0,
      color: Colors.red,
    ),
    Container(
      width: 160.0,
      color: Colors.blue,
    ),
    Container(
      width: 160.0,
      color: Colors.green,
    ),
    Container(
      width: 160.0,
      color: Colors.yellow,
    ),
    Container(
      width: 160.0,
      color: Colors.orange,
    ),
  ],
)
```

#### Example 5:
```dart
ListView.builder(
  physics: BouncingScrollPhysics(),
  itemCount: 100,
  itemBuilder: (context, index) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16.0),
        child: Text(
          'Item $index',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
      ),
    );
  },
)
```
"""


def demonstrate_truncation_strategies():
    """Demonstrate different truncation strategies."""
    
    # Create truncator
    truncator = AdaptiveTruncator(max_tokens=1000)
    
    # Get sample documentation
    doc = create_mock_flutter_doc()
    
    print("Flutter Documentation Smart Truncation Demo")
    print("=" * 60)
    print(f"\nOriginal document size: {len(doc)} characters")
    print(f"Estimated tokens: ~{len(doc) // 4}")
    
    strategies = ["balanced", "signatures", "examples", "minimal"]
    
    for strategy in strategies:
        print(f"\n\n{strategy.upper()} STRATEGY (max 1000 tokens)")
        print("-" * 60)
        
        truncated, metadata = truncator.truncate_with_strategy(
            doc, "ListView", "widgets", strategy
        )
        
        print(f"Result size: {len(truncated)} characters")
        print(f"Compression ratio: {metadata['compression_ratio']:.1%}")
        print(f"Was truncated: {metadata['was_truncated']}")
        
        # Show what sections survived
        sections_kept = []
        if "## Description" in truncated:
            sections_kept.append("Description")
        if "## Constructors" in truncated:
            sections_kept.append("Constructors")
        if "## Properties" in truncated:
            sections_kept.append("Properties")
        if "## Methods" in truncated:
            sections_kept.append("Methods")
        if "## Code Examples" in truncated:
            sections_kept.append("Examples")
        
        print(f"Sections kept: {', '.join(sections_kept)}")
        
        # Show a preview
        print("\nPreview (first 500 chars):")
        print("-" * 40)
        print(truncated[:500] + "...")


def demonstrate_progressive_truncation():
    """Show how the algorithm progressively removes content."""
    
    doc = create_mock_flutter_doc()
    
    print("\n\nPROGRESSIVE TRUNCATION DEMO")
    print("=" * 60)
    print("Showing how content is removed as token limit decreases:\n")
    
    token_limits = [8000, 4000, 2000, 1000, 500, 250]
    
    for limit in token_limits:
        truncator = AdaptiveTruncator(max_tokens=limit)
        truncated, metadata = truncator.truncate_with_strategy(
            doc, "ListView", "widgets", "balanced"
        )
        
        # Count what survived
        sections = {
            "Description": "## Description" in truncated,
            "Constructors": "## Constructors" in truncated,
            "Properties": "## Properties" in truncated,
            "Methods": "## Methods" in truncated,
            "Examples": "## Code Examples" in truncated,
            "Constructor sigs": "```dart" in truncated and "ListView(" in truncated,
            "Method sigs": "```dart" in truncated and "build(" in truncated,
        }
        
        kept = [name for name, present in sections.items() if present]
        
        print(f"Token limit: {limit:>4} | Size: {len(truncated):>5} chars | "
              f"Kept: {', '.join(kept)}")


def demonstrate_priority_system():
    """Show how the priority system works."""
    
    print("\n\nPRIORITY SYSTEM DEMO")
    print("=" * 60)
    print("Showing how different content is prioritized:\n")
    
    truncator = SmartTruncator()
    
    # Show priority assignments
    print("Content Priorities:")
    print("-" * 40)
    
    priorities = [
        ("Class description", ContentPriority.CRITICAL),
        ("Constructor signatures", ContentPriority.CRITICAL),
        ("build() method", ContentPriority.HIGH),
        ("Common properties (child, padding)", ContentPriority.HIGH),
        ("Other methods", ContentPriority.MEDIUM),
        ("Code examples (first 2)", ContentPriority.MEDIUM),
        ("Less common properties", ContentPriority.MEDIUM),
        ("Private methods", ContentPriority.LOW),
        ("Additional examples", ContentPriority.LOW),
        ("Inherited members", ContentPriority.MINIMAL),
    ]
    
    for content, priority in priorities:
        print(f"{content:<35} -> {priority.name} (priority {priority.value})")
    
    print("\n\nWhen truncating, content is removed in reverse priority order:")
    print("1. MINIMAL content is removed first")
    print("2. Then LOW priority content")
    print("3. Then MEDIUM priority content")
    print("4. HIGH priority content is kept if possible")
    print("5. CRITICAL content is always kept")


def main():
    """Run all demonstrations."""
    demonstrate_truncation_strategies()
    demonstrate_progressive_truncation()
    demonstrate_priority_system()
    
    print("\n\nCONCLUSION")
    print("=" * 60)
    print("The smart truncation algorithm ensures that even when severe")
    print("token limits are imposed, the most useful information is preserved:")
    print("- Constructor signatures for instantiation")
    print("- Key method signatures (build, createState)")
    print("- Essential properties (child, children)")
    print("- Class descriptions for understanding purpose")
    print("\nThis makes the documentation useful even when heavily truncated.")


if __name__ == "__main__":
    main()