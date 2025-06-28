#!/usr/bin/env python3
"""Test cases for the smart truncation algorithm."""

import pytest
from src.flutter_mcp.truncation import (
    SmartTruncator, AdaptiveTruncator, ContentPriority,
    DocumentationSection, truncate_flutter_docs
)


def create_sample_documentation():
    """Create a sample Flutter documentation for testing."""
    return """# Container

## Description
A convenience widget that combines common painting, positioning, and sizing widgets. 
Container is a very commonly used widget in Flutter applications. It provides a way to 
customize the appearance and layout of child widgets. The Container widget can be used 
to add padding, margins, borders, background color, and many other styling options 
to its child widget.

## Constructors

### Container({Key? key, AlignmentGeometry? alignment, EdgeInsetsGeometry? padding, Color? color, Decoration? decoration, Decoration? foregroundDecoration, double? width, double? height, BoxConstraints? constraints, EdgeInsetsGeometry? margin, Matrix4? transform, AlignmentGeometry? transformAlignment, Widget? child, Clip clipBehavior = Clip.none})
```dart
Container({
  Key? key,
  this.alignment,
  this.padding,
  this.color,
  this.decoration,
  this.foregroundDecoration,
  double? width,
  double? height,
  BoxConstraints? constraints,
  this.margin,
  this.transform,
  this.transformAlignment,
  this.child,
  this.clipBehavior = Clip.none,
})
```
Creates a widget that combines common painting, positioning, and sizing widgets.

### Container.fixed({required double width, required double height, Widget? child})
```dart
Container.fixed({
  required double width,
  required double height,
  Widget? child,
})
```
Creates a container with fixed dimensions.

## Properties

- **alignment**: How to align the child within the container
- **padding**: Empty space to inscribe inside the decoration
- **color**: The color to paint behind the child
- **decoration**: The decoration to paint behind the child
- **foregroundDecoration**: The decoration to paint in front of the child
- **width**: Container width constraint
- **height**: Container height constraint
- **constraints**: Additional constraints to apply to the child
- **margin**: Empty space to surround the decoration and child
- **transform**: The transformation matrix to apply before painting
- **transformAlignment**: The alignment of the origin
- **child**: The child contained by the container
- **clipBehavior**: How to clip the contents

## Methods

### build(BuildContext context)
```dart
@override
Widget build(BuildContext context) {
  Widget? current = child;

  if (child == null && (constraints == null || !constraints!.isTight)) {
    current = LimitedBox(
      maxWidth: 0.0,
      maxHeight: 0.0,
      child: ConstrainedBox(constraints: const BoxConstraints.expand()),
    );
  }

  if (alignment != null)
    current = Align(alignment: alignment!, child: current);

  final EdgeInsetsGeometry? effectivePadding = _paddingIncludingDecoration;
  if (effectivePadding != null)
    current = Padding(padding: effectivePadding, child: current);

  if (color != null)
    current = ColoredBox(color: color!, child: current);

  if (clipBehavior != Clip.none) {
    assert(decoration != null);
    current = ClipPath(
      clipper: _DecorationClipper(
        textDirection: Directionality.maybeOf(context),
        decoration: decoration!,
      ),
      clipBehavior: clipBehavior,
      child: current,
    );
  }

  if (decoration != null)
    current = DecoratedBox(decoration: decoration!, child: current);

  if (foregroundDecoration != null) {
    current = DecoratedBox(
      decoration: foregroundDecoration!,
      position: DecorationPosition.foreground,
      child: current,
    );
  }

  if (constraints != null)
    current = ConstrainedBox(constraints: constraints!, child: current);

  if (margin != null)
    current = Padding(padding: margin!, child: current);

  if (transform != null)
    current = Transform(transform: transform!, alignment: transformAlignment, child: current);

  return current!;
}
```
Describes the part of the user interface represented by this widget.

### debugFillProperties(DiagnosticPropertiesBuilder properties)
```dart
@override
void debugFillProperties(DiagnosticPropertiesBuilder properties) {
  super.debugFillProperties(properties);
  properties.add(DiagnosticsProperty<AlignmentGeometry>('alignment', alignment, showName: false, defaultValue: null));
  properties.add(DiagnosticsProperty<EdgeInsetsGeometry>('padding', padding, defaultValue: null));
  properties.add(DiagnosticsProperty<Clip>('clipBehavior', clipBehavior, defaultValue: Clip.none));
  // ... more properties
}
```
Add additional properties associated with the node.

### createElement()
```dart
@override
StatelessElement createElement() => StatelessElement(this);
```
Creates a StatelessElement to manage this widget's location in the tree.

### toStringShort()
```dart
@override
String toStringShort() {
  return key == null ? '$runtimeType' : '$runtimeType-$key';
}
```
A brief description of this object, usually just the runtimeType and hashCode.

## Code Examples

#### Example 1:
```dart
Container(
  width: 200,
  height: 200,
  color: Colors.blue,
  child: Center(
    child: Text(
      'Hello World',
      style: TextStyle(color: Colors.white, fontSize: 24),
    ),
  ),
)
```

#### Example 2:
```dart
Container(
  margin: EdgeInsets.all(20.0),
  padding: EdgeInsets.all(10.0),
  decoration: BoxDecoration(
    border: Border.all(color: Colors.black, width: 2.0),
    borderRadius: BorderRadius.circular(10.0),
    gradient: LinearGradient(
      colors: [Colors.blue, Colors.green],
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    ),
  ),
  child: Text('Decorated Container'),
)
```

#### Example 3:
```dart
Container(
  transform: Matrix4.rotationZ(0.1),
  child: Container(
    width: 100,
    height: 100,
    color: Colors.red,
    child: Center(
      child: Text('Rotated'),
    ),
  ),
)
```

#### Example 4:
```dart
Container(
  constraints: BoxConstraints(
    minWidth: 100,
    maxWidth: 200,
    minHeight: 50,
    maxHeight: 100,
  ),
  color: Colors.amber,
  child: Text(
    'This text will wrap based on the constraints',
    overflow: TextOverflow.ellipsis,
  ),
)
```

#### Example 5:
```dart
Container(
  decoration: BoxDecoration(
    color: Colors.white,
    boxShadow: [
      BoxShadow(
        color: Colors.grey.withOpacity(0.5),
        spreadRadius: 5,
        blurRadius: 7,
        offset: Offset(0, 3),
      ),
    ],
  ),
  child: Padding(
    padding: EdgeInsets.all(20.0),
    child: Text('Container with shadow'),
  ),
)
```
"""


