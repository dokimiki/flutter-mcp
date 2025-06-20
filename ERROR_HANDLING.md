# Flutter MCP Server - Error Handling & Resilience

This document describes the comprehensive error handling and resilience features implemented in the Flutter MCP Server.

## Overview

The Flutter MCP Server is designed to be highly resilient and provide a good user experience even when external services are unavailable or experiencing issues. The server implements multiple layers of error handling, retry logic, and graceful degradation.

## Error Handling Features

### 1. Retry Logic with Exponential Backoff

All HTTP requests implement automatic retry with exponential backoff:

- **Max retries**: 3 attempts
- **Base delay**: 1 second
- **Max delay**: 16 seconds
- **Jitter**: Random 0-1 second added to prevent thundering herd
- **Smart retries**: Only retries on network errors and 5xx server errors, not 4xx client errors

```python
@with_retry(max_retries=3)
async def fetch_data():
    # Automatic retry on network failures
    pass
```

### 2. Comprehensive Error Types

The server categorizes errors for better handling:

- `NetworkError`: Connection failures, timeouts
- `DocumentationNotFoundError`: Resource not found (404)
- `RateLimitError`: Rate limit exceeded (429)
- `CacheError`: Cache operation failures

### 3. User-Friendly Error Responses

All errors return structured responses with:

```json
{
  "error": true,
  "error_type": "not_found",
  "message": "Documentation not found for widgets.NonExistentWidget",
  "suggestions": [
    "Check if 'NonExistentWidget' is spelled correctly",
    "Verify that 'NonExistentWidget' exists in the 'widgets' library",
    "Common libraries: widgets, material, cupertino, painting, rendering",
    "Try searching with: search_flutter_docs('NonExistentWidget')"
  ],
  "context": {
    "class": "NonExistentWidget",
    "library": "widgets",
    "status_code": 404
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### 4. Circuit Breaker Pattern

Prevents cascading failures when external services are down:

- **Failure threshold**: 5 consecutive failures
- **Recovery timeout**: 60 seconds
- **States**: CLOSED (normal), OPEN (failing), HALF-OPEN (testing)

```python
flutter_docs_circuit = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0
)
```

### 5. Graceful Degradation

The server continues operating even when some components fail:

- **Cache failures**: Continue without caching
- **README fetch failures**: Return package info without README
- **Enrichment failures**: Return search results without full documentation

### 6. Health Monitoring

Comprehensive health check system:

```python
# Health check with timeout protection
async def health_check():
    # Tests Flutter docs API
    # Tests pub.dev API  
    # Tests cache functionality
    # Returns detailed status for each component
```

### 7. Timeout Protection

All operations have configurable timeouts:

- **Default timeout**: 30 seconds
- **Connection timeout**: 10 seconds
- **Health check timeout**: 10 seconds

### 8. Rate Limiting

Respectful rate limiting for external APIs:

- **Default rate**: 2 requests/second
- **Adjustable during high load**
- **Per-service rate limiters**

## Error Scenarios Handled

### Network Errors

- Connection timeouts
- DNS resolution failures
- Connection refused
- Network unreachable

**User Experience**: Clear message about network issues with retry suggestions

### API Errors

- 404 Not Found: Helpful suggestions for correct names/formats
- 429 Rate Limited: Advises waiting and provides retry timing
- 500-599 Server Errors: Indicates external service issues
- Invalid responses: Handles malformed JSON/HTML

### Input Validation

- Invalid class names
- Invalid package names (must be lowercase with underscores)
- Malformed queries
- Empty inputs

### Cache Errors

- Cache initialization failures: Falls back to no-cache mode
- Cache read/write errors: Logged but don't fail requests
- Corrupted cache entries: Automatic cleanup

## Testing Error Handling

Run the error handling test suite:

```bash
python test_error_handling.py
```

This tests:
1. Invalid Flutter class names
2. Invalid library names
3. Non-existent packages
4. Invalid package name formats
5. Search with no results
6. Mention processing with errors
7. Health check functionality
8. Graceful degradation

## Logging

Structured logging with contextual information:

```python
logger.error(
    "http_error",
    status_code=404,
    url="https://api.flutter.dev/...",
    class_name="NonExistentWidget",
    library="widgets"
)
```

## Recovery Mechanisms

### Automatic Recovery

1. **Cache clearing**: After 3 consecutive failures
2. **Connection pool reset**: After 5 consecutive failures  
3. **Rate limit reduction**: After 7 consecutive failures

### Manual Recovery

- Restart server to reset all circuit breakers
- Clear cache directory to remove corrupted data
- Check logs for specific error patterns

## Best Practices

1. **Always check for errors** in responses:
   ```python
   result = await get_flutter_docs("Widget", "widgets")
   if result.get("error"):
       # Handle error
   ```

2. **Use suggestions** provided in error responses
3. **Implement backoff** when seeing rate limit errors
4. **Monitor health endpoint** for service status

## Configuration

Error handling can be configured via environment variables:

```bash
# Retry configuration
MAX_RETRIES=3
BASE_RETRY_DELAY=1.0
MAX_RETRY_DELAY=16.0

# Timeout configuration  
DEFAULT_TIMEOUT=30.0
CONNECTION_TIMEOUT=10.0

# Circuit breaker
FAILURE_THRESHOLD=5
RECOVERY_TIMEOUT=60.0

# Rate limiting
REQUESTS_PER_SECOND=2.0
```

## Monitoring

Monitor these metrics for service health:

- Error rates by type
- Circuit breaker state changes
- Cache hit/miss rates
- Response times
- Retry counts

## Future Improvements

- [ ] Implement request queuing during rate limits
- [ ] Add fallback to cached documentation during outages
- [ ] Implement progressive retry delays based on error type
- [ ] Add webhook notifications for circuit breaker state changes
- [ ] Implement request deduplication