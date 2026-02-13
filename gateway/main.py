"""
LLMFlow Gateway - Main Application

Production LLM Gateway with intelligent routing, dual-layer caching,
and comprehensive monitoring.
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
from routers.semantic_cache import SemanticCache
from routers.complexity_classifier import classifier

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class QueryRequest(BaseModel):
    prompt: str
    provider: str = "auto"


class QueryResponse(BaseModel):
    response: str
    provider: str
    model: str
    cached: bool
    cache_type: str = "none"  # none, exact, semantic
    latency_ms: float
    tokens_used: int
    complexity_score: int = 0
    complexity_category: str = "unknown"
    fallback_used: bool = False
    similarity_score: float = 0.0  # For semantic cache hits


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

ollama_client: OllamaClient = None
groq_client: GroqClient = None
gemini_client: GeminiClient = None
llm_router: LLMRouter = None
cache_manager: CacheManager = None
semantic_cache: SemanticCache = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ollama_client, groq_client, gemini_client, llm_router, cache_manager, semantic_cache
    
    logger.info("🚀 LLMFlow Gateway starting up...")
    
    # 1. Initialize Cache Manager
    cache_manager = CacheManager(
        redis_host=settings.redis_host,
        redis_port=settings.redis_port,
        ttl_seconds=3600
    )
    await cache_manager.connect()
    
    # 2. Initialize Semantic Cache
    semantic_cache = SemanticCache(
        similarity_threshold=0.85,
        max_entries=1000
    )
    semantic_cache.initialize()
    cache_manager.semantic_cache = semantic_cache  # Link to cache manager
    
    # 3. Initialize Ollama
    ollama_client = OllamaClient(base_url=settings.ollama_base_url)
    if await ollama_client.check_health():
        logger.info("✅ Ollama connection successful")
        models = await ollama_client.list_models()
        logger.info(f"   Available models: {models}")
    else:
        logger.warning("⚠️ Ollama not responding")
    
    # 4. Initialize Groq
    if settings.groq_api_key:
        try:
            groq_client = GroqClient(api_key=settings.groq_api_key)
            logger.info("✅ Groq client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Groq initialization failed: {e}")
    else:
        logger.info("ℹ️ Groq API key not provided")
    
    # 5. Initialize Gemini
    if settings.gemini_api_key:
        try:
            gemini_client = GeminiClient(api_key=settings.gemini_api_key)
            logger.info("✅ Gemini client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Gemini initialization failed: {e}")
    else:
        logger.info("ℹ️ Gemini API key not provided")
    
    # 6. Initialize Router
    llm_router = LLMRouter(
        ollama_client=ollama_client,
        groq_client=groq_client,
        gemini_client=gemini_client
    )
    
    # Set gateway info
    llm_gateway_info.info({
        'version': '0.4.0',
        'environment': 'development',
        'providers': ','.join([k for k, v in llm_router.providers_available.items() if v]),
        'cache_enabled': str(cache_manager.redis_client is not None),
        'semantic_cache': str(semantic_cache.ready)
    })
    
    logger.info("✅ Gateway ready to accept requests")
    logger.info(f"📊 Active providers: {[k for k, v in llm_router.providers_available.items() if v]}")
    logger.info(f"💾 Cache: {'Enabled' if cache_manager.redis_client else 'Disabled'}")
    logger.info(f"🧠 Semantic cache: {'Enabled' if semantic_cache.ready else 'Disabled'}")
    
    yield
    
    logger.info("👋 LLMFlow Gateway shutting down...")
    await ollama_client.close()
    await cache_manager.close()


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="LLMFlow Gateway",
    description="Production LLM Gateway with Cost Intelligence",
    version="0.4.0",
    lifespan=lifespan
)


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/")
async def root():
    return {
        "service": "LLMFlow Gateway",
        "status": "healthy",
        "version": "0.4.0"
    }


@app.get("/health")
async def health():
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
    Main LLM query endpoint with intelligent routing and dual-layer caching.
    
    Flow:
    1. Check exact cache → semantic cache
    2. If miss: classify → route → call LLM
    3. Store result in both cache layers
    4. Record metrics and return enriched response
    """
    start_time = time.time()
    llm_active_requests.inc()
    
    try:
        logger.info(f"Received query: {request.prompt[:50]}...")
        
        force_provider = None if request.provider == "auto" else request.provider
        
        # Classify query
        classification = classifier.classify(request.prompt)
        cache_provider = force_provider or classifier.get_recommended_provider(classification["score"])
        
        # Step 1: Check cache (exact + semantic)
        cached_response = await cache_manager.get(request.prompt, cache_provider)
        
        if cached_response:
            latency = time.time() - start_time
            cache_type = cached_response.get("cache_type", "exact")
            similarity = cached_response.get("similarity_score", 1.0)
            
            logger.info(f"🔥 Cache HIT ({cache_type})! {latency*1000:.2f}ms")
            
            record_request(
                provider=cached_response["provider"],
                status="success",
                duration=latency,
                cache_hit=True,
                tokens=cached_response["tokens"],
                cache_type=cache_type
            )
            
            return QueryResponse(
                response=cached_response["response"],
                provider=cached_response["provider"],
                model=cached_response["model"],
                cached=True,
                cache_type=cache_type,
                latency_ms=latency * 1000,
                tokens_used=cached_response["tokens"],
                complexity_score=classification["score"],
                complexity_category=classification["category"],
                fallback_used=False,
                similarity_score=similarity if cache_type == "semantic" else 1.0
            )
        
        # Step 2: Cache MISS - Route to LLM
        logger.info("❄️ Cache MISS (both layers) - querying LLM")
        
        result = await llm_router.route_query(
            prompt=request.prompt,
            force_provider=force_provider
        )
        
        latency = time.time() - start_time
        
        # Step 3: Store in cache (both layers)
        await cache_manager.set(
            prompt=request.prompt,
            provider=result["provider"],
            response=result["response"],
            tokens=result["tokens"],
            model=result["model"]
        )
        
        record_request(
            provider=result["provider"],
            status="success",
            duration=latency,
            cache_hit=False,
            tokens=result["tokens"],
            cache_type="none"
        )
        
        response = QueryResponse(
            response=result["response"],
            provider=result["provider"],
            model=result["model"],
            cached=False,
            cache_type="none",
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
        
        return response
        
    except Exception as e:
        latency = time.time() - start_time
        record_request(provider="unknown", status="error", duration=latency, cache_hit=False, tokens=0)
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        llm_active_requests.dec()


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/cache/stats")
async def cache_stats():
    if not cache_manager:
        return {"error": "Cache manager not initialized"}
    return await cache_manager.get_stats()


@app.post("/cache/clear")
async def cache_clear():
    if not cache_manager:
        return {"error": "Cache manager not initialized"}
    deleted = await cache_manager.clear()
    return {"status": "success", "deleted_entries": deleted}


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
