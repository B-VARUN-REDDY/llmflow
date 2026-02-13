"""
LLMFlow Benchmark Report Generator

Runs comprehensive load testing and generates performance report.
Tests: cache effectiveness, provider distribution, latency under load.

Usage:
    python benchmark_report.py
"""

import asyncio
import aiohttp
import time
import statistics
import random
import json
from datetime import datetime
from typing import List, Dict


TEST_QUERIES = [
    # Group 1: AI/ML
    "What is artificial intelligence?",
    "Explain artificial intelligence to me",
    "Describe what artificial intelligence is",
    "What does machine learning mean?",
    "Describe neural networks",
    
    # Group 2: Docker/DevOps
    "What is Docker?",
    "Explain Docker to me",
    "What is Kubernetes?",
    "Tell me about Kubernetes",
    "What are microservices?",
    
    # Group 3: Programming
    "What is Python?",
    "Explain JavaScript",
    "What is TypeScript?",
    "Define REST API",
    "What is GraphQL?",
    
    # Group 4: Simple math
    "What is 2+2?",
    "Calculate 10 times 5",
    "What is 100 divided by 4?",
]


class BenchmarkRunner:
    """Runs load tests and generates performance report."""
    
    def __init__(self, gateway_url: str = "http://localhost:8000"):
        self.gateway_url = f"{gateway_url}/query"
        self.results: List[Dict] = []
        
    async def send_query(self, session: aiohttp.ClientSession, prompt: str) -> Dict:
        """Send single query and measure performance."""
        start = time.time()
        
        try:
            async with session.post(
                self.gateway_url,
                json={"prompt": prompt},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                data = await response.json()
                latency = (time.time() - start) * 1000
                
                return {
                    "prompt": prompt,
                    "latency_ms": latency,
                    "cached": data.get("cached", False),
                    "cache_type": data.get("cache_type"),
                    "similarity_score": data.get("similarity_score"),
                    "provider": data.get("provider"),
                    "complexity_category": data.get("complexity_category"),
                    "tokens": data.get("tokens_used", 0),
                    "success": True
                }
        except Exception as e:
            return {
                "prompt": prompt,
                "latency_ms": (time.time() - start) * 1000,
                "success": False,
                "error": str(e)
            }
    
    async def run_warmup(self):
        """Phase 1: Warm up cache with initial queries."""
        print("\n🔥 Phase 1: Cache Warmup")
        print("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            for i, query in enumerate(TEST_QUERIES):
                result = await self.send_query(session, query)
                status = "✅" if result["success"] else "❌"
                cached = "HIT" if result.get("cached") else "MISS"
                print(f"  {status} [{i+1}/{len(TEST_QUERIES)}] {cached} {result['latency_ms']:.0f}ms - {query[:40]}...")
                self.results.append(result)
        
        successful = sum(1 for r in self.results if r["success"])
        print(f"\n  Warmup complete: {successful}/{len(TEST_QUERIES)} queries cached")
    
    async def run_cache_test(self, iterations: int = 3):
        """Phase 2: Test cache effectiveness with repeated queries."""
        print(f"\n📊 Phase 2: Cache Effectiveness Test ({iterations} iterations)")
        print("=" * 60)
        
        for i in range(iterations):
            print(f"\n  Iteration {i+1}/{iterations}...")
            
            async with aiohttp.ClientSession() as session:
                tasks = [self.send_query(session, q) for q in TEST_QUERIES]
                results = await asyncio.gather(*tasks)
                
                cached = [r for r in results if r.get("cached") and r["success"]]
                uncached = [r for r in results if not r.get("cached") and r["success"]]
                exact = sum(1 for r in cached if r.get("cache_type") == "exact")
                semantic = sum(1 for r in cached if r.get("cache_type") == "semantic")
                
                avg_cached = statistics.mean(r["latency_ms"] for r in cached) if cached else 0
                avg_uncached = statistics.mean(r["latency_ms"] for r in uncached) if uncached else 0
                hit_rate = len(cached) / len(results) * 100 if results else 0
                
                print(f"    Hit rate: {hit_rate:.1f}% ({len(cached)}/{len(results)})")
                print(f"    Exact: {exact} | Semantic: {semantic}")
                print(f"    Cached avg: {avg_cached:.1f}ms | Uncached avg: {avg_uncached:.1f}ms")
                if avg_cached > 0:
                    print(f"    Speedup: {avg_uncached/avg_cached:.1f}x")
                
                self.results.extend(results)
    
    async def run_load_test(self, concurrent: int = 5, duration_sec: int = 20):
        """Phase 3: Test system under concurrent load."""
        print(f"\n⚡ Phase 3: Load Test ({concurrent} concurrent, {duration_sec}s)")
        print("=" * 60)
        
        start_time = time.time()
        query_count = 0
        errors = 0
        load_results = []
        
        async def worker():
            nonlocal query_count, errors
            async with aiohttp.ClientSession() as session:
                while (time.time() - start_time) < duration_sec:
                    query = random.choice(TEST_QUERIES)
                    result = await self.send_query(session, query)
                    
                    if result["success"]:
                        query_count += 1
                        load_results.append(result)
                    else:
                        errors += 1
                    
                    await asyncio.sleep(0.2)
        
        workers = [worker() for _ in range(concurrent)]
        await asyncio.gather(*workers)
        
        elapsed = time.time() - start_time
        qps = query_count / elapsed
        
        print(f"  Total queries: {query_count}")
        print(f"  Errors: {errors}")
        print(f"  Duration: {elapsed:.1f}s")
        print(f"  Throughput: {qps:.1f} queries/sec")
        
        self.results.extend(load_results)
    
    def generate_report(self):
        """Generate comprehensive benchmark report."""
        print("\n" + "=" * 60)
        print("📋 BENCHMARK REPORT")
        print("=" * 60)
        
        successful = [r for r in self.results if r["success"]]
        
        if not successful:
            print("❌ No successful queries to analyze")
            return
        
        # Overall stats
        print(f"\n📊 Overall Statistics")
        print(f"  Total queries: {len(successful)}")
        print(f"  Success rate: {len(successful)/len(self.results)*100:.1f}%")
        
        # Cache performance
        cached = [r for r in successful if r.get("cached")]
        uncached = [r for r in successful if not r.get("cached")]
        
        print(f"\n💾 Cache Performance")
        hit_rate = len(cached)/len(successful)*100
        print(f"  Hit rate: {hit_rate:.1f}%")
        exact = sum(1 for r in cached if r.get("cache_type") == "exact")
        semantic = sum(1 for r in cached if r.get("cache_type") == "semantic")
        print(f"  Exact matches: {exact}")
        print(f"  Semantic matches: {semantic}")
        
        if cached:
            latencies = sorted(r["latency_ms"] for r in cached)
            p50 = latencies[len(latencies)//2]
            p95 = latencies[int(len(latencies)*0.95)]
            print(f"\n  Cached latency:   p50={p50:.1f}ms  p95={p95:.1f}ms")
        
        if uncached:
            latencies = sorted(r["latency_ms"] for r in uncached)
            p50 = latencies[len(latencies)//2]
            p95 = latencies[int(len(latencies)*0.95)]
            print(f"  Uncached latency: p50={p50:.1f}ms  p95={p95:.1f}ms")
        
        if cached and uncached:
            speedup = statistics.median(r["latency_ms"] for r in uncached) / statistics.median(r["latency_ms"] for r in cached)
            print(f"\n  🚀 Cache speedup: {speedup:.1f}x")
        
        # Provider distribution
        providers = {}
        for r in successful:
            p = r.get("provider", "unknown")
            providers[p] = providers.get(p, 0) + 1
        
        print(f"\n🎯 Provider Distribution")
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(successful) * 100
            print(f"  {provider:12} {count:5} queries  ({pct:5.1f}%)")
        
        # Save JSON report
        report_file = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_queries": len(successful),
                    "cache_hit_rate": round(hit_rate, 1),
                    "exact_hits": exact,
                    "semantic_hits": semantic,
                    "providers": providers
                },
                "results": successful
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {report_file}")
        print("\n" + "=" * 60)
        print("✅ Benchmark complete!")
        print("=" * 60)


async def main():
    """Run full benchmark suite."""
    print("\n" + "=" * 60)
    print("🚀 LLMFlow Performance Benchmark")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    runner = BenchmarkRunner()
    
    # Phase 1: Warmup
    await runner.run_warmup()
    await asyncio.sleep(2)
    
    # Phase 2: Cache testing
    await runner.run_cache_test(iterations=2)
    await asyncio.sleep(1)
    
    # Phase 3: Load testing
    await runner.run_load_test(concurrent=5, duration_sec=20)
    
    # Report
    runner.generate_report()


if __name__ == "__main__":
    asyncio.run(main())
