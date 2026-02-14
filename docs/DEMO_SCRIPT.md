# 🎬 LLMFlow — Demo Recording Script

> **Duration:** ~5 minutes
> **Tone:** Professional, business-oriented, confident
> **Audience:** Engineering managers, hiring teams, technical recruiters

---

## Pre-Recording Checklist

```powershell
# All services running
docker-compose up -d

# Clear cache for clean demo
curl -X POST http://localhost:8000/cache/clear

# Browser tabs ready:
#   Tab 1: http://localhost:8000/docs
#   Tab 2: http://localhost:3000 (Grafana)
#   Tab 3: https://github.com/B-VARUN-REDDY/llmflow

# VS Code open with:
#   gateway/main.py
#   gateway/routers/semantic_cache.py
#   gateway/routers/llm_router.py
#   gateway/database/db_client.py
#   docs/BENCHMARKS.md

# Terminal: font 16pt+, dark theme
# VS Code: zoom 150%, hide sidebar initially
```

---

## SCENE 1: Introduction (40 seconds)

### 🖥️ SHOW: GitHub repo — README with architecture diagram visible

### 🎤 SAY:

> "Organizations deploying LLM applications face a fundamental challenge — every API call costs money, adds latency, and creates a dependency on external providers. At scale, these costs compound fast. A mid-size product making 10,000 LLM calls a day can spend upward of $1,500 a month on a single provider.
>
> LLMFlow is my answer to that problem. It's an intelligent LLM inference gateway that sits between your application and multiple LLM providers, making real-time decisions about routing, caching, and cost optimization — cutting API costs by over 98% while improving response times by 48x.
>
> Let me walk you through how it works."

### ⌨️ DO:
- Slowly scroll to the Mermaid architecture diagram
- Hold on it for 3 seconds

---

## SCENE 2: System Architecture (45 seconds)

### 🖥️ SHOW: Architecture diagram, then switch to terminal

### 🎤 SAY:

> "The platform is built on a microservices architecture with six containerized services — all deployable with a single Docker Compose command.
>
> The request lifecycle has three decision layers. First, a two-tier caching system — exact match using Redis for identical queries, and semantic match using BERT embeddings for queries that are phrased differently but ask the same thing.
>
> If the cache misses, a complexity classifier scores the query on a 0-to-100 scale and routes it to the optimal provider — simple queries stay local on Ollama at zero cost, medium queries go to Groq for fast cloud inference, and complex reasoning tasks go to Gemini Pro.
>
> Everything is logged to PostgreSQL for analytics and instrumented with 15-plus Prometheus metrics feeding into Grafana."

### ⌨️ RUN:
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 🎤 SAY:
> "Six services, one command, fully operational."

---

## SCENE 3: Intelligent Routing in Action (50 seconds)

### 🖥️ SHOW: Terminal (large font)

### 🎤 SAY:
> "Let's see the routing intelligence in action. I'll send two queries of different complexity and watch the system make different decisions."

### ⌨️ RUN:
```powershell
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"What is 2+2?\"}" | python -m json.tool
```

### 🎤 SAY:
> "A straightforward factual query — complexity score of 15, classified as 'simple,' routed to Ollama. Zero API cost. Now a harder one."

### ⌨️ RUN:
```powershell
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"Analyze the trade-offs between consistency and availability in distributed systems using the CAP theorem\"}" | python -m json.tool
```

### 🎤 SAY:
> "This time — complexity score of 82, classified as 'complex,' automatically routed to Gemini Pro for superior reasoning. The system is making cost-quality trade-offs in real time, sending expensive queries to premium models only when the task demands it."

---

## SCENE 4: Semantic Caching — The Differentiator (90 seconds)

### 🖥️ SHOW: Terminal (this is the key scene — take your time)

### 🎤 SAY:
> "Now, the feature that delivers the biggest ROI — semantic caching. Traditional caches require an exact string match. In production, users rarely ask the same question the same way twice. Our system uses sentence-BERT to understand query *intent*."

### ⌨️ RUN:
```powershell
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"What is artificial intelligence?\"}" | python -m json.tool
```

### 🎤 SAY:
> "First request — cache miss, routed to a provider. About 600 milliseconds. Now the same query."

### ⌨️ RUN:
```powershell
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"What is artificial intelligence?\"}" | python -m json.tool
```

### 🎤 SAY:
> "Exact cache hit — 1 millisecond. That's expected. But here's where it gets interesting."

### ⌨️ RUN:
```powershell
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"Explain artificial intelligence to me\"}" | python -m json.tool
```

### 🎤 SAY (with emphasis):
> "Different query, same intent. The system detected a semantic similarity of 0.87 and returned the cached response in 13 milliseconds — no LLM call, no cost, no wait.
>
> That's a 45x latency improvement. In our benchmarks, this brought the overall cache hit rate from 37% with exact matching alone to 67% with semantic matching — an 80% improvement. For a product handling 10,000 queries a day, that's thousands of API calls eliminated."

### 🖥️ SWITCH TO: VS Code → `gateway/routers/semantic_cache.py`

### 🎤 SAY:
> "Under the hood — we generate 384-dimensional embeddings with the all-MiniLM-L6-v2 model, store them in Redis, and compute cosine similarity on every cache lookup. The threshold is configurable — currently set at 0.80."

