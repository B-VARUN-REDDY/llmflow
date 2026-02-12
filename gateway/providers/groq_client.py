"""
Groq Provider Client

Groq provides ultra-fast LLM inference via their LPU (Language Processing Unit).
Free tier: 14,400 requests/day

Perfect for medium-complexity queries that need speed.
"""

from groq import AsyncGroq
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GroqClient:
    """
    Client for Groq LLM inference.
    
    Groq uses an OpenAI-compatible API, making integration straightforward.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key from console.groq.com
        """
        if not api_key:
            raise ValueError("Groq API key is required")
        
        self.client = AsyncGroq(api_key=api_key)
        self.default_model = "llama-3.3-70b-versatile"  # Fast, capable model
        
        logger.info("Groq client initialized")
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> dict:
        """
        Generate text using Groq.
        
        Args:
            prompt: The input prompt
            model: Which model to use (default: mixtral-8x7b-32768)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 2.0)
        
        Returns:
            dict with keys:
                - response: The generated text
                - tokens: Token count (prompt + completion)
                - model: Model that was used
        
        Raises:
            Exception: If Groq request fails
        """
        try:
            model = model or self.default_model
            
            logger.info(f"Sending request to Groq: model={model}, prompt_len={len(prompt)}")
            
            # Groq uses OpenAI-compatible API
            completion = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response
            response_text = completion.choices[0].message.content
            
            # Token usage from response
            prompt_tokens = completion.usage.prompt_tokens
            completion_tokens = completion.usage.completion_tokens
            total_tokens = completion.usage.total_tokens
            
            result = {
                "response": response_text,
                "tokens": total_tokens,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }
            
            logger.info(f"Groq response received: {total_tokens} tokens (prompt: {prompt_tokens}, completion: {completion_tokens})")
            
            return result
            
        except Exception as e:
            logger.error(f"Groq error: {e}")
            raise Exception(f"Groq request failed: {str(e)}")
    
    async def check_health(self) -> bool:
        """
        Check if Groq API is accessible.
        
        Returns:
            bool: True if Groq is healthy
        """
        try:
            # Send a minimal test request
            result = await self.generate(
                prompt="test",
                max_tokens=1
            )
            return True
        except:
            return False
