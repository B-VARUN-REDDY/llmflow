"""
Cache Manager for LLM Responses

Implements exact-match caching using Redis.
Phase 2: Exact match only
Phase 3: Will add semantic caching (similar queries)

Cache Strategy:
- Key: hash(prompt + provider)
- Value: JSON with response, tokens, model
- TTL: 1 hour (configurable)

This can save 50-80% of LLM costs for repeated queries.
"""

import redis.asyncio as redis
import hashlib
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages LLM response caching with Redis.
    """
    
    def __init__(
        self,
        redis_host: str = "redis",
        redis_port: int = 6379,
        ttl_seconds: int = 3600  # 1 hour default
    ):
        """
        Initialize cache manager.
        
        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
            ttl_seconds: Cache TTL in seconds (default: 1 hour)
        """
        self.redis_url = f"redis://{redis_host}:{redis_port}"
        self.ttl_seconds = ttl_seconds
        self.redis_client: Optional[redis.Redis] = None
        
        logger.info(f"Cache manager configured: {self.redis_url}, TTL={ttl_seconds}s")
    
    async def connect(self):
        """
        Connect to Redis.
        Call this during application startup.
        """
        try:
            self.redis_client = redis.Redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            logger.info("✅ Redis connection successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.warning("⚠️ Caching will be disabled")
            self.redis_client = None
            return False
    
    async def close(self):
        """
        Close Redis connection.
        Call this during application shutdown.
        """
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    def _generate_cache_key(self, prompt: str, provider: str) -> str:
        """
        Generate unique cache key for a query.
        
        We include provider in the key because different providers
        might give different responses to the same prompt.
        
        Args:
            prompt: The query text
            provider: Which provider (ollama/groq/gemini)
        
        Returns:
            str: Cache key (hex hash)
        """
        # Normalize prompt (lowercase, strip whitespace)
        normalized_prompt = prompt.lower().strip()
        
        # Create hash of prompt + provider
        cache_string = f"{normalized_prompt}|{provider}"
        hash_object = hashlib.sha256(cache_string.encode())
        cache_key = f"llm_cache:{hash_object.hexdigest()[:16]}"
        
        return cache_key
    
    async def get(self, prompt: str, provider: str) -> Optional[dict]:
        """
        Retrieve cached response.
        
        Args:
            prompt: The query text
            provider: Which provider to check cache for
        
        Returns:
            dict or None: Cached response if found, else None
        """
        if not self.redis_client:
            return None  # Cache disabled
        
        try:
            cache_key = self._generate_cache_key(prompt, provider)
            
            # Try to get from Redis
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                # Parse JSON
                result = json.loads(cached_data)
                logger.info(f"🔥 Cache HIT: {cache_key}")
                return result
            else:
                logger.debug(f"❄️ Cache MISS: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    async def set(
        self,
        prompt: str,
        provider: str,
        response: str,
        tokens: int,
        model: str
    ) -> bool:
        """
        Store response in cache.
        
        Args:
            prompt: The query text
            provider: Which provider generated this
            response: The LLM's response
            tokens: Token count
            model: Specific model used
        
        Returns:
            bool: True if cached successfully
        """
        if not self.redis_client:
            return False  # Cache disabled
        
        try:
            cache_key = self._generate_cache_key(prompt, provider)
            
            # Prepare data to cache
            cache_data = {
                "response": response,
                "tokens": tokens,
                "model": model,
                "provider": provider
            }
            
            # Store in Redis with TTL
            await self.redis_client.setex(
                cache_key,
                self.ttl_seconds,
                json.dumps(cache_data)
            )
            
            logger.info(f"💾 Cached response: {cache_key} (TTL: {self.ttl_seconds}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            return False
    
    async def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            dict: Cache stats (key count, memory usage, etc.)
        """
        if not self.redis_client:
            return {"status": "disabled"}
        
        try:
            # Get all cache keys
            keys = await self.redis_client.keys("llm_cache:*")
            
            # Get Redis info
            info = await self.redis_client.info("memory")
            
            return {
                "status": "active",
                "cached_entries": len(keys),
                "memory_used_bytes": info.get("used_memory", 0),
                "memory_used_human": info.get("used_memory_human", "0B"),
                "ttl_seconds": self.ttl_seconds
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "message": str(e)}
    
    async def clear(self) -> int:
        """
        Clear all cached responses.
        Useful for testing or manual cache invalidation.
        
        Returns:
            int: Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            # Find all cache keys
            keys = await self.redis_client.keys("llm_cache:*")
            
            if keys:
                # Delete all at once
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"🗑️ Cleared {deleted} cached entries")
                return deleted
            else:
                logger.info("Cache already empty")
                return 0
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
