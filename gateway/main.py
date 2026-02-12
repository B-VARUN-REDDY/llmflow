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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the application.
    
    Initializes all LLM providers and the intelligent router.
    """
    global ollama_client, groq_client, gemini_client, llm_router
    
    # STARTUP
    logger.info("🚀 LLMFlow Gateway starting up...")
    
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
        'version': '0.2.0',
        'environment': 'development',
        'providers': ','.join([k for k, v in llm_router.providers_available.items() if v])
    })
    
    logger.info("✅ Gateway ready to accept requests")
    logger.info(f"📊 Active providers: {[k for k, v in llm_router.providers_available.items() if v]}")
    
    yield  # Application runs here
    
    # SHUTDOWN
    logger.info("👋 LLMFlow Gateway shutting down...")
    await ollama_client.close()


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="LLMFlow Gateway",
    description="Production LLM Gateway with Cost Intelligence",
    version="0.2.0",
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
        "version": "0.2.0"
    }


@app.get("/health")
async def health():
    """
    Detailed health check with provider status.
    """
    provider_status = llm_router.get_provider_status() if llm_router else {}
    
    return {
        "status": "healthy",
        "active_requests": llm_active_requests._value._value,
        "providers": provider_status
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main LLM query endpoint with intelligent routing.
    
    Flow:
    1. Classify query complexity
    2. Route to optimal provider
    3. Handle fallbacks if needed
    4. Record comprehensive metrics
    5. Return enriched response
    """
    # Start timing
    start_time = time.time()
    
    # Increment active requests
    llm_active_requests.inc()
    
    try:
        logger.info(f"Received query: {request.prompt[:50]}...")
        
        # Route query through intelligent router
        force_provider = None if request.provider == "auto" else request.provider
        result = await llm_router.route_query(
            prompt=request.prompt,
            force_provider=force_provider
        )
        
        # Calculate latency
        latency = time.time() - start_time
        
        # Record metrics
        record_request(
            provider=result["provider"],
            status="success",
            duration=latency,
            cache_hit=False,  # No caching yet (Phase 2B)
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
    
    Example output:
    # HELP llm_requests_total Total number of LLM requests processed
    # TYPE llm_requests_total counter
    llm_requests_total{provider="ollama",status="success"} 42.0
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# DEVELOPMENT SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.gateway_port,
        reload=True,  # Auto-reload on code changes
        log_level=settings.log_level.lower()
    )
