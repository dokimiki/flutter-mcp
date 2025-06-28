# Token Counting Analysis for Flutter MCP

## Executive Summary

For the Flutter MCP documentation server, implementing accurate and performant token counting is crucial to ensure responses fit within LLM context windows. This analysis recommends using model-specific tokenizers with intelligent caching for optimal accuracy and performance.

## Recommended Approach

### Primary Strategy: Model-Specific Tokenizers with Caching

Use official tokenizers for each supported model family:
- **OpenAI Models**: `tiktoken` library
- **Claude Models**: `anthropic` library's `count_tokens()` API
- **Gemini Models**: `google-genai` library's `count_tokens()` method

### Implementation Architecture

```python
# utils/token_counter.py
import tiktoken
import anthropic
from google import genai
from google.genai.types import HttpOptions
from typing import Union, Dict, Any
import structlog

logger = structlog.get_logger()

class TokenCounter:
    """Unified token counter with model-specific tokenizer support."""
    
    def __init__(self):
        self._tokenizer_cache: Dict[str, Any] = {}
        self._anthropic_client = None
        self._genai_client = None
        
    def _get_openai_tokenizer(self, model: str):
        """Get or create OpenAI tokenizer."""
        if model not in self._tokenizer_cache:
            try:
                # Try model-specific encoding
                self._tokenizer_cache[model] = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to cl100k_base for newer models
                self._tokenizer_cache[model] = tiktoken.get_encoding("cl100k_base")
        return self._tokenizer_cache[model]
    
    def _get_anthropic_client(self):
        """Get or create Anthropic client."""
        if self._anthropic_client is None:
            self._anthropic_client = anthropic.Anthropic()
        return self._anthropic_client
    
    def _get_genai_client(self):
        """Get or create Google GenAI client."""
        if self._genai_client is None:
            self._genai_client = genai.Client(
                http_options=HttpOptions(api_version="v1")
            )
        return self._genai_client
    
    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """
        Count tokens for the given text and model.
        
        Args:
            text: The text to count tokens for
            model: The model name (e.g., "gpt-4", "claude-3-opus", "gemini-1.5-pro")
            
        Returns:
            Number of tokens
        """
        try:
            # OpenAI models
            if model.startswith(("gpt-", "text-embedding-")):
                tokenizer = self._get_openai_tokenizer(model)
                return len(tokenizer.encode(text))
            
            # Claude models
            elif model.startswith("claude-"):
                client = self._get_anthropic_client()
                response = client.beta.messages.count_tokens(
                    model=model,
                    messages=[{"role": "user", "content": text}]
                )
                return response.input_tokens
            
            # Gemini models
            elif model.startswith("gemini-"):
                client = self._get_genai_client()
                response = client.models.count_tokens(
                    model=model,
                    contents=text
                )
                return response.total_tokens
            
            # Unknown model - use cl100k_base as fallback
            else:
                logger.warning(f"Unknown model {model}, using cl100k_base tokenizer")
                tokenizer = self._get_openai_tokenizer("cl100k_base")
                return len(tokenizer.encode(text))
                
        except Exception as e:
            logger.error(f"Error counting tokens for {model}: {e}")
            # Fallback to character-based approximation with safety margin
            return int(len(text) / 3.5)  # Conservative estimate

# Global instance for reuse
token_counter = TokenCounter()
```

## Performance Optimization Strategies

### 1. Tokenizer Caching
- **Critical**: Cache tokenizer instances to avoid initialization overhead
- OpenAI's `tiktoken` has minimal overhead, but still benefits from caching
- Anthropic and Google clients should be singleton instances

### 2. Batch Processing
When processing multiple documents:
```python
# For tiktoken (OpenAI)
encoding = tiktoken.get_encoding("cl100k_base")
token_counts = [len(tokens) for tokens in encoding.encode_batch(texts)]

# For other providers, implement parallel processing
from concurrent.futures import ThreadPoolExecutor

def batch_count_tokens(texts: List[str], model: str) -> List[int]:
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(token_counter.count_tokens, text, model) 
                   for text in texts]
        return [future.result() for future in futures]
```

