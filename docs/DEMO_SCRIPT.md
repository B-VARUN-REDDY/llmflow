# 🎬 LLMFlow Demo Recording Script

> **Total Duration:** ~5 minutes
> **Format:** Screen recording + voiceover
> **Tool:** OBS Studio (free) or any screen recorder

---

## Pre-Recording Setup

Before hitting record, make sure these are ready:

```powershell
# 1. All services running
docker-compose up -d

# 2. Clear cache for a clean demo
curl -X POST http://localhost:8000/cache/clear

# 3. Open these tabs in your browser:
#    Tab 1: http://localhost:8000/docs        (Swagger API docs)
#    Tab 2: http://localhost:3000             (Grafana - login admin/admin)
#    Tab 3: https://github.com/B-VARUN-REDDY/llmflow  (GitHub repo)

# 4. Open VS Code with these files ready:
#    - README.md
#    - gateway/main.py
#    - gateway/routers/semantic_cache.py
#    - gateway/routers/llm_router.py
#    - gateway/database/db_client.py

# 5. Have a terminal open and ready
```

---

## SCENE 1: Introduction (30 seconds)

### 🖥️ SHOW ON SCREEN:
GitHub repo page (README.md visible with architecture diagram)

### 🎤 SAY:
> "Hey, I'm Varun. This is LLMFlow — a production-grade LLM gateway I built that reduces AI inference costs by 98% through intelligent routing and semantic caching.
>
> It's not just another ChatGPT wrapper. It's a full microservices platform with FastAPI, Redis, PostgreSQL, Prometheus, and Grafana — all orchestrated with Docker Compose."

### ⌨️ DO:
- Scroll down slowly through the README to show the architecture diagram
- Pause on the Mermaid diagram for 3-4 seconds so viewers can read it

---

## SCENE 2: Architecture Overview (45 seconds)

### 🖥️ SHOW ON SCREEN:
README.md architecture diagram, then switch to terminal

### 🎤 SAY:
> "The architecture has three layers of intelligence.
>
> First, when a query comes in, we check a two-layer cache — exact match in Redis for identical queries, and semantic match using BERT embeddings for similar questions.
>
> If the cache misses, a complexity classifier scores the query from 0 to 100. Simple questions go to Ollama running locally — totally free. Medium queries go to Groq's LPU for ultra-fast inference. Complex reasoning tasks go to Gemini Pro.
>
> Everything gets logged to PostgreSQL for analytics and tracked with Prometheus metrics."

### ⌨️ DO:
Show running containers:
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 🎤 SAY:
> "Here you can see all 6 services running — gateway, Redis, PostgreSQL, Ollama, Prometheus, and Grafana. One command to deploy everything."

---

## SCENE 3: Live Query Demo — Intelligent Routing (60 seconds)

### 🖥️ SHOW ON SCREEN:
Terminal (make font size large, at least 16pt)

### 🎤 SAY:
> "Let me show you the intelligent routing in action. Watch how different queries go to different providers."

### ⌨️ RUN:
```powershell
# Simple query → should route to Ollama
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"What is 2+2?\"}" | python -m json.tool
```

### 🎤 SAY:
> "This simple math question got a complexity score of 15, classified as 'simple,' and routed to Ollama — our free local model. Notice it took about 400 milliseconds."

### ⌨️ RUN:
```powershell
# Complex query → should route to Gemini
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"Analyze the trade-offs between consistency and availability in distributed systems using the CAP theorem\"}" | python -m json.tool
```

### 🎤 SAY:
> "Now this complex systems design question scored 82, classified as 'complex,' and was routed to Gemini Pro — our most capable model. Different queries, different providers, optimized for cost and quality."

---

## SCENE 4: Semantic Caching — The Star Feature (90 seconds)

### 🖥️ SHOW ON SCREEN:
Terminal (this is the most important part — go slow)

### 🎤 SAY:
> "Now here's the feature I'm most proud of — semantic caching with BERT embeddings. Traditional caches only match identical queries. Ours matches *similar* ones."

### ⌨️ RUN (pause between each):
```powershell
# Query 1: Fresh query (cache miss)
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"What is artificial intelligence?\"}" | python -m json.tool
```

### 🎤 SAY:
> "First query — cache miss, as expected. Took about 600 milliseconds. Now watch what happens when I ask the *same thing differently...*"

### ⌨️ RUN:
```powershell
# Query 2: Exact repeat (exact cache hit)
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"What is artificial intelligence?\"}" | python -m json.tool
```

### 🎤 SAY:
> "Exact same query — cache type is 'exact,' just 1 millisecond. That's a simple hash lookup. But here's where it gets interesting..."

### ⌨️ RUN:
```powershell
# Query 3: Paraphrased (semantic cache hit!)
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"Explain artificial intelligence to me\"}" | python -m json.tool
```

### 🎤 SAY (with enthusiasm):
> "Look at that! 'Explain artificial intelligence to me' — a completely *different* query — but it hit the semantic cache with a similarity score of 0.87. Only 13 milliseconds instead of 600. That's a 45x speedup.
>
> Under the hood, we're generating 384-dimensional BERT embeddings with sentence-transformers, storing them in Redis, and computing cosine similarity in real-time. The threshold is 0.80 — anything above that is considered a match."

### 🖥️ THEN SHOW:
Switch to VS Code → open `gateway/routers/semantic_cache.py`

### 🎤 SAY:
> "Here's the semantic cache implementation. We use the all-MiniLM-L6-v2 model — it's only 80 megabytes but produces high-quality embeddings. The find_similar method scans all cached embeddings and returns the best match above our threshold."

### ⌨️ DO:
- Scroll to the `find_similar` method (around line 140)
- Pause so viewers can see the cosine similarity logic
- Then scroll to `embedding_to_bytes` to show the Redis storage approach

