"""
Redis-based caching service for RAG queries and results.

Phase 3: Caching Layer
Purpose: Reduce latency and improve performance by caching frequently accessed RAG queries.
"""

import json
import hashlib
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGCacheService:
    """
    Redis-based caching service for RAG queries.

    Features:
    - Cache frequently retrieved queries
    - TTL-based automatic cache invalidation
    - Cache analytics and hit rate tracking
    - Query similarity matching (avoid duplicates)
    - Per-agent and per-project cache management
    """

    def __init__(self):
        """Initialize the cache service."""
        self.enabled = settings.RAG_CACHE_ENABLED
        self.ttl = settings.RAG_CACHE_TTL
        self.max_size = settings.RAG_CACHE_MAX_SIZE
        self.similarity_threshold = settings.RAG_CACHE_SIMILARITY_THRESHOLD
        self.analytics_enabled = settings.RAG_CACHE_ANALYTICS_ENABLED
        self.redis: Optional[Redis] = None
        self.cache_prefix = "rag:cache"
        self.stats_prefix = "rag:stats"

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            # Test connection
            await self.redis.ping()
            logger.info("✅ RAG Cache Service initialized (Redis connected)")
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize Redis cache: {e}")
            self.redis = None
            self.enabled = False

    async def shutdown(self) -> None:
        """Shutdown Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("✅ RAG Cache Service shutdown complete")

    async def get_cache_key(
        self,
        query: str,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        collections: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a cache key for a query.

        Args:
            query: Search query
            agent_id: Optional agent ID for filtering
            project_id: Optional project ID for filtering
            collections: Optional list of collections to search

        Returns:
            Cache key string
        """
        # Create a normalized query key
        key_parts = [
            query.lower().strip(),
            agent_id or "any",
            project_id or "any",
            "|".join(sorted(collections or [])),
        ]
        key_str = ":".join(key_parts)

        # Hash for shorter keys
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
        return f"{self.cache_prefix}:{key_hash}"

    async def get(
        self,
        query: str,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        collections: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached results for a query.

        Args:
            query: Search query
            agent_id: Optional agent ID
            project_id: Optional project ID
            collections: Optional list of collections

        Returns:
            Cached results dict or None if not found/expired
        """
        if not self.enabled or not self.redis:
            return None

        try:
            cache_key = await self.get_cache_key(query, agent_id, project_id, collections)
            cached = await self.redis.get(cache_key)

            if cached:
                result = json.loads(cached)
                await self._record_hit(cache_key)
                logger.debug(f"Cache HIT for query: {query[:50]}...")
                return result
            else:
                await self._record_miss(cache_key)
                logger.debug(f"Cache MISS for query: {query[:50]}...")
                return None
        except Exception as e:
            logger.warning(f"Error retrieving from cache: {e}")
            return None

    async def set(
        self,
        query: str,
        results: Dict[str, Any],
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        collections: Optional[List[str]] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache results for a query.

        Args:
            query: Search query
            results: Results to cache
            agent_id: Optional agent ID
            project_id: Optional project ID
            collections: Optional list of collections
            ttl: Optional TTL override (seconds)

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled or not self.redis:
            return False

        try:
            cache_key = await self.get_cache_key(query, agent_id, project_id, collections)
            ttl = ttl or self.ttl

            # Serialize and cache
            serialized = json.dumps(results, default=str)
            await self.redis.setex(cache_key, ttl, serialized)

            # Increment size counter
            cache_size = await self.redis.incr(f"{self.stats_prefix}:size")

            # Cleanup if exceeding max size
            if cache_size > self.max_size:
                await self._cleanup_oldest()

            logger.debug(f"Cache SET for query: {query[:50]}... (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Error setting cache: {e}")
            return False

    async def delete(
        self,
        query: str,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        collections: Optional[List[str]] = None,
    ) -> bool:
        """
        Delete cached results for a query.

        Args:
            query: Search query
            agent_id: Optional agent ID
            project_id: Optional project ID
            collections: Optional list of collections

        Returns:
            True if deleted, False if not found or error
        """
        if not self.enabled or not self.redis:
            return False

        try:
            cache_key = await self.get_cache_key(query, agent_id, project_id, collections)
            deleted = await self.redis.delete(cache_key)
            if deleted:
                await self.redis.decr(f"{self.stats_prefix}:size")
                logger.debug(f"Cache DELETE for key: {cache_key}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Error deleting from cache: {e}")
            return False

    async def clear_project(self, project_id: str) -> bool:
        """
        Clear all cache entries for a project.

        Args:
            project_id: Project ID to clear

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis:
            return False

        try:
            pattern = f"{self.cache_prefix}:*"
            cursor = 0
            deleted_count = 0

            # Scan all cache keys and delete those matching project
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                for key in keys:
                    # Check if key is associated with this project
                    try:
                        value = await self.redis.get(key)
                        if value:
                            data = json.loads(value)
                            if data.get("project_id") == project_id:
                                await self.redis.delete(key)
                                deleted_count += 1
                    except Exception:
                        continue

                if cursor == 0:
                    break

            logger.info(f"Cleared {deleted_count} cache entries for project {project_id}")
            return True
        except Exception as e:
            logger.warning(f"Error clearing project cache: {e}")
            return False

    async def clear_agent(self, agent_id: str) -> bool:
        """
        Clear all cache entries for an agent.

        Args:
            agent_id: Agent ID to clear

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis:
            return False

        try:
            pattern = f"{self.cache_prefix}:*"
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                for key in keys:
                    try:
                        value = await self.redis.get(key)
                        if value:
                            data = json.loads(value)
                            if data.get("agent_id") == agent_id:
                                await self.redis.delete(key)
                                deleted_count += 1
                    except Exception:
                        continue

                if cursor == 0:
                    break

            logger.info(f"Cleared {deleted_count} cache entries for agent {agent_id}")
            return True
        except Exception as e:
            logger.warning(f"Error clearing agent cache: {e}")
            return False

    async def clear_all(self) -> bool:
        """
        Clear all RAG cache entries.

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis:
            return False

        try:
            pattern = f"{self.cache_prefix}:*"
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted_count += await self.redis.delete(*keys)

                if cursor == 0:
                    break

            # Reset statistics
            await self.redis.delete(f"{self.stats_prefix}:size")
            await self.redis.delete(f"{self.stats_prefix}:hits")
            await self.redis.delete(f"{self.stats_prefix}:misses")

            logger.info(f"Cleared all RAG cache ({deleted_count} entries)")
            return True
        except Exception as e:
            logger.warning(f"Error clearing all cache: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled or not self.redis:
            return {
                "enabled": False,
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0,
                "size": 0,
            }

        try:
            size = await self.redis.get(f"{self.stats_prefix}:size")
            hits = await self.redis.get(f"{self.stats_prefix}:hits")
            misses = await self.redis.get(f"{self.stats_prefix}:misses")

            size = int(size or 0)
            hits = int(hits or 0)
            misses = int(misses or 0)

            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0.0

            return {
                "enabled": True,
                "size": size,
                "hits": hits,
                "misses": misses,
                "total_requests": total,
                "hit_rate": round(hit_rate, 2),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl,
            }
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {
                "enabled": False,
                "error": str(e),
            }

    async def _record_hit(self, cache_key: str) -> None:
        """Record a cache hit."""
        if not self.analytics_enabled or not self.redis:
            return

        try:
            await self.redis.incr(f"{self.stats_prefix}:hits")
        except Exception:
            pass

    async def _record_miss(self, cache_key: str) -> None:
        """Record a cache miss."""
        if not self.analytics_enabled or not self.redis:
            return

        try:
            await self.redis.incr(f"{self.stats_prefix}:misses")
        except Exception:
            pass

    async def _cleanup_oldest(self) -> None:
        """Remove oldest cache entries when max size exceeded."""
        if not self.redis:
            return

        try:
            # Get all cache keys sorted by access time
            pattern = f"{self.cache_prefix}:*"
            cursor = 0
            keys_ttl = []

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                for key in keys:
                    ttl = await self.redis.ttl(key)
                    keys_ttl.append((key, ttl))

                if cursor == 0:
                    break

            # Sort by TTL (oldest first) and delete 10% of cache
            keys_ttl.sort(key=lambda x: x[1])
            to_delete = int(len(keys_ttl) * 0.1)

            for key, _ in keys_ttl[:to_delete]:
                await self.redis.delete(key)

            logger.debug(f"Cleaned up {to_delete} cache entries (max size exceeded)")
        except Exception as e:
            logger.warning(f"Error cleaning up cache: {e}")


# Global cache service instance
_cache_service: Optional[RAGCacheService] = None


def get_cache_service() -> RAGCacheService:
    """Get or create the RAG cache service singleton."""
    global _cache_service
    if _cache_service is None:
        _cache_service = RAGCacheService()
    return _cache_service


async def initialize_cache_service() -> None:
    """Initialize the cache service at application startup."""
    service = get_cache_service()
    await service.initialize()


async def shutdown_cache_service() -> None:
    """Shutdown the cache service at application shutdown."""
    global _cache_service
    if _cache_service:
        await _cache_service.shutdown()
        _cache_service = None
