# LLMFlow Quick Start Guide

Get the entire system running in under 5 minutes.

---

## Prerequisites

- Docker Desktop installed and running
- Git installed
- 4GB free disk space (for Ollama model)
- Ports available: 8000, 3000, 9090, 11434, 6379, 5432

---

## Setup Steps

### 1. Clone Repository

```bash
git clone https://github.com/B-VARUN-REDDY/llmflow.git
cd llmflow
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# (Optional) Add API keys for Groq and Gemini
# nano .env
```

**Note:** You can run with just Ollama (no API keys needed). Groq and Gemini are optional.

### 3. Start All Services

```bash
# Start all 6 services in background
docker-compose up -d

# Wait for services to initialize (~30 seconds)
```

### 4. Pull Ollama Model

```bash
# Download Llama 3.2 1B model (~1.3GB)
docker exec -it llmflow-ollama ollama pull llama3.2:1b

# This takes 2-5 minutes depending on your internet
```

### 5. Verify Everything Works

```bash
# Check all services are running
docker-compose ps

# Test gateway health
curl http://localhost:8000/health

# Send test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is machine learning?"}' \
  | python -m json.tool
```

---

## Access Points

Once running, open these in your browser:

| Service | URL | Purpose |
|---------|-----|---------|
| **API Documentation** | http://localhost:8000/docs | Interactive API explorer |
| **Grafana Dashboards** | http://localhost:3000 | Metrics visualization (admin/admin) |
| **Prometheus** | http://localhost:9090 | Raw metrics & queries |
| **Gateway Health** | http://localhost:8000/health | Service status |
| **Metrics Endpoint** | http://localhost:8000/metrics | Prometheus scrape target |

---

## Generate Traffic for Dashboards

```bash
# Navigate to simulator
cd simulator

# Install dependencies (first time only)
pip install -r requirements.txt

# Run traffic generator
python traffic_generator.py

# Select scenario:
# 1 = Normal Traffic (5 min realistic load)
# 2 = Cache Warmup (repeated queries)
# 3 = Traffic Spike (load testing)
# 4 = Quick Burst (50 queries in 30 seconds) ← Fastest!
```

**Recommended:** Choose option 4 (Quick Burst) to populate dashboards fast for demos.

---

## Common Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart single service
docker-compose restart gateway

# View logs
docker-compose logs -f gateway
docker-compose logs -f ollama

# Rebuild after code changes
docker-compose up -d --build
```

### Testing

```bash
# Send test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain Docker in one sentence."}'

# Check metrics
curl http://localhost:8000/metrics | grep llm_

# Test Prometheus scraping
curl http://localhost:9090/api/v1/targets | python -m json.tool
```

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove containers + volumes (fresh start)
docker-compose down -v

# Remove Ollama model (free up disk space)
docker exec -it llmflow-ollama ollama rm llama3.2:1b
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker --version

# Check port availability
netstat -an | grep -E "8000|3000|9090"

# View detailed logs
docker-compose logs
```

### Ollama Model Download Fails

```bash
# Check Ollama is running
docker-compose ps ollama

# Try manual pull
docker exec -it llmflow-ollama ollama pull llama3.2:1b

# If still fails, check internet connection
```

### Grafana Shows "No Data"

```bash
# 1. Verify Prometheus is scraping
# Open: http://localhost:9090/targets
# Should show "llmflow-gateway" as UP

# 2. Check metrics are exposed
curl http://localhost:8000/metrics

# 3. Send test traffic
for i in {1..10}; do
  curl -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Test '$i'"}' -s -o /dev/null
  sleep 1
done

# 4. Refresh Grafana dashboard
```

### Gateway Not Responding

```bash
# Check logs
docker-compose logs gateway

# Common issues:
# - Ollama not ready → wait 30s after startup
# - Port 8000 in use → change in .env
# - Import errors → rebuild: docker-compose up -d --build
```

---

## Next Steps

1. ✅ Run Quick Burst to populate dashboards
2. ✅ Take screenshots for portfolio
3. 📖 Read `docs/METRICS_GUIDE.md` to understand what's being tracked
4. 🚀 Continue to Phase 2: Multi-provider routing

---

## Support

- **Documentation:** See `docs/` directory
- **Issues:** Check `docs/SESSION_LOG.md` for known issues
- **Architecture:** See `docs/ARCHITECTURE.md` (coming soon)

---

**Last Updated:** January 28, 2026
