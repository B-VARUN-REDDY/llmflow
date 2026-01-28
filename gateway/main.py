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
        "model": "auto"  # or specify: "ollama", "groq", "gemini"
    }
    """
    prompt: str
    model: str = "auto"  # Default: let the router decide


class QueryResponse(BaseModel):
    """
    Schema for LLM responses.
    
    Example:
    {
        "response": "The capital of France is Paris.",
        "provider": "ollama",
        "model": "llama3.1",
        "cached": false,
        "latency_ms": 450,
        "tokens_used": 150
    }
    """
    response: str
    provider: str
    model: str
    cached: bool
    latency_ms: float
    tokens_used: int


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

# Global Ollama client instance
ollama_client: OllamaClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the application.
    
    This runs once at startup and once at shutdown.
    Perfect for:
    - Setting static metrics (version info)
    - Initializing connections (Redis, PostgreSQL)
    - Cleanup on shutdown
    """
    global ollama_client
    
    # STARTUP
    logger.info("🚀 LLMFlow Gateway starting up...")
    
    # Initialize Ollama client
    ollama_client = OllamaClient(base_url=settings.ollama_base_url)
    
    # Check if Ollama is healthy
    if await ollama_client.check_health():
        logger.info("✅ Ollama connection successful")
        models = await ollama_client.list_models()
        logger.info(f"Available models: {models}")
    else:
        logger.warning("⚠️ Ollama not responding - check if container is running")
    
    # Set gateway info (static metadata)
    llm_gateway_info.info({
        'version': '0.1.0',
        'environment': 'development'
    })
    
    logger.info("✅ Gateway ready to accept requests")
    
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
    version="0.1.0",
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
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """
    Detailed health check.
    
    In production, this would check:
    - Redis connection
    - PostgreSQL connection
    - LLM provider availability
    
    For now, it's simple.
    """
    return {
        "status": "healthy",
        "active_requests": llm_active_requests._value._value
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main LLM query endpoint.
    
    This is where all the magic happens:
    1. Increment active requests gauge
    2. Check cache (Phase 2)
    3. Route to appropriate provider
    4. Record metrics
    5. Return response
    """
    # Start timing
    start_time = time.time()
    
    # Increment active requests
    llm_active_requests.inc()
    
    try:
        logger.info(f"Received query: {request.prompt[:50]}...")
        
        # Call Ollama with real LLM inference
        result = await ollama_client.generate(
            prompt=request.prompt,
            model="llama3.2:1b"
        )
        
        # Calculate latency
        latency = time.time() - start_time
        
        # Record metrics
        record_request(
            provider="ollama",
            status="success",
            duration=latency,
            cache_hit=False,
            tokens=result["tokens"]
        )
        
        # Build response
        response = QueryResponse(
            response=result["response"],
            provider="ollama",
            model=result["model"],
            cached=False,
            latency_ms=latency * 1000,
            tokens_used=result["tokens"]
        )
        
        logger.info(f"Query processed in {latency*1000:.2f}ms, {result['tokens']} tokens")
        
        return response
        
    except Exception as e:
        # Record error
        latency = time.time() - start_time
        record_request(
            provider="ollama",
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
