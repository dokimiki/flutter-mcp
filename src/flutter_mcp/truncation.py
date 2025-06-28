#!/usr/bin/env python3
"""Smart truncation algorithm for Flutter/Dart documentation.

This module implements intelligent truncation strategies that preserve
the most important information when token limits are reached.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class ContentPriority(Enum):
    """Priority levels for different documentation sections."""
    CRITICAL = 1      # Must keep: class description, constructor signatures
    HIGH = 2          # Try to keep: primary methods, key properties
    MEDIUM = 3        # Nice to have: code examples, secondary methods
    LOW = 4           # Can remove: inherited members, verbose descriptions
    MINIMAL = 5       # Remove first: see also, related classes


@dataclass
class DocumentationSection:
    """Represents a section of documentation with metadata."""
    name: str
    content: str
    priority: ContentPriority
    is_code: bool = False
    char_count: int = field(init=False)
    token_estimate: int = field(init=False)
    
    def __post_init__(self):
        self.char_count = len(self.content)
        # Rough token estimation: ~4 chars per token for English, ~3 for code
        self.token_estimate = self.char_count // (3 if self.is_code else 4)


class FlutterWidgetPriorities:
    """Predefined priorities for common Flutter widgets."""
    
    # Most commonly used widgets get special treatment
    HIGH_PRIORITY_WIDGETS = {
        "Container", "Row", "Column", "Text", "Image", "Scaffold",
        "AppBar", "ListView", "GridView", "Stack", "Positioned",
        "Center", "Padding", "SizedBox", "Expanded", "Flexible",
        "SingleChildScrollView", "GestureDetector", "InkWell",
        "TextField", "ElevatedButton", "IconButton", "Card"
    }
    
    # Method patterns that indicate high importance
    HIGH_PRIORITY_METHODS = {
        "build", "createState", "initState", "dispose", "setState",
        "didChangeDependencies", "didUpdateWidget", "deactivate"
    }
    
    # Properties that are commonly used
    HIGH_PRIORITY_PROPERTIES = {
        "child", "children", "width", "height", "color", "padding",
        "margin", "alignment", "decoration", "style", "onPressed",
        "onTap", "controller", "value", "enabled", "visible"
    }


class SmartTruncator:
    """Implements smart truncation strategies for Flutter documentation."""
    
    def __init__(self, max_tokens: int = 8000):
        """
        Initialize the truncator with a maximum token limit.
        
        Args:
            max_tokens: Maximum number of tokens to allow (default 8000)
        """
        self.max_tokens = max_tokens
        self.widget_priorities = FlutterWidgetPriorities()
    
    def truncate_documentation(
        self,
        doc_content: str,
        class_name: str,
        library: str = "widgets"
    ) -> str:
        """
        Intelligently truncate Flutter/Dart documentation.
        
        Args:
            doc_content: Full documentation content
            class_name: Name of the class being documented
            library: Flutter library (widgets, material, etc.)
            
        Returns:
            Truncated documentation that fits within token limits
        """
        # Parse documentation into sections
        sections = self._parse_documentation(doc_content, class_name)
        
        # Calculate total tokens
        total_tokens = sum(s.token_estimate for s in sections)
        
        # If it fits, return as-is
        if total_tokens <= self.max_tokens:
            return doc_content
        
        # Apply truncation strategies
        truncated_sections = self._apply_truncation_strategies(
            sections, class_name, library
        )
        
        # Rebuild documentation
        return self._rebuild_documentation(truncated_sections, class_name)
    
    def _parse_documentation(
        self,
        content: str,
        class_name: str
    ) -> List[DocumentationSection]:
        """Parse documentation into prioritized sections."""
        sections = []
        
        # Extract class description (CRITICAL)
        desc_match = re.search(
            r'## Description\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL
        )
        if desc_match:
            sections.append(DocumentationSection(
                name="description",
                content=desc_match.group(1).strip(),
                priority=ContentPriority.CRITICAL
            ))
        
        # Extract constructors (CRITICAL)
        const_match = re.search(
            r'## Constructors\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL
        )
        if const_match:
            # Keep constructor signatures but maybe trim descriptions
            constructors = self._parse_constructors(const_match.group(1))
            sections.extend(constructors)
        
        # Extract properties (HIGH/MEDIUM based on importance)
        props_match = re.search(
            r'## Properties\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL
        )
        if props_match:
            properties = self._parse_properties(props_match.group(1))
            sections.extend(properties)
        
        # Extract methods (HIGH/MEDIUM/LOW based on importance)
        methods_match = re.search(
            r'## Methods\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL
        )
        if methods_match:
            methods = self._parse_methods(methods_match.group(1))
            sections.extend(methods)
        
        # Extract code examples (MEDIUM)
        examples_match = re.search(
            r'## Code Examples\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL
        )
        if examples_match:
            examples = self._parse_examples(examples_match.group(1))
            sections.extend(examples)
        
        return sections
    
    def _parse_constructors(self, content: str) -> List[DocumentationSection]:
        """Parse constructor sections with appropriate priorities."""
        sections = []
        
        # Match individual constructors
        const_pattern = r'### (.*?)\n(.*?)(?=\n###|\Z)'
        matches = re.finditer(const_pattern, content, re.DOTALL)
        
        for match in matches:
            const_name = match.group(1).strip()
            const_content = match.group(2).strip()
            
            # Extract signature and description separately
            sig_match = re.search(r'```dart\n(.*?)\n```', const_content, re.DOTALL)
            
            if sig_match:
                # Signature is CRITICAL
                sections.append(DocumentationSection(
                    name=f"constructor_sig_{const_name}",
                    content=f"### {const_name}\n```dart\n{sig_match.group(1)}\n```",
                    priority=ContentPriority.CRITICAL,
                    is_code=True
                ))
                
                # Description is HIGH (can be trimmed)
                desc = const_content.replace(sig_match.group(0), "").strip()
                if desc:
                    sections.append(DocumentationSection(
                        name=f"constructor_desc_{const_name}",
                        content=desc,
                        priority=ContentPriority.HIGH
                    ))
        
        return sections
    
    def _parse_properties(self, content: str) -> List[DocumentationSection]:
        """Parse properties with importance-based priorities."""
        sections = []
        
        # Match individual properties
        prop_pattern = r'- \*\*(.*?)\*\*: (.*?)(?=\n-|\Z)'
        matches = re.finditer(prop_pattern, content, re.DOTALL)
        
        for match in matches:
            prop_name = match.group(1).strip()
            prop_desc = match.group(2).strip()
            
            # Determine priority based on property name
            if prop_name in self.widget_priorities.HIGH_PRIORITY_PROPERTIES:
                priority = ContentPriority.HIGH
            else:
                priority = ContentPriority.MEDIUM
            
            sections.append(DocumentationSection(
                name=f"property_{prop_name}",
                content=f"- **{prop_name}**: {prop_desc}",
                priority=priority
            ))
        
        return sections
    
    def _parse_methods(self, content: str) -> List[DocumentationSection]:
        """Parse methods with importance-based priorities."""
        sections = []
        
        # Match individual methods
        method_pattern = r'### (.*?)\n(.*?)(?=\n###|\Z)'
        matches = re.finditer(method_pattern, content, re.DOTALL)
        
        for match in matches:
            method_name = match.group(1).strip()
            method_content = match.group(2).strip()
            
            # Extract just the method name (remove parameters)
            base_method_name = re.match(r'(\w+)', method_name)
            base_name = base_method_name.group(1) if base_method_name else method_name
            
            # Determine priority
            if base_name in self.widget_priorities.HIGH_PRIORITY_METHODS:
                priority = ContentPriority.HIGH
            elif base_name.startswith('_'):  # Private methods
                priority = ContentPriority.LOW
            elif 'override' in method_content.lower():  # Overridden methods
                priority = ContentPriority.MEDIUM
            else:
                priority = ContentPriority.MEDIUM
            
            # Extract signature and description
            sig_match = re.search(r'```dart\n(.*?)\n```', method_content, re.DOTALL)
            
            if sig_match:
                # Keep signature with method
                sections.append(DocumentationSection(
                    name=f"method_{base_name}",
                    content=f"### {method_name}\n{sig_match.group(0)}",
                    priority=priority,
                    is_code=True
                ))
                
                # Description separately (lower priority)
                desc = method_content.replace(sig_match.group(0), "").strip()
                if desc and priority != ContentPriority.LOW:
                    sections.append(DocumentationSection(
                        name=f"method_desc_{base_name}",
                        content=desc,
                        priority=ContentPriority(min(priority.value + 1, 5))
                    ))
        
        return sections
    
    def _parse_examples(self, content: str) -> List[DocumentationSection]:
        """Parse code examples with priorities."""
        sections = []
        
        # Match individual examples
        example_pattern = r'#### Example (\d+):\n```dart\n(.*?)\n```'
        matches = re.finditer(example_pattern, content, re.DOTALL)
        
        for i, match in enumerate(matches):
            example_num = match.group(1)
            example_code = match.group(2).strip()
            
            # First 2 examples are MEDIUM, rest are LOW
            priority = ContentPriority.MEDIUM if i < 2 else ContentPriority.LOW
            
            sections.append(DocumentationSection(
                name=f"example_{example_num}",
                content=f"#### Example {example_num}:\n```dart\n{example_code}\n```",
                priority=priority,
                is_code=True
            ))
        
        return sections
    
    def _apply_truncation_strategies(
        self,
        sections: List[DocumentationSection],
        class_name: str,
        library: str
    ) -> List[DocumentationSection]:
        """Apply truncation strategies to fit within token limits."""
        
        # Sort sections by priority (keep high priority items)
        sections.sort(key=lambda s: (s.priority.value, -s.token_estimate))
        
        # Apply progressive truncation
        current_tokens = 0
        kept_sections = []
        
        for section in sections:
            if current_tokens + section.token_estimate <= self.max_tokens:
                kept_sections.append(section)
                current_tokens += section.token_estimate
            else:
                # Try to truncate this section
                remaining_tokens = self.max_tokens - current_tokens
                if remaining_tokens > 100:  # Worth truncating
                    truncated = self._truncate_section(section, remaining_tokens)
                    if truncated:
                        kept_sections.append(truncated)
                        current_tokens += truncated.token_estimate
                        break
        
        return kept_sections
    
    def _truncate_section(
        self,
        section: DocumentationSection,
        max_tokens: int
    ) -> Optional[DocumentationSection]:
        """Truncate a single section to fit within token limit."""
        if section.token_estimate <= max_tokens:
            return section
        
        # Calculate character limit (rough approximation)
        char_limit = max_tokens * (3 if section.is_code else 4)
        
        if section.is_code:
            # For code, try to keep it syntactically valid
            truncated_content = self._truncate_code(section.content, char_limit)
        else:
            # For text, truncate at sentence boundaries
            truncated_content = self._truncate_text(section.content, char_limit)
        
        if truncated_content:
            return DocumentationSection(
                name=section.name,
                content=truncated_content + "\n... (truncated)",
                priority=section.priority,
                is_code=section.is_code
            )
        
        return None
    
    def _truncate_code(self, code: str, char_limit: int) -> str:
        """Truncate code while trying to maintain syntax validity."""
        if len(code) <= char_limit:
            return code
        
        # Try to truncate at meaningful boundaries
        truncated = code[:char_limit]
        
        # Find last complete line
        last_newline = truncated.rfind('\n')
        if last_newline > char_limit * 0.8:  # Don't lose too much
            truncated = truncated[:last_newline]
        
        # Balance braces/brackets if possible
        # (Simple approach - just add closing braces)
        open_braces = truncated.count('{') - truncated.count('}')
        open_brackets = truncated.count('[') - truncated.count(']')
        open_parens = truncated.count('(') - truncated.count(')')
        
        if open_braces > 0:
            truncated += '\n' + '  // ...\n' + '}' * open_braces
        
        return truncated
    
    def _truncate_text(self, text: str, char_limit: int) -> str:
        """Truncate text at sentence boundaries."""
        if len(text) <= char_limit:
            return text
        
        # Try to truncate at sentence end
        truncated = text[:char_limit]
        
        # Find last sentence boundary
        sentence_ends = ['.', '!', '?']
        last_sentence = -1
        
        for end in sentence_ends:
            pos = truncated.rfind(end)
            if pos > last_sentence:
                last_sentence = pos
        
        if last_sentence > char_limit * 0.7:  # Don't lose too much
            truncated = truncated[:last_sentence + 1]
        
        return truncated
    
    def _rebuild_documentation(
        self,
        sections: List[DocumentationSection],
        class_name: str
    ) -> str:
        """Rebuild documentation from truncated sections."""
        # Group sections by type
        description = []
        constructors = []
        properties = []
        methods = []
        examples = []
        
        for section in sections:
            if section.name == "description":
                description.append(section.content)
            elif section.name.startswith("constructor"):
                constructors.append(section.content)
            elif section.name.startswith("property"):
                properties.append(section.content)
            elif section.name.startswith("method"):
                methods.append(section.content)
            elif section.name.startswith("example"):
                examples.append(section.content)
        
        # Rebuild in standard order
        parts = [f"# {class_name} (Truncated Documentation)"]
        
        if description:
            parts.append("## Description")
            parts.extend(description)
        
        if constructors:
            parts.append("\n## Constructors")
            parts.extend(constructors)
        
        if properties:
            parts.append("\n## Properties")
            parts.extend(properties)
        
        if methods:
            parts.append("\n## Methods")
            parts.extend(methods)
        
        if examples:
            parts.append("\n## Code Examples")
            parts.extend(examples)
        
        # Add truncation notice
        parts.append("\n---")
        parts.append("*Note: This documentation has been intelligently truncated to fit within token limits. Some sections may have been removed or shortened.*")
        
        return "\n".join(parts)


class AdaptiveTruncator(SmartTruncator):
    """Extended truncator with adaptive strategies based on content type."""
    
    def __init__(self, max_tokens: int = 8000):
        super().__init__(max_tokens)
        self.truncation_stats = {
            "total_processed": 0,
            "truncated": 0,
            "sections_removed": 0
        }
    
    def truncate_with_strategy(
        self,
        doc_content: str,
        class_name: str,
        library: str = "widgets",
        strategy: str = "balanced"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Truncate with different strategies based on use case.
        
        Strategies:
        - "balanced": Keep a bit of everything
        - "signatures": Prioritize method/constructor signatures
        - "examples": Prioritize code examples
        - "minimal": Just essential information
        
        Returns:
            Tuple of (truncated_content, truncation_metadata)
        """
        self.truncation_stats["total_processed"] += 1
        
        # Adjust priorities based on strategy
        original_priorities = self._save_priorities()
        self._apply_strategy(strategy)
        
        # Perform truncation
        truncated = self.truncate_documentation(doc_content, class_name, library)
        
        # Restore original priorities
        self._restore_priorities(original_priorities)
        
        # Generate metadata
        metadata = {
            "original_length": len(doc_content),
            "truncated_length": len(truncated),
            "compression_ratio": len(truncated) / len(doc_content),
            "strategy_used": strategy,
            "was_truncated": len(truncated) < len(doc_content)
        }
        
        if metadata["was_truncated"]:
            self.truncation_stats["truncated"] += 1
        
        return truncated, metadata
    
    def _save_priorities(self) -> Dict:
        """Save current priority settings."""
        return {
            "methods": self.widget_priorities.HIGH_PRIORITY_METHODS.copy(),
            "properties": self.widget_priorities.HIGH_PRIORITY_PROPERTIES.copy()
        }
    
    def _restore_priorities(self, saved: Dict):
        """Restore priority settings."""
        self.widget_priorities.HIGH_PRIORITY_METHODS = saved["methods"]
        self.widget_priorities.HIGH_PRIORITY_PROPERTIES = saved["properties"]
    
    def _apply_strategy(self, strategy: str):
        """Modify priorities based on strategy."""
        if strategy == "signatures":
            # Deprioritize everything except signatures
            self.widget_priorities.HIGH_PRIORITY_PROPERTIES = set()
        elif strategy == "examples":
            # Boost example priority (handled in parsing)
            pass
        elif strategy == "minimal":
            # Keep only the most essential
            self.widget_priorities.HIGH_PRIORITY_METHODS = {"build", "createState"}
            self.widget_priorities.HIGH_PRIORITY_PROPERTIES = {"child", "children"}
        # "balanced" uses default priorities


# Utility functions for easy integration

def create_truncator(max_tokens: int = 8000) -> AdaptiveTruncator:
    """Create a truncator instance with specified token limit."""
    return AdaptiveTruncator(max_tokens)


def truncate_flutter_docs(
    content: str,
    class_name: str,
    max_tokens: int = 8000,
    strategy: str = "balanced"
) -> str:
    """
    Convenience function to truncate Flutter documentation.
    
    Args:
        content: Documentation content to truncate
        class_name: Name of the class being documented
        max_tokens: Maximum token limit
        strategy: Truncation strategy to use
        
    Returns:
        Truncated documentation
    """
    truncator = create_truncator(max_tokens)
    truncated, _ = truncator.truncate_with_strategy(
        content, class_name, "widgets", strategy
    )
    return truncated