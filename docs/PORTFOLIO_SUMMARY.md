# LLMFlow — Portfolio One-Pager

> **Project Type:** Production ML Infrastructure
> **Role Demonstrated:** Senior ML Engineer / MLOps Engineer
> **Status:** Complete & Deployable
> **GitHub:** [github.com/B-VARUN-REDDY/llmflow](https://github.com/B-VARUN-REDDY/llmflow)

---

## Elevator Pitch (30 seconds)

LLMFlow is an intelligent LLM gateway that **reduces AI costs by 98%** through semantic caching and smart routing. It demonstrates production ML engineering — not just model training, but the infrastructure that makes AI applications economically viable at scale.

**Key metrics:** 67% cache hit rate, 48x latency improvement, 100% uptime under load.

---

## Technical Highlights

| Area | Details |
|------|---------|
| **🧠 ML** | BERT embeddings (384-dim), cosine similarity, complexity classification |
| **🏗️ Architecture** | 6 Docker services, async FastAPI, two-layer cache, fallback chains |
| **📊 Observability** | 15+ Prometheus metrics, 11-panel Grafana dashboard, SQL analytics |

---

## Business Impact

| Metric | Value |
|--------|-------|
| Cost savings | **$1,480/month** (98.7% reduction vs naive) |
| Cache hit rate | **67%** (vs 37% exact-only, +80%) |
| Latency improvement | **48x** for cached queries (299ms → 6ms) |
| System reliability | **100%** success rate under 50 QPS |

---

## What Makes It Portfolio-Worthy

1. **Real ML** — Actual BERT embeddings, not just API wrappers
2. **Business Value** — 98% cost reduction with benchmarks to prove it
3. **Production Quality** — Monitoring, logging, error handling, load testing
4. **Well-Documented** — README, benchmarks, guides, SQL analytics
5. **Reproducible** — `docker-compose up` and it works in 2 minutes

---

## Demo Script (3 minutes)

### 1. Architecture (30s)
Open README → show Mermaid diagram → "6 services, 3 LLM providers, intelligent routing"

### 2. Intelligent Routing (1 min)
```bash
# Simple → Ollama (free, local)
curl -X POST http://localhost:8000/query -d '{"prompt": "What is 2+2?"}'

# Complex → Gemini (reasoning)
curl -X POST http://localhost:8000/query \
  -d '{"prompt": "Analyze distributed system trade-offs"}'
```

### 3. Semantic Caching (1 min)
```bash
# Fresh query (miss, 580ms)
curl -X POST http://localhost:8000/query \
  -d '{"prompt": "What is artificial intelligence?"}'

# Paraphrased (semantic hit, 11ms!)
curl -X POST http://localhost:8000/query \
  -d '{"prompt": "Explain artificial intelligence to me"}'
# → cached=true, cache_type=semantic, similarity=0.872
```

### 4. Dashboards (30s)
Open Grafana → cache hit rate (67%) → provider distribution → cost savings

---

## Resume Bullet

> **LLMFlow — Production LLM Gateway with AI-Powered Optimization**
> - Built intelligent routing system reducing API costs 98% through semantic caching & complexity classification
> - Implemented BERT-based semantic search achieving 67% cache hit rate (80% improvement vs exact matching)
> - Architected microservices platform with FastAPI, Redis, PostgreSQL, Prometheus monitoring
> - Achieved 48x latency reduction for cached queries under 50 QPS sustained load with zero errors
> - *Tech: Python, FastAPI, Sentence-BERT, Docker, Redis, PostgreSQL, Prometheus, Grafana*

---

## Tech Stack

`Python 3.11` · `FastAPI` · `Sentence-BERT` · `Docker Compose` · `Redis` · `PostgreSQL` · `Prometheus` · `Grafana` · `Ollama` · `Groq` · `Gemini`

---

**Contact:** [@B-VARUN-REDDY](https://github.com/B-VARUN-REDDY)

⭐ *This project demonstrates I can build production ML infrastructure that solves real business problems.*
