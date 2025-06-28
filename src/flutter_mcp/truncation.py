"""
Smart truncation module for Flutter documentation.

Implements priority-based truncation that preserves the most important content
while respecting token limits and maintaining markdown formatting.
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Section:
    """Represents a documentation section with content and priority."""
    name: str
    content: str
    priority: int  # Lower number = higher priority
    start_pos: int
    end_pos: int


class DocumentTruncator:
    """Smart truncation for Flutter/Dart documentation."""
    
    # Section priorities (lower = more important)
    SECTION_PRIORITIES = {
        'description': 1,
        'summary': 1,
        'constructors': 2,
        'properties': 3,
        'methods': 4,
        'parameters': 5,
        'returns': 5,
        'examples': 6,
        'example': 6,
        'see also': 7,
        'implementation': 8,
        'source': 9,
    }
    
    # Approximate tokens per character (rough estimate)
    TOKENS_PER_CHAR = 0.25
    
    def __init__(self):
        """Initialize the document truncator."""
        pass
    
    def truncate_to_limit(self, content: str, token_limit: int) -> str:
        """
        Truncate content to fit within token limit while preserving structure.
        
        Args:
            content: The markdown content to truncate
            token_limit: Maximum number of tokens allowed
            
        Returns:
            Truncated content with truncation notice if needed
        """
        # Quick check - if content is already small enough, return as-is
        estimated_tokens = self._estimate_tokens(content)
        if estimated_tokens <= token_limit:
            return content
        
        # Detect sections in the content
        sections = self._detect_sections(content)
        
        # If no sections detected, fall back to simple truncation
        if not sections:
            return self._simple_truncate(content, token_limit)
        
        # Build truncated content based on priorities
        truncated = self._priority_truncate(content, sections, token_limit)
        
        # Add truncation notice
        return self._add_truncation_notice(truncated)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text length."""
        return int(len(text) * self.TOKENS_PER_CHAR)
    
    def _detect_sections(self, content: str) -> List[Section]:
        """Detect markdown sections in the content."""
        sections = []
        
        # Pattern for markdown headers (##, ###, ####)
        header_pattern = r'^(#{2,4})\s+(.+)$'
        
        lines = content.split('\n')
        current_section = None
        current_content = []
        current_start = 0
        
        for i, line in enumerate(lines):
            match = re.match(header_pattern, line, re.MULTILINE)
            
            if match:
                # Save previous section if exists
                if current_section:
                    section_content = '\n'.join(current_content)
                    sections.append(Section(
                        name=current_section,
                        content=section_content,
                        priority=self._get_section_priority(current_section),
                        start_pos=current_start,
                        end_pos=i
                    ))
                
                # Start new section
                current_section = match.group(2).lower().strip()
                current_content = [line]
                current_start = i
            elif current_section:
                current_content.append(line)
        
        # Don't forget the last section
        if current_section and current_content:
            section_content = '\n'.join(current_content)
            sections.append(Section(
                name=current_section,
                content=section_content,
                priority=self._get_section_priority(current_section),
                start_pos=current_start,
                end_pos=len(lines)
            ))
        
        # Sort sections by priority
        sections.sort(key=lambda s: s.priority)
        
        return sections
    
    def _get_section_priority(self, section_name: str) -> int:
        """Get priority for a section name."""
        section_lower = section_name.lower()
        
        # Check for exact matches first
        if section_lower in self.SECTION_PRIORITIES:
            return self.SECTION_PRIORITIES[section_lower]
        
        # Check for partial matches
        for key, priority in self.SECTION_PRIORITIES.items():
            if key in section_lower or section_lower in key:
                return priority
        
        # Default priority for unknown sections
        return 10
    
    def _simple_truncate(self, content: str, token_limit: int) -> str:
        """Simple truncation when no sections are detected."""
        char_limit = int(token_limit / self.TOKENS_PER_CHAR)
        
        if len(content) <= char_limit:
            return content
        
        # Try to truncate at a paragraph boundary
        truncated = content[:char_limit]
        last_para = truncated.rfind('\n\n')
        
        if last_para > char_limit * 0.8:  # If we found a paragraph break in the last 20%
            return truncated[:last_para]
        
        # Otherwise truncate at last complete sentence
        last_period = truncated.rfind('. ')
        if last_period > char_limit * 0.8:
            return truncated[:last_period + 1]
        
        # Last resort: truncate at word boundary
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space]
        
        return truncated
    
    def _priority_truncate(self, content: str, sections: List[Section], token_limit: int) -> str:
        """Truncate based on section priorities."""
        result_parts = []
        current_tokens = 0
        
        # First, try to get the content before any sections (usually the main description)
        lines = content.split('\n')
        pre_section_content = []
        
        for line in lines:
            if re.match(r'^#{2,4}\s+', line):
                break
            pre_section_content.append(line)
        
        if pre_section_content:
            pre_content = '\n'.join(pre_section_content).strip()
            if pre_content:
                pre_tokens = self._estimate_tokens(pre_content)
                if current_tokens + pre_tokens <= token_limit:
                    result_parts.append(pre_content)
                    current_tokens += pre_tokens
        
        # Add sections by priority
        for section in sections:
            section_tokens = self._estimate_tokens(section.content)
            
            if current_tokens + section_tokens <= token_limit:
                result_parts.append(section.content)
                current_tokens += section_tokens
            else:
                # Try to add at least part of this section
                remaining_tokens = token_limit - current_tokens
                if remaining_tokens > 100:  # Only add if we have reasonable space
                    partial = self._simple_truncate(section.content, remaining_tokens)
                    if partial.strip():
                        result_parts.append(partial)
                break
        
        return '\n\n'.join(result_parts)
    
    def _add_truncation_notice(self, content: str) -> str:
        """Add a notice that content was truncated."""
        if not content.endswith('\n'):
            content += '\n'
        
        notice = "\n---\n*Note: This documentation has been truncated to fit within token limits. " \
                 "Some sections may have been omitted or shortened.*"
        
        return content + notice


