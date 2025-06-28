"""Token counting module for Flutter MCP server.

Provides both approximate and accurate token counting methods with
configurable behavior via environment variables.
"""

import os
import re
from typing import Optional, Union
import structlog

logger = structlog.get_logger(__name__)


class TokenManager:
    """Manages token counting with both approximation and accurate methods."""
    
    # Average tokens per word based on empirical observations
    TOKENS_PER_WORD = 1.3
    
    # Word splitting pattern
    WORD_PATTERN = re.compile(r'\b\w+\b')
    
    def __init__(self):
        """Initialize the TokenManager."""
        self._tiktoken = None
        self._encoder = None
        self._accurate_mode = self._get_accurate_mode()
        
        logger.info(
            "TokenManager initialized",
            accurate_mode=self._accurate_mode
        )
    
    def _get_accurate_mode(self) -> bool:
        """Check if accurate token counting is enabled via environment variable."""
        env_value = os.environ.get('FLUTTER_MCP_ACCURATE_TOKENS', 'false').lower()
        return env_value in ('true', '1', 'yes', 'on')
    
    def _ensure_tiktoken(self) -> bool:
        """Lazy load tiktoken if needed and available.
        
        Returns:
            bool: True if tiktoken is available, False otherwise.
        """
        if self._tiktoken is None:
            try:
                import tiktoken
                self._tiktoken = tiktoken
                # Use cl100k_base encoding (used by GPT-3.5/GPT-4)
                self._encoder = tiktoken.get_encoding("cl100k_base")
                logger.info("Tiktoken loaded successfully")
                return True
            except ImportError:
                logger.warning(
                    "Tiktoken not available, falling back to approximation",
                    hint="Install with: pip install tiktoken"
                )
                return False
        return True
    
    def approximate_tokens(self, text: str) -> int:
        """Approximate token count using word-based estimation.
        
        This method is fast and doesn't require external dependencies.
        Uses a simple heuristic of 1.3 tokens per word.
        
        Args:
            text: The text to count tokens for.
            
        Returns:
            int: Approximate number of tokens.
        """
        if not text:
            return 0
        
        # Count words using regex pattern
        words = self.WORD_PATTERN.findall(text)
        word_count = len(words)
        
        # Apply multiplier for approximation
        token_count = int(word_count * self.TOKENS_PER_WORD)
        
        logger.debug(
            "Approximate token count",
            word_count=word_count,
            token_count=token_count,
            text_length=len(text)
        )
        
        return token_count
    
    def accurate_tokens(self, text: str) -> Optional[int]:
        """Count tokens accurately using tiktoken.
        
        This method requires the tiktoken library to be installed.
        It provides exact token counts but is slower than approximation.
        
        Args:
            text: The text to count tokens for.
            
        Returns:
            Optional[int]: Exact number of tokens, or None if tiktoken unavailable.
        """
        if not text:
            return 0
        
        if not self._ensure_tiktoken():
            return None
        
        try:
            tokens = self._encoder.encode(text)
            token_count = len(tokens)
            
            logger.debug(
                "Accurate token count",
                token_count=token_count,
                text_length=len(text)
            )
            
            return token_count
        except Exception as e:
            logger.error(
                "Error counting tokens with tiktoken",
                error=str(e),
                text_length=len(text)
            )
            return None
    
    def count_tokens(self, text: str, force_accurate: bool = False) -> int:
        """Count tokens using the configured method.
        
        By default, uses the method configured via FLUTTER_MCP_ACCURATE_TOKENS
        environment variable. Can be overridden with force_accurate parameter.
        
        Args:
            text: The text to count tokens for.
            force_accurate: Force accurate counting regardless of configuration.
            
        Returns:
            int: Number of tokens (approximate or accurate based on configuration).
        """
        if not text:
            return 0
        
        # Determine which method to use
        use_accurate = force_accurate or self._accurate_mode
        
        if use_accurate:
            # Try accurate counting first
            accurate_count = self.accurate_tokens(text)
            if accurate_count is not None:
                return accurate_count
            
            # Fall back to approximation if accurate counting fails
            logger.info(
                "Falling back to approximation",
                reason="Accurate counting failed or unavailable"
            )
        
        # Use approximation
        return self.approximate_tokens(text)
    
    def set_accurate_mode(self, enabled: bool) -> None:
        """Dynamically enable or disable accurate token counting.
        
        Args:
            enabled: Whether to use accurate token counting.
        """
        self._accurate_mode = enabled
        logger.info(
            "Token counting mode changed",
            accurate_mode=enabled
        )
    
    def get_mode(self) -> str:
        """Get the current token counting mode.
        
        Returns:
            str: 'accurate' if using tiktoken, 'approximate' otherwise.
        """
        return 'accurate' if self._accurate_mode else 'approximate'
    
    def estimate_cost(
        self, 
        token_count: int, 
        cost_per_1k_tokens: float = 0.002
    ) -> float:
        """Estimate cost based on token count.
        
        Args:
            token_count: Number of tokens.
            cost_per_1k_tokens: Cost per 1000 tokens (default: $0.002).
            
        Returns:
            float: Estimated cost in dollars.
        """
        return (token_count / 1000) * cost_per_1k_tokens


# Module-level instance for convenience
_token_manager = TokenManager()

# Expose main methods at module level
approximate_tokens = _token_manager.approximate_tokens
accurate_tokens = _token_manager.accurate_tokens
count_tokens = _token_manager.count_tokens
set_accurate_mode = _token_manager.set_accurate_mode
get_mode = _token_manager.get_mode
estimate_cost = _token_manager.estimate_cost


def get_token_manager() -> TokenManager:
    """Get the singleton TokenManager instance.
    
    Returns:
        TokenManager: The module-level token manager instance.
    """
    return _token_manager