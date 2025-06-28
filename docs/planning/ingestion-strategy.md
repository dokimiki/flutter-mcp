# Flutter MCP Ingestion Strategy

## Content Extraction Priorities

When we say we "support" a Flutter/Dart package, we extract and process the following content in priority order:

### 1. Essential Content (MVP)
- **Doc Comments (`///`)**: Primary source of API documentation
- **Class/Method Signatures**: Full signatures with parameter types and return values
- **Constructor Parameters**: Named parameters, required vs optional, default values
- **README.md**: Package overview, getting started, basic examples
- **pubspec.yaml**: Dependencies, Flutter/Dart SDK constraints

### 2. High-Value Content (Week 1)
- **Example Directory**: Complete runnable examples showing real usage
- **CHANGELOG.md**: Recent version changes, breaking changes, migration guides
- **Type Definitions**: Enums, typedefs, extension methods
- **Export Statements**: Understanding the public API surface

### 3. Context-Enhancing Content (Week 2+)
- **Test Files**: Understanding expected behavior and edge cases
- **Issue Templates**: Common problems and their solutions
- **Migration Guides**: Version-specific upgrade instructions
- **Platform-Specific Code**: iOS/Android/Web specific implementations

### What We DON'T Extract
- **Full Method Bodies**: Too much noise, not helpful for LLM context
- **Private Implementation Details**: Focus on public API only
- **Generated Code**: Skip `.g.dart`, `.freezed.dart` files
- **Build Configuration**: Detailed build settings aren't useful for API questions

## Semantic Chunking Strategy

Instead of naive text splitting, we chunk semantically:

```
CHUNK 1: package:provider, version:6.1.1, type:class
# ChangeNotifierProvider<T>
A widget that creates a ChangeNotifier and automatically disposes it.
Constructor: ChangeNotifierProvider({required Create<T> create, bool? lazy, Widget? child})
...

CHUNK 2: package:provider, version:6.1.1, type:method, class:ChangeNotifierProvider
# static T of<T>(BuildContext context, {bool listen = true})
Obtains the nearest Provider<T> up its widget tree and returns its value.
...
```

## Metadata Enrichment

Each chunk includes:
- Package name and version
- Source file path
- Content type (class/method/example/changelog)
- Null safety status
- Platform compatibility
- Last updated timestamp

This approach ensures high-quality, relevant context for LLMs while keeping storage and processing costs manageable.