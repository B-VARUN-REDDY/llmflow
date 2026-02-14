# 🎬 LLMFlow — Demo Recording Script

> **Duration:** ~5 minutes
> **Recording Tool:** OBS Studio or screen recorder of choice
> **IDE:** Antigravity IDE (screen being recorded)
> **Audience:** Engineering managers, hiring teams, technical recruiters

---

## Pre-Recording Setup

**Step 1 — Make sure all Docker services are running**
Open Antigravity terminal and run:
```
docker-compose up -d
```

**Step 2 — Clear the cache for a clean demo**
In the same terminal, run:
```
curl.exe -X POST http://localhost:8000/cache/clear
```

**Step 3 — Open these files in Antigravity IDE editor tabs (click each file in the sidebar)**
1. `README.md` (root)
2. `gateway/main.py`
3. `gateway/routers/semantic_cache.py`
4. `gateway/routers/llm_router.py`
5. `gateway/routers/cache_manager.py`
6. `gateway/database/db_client.py`
7. `docs/BENCHMARKS.md`

**Step 4 — Open these browser tabs**
1. `http://localhost:3000` → Grafana (login: admin / admin)
2. `https://github.com/B-VARUN-REDDY/llmflow` → your GitHub repo

**Step 5 — Start OBS recording, then begin**

---

## SCENE 1: Introduction (40 seconds)

### What to show:
Open your **browser** to the **GitHub repo page** so the README is visible with the architecture diagram at the top.

### What to say:

> "Organizations deploying LLM applications face a fundamental challenge — every API call costs money, adds latency, and creates a dependency on external providers. At scale, these costs compound fast. A mid-size product making 10,000 LLM calls a day can spend upward of $1,500 a month on a single provider.
>
> LLMFlow is my answer to that problem. It's an intelligent LLM inference gateway that sits between your application and multiple LLM providers, making real-time decisions about routing, caching, and cost optimization — cutting API costs by over 98% while improving response times by 48x.
>
> Let me walk you through how it works."

### What to do:
Slowly scroll down the GitHub README to reveal the **Mermaid architecture diagram**. Pause on it for 3-4 seconds so the viewer can read it.

---

## SCENE 2: System Architecture (45 seconds)

### What to show:
Stay on the **architecture diagram** in the browser for the first half. Then **switch to Antigravity IDE** and open the **terminal panel** at the bottom.

### What to say:

> "The platform is built on a microservices architecture with six containerized services — all deployable with a single Docker Compose command.
>
> The request lifecycle has three decision layers. First, a two-tier caching system — exact match using Redis for identical queries, and semantic match using BERT embeddings for queries that are phrased differently but ask the same thing.
>
> If the cache misses, a complexity classifier scores the query on a 0-to-100 scale and routes it to the optimal provider — simple queries stay local on Ollama at zero cost, medium queries go to Groq for fast cloud inference, and complex reasoning tasks go to Gemini Pro.
>
> Everything is logged to PostgreSQL for analytics and instrumented with 15-plus Prometheus metrics feeding into Grafana."

