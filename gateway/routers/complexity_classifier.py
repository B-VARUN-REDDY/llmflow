"""
Complexity Classifier for Query Routing

Analyzes incoming prompts and assigns a complexity score (0-100).
This determines which LLM provider to route to.

Phase 1: Simple heuristic-based classifier
Phase 3: Could be upgraded to ML-based classification
"""

import re
import logging

logger = logging.getLogger(__name__)


class ComplexityClassifier:
    """
    Classifies query complexity using heuristics.
    
    Complexity Score Ranges:
    - 0-30: Simple (factual, short, common questions) → Ollama
    - 31-70: Medium (explanations, comparisons) → Groq
    - 71-100: Complex (reasoning, analysis, multi-step) → Gemini
    """
    
    # Keywords indicating complex reasoning
    COMPLEX_KEYWORDS = [
        'explain', 'compare', 'contrast', 'analyze', 'evaluate', 
        'discuss', 'argue', 'justify', 'critique', 'assess',
        'why', 'how does', 'implications', 'trade-offs',
        'architecture', 'design', 'optimize', 'strategy'
    ]
    
    # Keywords indicating simple factual questions
    SIMPLE_KEYWORDS = [
        'what is', 'define', 'who is', 'when', 'where',
        'list', 'name', 'tell me', 'show me'
    ]
    
    # Technical/academic indicators (increase complexity)
    TECHNICAL_INDICATORS = [
        'algorithm', 'implementation', 'mathematical', 'theoretical',
        'distributed', 'concurrent', 'asynchronous', 'optimization',
        'security', 'cryptography', 'protocol', 'framework'
    ]
    
    def classify(self, prompt: str) -> dict:
        """
        Classify prompt complexity.
        
        Args:
            prompt: The input query
        
        Returns:
            dict with:
                - score: Complexity score (0-100)
                - category: 'simple', 'medium', or 'complex'
                - reasoning: Why this score was assigned
        """
        prompt_lower = prompt.lower()
        score = 50  # Start at medium
        reasoning = []
        
        # Factor 1: Length (longer = more complex)
        word_count = len(prompt.split())
        if word_count < 10:
            score -= 15
            reasoning.append(f"Short query ({word_count} words)")
        elif word_count > 30:
            score += 15
            reasoning.append(f"Long query ({word_count} words)")
        
        # Factor 2: Simple keywords
        simple_matches = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in prompt_lower)
        if simple_matches > 0:
            score -= (simple_matches * 10)
            reasoning.append(f"Simple keywords ({simple_matches} matches)")
        
        # Factor 3: Complex keywords
        complex_matches = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in prompt_lower)
        if complex_matches > 0:
            score += (complex_matches * 10)
            reasoning.append(f"Complex keywords ({complex_matches} matches)")
        
        # Factor 4: Technical indicators
        technical_matches = sum(1 for kw in self.TECHNICAL_INDICATORS if kw in prompt_lower)
        if technical_matches > 0:
            score += (technical_matches * 8)
            reasoning.append(f"Technical terms ({technical_matches} matches)")
        
        # Factor 5: Questions vs statements
        if '?' in prompt:
            question_marks = prompt.count('?')
            if question_marks == 1:
                score -= 5  # Single question, likely simpler
                reasoning.append("Single question")
            else:
                score += 10  # Multiple questions, more complex
                reasoning.append(f"Multiple questions ({question_marks})")
        
        # Factor 6: Sentence structure complexity
        sentence_count = len([s for s in prompt.split('.') if s.strip()])
        if sentence_count > 2:
            score += 10
            reasoning.append(f"Multi-sentence ({sentence_count} sentences)")
        
        # Clamp score to 0-100 range
        score = max(0, min(100, score))
        
        # Determine category
        if score < 30:
            category = "simple"
        elif score < 70:
            category = "medium"
        else:
            category = "complex"
        
        logger.info(f"Classified query as {category} (score: {score}): {prompt[:50]}...")
        
        return {
            "score": score,
            "category": category,
            "reasoning": reasoning
        }
    
    def get_recommended_provider(self, complexity_score: int) -> str:
        """
        Get recommended provider based on complexity score.
        
        Args:
            complexity_score: Score from 0-100
        
        Returns:
            str: Provider name ('ollama', 'groq', or 'gemini')
        """
        if complexity_score < 30:
            return "ollama"  # Simple → fast local model
        elif complexity_score < 70:
            return "groq"    # Medium → fast cloud model
        else:
            return "gemini"  # Complex → best reasoning model


# Global classifier instance
classifier = ComplexityClassifier()
