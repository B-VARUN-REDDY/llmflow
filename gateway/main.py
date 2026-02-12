"""
LLMFlow Gateway - Main Application

This is the entry point for the FastAPI application.
It sets up routes, middleware, and exposes the /metrics endpoint for Prometheus.
"""

import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from config import settings
from monitoring.metrics import (
    llm_requests_total,
    llm_active_requests,
    llm_gateway_info,
    record_request
)
from providers.ollama_client import OllamaClient
from providers.groq_client import GroqClient
from providers.gemini_client import GeminiClient
from routers.llm_router import LLMRouter
from routers.cache_manager import CacheManager
from routers.complexity_classifier import classifier

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS - Define request/response schemas
# ============================================================================

class QueryRequest(BaseModel):
    """
    Schema for incoming LLM queries.
    
    Example:
    {
        "prompt": "What is the capital of France?",
        "provider": "auto"  # or specify: "ollama", "groq", "gemini"
    }
    """
    prompt: str
    provider: str = "auto"  # Default: let the router decide


class QueryResponse(BaseModel):
    """
    Schema for LLM responses.
    
    Example:
    {
        "response": "The capital of France is Paris.",
        "provider": "ollama",
        "model": "llama3.2:1b",
        "cached": false,
        "latency_ms": 450,
        "tokens_used": 150,
        "complexity_score": 25,
        "complexity_category": "simple",
        "fallback_used": false
    }
    """
    response: str
    provider: str
    model: str
    cached: bool
    latency_ms: float
    tokens_used: int
    complexity_score: int = 0
    complexity_category: str = "unknown"
    fallback_used: bool = False


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

