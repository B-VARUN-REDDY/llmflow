"""
Traffic Generator for LLMFlow Dashboard Population

Generates realistic query patterns to demonstrate the system under load.
This makes dashboards look production-ready for portfolio demos.
"""

import asyncio
import aiohttp
import random
import time
from typing import List
import json


# Sample queries of varying complexity
SAMPLE_QUERIES = [
    # Simple queries (should be fast)
    "What is 2+2?",
    "Define AI.",
    "What is Python?",
    "Explain REST API.",
    "What is Docker?",
    
    # Medium queries
    "Explain the difference between supervised and unsupervised learning.",
    "How does a neural network work?",
    "What are the benefits of microservices architecture?",
    "Describe the OSI model in networking.",
    "What is the CAP theorem in distributed systems?",
    
    # Complex queries
    "Explain the mathematical foundations of backpropagation in neural networks with gradient descent optimization.",
    "Compare and contrast MapReduce, Spark, and Flink for big data processing, including their architectural differences.",
    "Describe the security implications of OAuth 2.0 flows and how to implement them securely in a production environment.",
    "Explain how Kubernetes orchestrates containerized applications, including pod scheduling and resource management.",
    "What are the trade-offs between consistency models in distributed databases like eventual consistency vs strong consistency?"
]


class TrafficGenerator:
    """
    Generates realistic traffic patterns for testing and demos.
    """
    
    def __init__(self, gateway_url: str = "http://localhost:8000"):
        self.gateway_url = f"{gateway_url}/query"
        self.session = None
    
    async def __aenter__(self):
        """Setup async HTTP session"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        """Cleanup async HTTP session"""
        await self.session.close()
    
    async def send_query(self, prompt: str) -> dict:
        """
        Send a single query to the gateway.
        
        Returns:
            dict: Response from gateway
        """
        try:
            async with self.session.post(
                self.gateway_url,
                json={"prompt": prompt},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                return await response.json()
        except Exception as e:
            print(f"❌ Error sending query: {e}")
            return None
    
    async def scenario_normal_traffic(self, duration_minutes: int = 5):
        """
        Scenario 1: Normal steady traffic
        
        Simulates typical production load:
        - 1-2 queries per second
        - Random distribution of query types
        - Realistic timing between requests
        """
        print(f"\n🚀 Starting Scenario: Normal Traffic ({duration_minutes} min)")
        print("=" * 60)
        
        end_time = time.time() + (duration_minutes * 60)
        query_count = 0
        
        while time.time() < end_time:
            # Pick random query
            query = random.choice(SAMPLE_QUERIES)
            
            # Send query
            start = time.time()
            response = await self.send_query(query)
            elapsed = time.time() - start
            
            query_count += 1
            
            if response:
                print(f"✅ Query {query_count}: {elapsed*1000:.0f}ms - {query[:50]}...")
            
            # Random delay between 0.5-2 seconds (realistic user behavior)
            await asyncio.sleep(random.uniform(0.5, 2.0))
        
        print(f"\n✅ Completed: {query_count} queries sent")
    
    async def scenario_cache_warmup(self, iterations: int = 3):
        """
        Scenario 2: Cache warmup demonstration
        
        Sends the same queries multiple times to show cache hit rate improving.
        """
        print(f"\n🚀 Starting Scenario: Cache Warmup ({iterations} iterations)")
        print("=" * 60)
        
        # Use subset of queries for repetition
        queries = SAMPLE_QUERIES[:10]
        
        for iteration in range(iterations):
            print(f"\n--- Iteration {iteration + 1}/{iterations} ---")
            
            for i, query in enumerate(queries):
                start = time.time()
                response = await self.send_query(query)
                elapsed = time.time() - start
                
                if response:
                    cached = response.get("cached", False)
                    cache_indicator = "🔥 CACHED" if cached else "🌐 MISS"
                    print(f"{cache_indicator} Query {i+1}: {elapsed*1000:.0f}ms")
                
                # Small delay
                await asyncio.sleep(0.3)
    
    async def scenario_traffic_spike(self, normal_duration: int = 2, spike_duration: int = 1):
        """
        Scenario 3: Traffic spike handling
        
        Shows how system handles sudden increase in load.
        """
        print(f"\n🚀 Starting Scenario: Traffic Spike")
        print("=" * 60)
        
        # Phase 1: Normal traffic
        print("\n📊 Phase 1: Normal traffic (1-2 req/s)")
        end_normal = time.time() + (normal_duration * 60)
        
        while time.time() < end_normal:
            query = random.choice(SAMPLE_QUERIES)
            await self.send_query(query)
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Phase 2: Traffic spike
        print("\n⚡ Phase 2: TRAFFIC SPIKE (10 req/s)")
        end_spike = time.time() + (spike_duration * 60)
        
        while time.time() < end_spike:
            # Send 5 queries concurrently
            tasks = [
                self.send_query(random.choice(SAMPLE_QUERIES))
                for _ in range(5)
            ]
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.5)
        
        # Phase 3: Back to normal
        print("\n📊 Phase 3: Back to normal traffic")
        end_recovery = time.time() + 60
        
        while time.time() < end_recovery:
            query = random.choice(SAMPLE_QUERIES)
            await self.send_query(query)
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        print("\n✅ Spike scenario completed")
    
    async def scenario_burst(self, num_queries: int = 50):
        """
        Scenario 4: Quick burst
        
        Sends many queries quickly to populate dashboard fast.
        Perfect for demos and screenshots.
        """
        print(f"\n🚀 Starting Scenario: Quick Burst ({num_queries} queries)")
        print("=" * 60)
        
        start_time = time.time()
        
        for i in range(num_queries):
            query = random.choice(SAMPLE_QUERIES)
            response = await self.send_query(query)
            
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                print(f"📈 Progress: {i+1}/{num_queries} ({rate:.1f} req/s)")
            
            # Small delay to avoid overwhelming
            await asyncio.sleep(0.1)
        
        total_time = time.time() - start_time
        avg_rate = num_queries / total_time
        
        print(f"\n✅ Completed: {num_queries} queries in {total_time:.1f}s")
        print(f"📊 Average rate: {avg_rate:.1f} req/s")


async def main():
    """
    Main entry point - run different scenarios.
    """
    print("\n" + "="*60)
    print("LLMFlow Traffic Generator")
    print("="*60)
    
    print("\nAvailable scenarios:")
    print("1. Normal Traffic (5 min) - Steady realistic load")
    print("2. Cache Warmup (3 iterations) - Show cache effectiveness")
    print("3. Traffic Spike (4 min) - Sudden load increase")
    print("4. Quick Burst (50 queries) - Fast dashboard population")
    
    choice = input("\nSelect scenario (1-4) or 'all': ").strip()
    
    async with TrafficGenerator() as generator:
        if choice == "1":
            await generator.scenario_normal_traffic(duration_minutes=5)
        elif choice == "2":
            await generator.scenario_cache_warmup(iterations=3)
        elif choice == "3":
            await generator.scenario_traffic_spike()
        elif choice == "4":
            await generator.scenario_burst(num_queries=50)
        elif choice.lower() == "all":
            print("\n🎯 Running all scenarios sequentially...")
            await generator.scenario_burst(num_queries=30)
            await asyncio.sleep(10)
            await generator.scenario_cache_warmup(iterations=2)
            await asyncio.sleep(10)
            await generator.scenario_normal_traffic(duration_minutes=2)
        else:
            print("Invalid choice. Running quick burst by default.")
            await generator.scenario_burst(num_queries=50)
    
    print("\n✨ All done! Check your Grafana dashboard at http://localhost:3000")


if __name__ == "__main__":
    asyncio.run(main())
