"""
Prometheus metrics instrumentation for LLMFlow.

This module defines all the metrics we'll track. Remember our discussion:
- Counters: Things that only go UP (requests, errors, tokens)
- Gauges: Things that go UP and DOWN (active requests, cache size)
- Histograms: Distributions (latency, response times)

Each metric here answers specific business/technical questions.
"""

from prometheus_client import Counter, Histogram, Gauge, Info


# ============================================================================
# COUNTER METRICS - "How many times did X happen?"
# ============================================================================

# Total requests processed by the gateway
# Labels let us break down by provider and status
llm_requests_total = Counter(
    'llm_requests_total',
    'Total number of LLM requests processed',
    ['provider', 'status']  # Labels for grouping
)
# Usage: llm_requests_total.labels(provider='ollama', status='success').inc()
# Question answered: "How many requests went to each provider? How many failed?"


# Cache performance metrics
llm_cache_hits_total = Counter(
    'llm_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']  # 'exact' or 'semantic'
)

llm_cache_misses_total = Counter(
    'llm_cache_misses_total',
    'Total number of cache misses'
)


# Cost tracking metrics
llm_cost_saved_total = Counter(
    'llm_cost_saved_total',
    'Estimated cost saved by caching (USD)',
    ['provider']
)

llm_estimated_cost_total = Counter(
    'llm_estimated_cost_total',
    'Estimated API cost incurred (USD)',
    ['provider']
)


# Token usage tracking (for cost calculation)
llm_tokens_used_total = Counter(
    'llm_tokens_used_total',
    'Total tokens consumed',
    ['provider']
)
# Question answered: "How much would this cost? Which provider uses most tokens?"


# Routing decisions (helps verify complexity classifier is working)
llm_routing_decisions_total = Counter(
    'llm_routing_decisions_total',
    'Total routing decisions made',
    ['complexity_bucket']  # simple/medium/complex
)
# Question answered: "Is our router smart? What % of queries are complex?"


# ============================================================================
# HISTOGRAM METRICS - "What's the DISTRIBUTION of X?"
# ============================================================================

# Request latency - THE most important metric for user experience
llm_request_duration_seconds = Histogram(
    'llm_request_duration_seconds',
    'Request duration in seconds',
    ['provider', 'cache_hit'],  # Break down by provider and whether cached
    # Buckets define our latency SLOs:
    # - 0.01s (10ms): Ideal for cached responses
    # - 0.1s (100ms): Great for simple queries
    # - 0.5s (500ms): Acceptable for medium queries
    # - 1.0s: Upper bound for user patience
    # - 5.0s: Complex queries might take this long
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)
# Question answered: "What's p50/p95/p99 latency? Are users experiencing delays?"


# ============================================================================
# GAUGE METRICS - "What's the current value of X?"
# ============================================================================

# Active requests (helps detect traffic spikes and potential overload)
llm_active_requests = Gauge(
    'llm_active_requests',
    'Number of requests currently being processed'
)
# Question answered: "Is the system overloaded? How many concurrent requests?"


# System info (static metadata about the deployment)
llm_gateway_info = Info(
    'llm_gateway_info',
    'Information about the LLM gateway'
)
# Set once at startup with version, build info, etc.


# ============================================================================
# HELPER FUNCTIONS - Make instrumentation easier
# ============================================================================

def get_cache_hit_rate() -> float:
    """
    Calculate current cache hit rate.
    
    Returns:
        float: Cache hit rate between 0.0 and 1.0
        
    Note: This is a derived metric - we calculate it from counters.
    Grafana will do this calculation too, but having it in code
    is useful for debugging and testing.
    """
    hits = llm_cache_hits_total._value._value  # Access internal counter value
    misses = llm_cache_misses_total._value._value
    
    total = hits + misses
    if total == 0:
        return 0.0
    
    return hits / total


# Provider cost per 1K tokens (USD) - approximate pricing
PROVIDER_COSTS = {
    'ollama': 0.0,       # Free (local)
    'groq': 0.0003,      # ~$0.30 per 1M tokens (free tier)
    'gemini': 0.00025,   # ~$0.25 per 1M tokens (flash)
}


def estimate_cost(provider: str, tokens: int) -> float:
    """Estimate the cost of an LLM call in USD."""
    cost_per_1k = PROVIDER_COSTS.get(provider, 0.001)
    return (tokens / 1000) * cost_per_1k


def record_request(
    provider: str,
    status: str,
    duration: float,
    cache_hit: bool,
    tokens: int = 0,
    cache_type: str = "none"
):
    """
    Record a complete request with all metrics including cost.
    
    Args:
        provider: Which LLM provider handled this request
        status: 'success', 'error', etc.
        duration: Request duration in seconds
        cache_hit: Was this served from cache?
        tokens: Tokens used (0 if cached)
        cache_type: 'none', 'exact', or 'semantic'
    """
    # Record the request
    llm_requests_total.labels(provider=provider, status=status).inc()
    
    # Record latency
    llm_request_duration_seconds.labels(
        provider=provider,
        cache_hit=str(cache_hit)
    ).observe(duration)
    
    # Record token usage (only if not cached)
    if tokens > 0:
        llm_tokens_used_total.labels(provider=provider).inc(tokens)
    
    # Record cache hit/miss + cost
    if cache_hit:
        llm_cache_hits_total.labels(cache_type=cache_type).inc()
        # Calculate cost saved by caching
        saved = estimate_cost(provider, tokens) if tokens > 0 else estimate_cost(provider, 150)  # estimate 150 tokens
        llm_cost_saved_total.labels(provider=provider).inc(saved)
    else:
        llm_cache_misses_total.inc()
        # Record actual cost
        cost = estimate_cost(provider, tokens)
        llm_estimated_cost_total.labels(provider=provider).inc(cost)