# Global client instances
ollama_client: OllamaClient = None
groq_client: GroqClient = None
gemini_client: GeminiClient = None
llm_router: LLMRouter = None
cache_manager: CacheManager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the application.
    
    Initializes all LLM providers, cache, and the intelligent router.
    """
    global ollama_client, groq_client, gemini_client, llm_router, cache_manager
    
    # STARTUP
    logger.info("🚀 LLMFlow Gateway starting up...")
    
    # Initialize Cache Manager
    cache_manager = CacheManager(
        redis_host=settings.redis_host,
        redis_port=settings.redis_port,
        ttl_seconds=3600  # 1 hour cache
    )
    await cache_manager.connect()
    
    # Initialize Ollama (always available)
    ollama_client = OllamaClient(base_url=settings.ollama_base_url)
    if await ollama_client.check_health():
        logger.info("✅ Ollama connection successful")
        models = await ollama_client.list_models()
        logger.info(f"   Available models: {models}")
    else:
        logger.warning("⚠️ Ollama not responding - check if container is running")
    
    # Initialize Groq (if API key provided)
    if settings.groq_api_key:
        try:
            groq_client = GroqClient(api_key=settings.groq_api_key)
            logger.info("✅ Groq client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Groq initialization failed: {e}")
    else:
        logger.info("ℹ️ Groq API key not provided - provider unavailable")
    
    # Initialize Gemini (if API key provided)
    if settings.gemini_api_key:
        try:
            gemini_client = GeminiClient(api_key=settings.gemini_api_key)
            logger.info("✅ Gemini client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Gemini initialization failed: {e}")
    else:
        logger.info("ℹ️ Gemini API key not provided - provider unavailable")
    
    # Initialize router with available providers
    llm_router = LLMRouter(
        ollama_client=ollama_client,
        groq_client=groq_client,
        gemini_client=gemini_client
    )
    
    # Set gateway info (static metadata)
    llm_gateway_info.info({
        'version': '0.3.0',
        'environment': 'development',
        'providers': ','.join([k for k, v in llm_router.providers_available.items() if v]),
        'cache_enabled': str(cache_manager.redis_client is not None)
    })
    
    logger.info("✅ Gateway ready to accept requests")
    logger.info(f"📊 Active providers: {[k for k, v in llm_router.providers_available.items() if v]}")
    logger.info(f"💾 Cache: {'Enabled' if cache_manager.redis_client else 'Disabled'}")
    
    yield  # Application runs here
    
    # SHUTDOWN
    logger.info("👋 LLMFlow Gateway shutting down...")
    await ollama_client.close()
    await cache_manager.close()


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="LLMFlow Gateway",
    description="Production LLM Gateway with Cost Intelligence",
    version="0.3.0",
    lifespan=lifespan
)


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/")
async def root():
    """
    Health check endpoint.
    """
    return {
        "service": "LLMFlow Gateway",
        "status": "healthy",
        "version": "0.3.0"
    }


@app.get("/health")
async def health():
    """
    Detailed health check with provider and cache status.
    """
    provider_status = llm_router.get_provider_status() if llm_router else {}
    cache_stats = await cache_manager.get_stats() if cache_manager else {"status": "not_initialized"}
    
    return {
        "status": "healthy",
        "active_requests": llm_active_requests._value._value,
        "providers": provider_status,
        "cache": cache_stats
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main LLM query endpoint with intelligent routing and caching.
    
    Flow:
    1. Check cache for existing response
    2. If cache miss:
       a. Classify query complexity
       b. Route to optimal provider
       c. Handle fallbacks if needed
       d. Store response in cache
    3. Record comprehensive metrics
    4. Return enriched response
    """
    # Start timing
    start_time = time.time()
    
    # Increment active requests
    llm_active_requests.inc()
    
    try:
        logger.info(f"Received query: {request.prompt[:50]}...")
        
        # Determine which provider we'd use (for cache key)
        force_provider = None if request.provider == "auto" else request.provider
        
        # Classify the query to determine cache key and routing
        classification = classifier.classify(request.prompt)
        
        if force_provider:
            cache_provider = force_provider
        else:
            cache_provider = classifier.get_recommended_provider(classification["score"])
        
        # Step 1: Check cache
        cached_response = await cache_manager.get(request.prompt, cache_provider)
        
        if cached_response:
            # Cache HIT! Return immediately
            latency = time.time() - start_time
            
            logger.info(f"🔥 Cache HIT! Response in {latency*1000:.2f}ms")
            
            # Record metrics (cache hit)
            record_request(
                provider=cached_response["provider"],
                status="success",
                duration=latency,
                cache_hit=True,
                tokens=0  # No tokens consumed (cached)
            )
            
            response = QueryResponse(
                response=cached_response["response"],
                provider=cached_response["provider"],
                model=cached_response["model"],
                cached=True,
                latency_ms=latency * 1000,
                tokens_used=cached_response["tokens"],
                complexity_score=classification["score"],
                complexity_category=classification["category"],
                fallback_used=False
            )
            
            return response
        
        # Step 2: Cache MISS - Route query through LLM
        logger.info("❄️ Cache MISS - querying LLM")
        
        result = await llm_router.route_query(
            prompt=request.prompt,
            force_provider=force_provider
        )
        
        # Calculate latency
        latency = time.time() - start_time
        
        # Step 3: Store in cache
        await cache_manager.set(
            prompt=request.prompt,
            provider=result["provider"],
            response=result["response"],
            tokens=result["tokens"],
            model=result["model"]
        )
        
        # Record metrics (cache miss)
        record_request(
            provider=result["provider"],
            status="success",
            duration=latency,
            cache_hit=False,
            tokens=result["tokens"]
        )
        
        # Build enriched response
        response = QueryResponse(
            response=result["response"],
            provider=result["provider"],
            model=result["model"],
            cached=False,
            latency_ms=latency * 1000,
            tokens_used=result["tokens"],
            complexity_score=result.get("complexity_score", 0),
            complexity_category=result.get("complexity_category", "unknown"),
            fallback_used=result.get("fallback_used", False)
        )
        
        logger.info(
            f"Query processed: {result['provider']} ({result['complexity_category']}) "
            f"in {latency*1000:.2f}ms, {result['tokens']} tokens"
        )
        
        if result.get("fallback_used"):
            logger.warning(f"Fallback was used - primary provider failed")
        
        return response
        
    except Exception as e:
        # Record error
        latency = time.time() - start_time
        record_request(
            provider="unknown",
            status="error",
            duration=latency,
            cache_hit=False,
            tokens=0
        )
        
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Always decrement active requests
        llm_active_requests.dec()


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    This is what Prometheus scrapes every 15 seconds.
    It returns ALL metrics in Prometheus text format.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/cache/stats")
async def cache_stats():
    """
    Get detailed cache statistics.
    
    Useful for debugging and monitoring cache performance.
    """
    if not cache_manager:
        return {"error": "Cache manager not initialized"}
    
    stats = await cache_manager.get_stats()
    return stats


@app.post("/cache/clear")
async def cache_clear():
    """
    Clear all cached responses.
    
    Useful for testing or manual cache invalidation.
    Requires deliberate action (POST not GET).
    """
    if not cache_manager:
        return {"error": "Cache manager not initialized"}
    
    deleted = await cache_manager.clear()
    return {
        "status": "success",
        "deleted_entries": deleted,
        "message": f"Cleared {deleted} cached responses"
    }


# ============================================================================
# DEVELOPMENT SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.gateway_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