# Module-level instance for convenience
_truncator = DocumentTruncator()


def truncate_flutter_docs(
    content: str, 
    class_name: str, 
    max_tokens: int,
    strategy: str = "balanced"
) -> str:
    """
    Truncate Flutter documentation to fit within token limit.
    
    Args:
        content: The documentation content to truncate
        class_name: Name of the class (for context, not currently used)
        max_tokens: Maximum number of tokens allowed
        strategy: Truncation strategy (currently only "balanced" is supported)
        
    Returns:
        Truncated documentation content
    """
    return _truncator.truncate_to_limit(content, max_tokens)


def create_truncator() -> DocumentTruncator:
    """
    Create a new DocumentTruncator instance.
    
    Returns:
        A new DocumentTruncator instance
    """
    return DocumentTruncator()


# Example usage and testing
if __name__ == "__main__":
    truncator = DocumentTruncator()
    
    # Test with sample Flutter documentation
    sample_content = """
# Widget class

A widget is an immutable description of part of a user interface.

## Description

Widgets are the central class hierarchy in the Flutter framework. A widget is an 
immutable description of part of a user interface. Widgets can be inflated into 
elements, which manage the underlying render tree.

## Constructors

### Widget({Key? key})

Initializes key for subclasses.

## Properties

### hashCode → int
The hash code for this object.

### key → Key?
Controls how one widget replaces another widget in the tree.

### runtimeType → Type
A representation of the runtime type of the object.

## Methods

### createElement() → Element
Inflates this configuration to a concrete instance.

### debugDescribeChildren() → List<DiagnosticsNode>
Returns a list of DiagnosticsNode objects describing this node's children.

### debugFillProperties(DiagnosticPropertiesBuilder properties) → void
Add additional properties associated with the node.

## Examples

```dart
class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      child: Text('Hello World'),
    );
  }
}
```

## See Also

- StatelessWidget
- StatefulWidget
- InheritedWidget
"""
    
    # Test truncation
    truncated = truncator.truncate_to_limit(sample_content, 500)
    print("Original length:", len(sample_content))
    print("Truncated length:", len(truncated))
    print("\nTruncated content:")
    print(truncated)