class TestSmartTruncator:
    """Test the basic SmartTruncator functionality."""
    
    def test_no_truncation_needed(self):
        """Test that small documents are not truncated."""
        truncator = SmartTruncator(max_tokens=10000)
        doc = "# Small Doc\n\nThis is a small document."
        
        result = truncator.truncate_documentation(doc, "SmallClass")
        assert result == doc
    
    def test_basic_truncation(self):
        """Test basic truncation of large documents."""
        truncator = SmartTruncator(max_tokens=500)
        doc = create_sample_documentation()
        
        result = truncator.truncate_documentation(doc, "Container")
        
        # Should be shorter than original
        assert len(result) < len(doc)
        
        # Should still contain critical sections
        assert "## Description" in result
        assert "## Constructors" in result
        
        # Should have truncation notice
        assert "truncated" in result.lower()
    
    def test_section_parsing(self):
        """Test that sections are parsed correctly."""
        truncator = SmartTruncator()
        doc = create_sample_documentation()
        
        sections = truncator._parse_documentation(doc, "Container")
        
        # Check that we have sections of different types
        section_names = [s.name for s in sections]
        assert any("description" in name for name in section_names)
        assert any("constructor" in name for name in section_names)
        assert any("property" in name for name in section_names)
        assert any("method" in name for name in section_names)
        assert any("example" in name for name in section_names)
    
    def test_priority_assignment(self):
        """Test that priorities are assigned correctly."""
        truncator = SmartTruncator()
        doc = create_sample_documentation()
        
        sections = truncator._parse_documentation(doc, "Container")
        
        # Description should be CRITICAL
        desc_sections = [s for s in sections if s.name == "description"]
        assert len(desc_sections) > 0
        assert desc_sections[0].priority == ContentPriority.CRITICAL
        
        # Constructor signatures should be CRITICAL
        const_sig_sections = [s for s in sections if "constructor_sig" in s.name]
        assert len(const_sig_sections) > 0
        assert all(s.priority == ContentPriority.CRITICAL for s in const_sig_sections)
        
        # build method should be HIGH priority
        build_sections = [s for s in sections if "method_build" in s.name]
        assert len(build_sections) > 0
        assert build_sections[0].priority == ContentPriority.HIGH
    
    def test_code_truncation(self):
        """Test that code is truncated intelligently."""
        truncator = SmartTruncator()
        
        code = """```dart
Container(
  width: 200,
  height: 200,
  child: Column(
    children: [
      Text('Line 1'),
      Text('Line 2'),
      Text('Line 3'),
    ],
  ),
)
```"""
        
        truncated = truncator._truncate_code(code, 100)
        
        # Should be shorter
        assert len(truncated) < len(code)
        
        # Should try to balance braces
        open_braces = truncated.count('{')
        close_braces = truncated.count('}')
        assert abs(open_braces - close_braces) <= 2


