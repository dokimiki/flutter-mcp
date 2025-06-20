#!/usr/bin/env python3
"""Flutter MCP Server - Real-time Flutter/Dart documentation for AI assistants"""

import asyncio
import json
import re
from typing import Optional, Dict, List, Any
from datetime import datetime
import time

from mcp.server.fastmcp import FastMCP
import httpx
# Redis removed - using SQLite cache instead
from bs4 import BeautifulSoup
import structlog
from structlog.contextvars import bind_contextvars
from rich.console import Console

# Import our custom logging utilities
from .logging_utils import format_cache_stats, print_server_header

# Initialize structured logging
# IMPORTANT: For MCP servers, logs must go to stderr, not stdout
# stdout is reserved for the JSON-RPC protocol
import sys
import logging

# Configure structlog with enhanced formatting
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False),
        # Our custom processor comes before the renderer!
        format_cache_stats,
        # Use ConsoleRenderer for beautiful colored output
        structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback,
        ),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger()

# Rich console for direct output
console = Console(stderr=True)

# Initialize FastMCP server
mcp = FastMCP("Flutter Docs Server")

# Import our SQLite-based cache
from .cache import get_cache
# Import error handling utilities
from .error_handling import (
    NetworkError, DocumentationNotFoundError, RateLimitError,
    with_retry, safe_http_get, format_error_response,
    CircuitBreaker
)

# Initialize cache manager
cache_manager = get_cache()
logger.info("cache_initialized", cache_type="sqlite", path=cache_manager.db_path)


class RateLimiter:
    """Rate limiter for respectful web scraping (2 requests/second)"""
    
    def __init__(self, calls_per_second: float = 2.0):
        self.semaphore = asyncio.Semaphore(1)
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
    
    async def acquire(self):
        async with self.semaphore:
            current_time = time.time()
            elapsed = current_time - self.last_call
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self.last_call = time.time()


# Global rate limiter instance
rate_limiter = RateLimiter()

# Circuit breakers for external services
flutter_docs_circuit = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    expected_exception=(NetworkError, httpx.HTTPStatusError)
)

pub_dev_circuit = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    expected_exception=(NetworkError, httpx.HTTPStatusError)
)

# Cache TTL strategy (in seconds)
CACHE_DURATIONS = {
    "flutter_api": 86400,      # 24 hours for stable APIs
    "dart_api": 86400,         # 24 hours for Dart APIs
    "pub_package": 43200,      # 12 hours for packages (may update more frequently)
    "cookbook": 604800,        # 7 days for examples
    "stackoverflow": 3600,     # 1 hour for community content
}


def get_cache_key(doc_type: str, identifier: str, version: str = None) -> str:
    """Generate cache keys for different documentation types"""
    if version:
        return f"{doc_type}:{identifier}:{version}"
    return f"{doc_type}:{identifier}"


def clean_text(element) -> str:
    """Clean and extract text from BeautifulSoup element"""
    if not element:
        return ""
    text = element.get_text(strip=True)
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def format_constructors(constructors: List) -> str:
    """Format constructor information for AI consumption"""
    if not constructors:
        return "No constructors found"
    
    result = []
    for constructor in constructors:
        name = constructor.find('h3')
        signature = constructor.find('pre')
        desc = constructor.find('p')
        
        if name:
            result.append(f"### {clean_text(name)}")
        if signature:
            result.append(f"```dart\n{clean_text(signature)}\n```")
        if desc:
            result.append(clean_text(desc))
        result.append("")
    
    return "\n".join(result)


def format_properties(properties: List) -> str:
    """Format property information"""
    if not properties:
        return "No properties found"
    
    result = []
    for prop_list in properties:
        items = prop_list.find_all('dt')
        for item in items:
            prop_name = clean_text(item)
            prop_desc = item.find_next_sibling('dd')
            if prop_name:
                result.append(f"- **{prop_name}**: {clean_text(prop_desc) if prop_desc else 'No description'}")
    
    return "\n".join(result)


def format_methods(methods: List) -> str:
    """Format method information"""
    if not methods:
        return "No methods found"
    
    result = []
    for method in methods:
        name = method.find('h3')
        signature = method.find('pre')
        desc = method.find('p')
        
        if name:
            result.append(f"### {clean_text(name)}")
        if signature:
            result.append(f"```dart\n{clean_text(signature)}\n```")
        if desc:
            result.append(clean_text(desc))
        result.append("")
    
    return "\n".join(result)


def extract_code_examples(soup: BeautifulSoup) -> str:
    """Extract code examples from documentation"""
    examples = soup.find_all('pre', class_='language-dart')
    if not examples:
        examples = soup.find_all('pre')  # Fallback to any pre tags
    
    if not examples:
        return "No code examples found"
    
    result = []
    for i, example in enumerate(examples[:5]):  # Limit to 5 examples
        code = clean_text(example)
        if code:
            result.append(f"#### Example {i+1}:\n```dart\n{code}\n```\n")
    
    return "\n".join(result)


async def process_documentation(html: str, class_name: str) -> str:
    """Context7-style documentation processing pipeline"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove navigation, scripts, styles, etc.
    for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
        element.decompose()
    
    # 1. Parse - Extract key sections
    description = soup.find('section', class_='desc')
    constructors = soup.find_all('section', class_='constructor')
    properties = soup.find_all('dl', class_='properties')
    methods = soup.find_all('section', class_='method')
    
    # 2. Enrich - Format for AI consumption
    markdown = f"""# {class_name}

## Description
{clean_text(description) if description else 'No description available'}

## Constructors
{format_constructors(constructors)}

## Properties
{format_properties(properties)}

## Methods
{format_methods(methods)}

