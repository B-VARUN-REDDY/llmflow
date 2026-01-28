"""
Ollama Provider Client

Handles all communication with local Ollama instance.
Ollama runs models locally (no API key needed, 100% free).
"""

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for Ollama local LLM inference.
    
    Ollama uses an OpenAI-compatible API, making it easy to swap providers.
    """
    
    def __init__(self, base_url: str = "http://ollama:11434"):
        """
        Initialize Ollama client.
        
        Args:
            base_url: URL where Ollama is running (default: Docker service name)
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
        # Use httpx for async requests (120s timeout for cold starts)
        self.client = httpx.AsyncClient(timeout=120.0)
        
        logger.info(f"Ollama client initialized: {base_url}")
    
    async def generate(
        self,
        prompt: str,
        model: str = "llama3.2:1b",
        stream: bool = False
    ) -> dict:
        """
        Generate text using Ollama.
        
        Args:
            prompt: The input prompt
            model: Which model to use (default: llama3.2:1b)
            stream: Whether to stream response (we'll use False for simplicity)
        
        Returns:
            dict with keys:
                - response: The generated text
                - tokens: Approximate token count
                - model: Model that was used
        
        Raises:
            Exception: If Ollama request fails
        """
        try:
            # Ollama API request format
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream
            }
            
            logger.info(f"Sending request to Ollama: model={model}, prompt_len={len(prompt)}")
            
            # Make async POST request
            response = await self.client.post(self.api_url, json=payload)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Extract text and metadata
            result = {
                "response": data.get("response", ""),
                "tokens": self._estimate_tokens(prompt, data.get("response", "")),
                "model": model
            }
            
            logger.info(f"Ollama response received: {result['tokens']} tokens")
            
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise Exception(f"Ollama request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise
    
    def _estimate_tokens(self, prompt: str, response: str) -> int:
        """
        Estimate token count.
        
        Rough approximation: 1 token ≈ 4 characters
        This is good enough for metrics tracking.
        
        For production, you'd use tiktoken or the model's tokenizer.
        """
        total_chars = len(prompt) + len(response)
        return total_chars // 4
    
    async def check_health(self) -> bool:
        """
        Check if Ollama is running and responsive.
        
        Returns:
            bool: True if Ollama is healthy
        """
        try:
            health_url = f"{self.base_url}/api/tags"
            response = await self.client.get(health_url)
            return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> list:
        """
        List available models in Ollama.
        
        Useful for debugging and health checks.
        """
        try:
            tags_url = f"{self.base_url}/api/tags"
            response = await self.client.get(tags_url)
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