### ⌨️ DO:
- Scroll to the `find_similar` method
- Pause 3-4 seconds so viewers can read the logic

---

## SCENE 5: Production Code Walkthrough (60 seconds)

### 🖥️ SHOW: VS Code — switch between files

### ⌨️ SHOW: `gateway/main.py` → scroll to `/query` endpoint (~line 190)

### 🎤 SAY:
> "The gateway is fully async — built on FastAPI with non-blocking I/O throughout. The query endpoint follows a clean pipeline: cache check, complexity classification, provider routing, result caching, and database logging — all in a single request cycle."

### ⌨️ SHOW: `gateway/routers/llm_router.py` → `route_query` method

### 🎤 SAY:
> "The router implements automatic fallback chains. If a provider hits a rate limit or goes down, the system gracefully degrades to the next available option. No manual intervention, no downtime."

### ⌨️ SHOW: `gateway/database/db_client.py`

### 🎤 SAY:
> "Every request is logged to PostgreSQL with full metadata — prompt, response, provider, latency, cache behavior, similarity scores, and cost estimates. This enables the kind of retrospective analytics that production ML teams need — what's our cache hit rate by provider? Which query categories are most expensive? Where should we invest in model optimization?"

---

## SCENE 6: Observability Stack (45 seconds)

### 🖥️ SHOW: Terminal, then Grafana

### ⌨️ RUN:
```powershell
curl -s http://localhost:8000/analytics/cache | python -m json.tool
```

### 🎤 SAY:
> "The analytics API pulls directly from PostgreSQL — cache hit rate, latency comparisons, cost breakdown, all queryable in real time."

### ⌨️ RUN:
```powershell
curl -s http://localhost:8000/analytics/complexity | python -m json.tool
```

### 🎤 SAY:
> "Complexity distribution — shows how queries are being classified and which providers are handling each tier."

### 🖥️ SWITCH TO: Grafana dashboard

### 🎤 SAY:
> "On the visualization side, Grafana ingests Prometheus metrics to provide real-time dashboards — 11 panels covering cache effectiveness, latency percentiles, provider health, and cost intelligence. This is the kind of operational visibility that lets you make data-driven decisions about model deployment."

### ⌨️ DO:
- Click through 2-3 panels, hover on charts briefly

---

## SCENE 7: Business Impact (30 seconds)

### 🖥️ SHOW: VS Code → `docs/BENCHMARKS.md`, scroll to Cost Analysis table

### 🎤 SAY:
> "Let's talk numbers. In a scenario of 10,000 queries per day — routing everything to a single cloud provider costs roughly $1,500 a month. With intelligent routing alone, that drops to $60. Add semantic caching, and it's $20 — a 98.7% reduction.
>
> Under load testing with 10 concurrent users, the system sustained over 50 queries per second with a 100% success rate and zero errors. Cached queries averaged 6 milliseconds at the 50th percentile."

### ⌨️ DO:
- Pause on the Executive Summary table
- Slowly scroll to the Cost Analysis section

---

## SCENE 8: Closing (20 seconds)

### 🖥️ SHOW: GitHub repo page

### 🎤 SAY:
> "LLMFlow demonstrates that the real challenge in production AI isn't building models — it's building the infrastructure that makes them economically viable. Intelligent caching, cost-aware routing, and comprehensive observability aren't nice-to-haves — they're what separates a prototype from a production system.
>
> The full source, benchmarks, and documentation are on GitHub. Thanks for watching."

---

## 📋 Files to Show — Quick Reference

| Scene | File | What to Highlight |
|-------|------|-------------------|
| 4 | `gateway/routers/semantic_cache.py` | `find_similar()` — cosine similarity logic |
| 5 | `gateway/main.py` | `/query` endpoint — async pipeline |
| 5 | `gateway/routers/llm_router.py` | `route_query()` — fallback chains |
| 5 | `gateway/database/db_client.py` | `log_query()` — metadata capture |
| 7 | `docs/BENCHMARKS.md` | Executive Summary + Cost Analysis tables |

## 📋 All Commands — Copy-Paste Ready

```powershell
# Scene 2: Running services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Scene 3: Simple query → Ollama
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"What is 2+2?\"}" | python -m json.tool

# Scene 3: Complex query → Gemini
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"Analyze the trade-offs between consistency and availability in distributed systems using the CAP theorem\"}" | python -m json.tool

# Scene 4: Fresh query (miss)
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"What is artificial intelligence?\"}" | python -m json.tool

# Scene 4: Exact cache hit
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"What is artificial intelligence?\"}" | python -m json.tool

# Scene 4: Semantic cache hit
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"Explain artificial intelligence to me\"}" | python -m json.tool

# Scene 6: Cache analytics
curl -s http://localhost:8000/analytics/cache | python -m json.tool

# Scene 6: Complexity distribution
curl -s http://localhost:8000/analytics/complexity | python -m json.tool
```

## 🎥 Recording Tips

- **Pace:** Speak slowly and deliberately — you're presenting to decision-makers
- **Pauses:** 2-3 seconds after every command output so viewers can read
- **Tone:** Confident, matter-of-fact — let the numbers do the talking
- **Energy:** Professional, not hype — "here's what it does and here's the proof"
- **Practice:** Run through once before recording so the commands flow naturally
- **Clear cache** before recording: `curl -X POST http://localhost:8000/cache/clear`
