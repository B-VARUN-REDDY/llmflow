"""
Cache Manager for LLM Responses - Dual Layer Cache

Layer 1: Exact match (SHA-256 hash) - ~1ms lookup
Layer 2: Semantic match (embedding similarity) - ~5-10ms lookup

Cache Flow:
1. Check exact match first (fastest)
2. If miss, check semantic similarity
3. If both miss, call LLM and store in both layers

This dual approach catches:
- Exact repeats: "What is Docker?" → instant
- Paraphrases: "Explain Docker" → semantic hit
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
    Supports both exact-match and semantic caching.
    """
    
    def __init__(
        self,
        redis_host: str = "redis",
        redis_port: int = 6379,
        ttl_seconds: int = 3600  # 1 hour default
    ):
        self.redis_url = f"redis://{redis_host}:{redis_port}"
        self.ttl_seconds = ttl_seconds
        self.redis_client: Optional[redis.Redis] = None
        self.semantic_cache = None  # Set externally after init
        
        logger.info(f"Cache manager configured: {self.redis_url}, TTL={ttl_seconds}s")
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_client = redis.Redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Redis connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    def _generate_cache_key(self, prompt: str, provider: str) -> str:
        """Generate unique cache key from prompt + provider."""
        normalized_prompt = prompt.lower().strip()
        cache_string = f"{normalized_prompt}|{provider}"
        hash_object = hashlib.sha256(cache_string.encode())
        return f"llm_cache:{hash_object.hexdigest()[:16]}"
    
    async def get(self, prompt: str, provider: str) -> Optional[dict]:
        """
        Retrieve cached response - tries exact match first, then semantic.
        
        Returns:
            dict with response data and 'cache_type' ('exact' or 'semantic'),
            or None if no match found.
        """
        if not self.redis_client:
            return None
        
        # Layer 1: Exact match
        try:
            cache_key = self._generate_cache_key(prompt, provider)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                result["cache_type"] = "exact"
                logger.info(f"🔥 Exact cache HIT: {cache_key}")
                return result
        except Exception as e:
            logger.error(f"Exact cache retrieval error: {e}")
        
        # Layer 2: Semantic match
        if self.semantic_cache and self.semantic_cache.ready:
            try:
                query_embedding = self.semantic_cache.get_embedding(prompt)
                if query_embedding is not None:
                    match = await self.semantic_cache.find_similar(
                        self.redis_client,
                        query_embedding
                    )
                    if match:
                        result, similarity = match
                        result["cache_type"] = "semantic"
                        result["similarity_score"] = round(similarity, 3)
                        logger.info(
                            f"🧠 Semantic cache HIT! "
                            f"Similarity: {similarity:.3f}"
                        )
                        return result
            except Exception as e:
                logger.error(f"Semantic cache retrieval error: {e}")
        
        logger.debug(f"❄️ Cache MISS (both layers)")
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
        Store response in both exact and semantic caches.
        """
        if not self.redis_client:
            return False
        
        response_data = {
            "response": response,
            "tokens": tokens,
            "model": model,
            "provider": provider
        }
        
        success = False
        
        # Store in exact cache
        try:
            cache_key = self._generate_cache_key(prompt, provider)
            await self.redis_client.setex(
                cache_key,
                self.ttl_seconds,
                json.dumps(response_data)
            )
            logger.info(f"💾 Exact cache stored: {cache_key}")
            success = True
        except Exception as e:
            logger.error(f"Exact cache storage error: {e}")
        
        # Store in semantic cache
        if self.semantic_cache and self.semantic_cache.ready:
            try:
                embedding = self.semantic_cache.get_embedding(prompt)
                if embedding is not None:
                    await self.semantic_cache.store(
                        self.redis_client,
                        prompt,
                        embedding,
                        response_data,
                        self.ttl_seconds
                    )
                    success = True
            except Exception as e:
                logger.error(f"Semantic cache storage error: {e}")
        
        return success
    
    async def get_stats(self) -> dict:
        """Get cache statistics for both layers."""
        if not self.redis_client:
            return {"status": "disabled"}
        
        try:
            # Exact cache stats
            exact_keys = await self.redis_client.keys("llm_cache:*")
            
            # Redis memory info
            info = await self.redis_client.info("memory")
            
            stats = {
                "status": "active",
                "exact_cache": {
                    "entries": len(exact_keys)
                },
                "memory_used_bytes": info.get("used_memory", 0),
                "memory_used_human": info.get("used_memory_human", "0B"),
                "ttl_seconds": self.ttl_seconds
            }
            
            # Semantic cache stats
            if self.semantic_cache:
                sem_stats = await self.semantic_cache.get_stats(self.redis_client)
                stats["semantic_cache"] = sem_stats
            else:
                stats["semantic_cache"] = {"status": "disabled"}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "message": str(e)}
    
    async def clear(self) -> int:
        """Clear all cached responses (both layers)."""
        if not self.redis_client:
            return 0
        
        total_deleted = 0
        
        try:
            # Clear exact cache
            exact_keys = await self.redis_client.keys("llm_cache:*")
            if exact_keys:
                total_deleted += await self.redis_client.delete(*exact_keys)
            
            # Clear semantic cache
            if self.semantic_cache:
                total_deleted += await self.semantic_cache.clear(self.redis_client)
            
            logger.info(f"🗑️ Cleared {total_deleted} total cache entries")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
