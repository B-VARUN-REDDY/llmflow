"""
Semantic Cache - Embedding-based similarity matching for LLM responses.

Uses sentence-transformers to generate embeddings and cosine similarity
to find similar queries that have already been answered.

Strategy:
- Generate embedding for each query prompt
- Store embedding + response in Redis
- On new query, compare embedding against stored embeddings
- If similarity > threshold (0.85), return cached response

This catches queries like:
- "What is Docker?" ≈ "Explain Docker to me" ≈ "Tell me about Docker"
- "How does Python work?" ≈ "Explain how Python works"

Expected improvement: Cache hit rate from ~50% → 75%+
"""

import json
import logging
import numpy as np
from typing import Optional, List, Tuple
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    Semantic similarity cache using sentence embeddings.
    
    Stores embeddings in Redis and performs cosine similarity
    search to find semantically similar cached queries.
    """
    
    # Model produces 384-dimensional embeddings, fast and lightweight
    MODEL_NAME = "all-MiniLM-L6-v2"
    
    def __init__(
        self,
        similarity_threshold: float = 0.85,
        max_entries: int = 1000
    ):
        """
        Initialize semantic cache.
        
        Args:
            similarity_threshold: Minimum cosine similarity to consider a hit (0-1)
            max_entries: Maximum number of entries to store
        """
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self.model: Optional[SentenceTransformer] = None
        self.ready = False
        
        logger.info(
            f"Semantic cache configured: threshold={similarity_threshold}, "
            f"max_entries={max_entries}"
        )
    
    def initialize(self):
        """
        Load the sentence transformer model.
        
        This downloads the model on first run (~90MB).
        Called during application startup.
        """
        try:
            logger.info(f"Loading embedding model: {self.MODEL_NAME}...")
            self.model = SentenceTransformer(self.MODEL_NAME)
            self.ready = True
            logger.info(f"✅ Semantic cache model loaded: {self.MODEL_NAME}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            self.ready = False
            return False
    
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding vector for a text string.
        
        Args:
            text: Input text to embed
        
        Returns:
            numpy array of shape (384,) or None if model not loaded
        """
        if not self.ready or not self.model:
            return None
        
        try:
            # Normalize text
            normalized = text.lower().strip()
            # Generate embedding
            embedding = self.model.encode(normalized, normalize_embeddings=True)
            return embedding
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return None
    
    def cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Since we use normalize_embeddings=True, this is just the dot product.
        
        Args:
            vec_a: First vector
            vec_b: Second vector
        
        Returns:
            float: Similarity score between -1 and 1
        """
        return float(np.dot(vec_a, vec_b))
    
    def embedding_to_bytes(self, embedding: np.ndarray) -> bytes:
        """Convert numpy embedding to bytes for Redis storage."""
        return embedding.astype(np.float32).tobytes()
    
    def bytes_to_embedding(self, data: bytes) -> np.ndarray:
        """Convert bytes back to numpy embedding."""
        return np.frombuffer(data, dtype=np.float32)
    
    async def find_similar(
        self,
        redis_client,
        query_embedding: np.ndarray
    ) -> Optional[Tuple[dict, float]]:
        """
        Search Redis for semantically similar cached queries.
        
        Performs brute-force cosine similarity against all stored embeddings.
        For <1000 entries, this is fast enough (<10ms).
        
        Args:
            redis_client: Async Redis client
            query_embedding: Embedding of the new query
        
        Returns:
            Tuple of (cached_response, similarity_score) or None
        """
        if not redis_client:
            return None
        
        try:
            # Get all semantic cache keys
            keys = await redis_client.keys("sem_cache:emb:*")
            
            if not keys:
                return None
            
            best_match = None
            best_score = 0.0
            
            for key in keys:
                # Get stored embedding (stored as bytes)
                stored_bytes = await redis_client.get(key)
                if not stored_bytes:
                    continue
                
                # Handle both string and bytes responses
                if isinstance(stored_bytes, str):
                    stored_bytes = stored_bytes.encode('latin-1')
                
                stored_embedding = self.bytes_to_embedding(stored_bytes)
                
                # Calculate similarity
                score = self.cosine_similarity(query_embedding, stored_embedding)
                
                if score > best_score:
                    best_score = score
                    best_match = key
            
            # Check if best match exceeds threshold
            if best_match and best_score >= self.similarity_threshold:
                # Extract the hash from the key (sem_cache:emb:HASH → HASH)
                cache_hash = best_match.split(":")[-1] if isinstance(best_match, str) else best_match.decode().split(":")[-1]
                
                # Get the cached response data
                response_key = f"sem_cache:data:{cache_hash}"
                cached_data = await redis_client.get(response_key)
                
                if cached_data:
                    result = json.loads(cached_data)
                    logger.info(
                        f"🧠 Semantic cache HIT! Similarity: {best_score:.3f} "
                        f"(threshold: {self.similarity_threshold})"
                    )
                    return (result, best_score)
            
            logger.debug(
                f"🧠 Semantic cache MISS. Best similarity: {best_score:.3f} "
                f"(threshold: {self.similarity_threshold})"
            )
            return None
            
        except Exception as e:
            logger.error(f"Semantic cache search error: {e}")
            return None
    
    async def store(
        self,
        redis_client,
        prompt: str,
        embedding: np.ndarray,
        response_data: dict,
        ttl_seconds: int = 3600
    ) -> bool:
        """
        Store a query embedding and response in semantic cache.
        
        Args:
            redis_client: Async Redis client
            prompt: Original prompt text
            embedding: Embedding vector for the prompt
            response_data: Dict with response, tokens, model, provider
            ttl_seconds: Cache TTL
        
        Returns:
            bool: True if stored successfully
        """
        if not redis_client:
            return False
        
        try:
            import hashlib
            # Generate unique hash for this entry
            cache_hash = hashlib.sha256(prompt.lower().strip().encode()).hexdigest()[:16]
            
            # Store embedding (as bytes, using a separate non-decode connection)
            emb_key = f"sem_cache:emb:{cache_hash}"
            data_key = f"sem_cache:data:{cache_hash}"
            
            # Store embedding bytes as latin-1 encoded string
            # (works with decode_responses=True Redis client)
            emb_bytes = self.embedding_to_bytes(embedding)
            emb_str = emb_bytes.decode('latin-1')
            await redis_client.setex(emb_key, ttl_seconds, emb_str)
            
            # Store response data as JSON
            await redis_client.setex(
                data_key,
                ttl_seconds,
                json.dumps(response_data)
            )
            
            logger.info(f"🧠💾 Semantic cache stored: {cache_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Semantic cache store error: {e}")
            return False
    
    async def get_stats(self, redis_client) -> dict:
        """Get semantic cache statistics."""
        if not redis_client:
            return {"status": "disabled"}
        
        try:
            emb_keys = await redis_client.keys("sem_cache:emb:*")
            return {
                "status": "active" if self.ready else "model_not_loaded",
                "model": self.MODEL_NAME,
                "entries": len(emb_keys),
                "similarity_threshold": self.similarity_threshold,
                "max_entries": self.max_entries
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def clear(self, redis_client) -> int:
        """Clear all semantic cache entries."""
        if not redis_client:
            return 0
        
        try:
            keys = await redis_client.keys("sem_cache:*")
            if keys:
                deleted = await redis_client.delete(*keys)
                logger.info(f"🗑️ Cleared {deleted} semantic cache entries")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Error clearing semantic cache: {e}")
            return 0
