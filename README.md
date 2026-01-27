# 🚀 LLMFlow - Production LLM Gateway with Cost Intelligence

> An intelligent LLM inference platform that routes queries to optimal providers, caches aggressively, and provides real-time cost/performance analytics.

![Project Status](https://img.shields.io/badge/status-in_development-yellow)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)

## What This Demonstrates

This project showcases production ML engineering skills:
- ✅ Multi-provider LLM routing with intelligent complexity classification
- ✅ Multi-layer caching (exact + semantic)
- ✅ Comprehensive monitoring (Prometheus + Grafana)
- ✅ Realistic traffic simulation for testing
- ✅ Production-quality architecture (Docker, async, error handling)

## Tech Stack

- **LLM Providers:** Ollama (local), Groq API, Google Gemini
- **Gateway:** FastAPI (async)
- **Caching:** Redis
- **Monitoring:** Prometheus + Grafana
- **Database:** PostgreSQL
- **Orchestration:** Docker Compose

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/llmflow
cd llmflow

# Setup environment
cp .env.example .env
# Edit .env and add your API keys (optional for Ollama-only)

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
- **Prometheus:** http://localhost:9090 (Metrics & queries)
- **Grafana:** http://localhost:3000 (Dashboards - admin/admin)
- **Health Check:** http://localhost:8000/health

## Quick Test

```bash
# Send a test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is machine learning?"}'

# View metrics
curl http://localhost:8000/metrics
```

## Project Structure

```
llmflow/
├── gateway/                   # FastAPI application
│   ├── main.py               # App entry point
│   ├── config.py             # Configuration management
│   ├── monitoring/           # Prometheus metrics
│   ├── routers/              # Request routing logic (coming soon)
│   └── providers/            # LLM provider clients (coming soon)
├── monitoring/
│   ├── prometheus/           # Prometheus config
│   └── grafana/              # Dashboard definitions (coming soon)
├── simulator/                # Traffic generation (coming soon)
├── docs/                     # Documentation (coming soon)
├── tests/                    # Test suite (coming soon)
└── docker-compose.yml        # Service orchestration
```

## Development Status

### Phase 1: Foundation ✅ COMPLETED
- [x] Project structure initialized
- [x] FastAPI gateway with async handling
- [x] Prometheus metrics instrumentation
- [x] Docker Compose orchestration
- [x] Basic health checks and testing

### Phase 1B: Monitoring Stack (In Progress)
- [ ] Grafana dashboard setup
- [ ] Real Ollama integration
- [ ] End-to-end query flow

### Phase 2: Multi-Provider Routing (Planned)
- [ ] Complexity classifier
- [ ] Router logic (Ollama/Groq/Gemini)
- [ ] Redis caching layer
- [ ] Provider fallback handling

### Phase 3: Advanced Features (Planned)
- [ ] Semantic caching
- [ ] Prompt compression
- [ ] Traffic simulator
- [ ] Cost tracking dashboard

### Phase 4: Polish (Planned)
- [ ] Comprehensive documentation
- [ ] Architecture diagrams
- [ ] Demo mode
- [ ] Portfolio video

## Current Metrics

The gateway currently tracks:

| Metric | Type | Purpose |
|--------|------|---------|
| `llm_requests_total` | Counter | Total requests by provider & status |
| `llm_request_duration_seconds` | Histogram | Latency distribution (p50/p95/p99) |
| `llm_cache_hits_total` | Counter | Cache effectiveness |
| `llm_cache_misses_total` | Counter | Cache miss rate |
| `llm_tokens_used_total` | Counter | Token consumption by provider |
| `llm_active_requests` | Gauge | Current concurrent requests |
| `llm_routing_decisions_total` | Counter | Routing distribution |

## Useful Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View logs
docker-compose logs -f [service_name]

# Remove all data and start fresh
docker-compose down -v
```

## Documentation

See [docs/](./docs/) for detailed documentation:
- Architecture overview (coming soon)
- API reference (coming soon)
- Deployment guide (coming soon)
- Metrics guide (coming soon)

## Contributing

This is a portfolio project, but feedback is welcome! Feel free to open issues for:
- Bug reports
- Feature suggestions
- Documentation improvements

## License

MIT License - See LICENSE file for details

---

**Built to demonstrate production ML engineering capabilities for portfolio purposes.**

Last Updated: January 27, 2026
