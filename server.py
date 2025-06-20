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
import redis
from bs4 import BeautifulSoup
import structlog
from structlog.contextvars import bind_contextvars

# Initialize structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)
logger = structlog.get_logger()

# Initialize FastMCP server
mcp = FastMCP("Flutter Docs Server")

# Redis client for caching (Context7-style)
try:
    redis_client = redis.Redis(
        host='localhost', 
        port=6379, 
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()
    logger.info("redis_connected", host="localhost", port=6379)
except Exception as e:
    logger.warning("redis_connection_failed", error=str(e))
    redis_client = None


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
        r"^dart:core\.(\w+)$": "https://api.dart.dev/stable/dart-core/{0}-class.html",
        r"^dart:async\.(\w+)$": "https://api.dart.dev/stable/dart-async/{0}-class.html",
        r"^dart:collection\.(\w+)$": "https://api.dart.dev/stable/dart-collection/{0}-class.html",
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
    
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info("cache_hit")
                return {
                    "source": "cache",
                    "class": class_name,
                    "library": library,
                    "content": cached,
                    "cached_at": redis_client.ttl(cache_key)
                }
        except Exception as e:
            logger.warning("cache_read_error", error=str(e))
    
    # Rate-limited fetch from Flutter docs
    await rate_limiter.acquire()
    
    url = f"https://api.flutter.dev/flutter/{library}/{class_name}-class.html"
    logger.info("fetching_docs", url=url)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Flutter-MCP-Docs/1.0 (github.com/flutter-mcp/flutter-mcp)"
                }
            )
            response.raise_for_status()
            
            # Process HTML - Context7 style pipeline
            content = await process_documentation(response.text, class_name)
            
            # Cache for 24 hours
            if redis_client:
                try:
                    redis_client.setex(
                        cache_key, 
                        CACHE_DURATIONS["flutter_api"], 
                        content
                    )
                except Exception as e:
                    logger.warning("cache_write_error", error=str(e))
            
            logger.info("docs_fetched_success", content_length=len(content))
            
            return {
                "source": "live",
                "class": class_name,
                "library": library,
                "content": content,
                "fetched_at": datetime.utcnow().isoformat()
            }
            
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
    Search across Flutter/Dart documentation sources.
    
    Args:
        query: Search query (e.g., "Container", "material.AppBar", "dart:core.List")
    
    Returns:
        Search results with documentation content
    """
    bind_contextvars(tool="search_flutter_docs", query=query)
    logger.info("searching_docs")
    
    results = []
    
    # Try direct URL resolution first
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
                results.append(doc)
    
    # If no direct match, try common variations
    if not results:
        # Try as widget
        doc = await get_flutter_docs(query, "widgets")
        if "error" not in doc:
            results.append(doc)
        
        # Try as material widget
        doc = await get_flutter_docs(query, "material")
        if "error" not in doc:
            results.append(doc)
    
    return {
        "query": query,
        "results": results,
        "total": len(results),
        "timestamp": datetime.utcnow().isoformat()
    }


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
    
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info("cache_hit")
                return json.loads(cached)
        except Exception as e:
            logger.warning("cache_read_error", error=str(e))
    
    # Rate limit before fetching
    await rate_limiter.acquire()
    
    # Fetch from pub.dev API
    url = f"https://pub.dev/api/packages/{package_name}"
    logger.info("fetching_package", url=url)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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
            if redis_client:
                try:
                    redis_client.setex(
                        cache_key,
                        CACHE_DURATIONS["pub_package"],
                        json.dumps(result)
                    )
                except Exception as e:
                    logger.warning("cache_write_error", error=str(e))
            
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
        
        if "error" in result:
            checks["pub_dev"] = {
                "status": "failed",
                "target": "provider package",
                "duration_ms": pub_duration,
                "error": result["error"]
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
    
    # Check Redis connection
    if redis_client:
        try:
            redis_client.ping()
            checks["redis"] = {
                "status": "ok",
                "message": "Redis connection healthy"
            }
        except Exception as e:
            checks["redis"] = {
                "status": "degraded",
                "message": "Redis not available - running without cache",
                "error": str(e)
            }
    else:
        checks["redis"] = {
            "status": "degraded",
            "message": "Redis not configured - running without cache"
        }
    
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
    logger.info("flutter_mcp_starting", version="0.1.0")
    
    # Test Redis connection
    if not redis_client:
        logger.warning("running_without_cache", 
                      message="Redis not available. Running without cache - responses will be slower.")
    
    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()