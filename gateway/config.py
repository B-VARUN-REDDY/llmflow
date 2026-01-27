"""
Configuration management for LLMFlow Gateway.

This module handles all environment variables and configuration settings.
We use pydantic-settings for type-safe config with validation.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Pydantic automatically:
    - Loads from .env file
    - Validates types
    - Provides defaults
    - Raises clear errors if required vars are missing
    """
    
    # API Keys
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    
    # Ollama (runs locally)
    ollama_base_url: str = "http://ollama:11434"
    
    # Gateway Config
    gateway_port: int = 8000
    log_level: str = "INFO"
    
    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    
    # PostgreSQL
    postgres_user: str = "llmflow"
    postgres_password: str = "llmflow_dev_password"
    postgres_db: str = "llmflow"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    
    # Prometheus
    prometheus_port: int = 9090
    
    # Grafana
    grafana_port: int = 3000
    
    class Config:
        # Load from .env file
        env_file = ".env"
        # Case insensitive env vars
        case_sensitive = False


# Create global settings instance
# This will be imported by other modules
settings = Settings()
