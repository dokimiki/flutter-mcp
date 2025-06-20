"""
Error handling utilities for Flutter MCP Server.

This module provides comprehensive error handling, retry logic, and user-friendly
error responses for the Flutter documentation server.
"""

import asyncio
import random
import time
from typing import Optional, Dict, List, Any, Callable
from functools import wraps
import httpx
import structlog

logger = structlog.get_logger()

# Error handling constants
MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 16.0  # seconds
DEFAULT_TIMEOUT = 30.0  # seconds
CONNECTION_TIMEOUT = 10.0  # seconds


class NetworkError(Exception):
    """Custom exception for network-related errors"""
    pass


class DocumentationNotFoundError(Exception):
    """Custom exception when documentation is not found"""
    pass


class RateLimitError(Exception):
    """Custom exception for rate limit violations"""
    pass


class CacheError(Exception):
    """Custom exception for cache-related errors"""
    pass


def calculate_backoff_delay(attempt: int) -> float:
    """Calculate exponential backoff delay with jitter."""
    delay = min(
        BASE_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1),
        MAX_RETRY_DELAY
    )
    return delay


def with_retry(max_retries: int = MAX_RETRIES, retry_on: tuple = None):
    """
    Decorator for adding retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_on: Tuple of exception types to retry on (default: network errors)
    """
    if retry_on is None:
        retry_on = (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = calculate_backoff_delay(attempt)
                        logger.warning(
                            "retrying_request",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            delay=delay,
                            error=str(e),
                            error_type=type(e).__name__
                        )
                        await asyncio.sleep(delay)
                    else:
                        raise NetworkError(
                            f"Network error after {max_retries} attempts: {str(e)}"
                        ) from e
                except httpx.HTTPStatusError as e:
                    # Don't retry on 4xx errors (client errors)
                    if 400 <= e.response.status_code < 500:
                        raise
                    # Retry on 5xx errors (server errors)
                    last_exception = e
                    if attempt < max_retries - 1 and e.response.status_code >= 500:
                        delay = calculate_backoff_delay(attempt)
                        logger.warning(
                            "retrying_server_error",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            delay=delay,
                            status_code=e.response.status_code
                        )
                        await asyncio.sleep(delay)
                    else:
                        raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


async def safe_http_get(
    url: str, 
    headers: Optional[Dict] = None, 
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES
) -> httpx.Response:
    """
    Safely perform HTTP GET request with proper error handling and retries.
    
    Args:
        url: URL to fetch
        headers: Optional HTTP headers
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        HTTP response object
        
    Raises:
        NetworkError: For network-related failures after retries
        httpx.HTTPStatusError: For HTTP errors
    """
    if headers is None:
        headers = {}
    
    headers.setdefault(
        "User-Agent",
        "Flutter-MCP-Docs/1.0 (github.com/flutter-mcp/flutter-mcp)"
    )
    
    @with_retry(max_retries=max_retries)
    async def _get():
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=CONNECTION_TIMEOUT),
            follow_redirects=True,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        ) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response
    
    return await _get()


