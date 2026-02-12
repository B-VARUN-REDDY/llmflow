"""
LLM Router - Intelligent Query Routing

Routes queries to the optimal provider based on complexity analysis.
Handles fallbacks if a provider fails.

Routing Strategy:
- Simple queries (0-30) → Ollama (free, local, fast)
- Medium queries (31-70) → Groq (free tier, very fast)
- Complex queries (71-100) → Gemini (free tier, best reasoning)
"""

import logging
from typing import Optional
from providers.ollama_client import OllamaClient
from providers.groq_client import GroqClient
from providers.gemini_client import GeminiClient
from routers.complexity_classifier import classifier
from monitoring.metrics import llm_routing_decisions_total

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    Intelligent router for LLM queries.
    
    Analyzes query complexity and routes to the most appropriate provider.
    Implements fallback logic if primary provider fails.
    """
    
    def __init__(
        self,
        ollama_client: OllamaClient,
        groq_client: Optional[GroqClient] = None,
        gemini_client: Optional[GeminiClient] = None
    ):
        """
        Initialize router with available providers.
        
        Args:
            ollama_client: Ollama client (required, always available)
            groq_client: Groq client (optional, needs API key)
            gemini_client: Gemini client (optional, needs API key)
        """
        self.ollama = ollama_client
        self.groq = groq_client
        self.gemini = gemini_client
        
        # Track which providers are available
        self.providers_available = {
            "ollama": True,
            "groq": groq_client is not None,
            "gemini": gemini_client is not None
        }
        
        logger.info(f"LLM Router initialized. Available providers: {[k for k, v in self.providers_available.items() if v]}")
    
    async def route_query(self, prompt: str, force_provider: Optional[str] = None) -> dict:
        """
        Route query to optimal provider.
        
        Args:
            prompt: The input query
            force_provider: Override routing logic (for testing)
        
        Returns:
            dict with:
                - response: Generated text
                - provider: Which provider was used
                - model: Specific model used
                - tokens: Token count
                - complexity_score: Query complexity (0-100)
                - complexity_category: simple/medium/complex
                - fallback_used: Whether fallback was needed
        
        Raises:
            Exception: If all providers fail
        """
        # Step 1: Classify query complexity
        classification = classifier.classify(prompt)
        complexity_score = classification["score"]
        complexity_category = classification["category"]
        
        # Record routing decision in metrics
        llm_routing_decisions_total.labels(
            complexity_bucket=complexity_category
        ).inc()
        
        logger.info(f"Query classified: {complexity_category} (score: {complexity_score})")
        logger.debug(f"Classification reasoning: {classification['reasoning']}")
        
        # Step 2: Determine target provider
        if force_provider:
            target_provider = force_provider
            logger.info(f"Provider forced: {target_provider}")
        else:
            target_provider = classifier.get_recommended_provider(complexity_score)
            logger.info(f"Recommended provider: {target_provider}")
        
        # Step 3: Define fallback chain
        fallback_chain = self._get_fallback_chain(target_provider)
        
        # Step 4: Try providers in order
        last_error = None
        for provider_name in fallback_chain:
            if not self.providers_available.get(provider_name):
                logger.debug(f"Provider {provider_name} not available, skipping")
                continue
            
            try:
                logger.info(f"Attempting {provider_name}...")
                result = await self._call_provider(provider_name, prompt)
                
                # Add routing metadata
                result["complexity_score"] = complexity_score
                result["complexity_category"] = complexity_category
                result["fallback_used"] = (provider_name != target_provider)
                
                logger.info(f"Success with {provider_name}")
                return result
                
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                last_error = e
                continue
        
        # All providers failed
        logger.error("All providers failed!")
        raise Exception(f"All LLM providers failed. Last error: {last_error}")
    
    async def _call_provider(self, provider_name: str, prompt: str) -> dict:
        """
        Call specific provider.
        
        Args:
            provider_name: 'ollama', 'groq', or 'gemini'
            prompt: Query text
        
        Returns:
            dict with response, tokens, model, provider
        """
        if provider_name == "ollama":
            result = await self.ollama.generate(prompt)
            result["provider"] = "ollama"
            return result
        
        elif provider_name == "groq":
            if not self.groq:
                raise Exception("Groq client not initialized (missing API key?)")
            result = await self.groq.generate(prompt)
            result["provider"] = "groq"
            return result
        
        elif provider_name == "gemini":
            if not self.gemini:
                raise Exception("Gemini client not initialized (missing API key?)")
            
            # Gemini's generate is sync, run in thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.gemini.model.generate_content(prompt)
            )
            
            # Format response
            return {
                "response": result.text,
                "tokens": (len(prompt) + len(result.text)) // 4,  # Estimate
                "model": "gemini-2.0-flash",
                "provider": "gemini"
            }
        
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
    
    def _get_fallback_chain(self, primary_provider: str) -> list:
        """
        Define fallback order based on primary provider.
        
        Strategy:
        - If cloud provider fails → fallback to Ollama (always available)
        - If Ollama targeted but fails → try cloud providers
        
        Args:
            primary_provider: The recommended provider
        
        Returns:
            list: Ordered list of providers to try
        """
        if primary_provider == "ollama":
            return ["ollama", "groq", "gemini"]
        elif primary_provider == "groq":
            return ["groq", "gemini", "ollama"]
        elif primary_provider == "gemini":
            return ["gemini", "groq", "ollama"]
        else:
            return ["ollama", "groq", "gemini"]
    
    def get_provider_status(self) -> dict:
        """
        Get status of all providers.
        
        Returns:
            dict: Provider availability and health
        """
        return {
            "ollama": {
                "available": self.providers_available["ollama"],
                "status": "ready"
            },
            "groq": {
                "available": self.providers_available["groq"],
                "status": "ready" if self.groq else "no_api_key"
            },
            "gemini": {
                "available": self.providers_available["gemini"],
                "status": "ready" if self.gemini else "no_api_key"
            }
        }
