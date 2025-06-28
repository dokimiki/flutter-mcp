"""Tests for token management functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flutter_mcp.token_manager import TokenManager
from flutter_mcp.truncation import DocumentTruncator
from flutter_mcp.server import process_documentation
import json


class TestTokenManager:
    """Test TokenManager functionality."""
    
    def test_approximate_tokens(self):
        """Test word-based token approximation."""
        manager = TokenManager()
        
        # Test various text samples
        assert manager.approximate_tokens("Hello world") == 2  # 2 words * 1.3 = 2.6 -> 2
        assert manager.approximate_tokens("The quick brown fox") == 5  # 4 * 1.3 = 5.2 -> 5
        assert manager.approximate_tokens("") == 0
        assert manager.approximate_tokens("   ") == 0
        
        # Test with punctuation and special characters
        text = "Hello, world! How are you?"
        expected = int(5 * 1.3)  # 5 words
        assert manager.approximate_tokens(text) == expected
    
    def test_count_tokens_approximation(self):
        """Test count_tokens in approximation mode."""
        manager = TokenManager()
        manager.set_accurate_mode(False)
        
        text = "This is a test sentence with several words"
        tokens = manager.count_tokens(text)
        expected = int(8 * 1.3)  # 8 words
        assert tokens == expected
    
    @patch('flutter_mcp.token_manager.tiktoken')
    def test_accurate_tokens(self, mock_tiktoken):
        """Test accurate token counting with tiktoken."""
        # Mock tiktoken encoder
        mock_encoder = Mock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_tiktoken.get_encoding.return_value = mock_encoder
        
        manager = TokenManager()
        tokens = manager.accurate_tokens("Test text")
        
        assert tokens == 5
        mock_tiktoken.get_encoding.assert_called_once_with("cl100k_base")
        mock_encoder.encode.assert_called_once_with("Test text")
    
    def test_mode_switching(self):
        """Test switching between accurate and approximation modes."""
        manager = TokenManager()
        
        # Default should be approximation
        assert manager.get_mode() == "approximation"
        
        # Switch to accurate
        manager.set_accurate_mode(True)
        assert manager.get_mode() == "accurate"
        
        # Switch back
        manager.set_accurate_mode(False)
        assert manager.get_mode() == "approximation"


class TestDocumentTruncator:
    """Test DocumentTruncator functionality."""
    
    def test_detect_sections(self):
        """Test markdown section detection."""
        truncator = DocumentTruncator()
        
        content = """# Widget

## Description
This is a description.

## Constructors
Here are constructors.

## Properties
Some properties.

## Methods
Various methods.

## Examples
Code examples here.
"""
        sections = truncator._detect_sections(content)
        
        assert len(sections) == 6  # Including pre-section content
        assert "Description" in sections
        assert "Constructors" in sections
        assert "Properties" in sections
        assert "Methods" in sections
        assert "Examples" in sections
    
    def test_truncate_no_truncation_needed(self):
        """Test that content within limit is not truncated."""
        truncator = DocumentTruncator()
        
        content = "Short content"
        result = truncator.truncate_to_limit(content, 10000)
        
        assert result == content  # Should be unchanged
    
    def test_simple_truncation(self):
        """Test simple truncation when no sections detected."""
        truncator = DocumentTruncator()
        
        # Create content that will exceed token limit
        content = "word " * 1000  # 5000 characters, ~1250 tokens
        result = truncator.truncate_to_limit(content, 100)  # Very low limit
        
        assert len(result) < len(content)
        assert result.endswith("...")
        assert "\n\n---\n*Note: Documentation has been truncated" not in result  # Simple truncation
    
    def test_section_based_truncation(self):
        """Test priority-based section truncation."""
        truncator = DocumentTruncator()
        
        content = """# Widget

## Description
This is a very important description that should be kept.

## Constructors
Constructor information here.

## Properties
Property details.

## Methods
Method information.

## Examples
""" + "Example code " * 100 + """