---

## SCENE 5: Code Walkthrough (60 seconds)

### 🖥️ SHOW ON SCREEN:
VS Code — switch between files

### 🎤 SAY:
> "Let me quickly walk through the key code."

### ⌨️ SHOW FILE: `gateway/main.py`
Scroll to the `/query` endpoint (around line 190)

### 🎤 SAY:
> "The main query endpoint follows a clean flow — check cache, classify complexity, route to provider, store result, log to database. Everything is async with FastAPI."

### ⌨️ SHOW FILE: `gateway/routers/llm_router.py`
Scroll to the `route_query` method

### 🎤 SAY:
> "The router has built-in fallback chains. If Groq hits a rate limit, we automatically fall back to Gemini, then to Ollama. Graceful degradation — the system never hard fails."

### ⌨️ SHOW FILE: `gateway/routers/cache_manager.py`
Scroll to the `get` method

### 🎤 SAY:
> "The cache manager implements a two-layer strategy. Layer 1 is exact hash match in Redis — sub-millisecond. Layer 2 is semantic search with BERT embeddings. If both miss, we call the LLM and store the result in both layers."

### ⌨️ SHOW FILE: `gateway/database/db_client.py`

### 🎤 SAY:
> "Every query gets logged to PostgreSQL with full metadata — prompt, provider, latency, cache type, similarity score, cost estimate. This powers our SQL analytics endpoints."

---

## SCENE 6: Analytics & Monitoring (45 seconds)

### 🖥️ SHOW ON SCREEN:
Terminal first, then switch to Grafana

### 🎤 SAY:
> "All this data flows into analytics endpoints and dashboards."

### ⌨️ RUN:
```powershell
# Show analytics from PostgreSQL
curl -s http://localhost:8000/analytics/cache | python -m json.tool
```

### 🎤 SAY:
> "The cache analytics endpoint pulls from PostgreSQL — you can see the hit rate, average cached versus uncached latency, broken down by provider."

### ⌨️ RUN:
```powershell
curl -s http://localhost:8000/analytics/recent | python -m json.tool
```

### 🎤 SAY:
> "And here's the full query log — every request with its classification, provider, cache status, and latency."

### 🖥️ SWITCH TO:
Grafana dashboard (Tab 2) → navigate to LLMFlow dashboard

### 🎤 SAY:
> "On the Grafana side, we have 11 panels tracking everything — cache hit rate over time, latency percentiles, cost savings, provider distribution. All powered by Prometheus metrics that the gateway exposes."

### ⌨️ DO:
- Click through a few panels
- Hover over charts to show tooltips
- Spend ~10 seconds on the dashboard

---

## SCENE 7: Performance Numbers (30 seconds)

### 🖥️ SHOW ON SCREEN:
Switch to VS Code → open `docs/BENCHMARKS.md`

### 🎤 SAY:
> "Finally — real benchmark results. Under load testing with 10 concurrent users, the system handled over 50 queries per second with zero errors. 
>
> The cache hit rate stabilized at 67% — that means two-thirds of queries never even touch an LLM. Cached queries average 6 milliseconds. And the cost model shows a 98% reduction compared to routing everything to a cloud provider.
>
> These aren't theoretical numbers — they're from actual load tests I ran and documented."

### ⌨️ DO:
- Scroll through the benchmarks tables slowly
- Pause on the "Executive Summary" table
- Pause on the "Cost Analysis" section

---

## SCENE 8: Closing (15 seconds)

### 🖥️ SHOW ON SCREEN:
GitHub repo page

### 🎤 SAY:
> "That's LLMFlow — an intelligent LLM gateway with semantic caching, smart routing, and production-grade monitoring. The entire stack deploys with one Docker Compose command.
>
> Check out the repo — link in the description. Thanks for watching."

---

## 📋 Quick Reference: Files to Show

| When | File | What to Highlight |
|------|------|-------------------|
| Scene 4 | `gateway/routers/semantic_cache.py` | `find_similar()` method, cosine similarity |
| Scene 5 | `gateway/main.py` | `/query` endpoint (~line 190) |
| Scene 5 | `gateway/routers/llm_router.py` | `route_query()`, fallback logic |
| Scene 5 | `gateway/routers/cache_manager.py` | `get()` — two-layer cache |
| Scene 5 | `gateway/database/db_client.py` | `log_query()` — async DB writes |
| Scene 7 | `docs/BENCHMARKS.md` | Executive summary table, cost analysis |

## 📋 Quick Reference: All Commands

```powershell
# Scene 2: Show containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Scene 3: Simple query
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"What is 2+2?\"}" | python -m json.tool

# Scene 3: Complex query
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"Analyze the trade-offs between consistency and availability in distributed systems using the CAP theorem\"}" | python -m json.tool

# Scene 4: Fresh query
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"What is artificial intelligence?\"}" | python -m json.tool

# Scene 4: Exact hit
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"What is artificial intelligence?\"}" | python -m json.tool

# Scene 4: Semantic hit
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"Explain artificial intelligence to me\"}" | python -m json.tool

# Scene 6: Analytics
curl -s http://localhost:8000/analytics/cache | python -m json.tool
curl -s http://localhost:8000/analytics/recent | python -m json.tool
```

## 🎥 Recording Tips

1. **Font size:** Set terminal to 16pt+ so text is readable
2. **VS Code:** Use a dark theme, zoom to 150%
3. **Browser:** Hide bookmarks bar for cleaner look
4. **Pace:** Pause 2-3 seconds after each command output so viewers can read
5. **Clear cache** before starting: `curl -X POST http://localhost:8000/cache/clear`
6. **Practice once** before recording — the commands should flow naturally
7. **Energy:** Sound confident, not scripted — these are YOUR results
