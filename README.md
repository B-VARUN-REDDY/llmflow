# 🚀 LLMFlow - Production LLM Gateway with Cost Intelligence

> An intelligent LLM inference platform that routes queries to optimal providers, caches aggressively, and provides real-time cost/performance analytics.

![Project Status](https://img.shields.io/badge/status-in_development-yellow)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)

## What This Demonstrates

This project showcases production ML engineering skills:
- ✅ Multi-provider LLM routing with intelligent complexity classification
- ✅ Redis caching (24,000x speedup on cached queries)
- ✅ Comprehensive monitoring (Prometheus + Grafana)
- ✅ Fallback handling for provider resilience
- ✅ Production-quality architecture (Docker, async, error handling)

## Tech Stack

- **LLM Providers:** Ollama (local), Groq API, Google Gemini
- **Gateway:** FastAPI (async)
- **Caching:** Redis (exact-match, 1-hour TTL)
- **Monitoring:** Prometheus + Grafana
- **Database:** PostgreSQL
- **Orchestration:** Docker Compose (6 services)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LLMFlow Gateway                      │
│                                                         │
│  Query ──► Cache Check ──► Complexity Classifier        │
│                │                    │                    │
│            HIT │              ┌─────┼─────┐             │
│             ▼  │              ▼     ▼     ▼             │
│           Redis│          Ollama  Groq  Gemini          │
│                │         (simple)(medium)(complex)       │
│                │              │     │     │              │
│                │              └─────┼─────┘              │
│                │                    ▼                    │
│                │              Cache Store               │
│                └──────────► Response ──► Metrics         │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/B-VARUN-REDDY/llmflow
cd llmflow

# Setup environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY and GEMINI_API_KEY (optional)

# Start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f gateway
```

## Access Points

Once running:
- **Gateway API:** http://localhost:8000/docs (Interactive API docs)
- **Health Check:** http://localhost:8000/health
- **Cache Stats:** http://localhost:8000/cache/stats
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (admin/admin)

## API Examples

```bash
# Simple query (auto-routes to Ollama)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2+2?"}'

# Complex query (auto-routes to Gemini/Groq)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze microservices vs monolithic architectures"}'

# Force a specific provider
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "provider": "groq"}'

# Check health with provider + cache status
curl http://localhost:8000/health

# View cache stats
curl http://localhost:8000/cache/stats

# Clear cache
curl -X POST http://localhost:8000/cache/clear
```

## Intelligent Routing

Queries are classified by complexity (0-100) and routed to the optimal provider:

| Complexity | Score | Provider | Why |
|-----------|-------|----------|-----|
| Simple | 0-30 | Ollama (local) | Free, fast for simple tasks |
| Medium | 31-70 | Groq (llama-3.3-70b) | Free tier, very fast inference |
| Complex | 71-100 | Gemini (2.0-flash) | Best reasoning for hard queries |

If the primary provider fails, the router automatically falls back through a chain of alternatives.

## Caching Performance

| Metric | Value |
|--------|-------|
| Cache MISS (full LLM call) | ~5,000-30,000ms |
| Cache HIT (Redis lookup) | ~1ms |
| Speedup | **24,000x** |
| TTL | 1 hour (configurable) |
| Strategy | Exact-match (SHA-256 hash) |

## Project Structure

```
llmflow/
├── gateway/                   # FastAPI application
│   ├── main.py               # App entry point + routes
│   ├── config.py             # Environment configuration
│   ├── Dockerfile            # Gateway container
│   ├── monitoring/
│   │   └── metrics.py        # Prometheus metrics definitions
│   ├── providers/
│   │   ├── ollama_client.py  # Local Ollama provider
│   │   ├── groq_client.py    # Groq cloud provider
│   │   └── gemini_client.py  # Google Gemini provider
│   └── routers/
│       ├── complexity_classifier.py  # Query analysis (0-100)
│       ├── llm_router.py     # Routing + fallback logic
│       └── cache_manager.py  # Redis caching layer
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml    # Scrape configuration
│   └── grafana/
│       └── dashboards/       # Pre-built dashboards
├── simulator/                # Traffic generation tools
├── docs/                     # Documentation
├── docker-compose.yml        # 6-service orchestration
├── .env.example              # Environment template
└── README.md
```

## Development Status

### Phase 1: Foundation ✅
- [x] FastAPI gateway with async handling
- [x] Prometheus metrics instrumentation (11 metrics)
- [x] Docker Compose orchestration (6 services)
- [x] Ollama integration with llama3.2:1b
- [x] Grafana dashboards (8 panels)

### Phase 2: Multi-Provider Routing ✅
- [x] Complexity classifier (heuristic, score 0-100)
- [x] Router logic (Ollama → Groq → Gemini)
- [x] Provider fallback handling
- [x] Redis exact-match caching (24,000x speedup)
- [x] Cache stats + clear endpoints

### Phase 3: Advanced Features (Planned)
- [ ] Semantic caching (similar query matching)
- [ ] Prompt compression
- [ ] Cost tracking per provider
- [ ] Advanced traffic simulator

### Phase 4: Polish (Planned)
- [ ] Comprehensive test suite
- [ ] Architecture diagrams
- [ ] Demo mode
- [ ] Portfolio video

## Metrics Tracked

| Metric | Type | Purpose |
|--------|------|---------|
| `llm_requests_total` | Counter | Total requests by provider & status |
| `llm_request_duration_seconds` | Histogram | Latency distribution (p50/p95/p99) |
| `llm_cache_hits_total` | Counter | Cache effectiveness |
| `llm_cache_misses_total` | Counter | Cache miss rate |
| `llm_tokens_used_total` | Counter | Token consumption by provider |
| `llm_active_requests` | Gauge | Current concurrent requests |
| `llm_routing_decisions_total` | Counter | Routing distribution by complexity |
| `llm_gateway_info` | Info | Gateway version & config |

## Useful Commands

```bash
# Start all services
docker-compose up -d --build

# Stop all services
docker-compose down

# View logs
docker-compose logs -f gateway

# Remove all data and start fresh
docker-compose down -v

# Check service status
docker-compose ps
```

## License

MIT License - See LICENSE file for details

---

**Built to demonstrate production ML engineering capabilities.**

Last Updated: February 11, 2026
