"""
Gemini Provider Client

Google's Gemini models via AI Studio API.
Free tier: 60 requests/min, 1500 requests/day

Best for complex reasoning tasks that need high-quality responses.
"""

import google.generativeai as genai
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Client for Google Gemini LLM inference.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google AI Studio API key
        """
        if not api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure API key
        genai.configure(api_key=api_key)
        
        # Use Gemini Pro model (best balance of speed/quality)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        logger.info("Gemini client initialized")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> dict:
        """
        Generate text using Gemini.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 2.0)
        
        Returns:
            dict with keys:
                - response: The generated text
                - tokens: Estimated token count
                - model: Model that was used
        
        Raises:
            Exception: If Gemini request fails
        """
        try:
            logger.info(f"Sending request to Gemini: prompt_len={len(prompt)}")
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            # Generate response (note: Gemini SDK is sync, we'll run in executor)
            # For now, we'll use the sync version and handle async at the gateway level
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Extract text
            response_text = response.text
            
            # Estimate tokens (Gemini doesn't always provide token counts)
            # Rough estimate: 1 token ≈ 4 characters
            estimated_tokens = (len(prompt) + len(response_text)) // 4
            
            result = {
                "response": response_text,
                "tokens": estimated_tokens,
                "model": "gemini-2.0-flash"
            }
            
            logger.info(f"Gemini response received: ~{estimated_tokens} tokens")
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise Exception(f"Gemini request failed: {str(e)}")
    
    async def check_health(self) -> bool:
        """
        Check if Gemini API is accessible.
        
        Returns:
            bool: True if Gemini is healthy
        """
        try:
            result = await self.generate(
                prompt="test",
                max_tokens=1
            )
            return True
        except:
            return False
