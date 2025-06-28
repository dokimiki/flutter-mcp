# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-06-28

### Fixed
- Fixed HTTP and SSE transport modes that were failing with FastMCP API errors
  - Removed incorrect `sse_params` parameter usage 
  - Removed `get_asgi_app()` call that doesn't exist in FastMCP
  - FastMCP now handles HTTP transport internally without uvicorn

### Changed
- Removed uvicorn dependency as it's no longer needed (FastMCP handles HTTP transport internally)

## [0.1.0] - 2025-06-22

### Added
- Initial release of Flutter MCP Server
- Real-time Flutter and Dart documentation fetching
- pub.dev package documentation support
- SQLite caching for performance
- Multiple transport modes: stdio, HTTP, SSE
- Rich CLI interface with progress indicators