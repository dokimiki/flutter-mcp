"""SQLite-based cache implementation for Flutter MCP Server."""

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional, Dict, Any
import logging

try:
    from platformdirs import user_cache_dir
except ImportError:
    # Fallback to simple home directory approach
    def user_cache_dir(app_name: str, app_author: str) -> str:
        """Simple fallback for cache directory."""
        home = Path.home()
        if hasattr(home, 'absolute'):
            return str(home / '.cache' / app_name)
        return str(Path('.') / '.cache' / app_name)

logger = logging.getLogger(__name__)


class CacheManager:
    """SQLite-based cache manager for Flutter documentation."""
    
    def __init__(self, app_name: str = "FlutterMCP", ttl_hours: int = 24):
        """Initialize cache manager.
        
        Args:
            app_name: Application name for cache directory
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.app_name = app_name
        self.ttl_seconds = ttl_hours * 3600
        self.db_path = self._get_db_path()
        self._init_db()
    
    def _get_db_path(self) -> Path:
        """Get platform-specific cache database path."""
        cache_dir = user_cache_dir(self.app_name, self.app_name)
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path / "cache.db"
    
    def _init_db(self) -> None:
        """Initialize the cache database."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS doc_cache (
                    key TEXT PRIMARY KEY NOT NULL,
                    value TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL
                )
            """)
            # Create index for expiration queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                ON doc_cache(expires_at)
            """)
            conn.commit()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache with lazy expiration.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value as dict or None if not found/expired
        """
        current_time = int(time.time())
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT value, expires_at FROM doc_cache WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            value, expires_at = row
            
            # Check if expired
            if expires_at < current_time:
                # Lazy deletion
                conn.execute("DELETE FROM doc_cache WHERE key = ?", (key,))
                conn.commit()
                logger.debug(f"Cache expired for key: {key}")
                return None
            
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode cache value for key: {key}")
                return None
    
    def set(self, key: str, value: Dict[str, Any], ttl_override: Optional[int] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl_override: Optional TTL override in seconds
        """
        current_time = int(time.time())
        ttl = ttl_override or self.ttl_seconds
        expires_at = current_time + ttl
        
        try:
            value_json = json.dumps(value)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize value for key {key}: {e}")
            return
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO doc_cache 
                   (key, value, created_at, expires_at) 
                   VALUES (?, ?, ?, ?)""",
                (key, value_json, current_time, expires_at)
            )
            conn.commit()
            logger.debug(f"Cached key: {key} (expires in {ttl}s)")
    
    def delete(self, key: str) -> None:
        """Delete a key from cache.
        
        Args:
            key: Cache key to delete
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM doc_cache WHERE key = ?", (key,))
            conn.commit()
    
    def clear_expired(self) -> int:
        """Clear all expired entries from cache.
        
        Returns:
            Number of entries cleared
        """
        current_time = int(time.time())
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "DELETE FROM doc_cache WHERE expires_at < ?",
                (current_time,)
            )
            conn.commit()
            return cursor.rowcount
    
    def clear_all(self) -> None:
        """Clear all entries from cache."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM doc_cache")
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        current_time = int(time.time())
        
        with sqlite3.connect(str(self.db_path)) as conn:
            # Total entries
            total = conn.execute("SELECT COUNT(*) FROM doc_cache").fetchone()[0]
            
            # Expired entries
            expired = conn.execute(
                "SELECT COUNT(*) FROM doc_cache WHERE expires_at < ?",
                (current_time,)
            ).fetchone()[0]
            
            # Database size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                "total_entries": total,
                "expired_entries": expired,
                "active_entries": total - expired,
                "database_size_bytes": db_size,
                "database_path": str(self.db_path)
            }


# Global cache instance
_cache_instance: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get or create the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager()
    return _cache_instance