### What to run in the Antigravity terminal:
```
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### What to say after the output appears:
> "Six services, one command, fully operational."

---

## SCENE 3: Intelligent Routing in Action (50 seconds)

### What to show:
Stay in **Antigravity IDE** with the **terminal panel** visible and large enough to read.

### What to say:
> "Let's see the routing intelligence in action. I'll send two queries of different complexity and watch the system make different decisions."

### What to run in the terminal:
```
curl.exe -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{\"prompt\": \"What is 2+2?\"}' | python -m json.tool
```

Wait for the response to appear.

### What to say:
> "A straightforward factual query — complexity score of 15, classified as 'simple,' routed to Ollama. Zero API cost. Now a harder one."

### What to run next:
```
curl.exe -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{\"prompt\": \"Analyze the trade-offs between consistency and availability in distributed systems using the CAP theorem\"}' | python -m json.tool
```

Wait for the response to appear.

### What to say:
> "This time — complexity score of 82, classified as 'complex,' automatically routed to Gemini Pro for superior reasoning. The system is making cost-quality trade-offs in real time, sending expensive queries to premium models only when the task demands it."

---

## SCENE 4: Semantic Caching — The Differentiator (90 seconds)

**This is the most important scene. Go slowly.**

### What to show:
Stay in **Antigravity IDE** with the **terminal panel** visible.

### What to say:
> "Now, the feature that delivers the biggest ROI — semantic caching. Traditional caches require an exact string match. In production, users rarely ask the same question the same way twice. Our system uses sentence-BERT to understand query intent."

### What to run (Query 1 — cache miss):
```
curl.exe -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{\"prompt\": \"What is artificial intelligence?\"}' | python -m json.tool
```

Wait for response.

### What to say:
> "First request — cache miss, as expected. About 600 milliseconds. Now the same query."

### What to run (Query 2 — exact cache hit):
```
curl.exe -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{\"prompt\": \"What is artificial intelligence?\"}' | python -m json.tool
```

Wait for response.

### What to say:
> "Exact cache hit — 1 millisecond. That's a simple hash lookup. But here's where it gets interesting."

### What to run (Query 3 — SEMANTIC cache hit):
```
curl.exe -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{\"prompt\": \"Explain artificial intelligence to me\"}' | python -m json.tool
```

Wait for response.

### What to say (with emphasis):
> "Different query, same intent. The system detected a semantic similarity of 0.87 and returned the cached response in 13 milliseconds — no LLM call, no cost, no wait.
>
> That's a 45x latency improvement. In our benchmarks, this brought the overall cache hit rate from 37% with exact matching alone to 67% with semantic matching — an 80% improvement. For a product handling 10,000 queries a day, that's thousands of API calls eliminated."

### Now switch to showing the code:
**In the Antigravity editor**, click on the `gateway/routers/semantic_cache.py` tab. Scroll down to the `find_similar` method.

### What to say while showing the code:
> "Under the hood — we generate 384-dimensional embeddings with the all-MiniLM-L6-v2 model, store them in Redis, and compute cosine similarity on every cache lookup. The threshold is configurable — currently set at 0.80."

Pause on the `find_similar` method for 3-4 seconds so viewers can read the cosine similarity logic.

---

## SCENE 5: Production Code Walkthrough (60 seconds)

### What to show:
Stay in **Antigravity IDE editor**. You'll click between file tabs.

---

**File 1:** Click the **`gateway/main.py`** tab. Scroll to the `/query` endpoint (around line 190).

### What to say:
> "The gateway is fully async — built on FastAPI with non-blocking I/O throughout. The query endpoint follows a clean pipeline: cache check, complexity classification, provider routing, result caching, and database logging — all in a single request cycle."

Pause 3 seconds on the code.

---

**File 2:** Click the **`gateway/routers/llm_router.py`** tab. Scroll to the `route_query` method.

### What to say:
> "The router implements automatic fallback chains. If a provider hits a rate limit or goes down, the system gracefully degrades to the next available option. No manual intervention, no downtime."

Pause 3 seconds on the code.

---

**File 3:** Click the **`gateway/database/db_client.py`** tab. Show the `log_query` method.

### What to say:
> "Every request is logged to PostgreSQL with full metadata — prompt, response, provider, latency, cache behavior, similarity scores, and cost estimates. This enables the kind of retrospective analytics that production ML teams need — what's our cache hit rate by provider? Which query categories are most expensive? Where should we invest in model optimization?"

---

## SCENE 6: Observability Stack (45 seconds)

### What to show:
Switch back to the **Antigravity terminal panel**.

### What to run:
```
curl.exe -s http://localhost:8000/analytics/cache | python -m json.tool
```

Wait for response.

### What to say:
> "The analytics API pulls directly from PostgreSQL — cache hit rate, latency comparisons, cost breakdown, all queryable in real time."

### What to run next:
```
curl.exe -s http://localhost:8000/analytics/complexity | python -m json.tool
```

Wait for response.

### What to say:
> "Complexity distribution — shows how queries are being classified and which providers are handling each tier."

### Now switch to the browser:
Open the **Grafana tab** (`http://localhost:3000`). Navigate to the LLMFlow dashboard.

### What to say:
> "On the visualization side, Grafana ingests Prometheus metrics to provide real-time dashboards — 11 panels covering cache effectiveness, latency percentiles, provider health, and cost intelligence. This is the kind of operational visibility that lets you make data-driven decisions about model deployment."

### What to do:
Click through 2-3 panels on the Grafana dashboard. Hover over charts briefly to show tooltips. Spend about 10 seconds here.

---

## SCENE 7: Business Impact (30 seconds)

### What to show:
Switch back to **Antigravity IDE**. Click the **`docs/BENCHMARKS.md`** tab. Scroll to the **Executive Summary** table at the top.

### What to say:
> "Let's talk numbers. In a scenario of 10,000 queries per day — routing everything to a single cloud provider costs roughly $1,500 a month. With intelligent routing alone, that drops to $60. Add semantic caching, and it's $20 — a 98.7% reduction.
>
> Under load testing with 10 concurrent users, the system sustained over 50 queries per second with a 100% success rate and zero errors. Cached queries averaged 6 milliseconds at the 50th percentile."

### What to do:
Slowly scroll down to the **Cost Analysis** section. Pause so viewers can see the cost comparison table.

---

## SCENE 8: Closing (20 seconds)

### What to show:
Switch to **browser** → GitHub repo page.

### What to say:
> "LLMFlow demonstrates that the real challenge in production AI isn't building models — it's building the infrastructure that makes them economically viable. Intelligent caching, cost-aware routing, and comprehensive observability aren't nice-to-haves — they're what separates a prototype from a production system.
>
> The full source, benchmarks, and documentation are on GitHub. Thanks for watching."

---

## 📋 Complete Scene Map

| Scene | Duration | Where to Look | What Viewers See |
|-------|----------|---------------|-----------------|
| 1. Intro | 40s | **Browser** → GitHub README | Architecture diagram |
| 2. Architecture | 45s | **Browser** → diagram, then **IDE terminal** | `docker ps` output |
| 3. Routing | 50s | **IDE terminal** | Two curl commands, different providers |
| 4. Semantic Cache | 90s | **IDE terminal** → then **editor** `semantic_cache.py` | 3 queries + code |
| 5. Code Walk | 60s | **IDE editor** → 3 file tabs | `main.py` → `llm_router.py` → `db_client.py` |
| 6. Analytics | 45s | **IDE terminal** → then **browser** Grafana | JSON output + dashboard |
| 7. Business Impact | 30s | **IDE editor** → `BENCHMARKS.md` | Cost comparison tables |
| 8. Closing | 20s | **Browser** → GitHub repo | Clean repo page |

## 🎥 Recording Tips

- **Pace:** Speak slowly and deliberately — you're presenting to decision-makers
- **Pauses:** Wait 2-3 seconds after each command's output appears before speaking
- **Transitions:** When switching between terminal/editor/browser, pause briefly so the viewer can orient themselves
- **Terminal:** Make the Antigravity terminal panel tall enough to show full JSON output
- **Editor:** When showing code, scroll so the relevant method is centered on screen
- **Tone:** Confident, matter-of-fact — let the numbers speak
- **Practice:** Do one dry run without recording so transitions feel smooth
