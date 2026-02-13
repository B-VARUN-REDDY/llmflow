"""
Database Client for Query Logging

Handles all PostgreSQL interactions for storing and querying request history.
Uses asyncpg for async connection pooling.
"""

import asyncpg
import logging
import os
import uuid
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Async PostgreSQL client for query logging and analytics."""
    
    def __init__(
        self,
        host: str = "postgres",
        port: int = 5432,
        database: str = "llmflow",
        user: str = "llmflow",
        password: str = "llmflow_dev_password"
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool: Optional[asyncpg.Pool] = None
        
        logger.info(f"Database client configured: {user}@{host}:{port}/{database}")
    
    async def connect(self):
        """Create connection pool and initialize schema."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            logger.info("✅ Database connection pool created")
            await self._init_schema()
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            logger.warning("⚠️ Query logging will be disabled")
            return False
    
    async def _init_schema(self):
        """Initialize database schema from schema.sql."""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            async with self.pool.acquire() as conn:
                await conn.execute(schema_sql)
            
            logger.info("✅ Database schema initialized")
            
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def log_query(
        self,
        prompt: str,
        response: str,
        provider: str,
        model: str,
        tokens_used: int,
        latency_ms: float,
        cached: bool,
        cache_type: Optional[str] = None,
        similarity_score: Optional[float] = None,
        complexity_score: Optional[int] = None,
        complexity_category: Optional[str] = None,
        fallback_used: bool = False,
        estimated_cost_usd: float = 0.0,
        cost_saved_usd: float = 0.0,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> bool:
        """Log a query to the database. Returns True if logged successfully."""
        if not self.pool:
            return False
        
        try:
            request_id = uuid.uuid4()
            
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO query_logs (
                        request_id, timestamp,
                        prompt, prompt_length,
                        complexity_score, complexity_category,
                        provider, model, fallback_used,
                        response, response_length, tokens_used,
                        cached, cache_type, similarity_score,
                        latency_ms,
                        estimated_cost_usd, cost_saved_usd,
                        status, error_message
                    ) VALUES (
                        $1, $2,
                        $3, $4,
                        $5, $6,
                        $7, $8, $9,
                        $10, $11, $12,
                        $13, $14, $15,
                        $16,
                        $17, $18,
                        $19, $20
                    )
                    """,
                    request_id, datetime.utcnow(),
                    prompt, len(prompt),
                    complexity_score, complexity_category,
                    provider, model, fallback_used,
                    response, len(response) if response else 0, tokens_used,
                    cached, cache_type, similarity_score,
                    latency_ms,
                    estimated_cost_usd, cost_saved_usd,
                    status, error_message
                )
            
            logger.debug(f"📝 Logged query: {request_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log query: {e}")
            return False
    
    async def get_recent_queries(self, limit: int = 100) -> list:
        """Get recent queries from the database."""
        if not self.pool:
            return []
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM recent_queries LIMIT $1", limit
                )
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch recent queries: {e}")
            return []
    
    async def get_cache_stats(self) -> dict:
        """Get cache effectiveness statistics by provider."""
        if not self.pool:
            return {}
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM cache_effectiveness")
                return {row['provider']: dict(row) for row in rows}
        except Exception as e:
            logger.error(f"Failed to fetch cache stats: {e}")
            return {}
    
    async def get_cost_analysis(self, days: int = 7) -> list:
        """Get cost analysis for recent days."""
        if not self.pool:
            return []
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM cost_analysis
                    WHERE date >= CURRENT_DATE - $1 * INTERVAL '1 day'
                    ORDER BY date DESC, provider
                    """,
                    days
                )
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch cost analysis: {e}")
            return []
    
    async def get_complexity_distribution(self) -> dict:
        """Get query complexity distribution."""
        if not self.pool:
            return {}
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM complexity_distribution")
                return {row['complexity_category']: dict(row) for row in rows}
        except Exception as e:
            logger.error(f"Failed to fetch complexity distribution: {e}")
            return {}