class TestAdaptiveTruncator:
    """Test the AdaptiveTruncator with different strategies."""
    
    def test_balanced_strategy(self):
        """Test balanced truncation strategy."""
        truncator = AdaptiveTruncator(max_tokens=1000)
        doc = create_sample_documentation()
        
        result, metadata = truncator.truncate_with_strategy(
            doc, "Container", "widgets", "balanced"
        )
        
        # Should have a mix of content
        assert "## Description" in result
        assert "## Constructors" in result
        assert "## Properties" in result
        assert metadata["strategy_used"] == "balanced"
    
    def test_signatures_strategy(self):
        """Test signatures-focused truncation strategy."""
        truncator = AdaptiveTruncator(max_tokens=800)
        doc = create_sample_documentation()
        
        result, metadata = truncator.truncate_with_strategy(
            doc, "Container", "widgets", "signatures"
        )
        
        # Should prioritize method signatures
        assert "```dart" in result  # Code blocks
        assert metadata["strategy_used"] == "signatures"
    
    def test_minimal_strategy(self):
        """Test minimal truncation strategy."""
        truncator = AdaptiveTruncator(max_tokens=400)
        doc = create_sample_documentation()
        
        result, metadata = truncator.truncate_with_strategy(
            doc, "Container", "widgets", "minimal"
        )
        
        # Should be very short
        assert len(result) < 2000  # Much shorter than original
        assert metadata["strategy_used"] == "minimal"
        
        # Should still have the most essential parts
        assert "Container" in result
        assert "## Description" in result
    
    def test_truncation_metadata(self):
        """Test that truncation metadata is accurate."""
        truncator = AdaptiveTruncator(max_tokens=500)
        doc = create_sample_documentation()
        
        result, metadata = truncator.truncate_with_strategy(
            doc, "Container", "widgets", "balanced"
        )
        
        assert "original_length" in metadata
        assert "truncated_length" in metadata
        assert "compression_ratio" in metadata
        assert "was_truncated" in metadata
        
        assert metadata["original_length"] == len(doc)
        assert metadata["truncated_length"] == len(result)
        assert 0 < metadata["compression_ratio"] < 1
        assert metadata["was_truncated"] is True


class TestUtilityFunctions:
    """Test the utility functions."""
    
    def test_truncate_flutter_docs_function(self):
        """Test the convenience function."""
        doc = create_sample_documentation()
        
        result = truncate_flutter_docs(
            doc,
            "Container",
            max_tokens=500,
            strategy="minimal"
        )
        
        assert len(result) < len(doc)
        assert "Container" in result
        assert "truncated" in result.lower()


def test_high_priority_widgets():
    """Test that high-priority widgets are recognized."""
    truncator = SmartTruncator()
    
    # Test some high-priority widgets
    for widget in ["Container", "Scaffold", "Row", "Column"]:
        assert widget in truncator.widget_priorities.HIGH_PRIORITY_WIDGETS


def test_token_estimation():
    """Test token estimation accuracy."""
    section = DocumentationSection(
        name="test",
        content="This is a test content with some words.",
        priority=ContentPriority.MEDIUM
    )
    
    # Rough estimation check
    assert 5 <= section.token_estimate <= 15  # Should be around 10 tokens


if __name__ == "__main__":
    # Run a simple demonstration
    print("Smart Truncation Algorithm Demo")
    print("=" * 50)
    
    doc = create_sample_documentation()
    print(f"Original document length: {len(doc)} characters")
    
    for max_tokens in [500, 1000, 2000]:
        print(f"\nTruncating to {max_tokens} tokens:")
        result = truncate_flutter_docs(doc, "Container", max_tokens)
        print(f"  Result length: {len(result)} characters")
        print(f"  Compression ratio: {len(result)/len(doc):.2%}")
        
        # Check what sections survived
        sections = []
        if "## Description" in result:
            sections.append("Description")
        if "## Constructors" in result:
            sections.append("Constructors")
        if "## Properties" in result:
            sections.append("Properties")
        if "## Methods" in result:
            sections.append("Methods")
        if "## Code Examples" in result:
            sections.append("Examples")
        
        print(f"  Sections kept: {', '.join(sections)}")