### 3. Redis Integration for Token Count Caching
```python
async def get_documentation_with_token_count(
    self, 
    query: str, 
    model: str = "gpt-4"
) -> Tuple[str, int]:
    """Get documentation with pre-calculated token count."""
    
    # Check Redis for cached result with token count
    cache_key = f"flutter_doc:{query}:{model}"
    cached = await self.redis.get(cache_key)
    
    if cached:
        data = json.loads(cached)
        return data["content"], data["token_count"]
    
    # Fetch and process documentation
    content = await self.fetch_documentation(query)
    
    # Count tokens on final formatted content
    token_count = token_counter.count_tokens(content, model)
    
    # Cache with token count
    await self.redis.set(
        cache_key,
        json.dumps({
            "content": content,
            "token_count": token_count
        }),
        ex=86400  # 24 hour TTL
    )
    
    return content, token_count
```

## Markdown Formatting Considerations

### Count Tokens on Final Output
Always count tokens on the exact string sent to the LLM:

```python
def prepare_response(raw_content: str, max_tokens: int, model: str) -> str:
    """Prepare and truncate response to fit token limit."""
    
    # Apply all formatting transformations
    formatted_content = format_markdown(raw_content)
    
    # Count tokens on formatted content
    token_count = token_counter.count_tokens(formatted_content, model)
    
    # Truncate if necessary
    if token_count > max_tokens:
        # Intelligent truncation - keep complete sections
        formatted_content = truncate_intelligently(
            formatted_content, 
            max_tokens, 
            model
        )
    
    return formatted_content
```

### Token Impact of Markdown Elements
- **Code blocks**: Very token-intensive (backticks + language + indentation)
- **Links**: Full markdown syntax counts `[text](url)`
- **Headers**: All `#` characters count as tokens
- **Lists**: Bullets and indentation consume tokens

## Approximation Methods (Fallback Only)

When model-specific tokenizers are unavailable:

```python
def approximate_tokens(text: str, model_family: str = "general") -> int:
    """
    Approximate token count with model-specific adjustments.
    Use only as fallback when proper tokenizers unavailable.
    """
    # Base approximations
    char_ratio = {
        "gpt": 4.0,      # GPT models: ~4 chars/token
        "claude": 3.8,   # Claude: slightly more tokens
        "gemini": 4.2,   # Gemini: slightly fewer tokens
        "general": 3.5   # Conservative default
    }
    
    ratio = char_ratio.get(model_family, 3.5)
    base_count = len(text) / ratio
    
    # Adjust for code content (more tokens)
    code_blocks = text.count("```")
    if code_blocks > 0:
        base_count *= 1.15
    
    # Safety margin
    return int(base_count * 1.2)
```

## Implementation Timeline

### Phase 1: Core Implementation (2 hours)
1. Implement `TokenCounter` class with OpenAI support
2. Add fallback approximation method
3. Integrate with existing response pipeline

### Phase 2: Multi-Model Support (2 hours)
1. Add Anthropic client support
2. Add Google GenAI client support
3. Implement model detection logic

### Phase 3: Optimization (1 hour)
1. Add Redis caching for token counts
2. Implement batch processing
3. Add performance monitoring

## Testing Strategy

```python
# tests/test_token_counter.py
import pytest
from utils.token_counter import token_counter

class TestTokenCounter:
    
    @pytest.mark.parametrize("model,text,expected_range", [
        ("gpt-4", "Hello, world!", (3, 5)),
        ("claude-3-opus-20240229", "Hello, world!", (3, 5)),
        ("gemini-1.5-pro", "Hello, world!", (3, 5)),
    ])
    def test_basic_counting(self, model, text, expected_range):
        count = token_counter.count_tokens(text, model)
        assert expected_range[0] <= count <= expected_range[1]
    
    def test_markdown_formatting(self):
        markdown = "# Header\n```python\nprint('hello')\n```"
        count = token_counter.count_tokens(markdown, "gpt-4")
        # Markdown should produce more tokens than plain text
        plain_count = token_counter.count_tokens("Header print hello", "gpt-4")
        assert count > plain_count
    
    def test_fallback_approximation(self):
        # Test with unknown model
        count = token_counter.count_tokens("Test text", "unknown-model")
        assert count > 0
```

## Recommendations

1. **Use Model-Specific Tokenizers**: Accuracy is worth the minimal performance cost
2. **Cache Everything**: Both tokenizer instances and token counts
3. **Count Final Output**: Always count tokens on the exact formatted string
4. **Plan for Growth**: Design the system to easily add new model support
5. **Monitor Performance**: Track token counting time in your metrics

## Conclusion

For the Flutter MCP project, implementing proper token counting with model-specific tokenizers will ensure accurate context window management while maintaining the fast response times required by the Context7-style architecture. The recommended approach balances accuracy, performance, and maintainability while providing graceful fallbacks for edge cases.