def format_error_response(
    error_type: str, 
    message: str, 
    suggestions: Optional[List[str]] = None, 
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Format consistent error responses with helpful information.
    
    Args:
        error_type: Type of error (e.g., "not_found", "network_error")
        message: Human-readable error message
        suggestions: List of helpful suggestions for the user
        context: Additional context information
        
    Returns:
        Formatted error response dictionary
    """
    from datetime import datetime
    
    response = {
        "error": True,
        "error_type": error_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if suggestions:
        response["suggestions"] = suggestions
    
    if context:
        response["context"] = context
    
    return response


def get_error_suggestions(error_type: str, context: Dict = None) -> List[str]:
    """
    Get context-aware suggestions based on error type.
    
    Args:
        error_type: Type of error
        context: Error context (e.g., class name, library, etc.)
        
    Returns:
        List of helpful suggestions
    """
    suggestions_map = {
        "not_found": [
            "Check if the name is spelled correctly",
            "Verify that the item exists in the specified library",
            "Try searching with search_flutter_docs() for similar items",
            "Common libraries: widgets, material, cupertino, painting, rendering"
        ],
        "network_error": [
            "Check your internet connection",
            "The documentation server may be temporarily unavailable",
            "Try again in a few moments",
            "Check if you can access https://api.flutter.dev in your browser"
        ],
        "timeout": [
            "The server is taking too long to respond",
            "Try again with a simpler query",
            "The documentation server might be under heavy load",
            "Check https://status.flutter.dev/ for service status"
        ],
        "rate_limited": [
            "You've made too many requests in a short time",
            "Wait a few minutes before retrying",
            "Consider implementing local caching for frequently accessed docs",
            "Space out your requests to avoid rate limits"
        ],
        "parse_error": [
            "The documentation format may have changed",
            "Try using a different query format",
            "Report this issue if it persists",
            "The server response was not in the expected format"
        ],
        "cache_error": [
            "The local cache encountered an error",
            "The request will proceed without caching",
            "Consider restarting the server if this persists",
            "Check disk space and permissions for the cache directory"
        ]
    }
    
    base_suggestions = suggestions_map.get(error_type, [
        "An unexpected error occurred",
        "Please try again",
        "If the problem persists, check the server logs"
    ])
    
    # Add context-specific suggestions
    if context:
        if "class" in context and "library" in context:
            base_suggestions.insert(0, 
                f"Verify '{context['class']}' exists in the '{context['library']}' library"
            )
        elif "package" in context:
            base_suggestions.insert(0,
                f"Verify package name '{context['package']}' is correct"
            )
    
    return base_suggestions


async def with_error_handling(
    operation: Callable,
    operation_name: str,
    context: Dict = None,
    fallback_value: Any = None
) -> Any:
    """
    Execute an operation with comprehensive error handling.
    
    Args:
        operation: Async callable to execute
        operation_name: Name of the operation for logging
        context: Context information for error messages
        fallback_value: Value to return on error (if None, error is returned)
        
    Returns:
        Operation result or error response
    """
    try:
        return await operation()
    
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        logger.error(
            f"{operation_name}_http_error",
            status_code=status_code,
            url=str(e.request.url),
            **context or {}
        )
        
        if status_code == 404:
            error_type = "not_found"
            message = f"Resource not found (HTTP 404)"
        elif status_code == 429:
            error_type = "rate_limited"
            message = "Rate limit exceeded"
        elif 500 <= status_code < 600:
            error_type = "server_error"
            message = f"Server error (HTTP {status_code})"
        else:
            error_type = "http_error"
            message = f"HTTP error {status_code}"
        
        suggestions = get_error_suggestions(error_type, context)
        
        if fallback_value is not None:
            return fallback_value
        
        return format_error_response(
            error_type,
            message,
            suggestions=suggestions,
            context={
                **(context or {}),
                "status_code": status_code,
                "url": str(e.request.url)
            }
        )
    
    except NetworkError as e:
        logger.error(
            f"{operation_name}_network_error",
            error=str(e),
            **context or {}
        )
        
        if fallback_value is not None:
            return fallback_value
        
        return format_error_response(
            "network_error",
            "Network connection error",
            suggestions=get_error_suggestions("network_error"),
            context=context
        )
    
    except asyncio.TimeoutError:
        logger.error(
            f"{operation_name}_timeout",
            **context or {}
        )
        
        if fallback_value is not None:
            return fallback_value
        
        return format_error_response(
            "timeout",
            "Request timed out",
            suggestions=get_error_suggestions("timeout"),
            context={
                **(context or {}),
                "timeout": DEFAULT_TIMEOUT
            }
        )
    
    except Exception as e:
        logger.error(
            f"{operation_name}_unexpected_error",
            error=str(e),
            error_type=type(e).__name__,
            **context or {}
        )
        
        if fallback_value is not None:
            return fallback_value
        
        return format_error_response(
            "unexpected_error",
            f"An unexpected error occurred: {str(e)}",
            suggestions=[
                "This is an unexpected error",
                "Please try again",
                "If the problem persists, report it with the error details"
            ],
            context={
                **(context or {}),
                "error_type": type(e).__name__
            }
        )


class CircuitBreaker:
    """
    Circuit breaker pattern for handling repeated failures.
    
    Prevents cascading failures by temporarily disabling operations
    that are consistently failing.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                logger.info("circuit_breaker_half_open", function=func.__name__)
            else:
                raise NetworkError("Circuit breaker is OPEN - service temporarily disabled")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("circuit_breaker_closed", function=func.__name__)
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    "circuit_breaker_open",
                    function=func.__name__,
                    failure_count=self.failure_count
                )
            
            raise