## See Also
References and links.
"""
        
        # Truncate to a limit that should keep only high-priority sections
        result = truncator.truncate_to_limit(content, 200)  # ~800 characters
        
        assert "Description" in result
        assert "very important description" in result
        assert "See Also" not in result  # Low priority
        assert "*Note: Documentation has been truncated" in result


class TestServerIntegration:
    """Test token management integration with server."""
    
    @patch('flutter_mcp.server.token_manager')
    @patch('flutter_mcp.server.truncator')
    def test_process_documentation_with_tokens(self, mock_truncator, mock_token_manager):
        """Test process_documentation with token limit."""
        # Mock token counting
        mock_token_manager.count_tokens.side_effect = [5000, 2000]  # Before and after truncation
        
        # Mock truncation
        mock_truncator.truncate_to_limit.return_value = "Truncated content"
        
        # Mock BeautifulSoup
        with patch('flutter_mcp.server.BeautifulSoup') as mock_bs:
            mock_soup = Mock()
            mock_soup.find.return_value = None
            mock_soup.find_all.return_value = []
            mock_bs.return_value = mock_soup
            
            result = process_documentation("<html></html>", "TestClass", tokens=2000)
        
        assert isinstance(result, dict)
        assert result["content"] == "Truncated content"
        assert result["token_count"] == 2000
        assert result["original_tokens"] == 5000
        assert result["truncated"] == True
        assert "truncation_note" in result
        
        # Verify truncation was called with correct parameters
        mock_truncator.truncate_to_limit.assert_called_once()
        args = mock_truncator.truncate_to_limit.call_args[0]
        assert args[1] == 2000  # Token limit
    
    @patch('flutter_mcp.server.token_manager')
    def test_process_documentation_without_truncation(self, mock_token_manager):
        """Test process_documentation when no truncation needed."""
        # Mock token counting - content fits within limit
        mock_token_manager.count_tokens.return_value = 1000
        
        # Mock BeautifulSoup
        with patch('flutter_mcp.server.BeautifulSoup') as mock_bs:
            mock_soup = Mock()
            mock_soup.find.return_value = None
            mock_soup.find_all.return_value = []
            mock_bs.return_value = mock_soup
            
            result = process_documentation("<html></html>", "TestClass", tokens=5000)
        
        assert isinstance(result, dict)
        assert result["token_count"] == 1000
        assert result["original_tokens"] == 1000
        assert result["truncated"] == False
        assert result["truncation_note"] == ""


class TestCacheIntegration:
    """Test token count storage in cache."""
    
    def test_cache_with_token_count(self):
        """Test that cache stores and retrieves token counts."""
        from flutter_mcp.cache import SQLiteCache
        import tempfile
        import os
        
        # Create temporary cache
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = os.path.join(temp_dir, "test_cache.db")
            cache = SQLiteCache(cache_path)
            
            # Test data with token count
            test_data = {
                "content": "Test content",
                "_cached_token_count": 42
            }
            
            # Store in cache
            cache.set("test_key", test_data, ttl=3600, token_count=42)
            
            # Retrieve from cache
            result = cache.get("test_key")
            
            assert result is not None
            assert result["content"] == "Test content"
            assert result["_cached_token_count"] == 42
            
            # Test statistics
            stats = cache.get_stats()
            assert stats["entries_with_token_counts"] == 1
            assert stats["total_cached_tokens"] == 42
    
    def test_cache_backward_compatibility(self):
        """Test that old cache entries without token counts still work."""
        from flutter_mcp.cache import SQLiteCache
        import tempfile
        import os
        import sqlite3
        
        # Create temporary cache
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = os.path.join(temp_dir, "test_cache.db")
            
            # Manually create old-style cache entry
            conn = sqlite3.connect(cache_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS doc_cache (
                    key TEXT PRIMARY KEY NOT NULL,
                    value TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL
                )
            """)
            
            import time
            import json
            now = int(time.time())
            conn.execute(
                "INSERT INTO doc_cache (key, value, created_at, expires_at) VALUES (?, ?, ?, ?)",
                ("old_key", json.dumps({"content": "Old content"}), now, now + 3600)
            )
            conn.commit()
            conn.close()
            
            # Now use the cache (should migrate schema)
            cache = SQLiteCache(cache_path)
            
            # Should be able to retrieve old entry
            result = cache.get("old_key")
            assert result is not None
            assert result["content"] == "Old content"
            assert "_cached_token_count" not in result  # No token count for old entry
            
            # Should be able to add new entry with token count
            cache.set("new_key", {"content": "New content"}, ttl=3600, token_count=100)
            
            # Verify both entries exist
            stats = cache.get_stats()
            assert stats["total_entries"] == 2
            assert stats["entries_with_token_counts"] == 1
            assert stats["total_cached_tokens"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])