## Code Examples
{extract_code_examples(soup)}
"""
    
    return markdown


def resolve_flutter_url(query: str) -> Optional[str]:
    """Intelligently resolve documentation URLs from queries"""
    # Common Flutter class patterns
    patterns = {
        r"^(\w+)$": "https://api.flutter.dev/flutter/widgets/{0}-class.html",
        r"^widgets\.(\w+)$": "https://api.flutter.dev/flutter/widgets/{0}-class.html",
        r"^material\.(\w+)$": "https://api.flutter.dev/flutter/material/{0}-class.html",
        r"^cupertino\.(\w+)$": "https://api.flutter.dev/flutter/cupertino/{0}-class.html",
        r"^painting\.(\w+)$": "https://api.flutter.dev/flutter/painting/{0}-class.html",
        r"^animation\.(\w+)$": "https://api.flutter.dev/flutter/animation/{0}-class.html",
        r"^rendering\.(\w+)$": "https://api.flutter.dev/flutter/rendering/{0}-class.html",
        r"^services\.(\w+)$": "https://api.flutter.dev/flutter/services/{0}-class.html",
        r"^gestures\.(\w+)$": "https://api.flutter.dev/flutter/gestures/{0}-class.html",
        r"^foundation\.(\w+)$": "https://api.flutter.dev/flutter/foundation/{0}-class.html",
        # Dart core libraries
        r"^dart:core\.(\w+)$": "https://api.dart.dev/stable/dart-core/{0}-class.html",
        r"^dart:async\.(\w+)$": "https://api.dart.dev/stable/dart-async/{0}-class.html",
        r"^dart:collection\.(\w+)$": "https://api.dart.dev/stable/dart-collection/{0}-class.html",
        r"^dart:convert\.(\w+)$": "https://api.dart.dev/stable/dart-convert/{0}-class.html",
        r"^dart:io\.(\w+)$": "https://api.dart.dev/stable/dart-io/{0}-class.html",
        r"^dart:math\.(\w+)$": "https://api.dart.dev/stable/dart-math/{0}-class.html",
        r"^dart:typed_data\.(\w+)$": "https://api.dart.dev/stable/dart-typed_data/{0}-class.html",
        r"^dart:ui\.(\w+)$": "https://api.dart.dev/stable/dart-ui/{0}-class.html",
    }
    
    for pattern, url_template in patterns.items():
        if match := re.match(pattern, query, re.IGNORECASE):
            return url_template.format(*match.groups())
    
    return None


@mcp.tool()
async def get_flutter_docs(
    class_name: str, 
    library: str = "widgets"
) -> Dict[str, Any]:
    """
    Get Flutter class documentation on-demand.
    
    Args:
        class_name: Name of the Flutter class (e.g., "Container", "Scaffold")
        library: Flutter library (e.g., "widgets", "material", "cupertino")
    
    Returns:
        Dictionary with documentation content or error message
    """
    bind_contextvars(tool="get_flutter_docs", class_name=class_name, library=library)
    
    # Check cache first
    cache_key = get_cache_key("flutter_api", f"{library}:{class_name}")
    
    # Check cache
    cached_data = cache_manager.get(cache_key)
    if cached_data:
        logger.info("cache_hit")
        return cached_data
    
    # Rate-limited fetch from Flutter docs
    await rate_limiter.acquire()
    
    # Determine URL based on library type
    if library.startswith("dart:"):
        # Convert dart:core to dart-core format for Dart API
        dart_lib = library.replace("dart:", "dart-")
        url = f"https://api.dart.dev/stable/{dart_lib}/{class_name}-class.html"
    else:
        # Flutter libraries use api.flutter.dev
        url = f"https://api.flutter.dev/flutter/{library}/{class_name}-class.html"
    
    logger.info("fetching_docs", url=url)
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Flutter-MCP-Docs/1.0 (github.com/flutter-mcp/flutter-mcp)"
                }
            )
            response.raise_for_status()
            
            # Process HTML - Context7 style pipeline
            content = await process_documentation(response.text, class_name)
            
            # Cache the result
            result = {
                "source": "live",
                "class": class_name,
                "library": library,
                "content": content,
                "fetched_at": datetime.utcnow().isoformat()
            }
            cache_manager.set(cache_key, result, CACHE_DURATIONS["flutter_api"])
            
            logger.info("docs_fetched_success", content_length=len(content))
            return result
            
    except httpx.HTTPStatusError as e:
        logger.error("http_error", status_code=e.response.status_code)
        return {
            "error": f"HTTP {e.response.status_code}: Documentation not found for {library}.{class_name}",
            "suggestion": "Check the class name and library. Common libraries: widgets, material, cupertino"
        }
    except Exception as e:
        logger.error("fetch_error", error=str(e))
        return {
            "error": f"Failed to fetch documentation: {str(e)}",
            "url": url
        }


@mcp.tool()
async def search_flutter_docs(query: str) -> Dict[str, Any]:
    """
    Search across Flutter/Dart documentation sources with fuzzy matching.
    
    Searches Flutter API docs, Dart API docs, and pub.dev packages.
    Returns top 5-10 most relevant results with brief descriptions.
    
    Args:
        query: Search query (e.g., "state management", "Container", "navigation", "http requests")
    
    Returns:
        Search results with relevance scores and brief descriptions
    """
    bind_contextvars(tool="search_flutter_docs", query=query)
    logger.info("searching_docs")
    
    results = []
    query_lower = query.lower()
    
    # Check cache for search results
    cache_key = get_cache_key("search_results", query_lower)
    cached_data = cache_manager.get(cache_key)
    if cached_data:
        logger.info("search_cache_hit")
        return cached_data
    
    # 1. Try direct URL resolution first (exact matches)
    if url := resolve_flutter_url(query):
        logger.info("url_resolved", url=url)
        
        # Extract class name and library from URL
        if "flutter/widgets" in url:
            library = "widgets"
        elif "flutter/material" in url:
            library = "material"
        elif "flutter/cupertino" in url:
            library = "cupertino"
        else:
            library = "unknown"
        
        class_match = re.search(r'/([^/]+)-class\.html$', url)
        if class_match:
            class_name = class_match.group(1)
            doc = await get_flutter_docs(class_name, library)
            if "error" not in doc:
                results.append({
                    "type": "flutter_class",
                    "relevance": 1.0,
                    "title": f"{class_name} ({library})",
                    "description": f"Flutter {library} widget/class",
                    "url": url,
                    "content_preview": doc.get("content", "")[:200] + "..."
                })
    
    # 2. Check common Flutter widgets and classes
    common_flutter_items = [
        # State management related
        ("StatefulWidget", "widgets", "Base class for widgets that have mutable state"),
        ("StatelessWidget", "widgets", "Base class for widgets that don't require mutable state"),
        ("State", "widgets", "Logic and internal state for a StatefulWidget"),
        ("InheritedWidget", "widgets", "Base class for widgets that propagate information down the tree"),
        ("Provider", "widgets", "A widget that provides a value to its descendants"),
        ("ValueListenableBuilder", "widgets", "Rebuilds when ValueListenable changes"),
        ("NotificationListener", "widgets", "Listens for Notifications bubbling up"),
        
        # Layout widgets
        ("Container", "widgets", "A convenience widget that combines common painting, positioning, and sizing"),
        ("Row", "widgets", "Displays children in a horizontal array"),
        ("Column", "widgets", "Displays children in a vertical array"),
        ("Stack", "widgets", "Positions children relative to the box edges"),
        ("Scaffold", "material", "Basic material design visual layout structure"),
        ("Expanded", "widgets", "Expands a child to fill available space in Row/Column"),
        ("Flexible", "widgets", "Controls how a child flexes in Row/Column"),
        ("Wrap", "widgets", "Displays children in multiple runs"),
        ("Flow", "widgets", "Positions children using transformation matrices"),
        ("Table", "widgets", "Displays children in a table layout"),
        ("Align", "widgets", "Aligns a child within itself"),
        ("Center", "widgets", "Centers a child within itself"),
        ("Positioned", "widgets", "Positions a child in a Stack"),
        ("FittedBox", "widgets", "Scales and positions child within itself"),
        ("AspectRatio", "widgets", "Constrains child to specific aspect ratio"),
        ("ConstrainedBox", "widgets", "Imposes additional constraints on child"),
        ("SizedBox", "widgets", "Box with a specified size"),
        ("FractionallySizedBox", "widgets", "Sizes child to fraction of total space"),
        ("LimitedBox", "widgets", "Limits child size when unconstrained"),
        ("Offstage", "widgets", "Lays out child as if visible but paints nothing"),
        ("LayoutBuilder", "widgets", "Builds widget tree based on parent constraints"),
        
        # Navigation
        ("Navigator", "widgets", "Manages a stack of Route objects"),
        ("Route", "widgets", "An abstraction for an entry managed by a Navigator"),
        ("MaterialPageRoute", "material", "A modal route that replaces the entire screen"),
        ("NavigationBar", "material", "Material 3 navigation bar"),
        ("NavigationRail", "material", "Material navigation rail"),
        ("BottomNavigationBar", "material", "Bottom navigation bar"),
        ("Drawer", "material", "Material design drawer"),
        ("TabBar", "material", "Material design tabs"),
        ("TabBarView", "material", "Page view for TabBar"),
        ("WillPopScope", "widgets", "Intercepts back button press"),
        ("BackButton", "material", "Material design back button"),
        
        # Input widgets
        ("TextField", "material", "A material design text field"),
        ("TextFormField", "material", "A FormField that contains a TextField"),
        ("Form", "widgets", "Container for form fields"),
        ("GestureDetector", "widgets", "Detects gestures on widgets"),
        ("InkWell", "material", "Rectangular area that responds to touch with ripple"),
        ("Dismissible", "widgets", "Can be dismissed by dragging"),
        ("Draggable", "widgets", "Can be dragged to DragTarget"),
        ("LongPressDraggable", "widgets", "Draggable triggered by long press"),
        ("DragTarget", "widgets", "Receives data from Draggable"),
        ("DropdownButton", "material", "Material design dropdown button"),
        ("Slider", "material", "Material design slider"),
        ("Switch", "material", "Material design switch"),
        ("Checkbox", "material", "Material design checkbox"),
        ("Radio", "material", "Material design radio button"),
        ("DatePicker", "material", "Material design date picker"),
        ("TimePicker", "material", "Material design time picker"),
        
        # Lists & Grids
        ("ListView", "widgets", "Scrollable list of widgets"),
        ("GridView", "widgets", "Scrollable 2D array of widgets"),
        ("CustomScrollView", "widgets", "ScrollView with slivers"),
        ("SingleChildScrollView", "widgets", "Box with single scrollable child"),
        ("PageView", "widgets", "Scrollable list that works page by page"),
        ("ReorderableListView", "material", "List where items can be reordered"),
        ("RefreshIndicator", "material", "Material design pull-to-refresh"),
        
        # Common material widgets
        ("AppBar", "material", "A material design app bar"),
        ("Card", "material", "A material design card"),
        ("ListTile", "material", "A single fixed-height row for lists"),
        ("IconButton", "material", "A material design icon button"),
        ("ElevatedButton", "material", "A material design elevated button"),
        ("FloatingActionButton", "material", "A material design floating action button"),
        ("Chip", "material", "Material design chip"),
        ("ChoiceChip", "material", "Material design choice chip"),
        ("FilterChip", "material", "Material design filter chip"),
        ("ActionChip", "material", "Material design action chip"),
        ("CircularProgressIndicator", "material", "Material circular progress"),
        ("LinearProgressIndicator", "material", "Material linear progress"),
        ("SnackBar", "material", "Material design snackbar"),
        ("BottomSheet", "material", "Material design bottom sheet"),
        ("ExpansionPanel", "material", "Material expansion panel"),
        ("Stepper", "material", "Material design stepper"),
        ("DataTable", "material", "Material design data table"),
        
        # Visual Effects
        ("Opacity", "widgets", "Makes child partially transparent"),
        ("Transform", "widgets", "Applies transformation before painting"),
        ("RotatedBox", "widgets", "Rotates child by integral quarters"),
        ("ClipRect", "widgets", "Clips child to rectangle"),
        ("ClipRRect", "widgets", "Clips child to rounded rectangle"),
        ("ClipOval", "widgets", "Clips child to oval"),
        ("ClipPath", "widgets", "Clips child to path"),
        ("DecoratedBox", "widgets", "Paints decoration around child"),
        ("BackdropFilter", "widgets", "Applies filter to existing painted content"),
        
        # Animation
        ("AnimatedBuilder", "widgets", "A widget that rebuilds when animation changes"),
        ("AnimationController", "animation", "Controls an animation"),
        ("Hero", "widgets", "Marks a child for hero animations"),
        ("AnimatedContainer", "widgets", "Animated version of Container"),
        ("AnimatedOpacity", "widgets", "Animated version of Opacity"),
        ("AnimatedPositioned", "widgets", "Animated version of Positioned"),
        ("AnimatedDefaultTextStyle", "widgets", "Animated version of DefaultTextStyle"),
        ("AnimatedAlign", "widgets", "Animated version of Align"),
        ("AnimatedPadding", "widgets", "Animated version of Padding"),
        ("AnimatedSize", "widgets", "Animates its size to match child"),
        ("AnimatedCrossFade", "widgets", "Cross-fades between two children"),
        ("AnimatedSwitcher", "widgets", "Animates when switching between children"),
        
        # Async widgets
        ("FutureBuilder", "widgets", "Builds based on interaction with a Future"),
        ("StreamBuilder", "widgets", "Builds based on interaction with a Stream"),
        
        # Utility widgets
        ("MediaQuery", "widgets", "Establishes media query subtree"),
        ("Theme", "material", "Applies theme to descendant widgets"),
        ("DefaultTextStyle", "widgets", "Default text style for descendants"),
        ("Semantics", "widgets", "Annotates widget tree with semantic descriptions"),
        ("MergeSemantics", "widgets", "Merges semantics of descendants"),
        ("ExcludeSemantics", "widgets", "Drops semantics of descendants"),
    ]
    
    # Score Flutter items based on query match
    for class_name, library, description in common_flutter_items:
        relevance = calculate_relevance(query_lower, class_name.lower(), description.lower())
        if relevance > 0.3:  # Threshold for inclusion
            results.append({
                "type": "flutter_class",
                "relevance": relevance,
                "title": f"{class_name} ({library})",
                "description": description,
                "class_name": class_name,
                "library": library
            })
    
    # 3. Check common Dart core classes
    common_dart_items = [
        ("List", "dart:core", "An indexable collection of objects with a length"),
        ("Map", "dart:core", "A collection of key/value pairs"),
        ("Set", "dart:core", "A collection of objects with no duplicate elements"),
        ("String", "dart:core", "A sequence of UTF-16 code units"),
        ("Future", "dart:async", "Represents a computation that completes with a value or error"),
        ("Stream", "dart:async", "A source of asynchronous data events"),
        ("Duration", "dart:core", "A span of time"),
        ("DateTime", "dart:core", "An instant in time"),
        ("RegExp", "dart:core", "A regular expression pattern"),
        ("Iterable", "dart:core", "A collection of values that can be accessed sequentially"),
    ]
    
    for class_name, library, description in common_dart_items:
        relevance = calculate_relevance(query_lower, class_name.lower(), description.lower())
        if relevance > 0.3:
            results.append({
                "type": "dart_class",
                "relevance": relevance,
                "title": f"{class_name} ({library})",
                "description": description,
                "class_name": class_name,
                "library": library
            })
    
    # 4. Search popular pub.dev packages
    popular_packages = [
        # State Management
        ("provider", "State management library that makes it easy to connect business logic to widgets"),
        ("riverpod", "A reactive caching and data-binding framework"),
        ("bloc", "State management library implementing the BLoC design pattern"),
        ("get", "Open source state management, navigation and utilities"),
        ("mobx", "Reactive state management library"),
        ("redux", "Predictable state container"),
        ("stacked", "MVVM architecture solution"),
        ("get_it", "Service locator for dependency injection"),
        
        # Networking
        ("dio", "Powerful HTTP client for Dart with interceptors and FormData"),
        ("http", "A composable, multi-platform, Future-based API for HTTP requests"),
        ("retrofit", "Type-safe HTTP client generator"),
        ("chopper", "HTTP client with built-in JsonConverter"),
        ("graphql_flutter", "GraphQL client for Flutter"),
        ("socket_io_client", "Socket.IO client"),
        ("web_socket_channel", "WebSocket connections"),
        
        # Storage & Database
        ("shared_preferences", "Flutter plugin for reading and writing simple key-value pairs"),
        ("sqflite", "SQLite plugin for Flutter with support for iOS, Android and MacOS"),
        ("hive", "Lightweight and blazing fast key-value database written in pure Dart"),
        ("isar", "Fast cross-platform database"),
        ("objectbox", "High-performance NoSQL database"),
        ("drift", "Reactive persistence library"),
        ("floor", "SQLite abstraction with Room-like API"),
        
        # Firebase
        ("firebase_core", "Flutter plugin to use Firebase Core API"),
        ("firebase_auth", "Flutter plugin for Firebase Auth"),
        ("firebase_database", "Flutter plugin for Firebase Realtime Database"),
        ("cloud_firestore", "Flutter plugin for Cloud Firestore"),
        ("firebase_messaging", "Push notifications via FCM"),
        ("firebase_storage", "Flutter plugin for Firebase Cloud Storage"),
        ("firebase_analytics", "Flutter plugin for Google Analytics for Firebase"),
        
        # UI/UX Libraries
        ("flutter_bloc", "Flutter widgets that make it easy to implement BLoC design pattern"),
        ("animations", "Beautiful pre-built animations for Flutter"),
        ("flutter_svg", "SVG rendering and widget library for Flutter"),
        ("cached_network_image", "Flutter library to load and cache network images"),
        ("flutter_slidable", "Slidable list item actions"),
        ("shimmer", "Shimmer loading effect"),
        ("liquid_swipe", "Liquid swipe page transitions"),
        ("flutter_staggered_grid_view", "Staggered grid layouts"),
        ("carousel_slider", "Carousel widget"),
        ("photo_view", "Zoomable image widget"),
        ("flutter_spinkit", "Loading indicators collection"),
        ("lottie", "Render After Effects animations"),
        ("rive", "Interactive animations"),
        
        # Platform Integration
        ("url_launcher", "Flutter plugin for launching URLs"),
        ("path_provider", "Flutter plugin for getting commonly used locations on the filesystem"),
        ("image_picker", "Flutter plugin for selecting images from image library or camera"),
        ("connectivity_plus", "Flutter plugin for discovering network connectivity"),
        ("permission_handler", "Permission plugin for Flutter"),
        ("geolocator", "Flutter geolocation plugin for Android and iOS"),
        ("google_fonts", "Flutter package to use fonts from fonts.google.com"),
        ("flutter_local_notifications", "Local notifications"),
        ("share_plus", "Share content to other apps"),
        ("file_picker", "Native file picker"),
        ("open_file", "Open files with default apps"),
        
        # Navigation
        ("go_router", "A declarative routing package for Flutter"),
        ("auto_route", "Code generation for type-safe route navigation"),
        ("beamer", "Handle your application routing"),
        ("fluro", "Flutter routing library"),
        
        # Developer Tools
        ("logger", "Beautiful logging utility"),
        ("pretty_dio_logger", "Dio interceptor for logging"),
        ("flutter_dotenv", "Load environment variables"),
        ("device_info_plus", "Device information"),
        ("package_info_plus", "App package information"),
        ("equatable", "Simplify equality comparisons"),
        ("freezed", "Code generation for immutable classes"),
        ("json_serializable", "Automatically generate code for JSON"),
        ("build_runner", "Build system for Dart code generation"),
    ]
    
    for package_name, description in popular_packages:
        relevance = calculate_relevance(query_lower, package_name.lower(), description.lower())
        if relevance > 0.3:
            results.append({
                "type": "pub_package",
                "relevance": relevance,
                "title": f"{package_name} (pub.dev)",
                "description": description,
                "package_name": package_name
            })
    
    # 5. Concept-based search (for queries like "state management", "navigation", etc.)
    concepts = {
        "state management": [
            ("setState", "The simplest way to manage state in Flutter"),
            ("InheritedWidget", "Share data across the widget tree"),
            ("provider", "Popular state management package"),
            ("riverpod", "Improved provider with compile-time safety"),
            ("bloc", "Business Logic Component pattern"),
            ("get", "Lightweight state management solution"),
            ("mobx", "Reactive state management"),
            ("redux", "Predictable state container"),
            ("ValueNotifier", "Simple observable pattern"),
            ("ChangeNotifier", "Observable object for multiple listeners"),
        ],
        "navigation": [
            ("Navigator", "Stack-based navigation in Flutter"),
            ("go_router", "Declarative routing package"),
            ("auto_route", "Code generation for routes"),
            ("Named routes", "Navigation using route names"),
            ("Deep linking", "Handle URLs in your app"),
            ("WillPopScope", "Intercept back navigation"),
            ("NavigatorObserver", "Observe navigation events"),
            ("Hero animations", "Animate widgets between routes"),
            ("Modal routes", "Full-screen modal pages"),
            ("BottomSheet navigation", "Navigate with bottom sheets"),
        ],
        "http": [
            ("http", "Official Dart HTTP package"),
            ("dio", "Advanced HTTP client with interceptors"),
            ("retrofit", "Type-safe HTTP client generator"),
            ("chopper", "HTTP client with built-in JsonConverter"),
            ("GraphQL", "Query language for APIs"),
            ("REST API", "RESTful web services"),
            ("WebSocket", "Real-time bidirectional communication"),
            ("gRPC", "High performance RPC framework"),
        ],
        "database": [
            ("sqflite", "SQLite for Flutter"),
            ("hive", "NoSQL database for Flutter"),
            ("drift", "Reactive persistence library"),
            ("objectbox", "Fast NoSQL database"),
            ("shared_preferences", "Simple key-value storage"),
            ("isar", "Fast cross-platform database"),
            ("floor", "SQLite abstraction"),
            ("sembast", "NoSQL persistent store"),
            ("Firebase Realtime Database", "Cloud-hosted NoSQL database"),
            ("Cloud Firestore", "Scalable NoSQL cloud database"),
        ],
        "animation": [
            ("AnimationController", "Control animations"),
            ("AnimatedBuilder", "Build animations efficiently"),
            ("Hero", "Shared element transitions"),
            ("animations", "Pre-built animation package"),
            ("rive", "Interactive animations"),
            ("lottie", "After Effects animations"),
            ("AnimatedContainer", "Implicit animations"),
            ("TweenAnimationBuilder", "Simple custom animations"),
            ("Curves", "Animation easing functions"),
            ("Physics-based animations", "Spring and friction animations"),
        ],
        "architecture": [
            ("BLoC Pattern", "Business Logic Component pattern for state management"),
            ("MVVM", "Model-View-ViewModel architecture pattern"),
            ("Clean Architecture", "Domain-driven design with clear separation"),
            ("Repository Pattern", "Abstraction layer for data sources"),
            ("Provider Pattern", "Dependency injection and state management"),
            ("GetX Pattern", "Reactive state management with GetX"),
            ("MVC", "Model-View-Controller pattern in Flutter"),
            ("Redux", "Predictable state container pattern"),
            ("Riverpod Architecture", "Modern reactive caching framework"),
            ("Domain Driven Design", "DDD principles in Flutter"),
            ("Hexagonal Architecture", "Ports and adapters pattern"),
            ("Feature-based structure", "Organize code by features"),
        ],
        "testing": [
            ("Widget Testing", "Testing Flutter widgets in isolation"),
            ("Integration Testing", "End-to-end testing of Flutter apps"),
            ("Unit Testing", "Testing Dart code logic"),
            ("Golden Testing", "Visual regression testing"),
            ("Mockito", "Mocking framework for Dart"),
            ("flutter_test", "Flutter testing framework"),
            ("test", "Dart testing package"),
            ("integration_test", "Flutter integration testing"),
            ("mocktail", "Type-safe mocking library"),
            ("Test Coverage", "Measuring test completeness"),
            ("TDD", "Test-driven development"),
            ("BDD", "Behavior-driven development"),
        ],
        "performance": [
            ("Performance Profiling", "Analyzing app performance"),
            ("Widget Inspector", "Debugging widget trees"),
            ("Timeline View", "Performance timeline analysis"),
            ("Memory Profiling", "Analyzing memory usage"),
            ("Shader Compilation", "Reducing shader jank"),
            ("Build Optimization", "Optimizing build methods"),
            ("Lazy Loading", "Loading content on demand"),
            ("Image Caching", "Efficient image loading"),
            ("Code Splitting", "Reducing initial bundle size"),
            ("Tree Shaking", "Removing unused code"),
            ("Const Constructors", "Compile-time optimizations"),
            ("RepaintBoundary", "Isolate expensive paints"),
        ],
        "platform": [
            ("Platform Channels", "Communication with native code"),
            ("Method Channel", "Invoking platform-specific APIs"),
            ("Event Channel", "Streaming data from platform"),
            ("iOS Integration", "Flutter iOS-specific features"),
            ("Android Integration", "Flutter Android-specific features"),
            ("Web Support", "Flutter web-specific features"),
            ("Desktop Support", "Flutter desktop applications"),
            ("Embedding Flutter", "Adding Flutter to existing apps"),
            ("Platform Views", "Embedding native views"),
            ("FFI", "Foreign Function Interface"),
            ("Plugin Development", "Creating Flutter plugins"),
            ("Platform-specific UI", "Adaptive UI patterns"),
        ],
        "debugging": [
            ("Flutter Inspector", "Visual debugging tool"),
            ("Logging", "Debug logging in Flutter"),
            ("Breakpoints", "Using breakpoints in Flutter"),
            ("DevTools", "Flutter DevTools suite"),
            ("Error Handling", "Handling errors in Flutter"),
            ("Crash Reporting", "Capturing and reporting crashes"),
            ("Debug Mode", "Flutter debug mode features"),
            ("Assert Statements", "Debug-only checks"),
            ("Stack Traces", "Understanding error traces"),
            ("Network Debugging", "Inspecting network requests"),
            ("Layout Explorer", "Visualize layout constraints"),
            ("Performance Overlay", "On-device performance metrics"),
        ],
        "forms": [
            ("Form", "Container for form fields"),
            ("TextFormField", "Text input with validation"),
            ("FormField", "Base class for form fields"),
            ("Form Validation", "Validating user input"),
            ("Input Decoration", "Styling form fields"),
            ("Focus Management", "Managing input focus"),
            ("Keyboard Actions", "Custom keyboard actions"),
            ("Input Formatters", "Format input as typed"),
            ("Form State", "Managing form state"),
            ("Custom Form Fields", "Creating custom inputs"),
        ],
        "theming": [
            ("ThemeData", "Application theme configuration"),
            ("Material Theme", "Material Design theming"),
            ("Dark Mode", "Supporting dark theme"),
            ("Custom Themes", "Creating custom themes"),
            ("Theme Extensions", "Extending theme data"),
            ("Color Schemes", "Material 3 color system"),
            ("Typography", "Text theming"),
            ("Dynamic Theming", "Runtime theme changes"),
            ("Platform Theming", "Platform-specific themes"),
        ],
    }
    
    # Check if query matches any concept
    for concept, items in concepts.items():
        if concept in query_lower or any(word in concept for word in query_lower.split()):
            for item_name, item_desc in items:
                results.append({
                    "type": "concept",
                    "relevance": 0.8,
                    "title": item_name,
                    "description": item_desc,
                    "concept": concept
                })
    
    # Sort results by relevance
    results.sort(key=lambda x: x["relevance"], reverse=True)
    
    # Limit to top 10 results
    results = results[:10]
    
    # Fetch actual documentation for top results if needed
    enriched_results = []
    for result in results:
        if result["type"] == "flutter_class" and "class_name" in result:
            # Only fetch full docs for top 3 Flutter classes
            if len(enriched_results) < 3:
                try:
                    doc = await get_flutter_docs(result["class_name"], result["library"])
                    if not doc.get("error"):
                        result["documentation_available"] = True
                        result["content_preview"] = doc.get("content", "")[:300] + "..."
                    else:
                        result["documentation_available"] = False
                        result["error_info"] = doc.get("error_type", "unknown")
                except Exception as e:
                    logger.warning("search_enrichment_error", error=str(e), class_name=result.get("class_name"))
                    result["documentation_available"] = False
                    result["error_info"] = "enrichment_failed"
        elif result["type"] == "pub_package" and "package_name" in result:
            # Add pub.dev URL
            result["url"] = f"https://pub.dev/packages/{result['package_name']}"
            result["documentation_available"] = True
        
        enriched_results.append(result)
    
    # Prepare final response
    response = {
        "query": query,
        "results": enriched_results,
        "total": len(enriched_results),
        "timestamp": datetime.utcnow().isoformat(),
        "suggestions": generate_search_suggestions(query_lower, enriched_results)
    }
    
    # Cache the search results for 1 hour
    cache_manager.set(cache_key, response, 3600)
    
    return response


def calculate_relevance(query: str, title: str, description: str) -> float:
    """Calculate relevance score based on fuzzy matching."""
    score = 0.0
    
    # Exact match in title
    if query == title:
        score += 1.0
    # Partial match in title
    elif query in title:
        score += 0.8
    # Word match in title
    elif any(word in title for word in query.split()):
        score += 0.6
    
    # Match in description
    if query in description:
        score += 0.4
    elif any(word in description for word in query.split() if len(word) > 3):
        score += 0.2
    
    # Fuzzy match using character overlap
    title_overlap = len(set(query) & set(title)) / len(set(query) | set(title)) if title else 0
    desc_overlap = len(set(query) & set(description)) / len(set(query) | set(description)) if description else 0
    score += (title_overlap * 0.3 + desc_overlap * 0.1)
    
    return min(score, 1.0)


def generate_search_suggestions(query: str, results: List[Dict]) -> List[str]:
    """Generate helpful search suggestions based on query and results."""
    suggestions = []
    
    if not results:
        suggestions.append(f"Try searching for specific widget names like 'Container' or 'Scaffold'")
        suggestions.append(f"Use package names from pub.dev like 'provider' or 'dio'")
        suggestions.append(f"Search for concepts like 'state management' or 'navigation'")
    elif len(results) < 3:
        suggestions.append(f"For more results, try broader terms or related concepts")
        if any(r["type"] == "flutter_class" for r in results):
            suggestions.append(f"You can also search for specific libraries like 'material.AppBar'")
    
    return suggestions


@mcp.tool()
async def process_flutter_mentions(text: str) -> Dict[str, Any]:
    """
    Parse text for @flutter_mcp mentions and return relevant documentation.
    
    Supports patterns like:
    - @flutter_mcp provider (pub.dev package)
    - @flutter_mcp material.AppBar (Flutter class)
    - @flutter_mcp dart:async.Future (Dart API)
    - @flutter_mcp Container (widget)
    
    Args:
        text: Text containing @flutter_mcp mentions
    
    Returns:
        Dictionary with parsed mentions and their documentation
    """
    bind_contextvars(tool="process_flutter_mentions", text_length=len(text))
    
    # Pattern to match @flutter_mcp mentions
    pattern = r'@flutter_mcp\s+([a-zA-Z0-9_.:]+)'
    mentions = re.findall(pattern, text)
    
    if not mentions:
        return {
            "mentions_found": 0,
            "message": "No @flutter_mcp mentions found in text",
            "results": []
        }
    
    logger.info("mentions_found", count=len(mentions))
    results = []
    
    for mention in mentions:
        logger.info("processing_mention", mention=mention)
        
        # Determine the type of mention
        if ':' in mention:
            # Dart API pattern (e.g., dart:async.Future)
            result = await search_flutter_docs(mention)
            if result.get("results"):
                results.append({
                    "mention": mention,
                    "type": "dart_api",
                    "documentation": result["results"][0]
                })
            else:
                results.append({
                    "mention": mention,
                    "type": "dart_api",
                    "error": "Documentation not found"
                })
                
        elif '.' in mention:
            # Flutter library.class pattern (e.g., material.AppBar)
            parts = mention.split('.')
            if len(parts) == 2:
                library, class_name = parts
                if library in ["material", "widgets", "cupertino"]:
                    # Flutter class
                    doc = await get_flutter_docs(class_name, library)
                    results.append({
                        "mention": mention,
                        "type": "flutter_class",
                        "documentation": doc
                    })
                else:
                    # Try as general search
                    result = await search_flutter_docs(mention)
                    if result.get("results"):
                        results.append({
                            "mention": mention,
                            "type": "flutter_search",
                            "documentation": result["results"][0]
                        })
                    else:
                        results.append({
                            "mention": mention,
                            "type": "unknown",
                            "error": "Documentation not found"
                        })
            else:
                # Invalid format
                results.append({
                    "mention": mention,
                    "type": "invalid",
                    "error": "Invalid format for library.class pattern"
                })
                
        else:
            # Single word - could be package or widget
            # First try as pub.dev package
            package_info = await get_pub_package_info(mention)
            
            if "error" not in package_info:
                results.append({
                    "mention": mention,
                    "type": "pub_package",
                    "documentation": package_info
                })
            else:
                # Try as Flutter widget/class
                search_result = await search_flutter_docs(mention)
                if search_result.get("results"):
                    results.append({
                        "mention": mention,
                        "type": "flutter_widget",
                        "documentation": search_result["results"][0]
                    })
                else:
                    results.append({
                        "mention": mention,
                        "type": "not_found",
                        "error": f"No documentation found for '{mention}' as package or Flutter class"
                    })
    
    # Format results for AI context injection
    formatted_results = []
    for result in results:
        if "error" in result:
            formatted_results.append({
                "mention": result["mention"],
                "type": result["type"],
                "error": result["error"]
            })
        else:
            doc = result["documentation"]
            if result["type"] == "pub_package":
                # Format package info
                formatted_results.append({
                    "mention": result["mention"],
                    "type": "pub_package",
                    "name": doc["name"],
                    "version": doc["version"],
                    "description": doc["description"],
                    "documentation_url": doc["documentation"],
                    "dependencies": doc.get("dependencies", []),
                    "likes": doc.get("likes", 0),
                    "pub_points": doc.get("pub_points", 0)
                })
            else:
                # Format Flutter/Dart documentation
                formatted_results.append({
                    "mention": result["mention"],
                    "type": result["type"],
                    "class": doc.get("class", ""),
                    "library": doc.get("library", ""),
                    "content": doc.get("content", ""),
                    "source": doc.get("source", "live")
                })
    
    return {
        "mentions_found": len(mentions),
        "unique_mentions": len(set(mentions)),
        "results": formatted_results,
        "timestamp": datetime.utcnow().isoformat()
    }


def clean_readme_markdown(readme_content: str) -> str:
    """Clean and format README markdown for AI consumption"""
    if not readme_content:
        return "No README available"
    
    # Remove HTML comments
    readme_content = re.sub(r'<!--.*?-->', '', readme_content, flags=re.DOTALL)
    
    # Remove excessive blank lines
    readme_content = re.sub(r'\n{3,}', '\n\n', readme_content)
    
    # Remove badges/shields (common in READMEs but not useful for AI)
    readme_content = re.sub(r'!\[.*?\]\(.*?shields\.io.*?\)', '', readme_content)
    readme_content = re.sub(r'!\[.*?\]\(.*?badge.*?\)', '', readme_content)
    
    # Clean up any remaining formatting issues
    readme_content = readme_content.strip()
    
    return readme_content


@mcp.tool()
async def get_pub_package_info(package_name: str) -> Dict[str, Any]:
    """
    Get package information from pub.dev including README content.
    
    Args:
        package_name: Name of the pub.dev package (e.g., "provider", "bloc", "dio")
    
    Returns:
        Package information including version, description, metadata, and README
    """
    bind_contextvars(tool="get_pub_package_info", package=package_name)
    
    # Check cache first
    cache_key = get_cache_key("pub_package", package_name)
    
    # Check cache
    cached_data = cache_manager.get(cache_key)
    if cached_data:
        logger.info("cache_hit")
        return cached_data
    
    # Rate limit before fetching
    await rate_limiter.acquire()
    
    # Fetch from pub.dev API
    url = f"https://pub.dev/api/packages/{package_name}"
    logger.info("fetching_package", url=url)
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Fetch package info
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Flutter-MCP-Docs/1.0 (github.com/flutter-mcp/flutter-mcp)"
                }
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant information
            latest = data.get("latest", {})
            pubspec = latest.get("pubspec", {})
            version = latest.get("version", "unknown")
            
            result = {
                "source": "live",
                "name": package_name,
                "version": version,
                "description": pubspec.get("description", "No description available"),
                "homepage": pubspec.get("homepage", ""),
                "repository": pubspec.get("repository", ""),
                "documentation": pubspec.get("documentation", f"https://pub.dev/packages/{package_name}"),
                "dependencies": list(pubspec.get("dependencies", {}).keys()),
                "dev_dependencies": list(pubspec.get("dev_dependencies", {}).keys()),
                "environment": pubspec.get("environment", {}),
                "platforms": data.get("platforms", []),
                "updated": latest.get("published", ""),
                "publisher": data.get("publisher", ""),
                "likes": data.get("likeCount", 0),
                "pub_points": data.get("pubPoints", 0),
                "popularity": data.get("popularityScore", 0)
            }
            
            # Fetch README content from package page
            readme_url = f"https://pub.dev/packages/{package_name}"
            logger.info("fetching_readme", url=readme_url)
            
            try:
                # Rate limit before second request
                await rate_limiter.acquire()
                
                readme_response = await client.get(
                    readme_url,
                    headers={
                        "User-Agent": "Flutter-MCP-Docs/1.0 (github.com/flutter-mcp/flutter-mcp)"
                    }
                )
                readme_response.raise_for_status()
                
                # Parse page HTML to extract README
                soup = BeautifulSoup(readme_response.text, 'html.parser')
                
                # Find the README content - pub.dev uses a section with specific classes
                readme_div = soup.find('section', class_='detail-tab-readme-content')
                if not readme_div:
                    # Try finding any section with markdown-body class
                    readme_div = soup.find('section', class_='markdown-body')
                    if not readme_div:
                        # Try finding div with markdown-body
                        readme_div = soup.find('div', class_='markdown-body')
                
                if readme_div:
                    # Extract text content and preserve basic markdown structure
                    # Convert common HTML elements back to markdown
                    for br in readme_div.find_all('br'):
                        br.replace_with('\n')
                    
                    for p in readme_div.find_all('p'):
                        p.insert_after('\n\n')
                    
                    for h1 in readme_div.find_all('h1'):
                        h1.insert_before('# ')
                        h1.insert_after('\n\n')
                    
                    for h2 in readme_div.find_all('h2'):
                        h2.insert_before('## ')
                        h2.insert_after('\n\n')
                    
                    for h3 in readme_div.find_all('h3'):
                        h3.insert_before('### ')
                        h3.insert_after('\n\n')
                    
                    for code in readme_div.find_all('code'):
                        if code.parent.name != 'pre':
                            code.insert_before('`')
                            code.insert_after('`')
                    
                    for pre in readme_div.find_all('pre'):
                        code_block = pre.find('code')
                        if code_block:
                            lang_class = code_block.get('class', [])
                            lang = ''
                            for cls in lang_class if isinstance(lang_class, list) else [lang_class]:
                                if cls and cls.startswith('language-'):
                                    lang = cls.replace('language-', '')
                                    break
                            pre.insert_before(f'\n```{lang}\n')
                            pre.insert_after('\n```\n')
                    
                    readme_text = readme_div.get_text()
                    result["readme"] = clean_readme_markdown(readme_text)
                else:
                    result["readme"] = "README parsing failed - content structure not recognized"
                    
            except httpx.HTTPStatusError as e:
                logger.warning("readme_fetch_failed", status_code=e.response.status_code)
                result["readme"] = f"README not available (HTTP {e.response.status_code})"
            except Exception as e:
                logger.warning("readme_fetch_error", error=str(e))
                result["readme"] = f"Failed to fetch README: {str(e)}"
            
            # Cache for 12 hours
            cache_manager.set(cache_key, result, CACHE_DURATIONS["pub_package"])
            
            logger.info("package_fetched_success", has_readme="readme" in result)
            return result
            
    except httpx.HTTPStatusError as e:
        logger.error("http_error", status_code=e.response.status_code)
        return {
            "error": f"Package '{package_name}' not found on pub.dev",
            "status_code": e.response.status_code
        }
    except Exception as e:
        logger.error("fetch_error", error=str(e))
        return {
            "error": f"Failed to fetch package information: {str(e)}"
        }


@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Check the health status of all scrapers and services.
    
    Returns:
        Health status including individual scraper checks and overall status
    """
    checks = {}
    overall_status = "ok"
    timestamp = datetime.utcnow().isoformat()
    
    # Check Flutter docs scraper
    flutter_start = time.time()
    try:
        # Test with Container widget - a stable, core widget unlikely to be removed
        result = await get_flutter_docs("Container", "widgets")
        flutter_duration = int((time.time() - flutter_start) * 1000)
        
        if "error" in result:
            checks["flutter_docs"] = {
                "status": "failed",
                "target": "Container widget",
                "duration_ms": flutter_duration,
                "error": result["error"]
            }
            overall_status = "degraded"
        else:
            checks["flutter_docs"] = {
                "status": "ok",
                "target": "Container widget",
                "duration_ms": flutter_duration,
                "cached": result.get("source") == "cache"
            }
    except Exception as e:
        flutter_duration = int((time.time() - flutter_start) * 1000)
        checks["flutter_docs"] = {
            "status": "failed",
            "target": "Container widget",
            "duration_ms": flutter_duration,
            "error": str(e)
        }
        overall_status = "failed"
    
    # Check pub.dev scraper
    pub_start = time.time()
    try:
        # Test with provider package - extremely popular, unlikely to be removed
        result = await get_pub_package_info("provider")
        pub_duration = int((time.time() - pub_start) * 1000)
        
        if result is None:
            checks["pub_dev"] = {
                "status": "timeout",
                "target": "provider package",
                "duration_ms": pub_duration,
                "error": "Health check timed out after 10 seconds"
            }
            overall_status = "degraded" if overall_status == "ok" else overall_status
        elif result.get("error"):
            checks["pub_dev"] = {
                "status": "failed",
                "target": "provider package",
                "duration_ms": pub_duration,
                "error": result.get("message", "Unknown error"),
                "error_type": result.get("error_type", "unknown")
            }
            overall_status = "degraded" if overall_status == "ok" else overall_status
        else:
            # Additional validation - check if we got expected fields
            has_version = "version" in result and result["version"] != "unknown"
            has_readme = "readme" in result and len(result.get("readme", "")) > 100
            
            if not has_version:
                checks["pub_dev"] = {
                    "status": "degraded",
                    "target": "provider package",
                    "duration_ms": pub_duration,
                    "error": "Could not parse version information",
                    "cached": result.get("source") == "cache"
                }
                overall_status = "degraded" if overall_status == "ok" else overall_status
            elif not has_readme:
                checks["pub_dev"] = {
                    "status": "degraded",
                    "target": "provider package",
                    "duration_ms": pub_duration,
                    "error": "Could not parse README content",
                    "cached": result.get("source") == "cache"
                }
                overall_status = "degraded" if overall_status == "ok" else overall_status
            else:
                checks["pub_dev"] = {
                    "status": "ok",
                    "target": "provider package",
                    "duration_ms": pub_duration,
                    "version": result["version"],
                    "cached": result.get("source") == "cache"
                }
    except Exception as e:
        pub_duration = int((time.time() - pub_start) * 1000)
        checks["pub_dev"] = {
            "status": "failed",
            "target": "provider package",
            "duration_ms": pub_duration,
            "error": str(e)
        }
        overall_status = "failed" if overall_status == "failed" else "degraded"
    
    # Check cache status
    try:
        cache_stats = cache_manager.get_stats()
        checks["cache"] = {
            "status": "ok",
            "message": "SQLite cache operational",
            "stats": cache_stats
        }
    except Exception as e:
        checks["cache"] = {
            "status": "degraded",
            "message": "Cache error",
            "error": str(e)
        }
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "timestamp": timestamp,
        "checks": checks,
        "message": get_health_message(overall_status)
    }


def get_health_message(status: str) -> str:
    """Get a human-readable message for the health status"""
    messages = {
        "ok": "All systems operational",
        "degraded": "Service degraded - some features may be slow or unavailable",
        "failed": "Service failed - critical components are not working"
    }
    return messages.get(status, "Unknown status")


def main():
    """Main entry point for the Flutter MCP server"""
    # When running from CLI, the header is already printed
    # Only log when not running from CLI (e.g., direct execution)
    if not hasattr(sys, '_flutter_mcp_cli'):
        logger.info("flutter_mcp_starting", version="0.1.0")
    
    # Initialize cache and show stats
    try:
        cache_stats = cache_manager.get_stats()
        logger.info("cache_ready", stats=cache_stats)
    except Exception as e:
        logger.warning("cache_initialization_warning", error=str(e))
    
    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()