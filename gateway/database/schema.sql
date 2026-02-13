-- LLMFlow Query Logging Schema
-- 
-- Stores all query history for analytics and debugging.
-- Enables SQL-based analysis of usage patterns, costs, and performance.

CREATE TABLE IF NOT EXISTS query_logs (
    id BIGSERIAL PRIMARY KEY,
    
    -- Request metadata
    request_id UUID NOT NULL UNIQUE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Query details
    prompt TEXT NOT NULL,
    prompt_length INTEGER NOT NULL,
    
    -- Routing & provider
    complexity_score INTEGER,
    complexity_category VARCHAR(20),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    fallback_used BOOLEAN DEFAULT FALSE,
    
    -- Response details
    response TEXT,
    response_length INTEGER,
    tokens_used INTEGER NOT NULL,
    
    -- Cache performance
    cached BOOLEAN DEFAULT FALSE,
    cache_type VARCHAR(20),
    similarity_score FLOAT,
    
    -- Performance metrics
    latency_ms FLOAT NOT NULL,
    
    -- Cost tracking
    estimated_cost_usd FLOAT DEFAULT 0.0,
    cost_saved_usd FLOAT DEFAULT 0.0,
    
    -- Request status
    status VARCHAR(20) NOT NULL,
    error_message TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_query_logs_timestamp ON query_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_query_logs_provider ON query_logs(provider);
CREATE INDEX IF NOT EXISTS idx_query_logs_cached ON query_logs(cached);
CREATE INDEX IF NOT EXISTS idx_query_logs_cache_type ON query_logs(cache_type);
CREATE INDEX IF NOT EXISTS idx_query_logs_complexity ON query_logs(complexity_category);
CREATE INDEX IF NOT EXISTS idx_query_logs_status ON query_logs(status);
CREATE INDEX IF NOT EXISTS idx_query_logs_cost ON query_logs(estimated_cost_usd, cost_saved_usd);
CREATE INDEX IF NOT EXISTS idx_query_logs_time_provider ON query_logs(timestamp DESC, provider);

-- View: Recent queries with key metrics
CREATE OR REPLACE VIEW recent_queries AS
SELECT 
    timestamp,
    LEFT(prompt, 50) || '...' AS prompt_preview,
    provider,
    complexity_category,
    cached,
    cache_type,
    ROUND(latency_ms::numeric, 2) AS latency_ms,
    tokens_used,
    status
FROM query_logs
ORDER BY timestamp DESC
LIMIT 100;

-- View: Cache effectiveness by provider
CREATE OR REPLACE VIEW cache_effectiveness AS
SELECT 
    provider,
    COUNT(*) AS total_queries,
    SUM(CASE WHEN cached THEN 1 ELSE 0 END) AS cache_hits,
    ROUND(100.0 * SUM(CASE WHEN cached THEN 1 ELSE 0 END) / COUNT(*), 2) AS hit_rate_pct,
    ROUND(AVG(CASE WHEN cached THEN latency_ms END)::numeric, 2) AS avg_cached_latency_ms,
    ROUND(AVG(CASE WHEN NOT cached THEN latency_ms END)::numeric, 2) AS avg_uncached_latency_ms
FROM query_logs
WHERE status = 'success'
GROUP BY provider;

-- View: Cost analysis
CREATE OR REPLACE VIEW cost_analysis AS
SELECT 
    DATE(timestamp) AS date,
    provider,
    COUNT(*) AS queries,
    SUM(tokens_used) AS total_tokens,
    ROUND(SUM(estimated_cost_usd)::numeric, 4) AS total_estimated_cost,
    ROUND(SUM(cost_saved_usd)::numeric, 4) AS total_saved,
    ROUND((SUM(cost_saved_usd) / NULLIF(SUM(estimated_cost_usd) + SUM(cost_saved_usd), 0) * 100)::numeric, 2) AS savings_pct
FROM query_logs
WHERE status = 'success'
GROUP BY DATE(timestamp), provider
ORDER BY date DESC, provider;

-- View: Complexity distribution
CREATE OR REPLACE VIEW complexity_distribution AS
SELECT 
    complexity_category,
    COUNT(*) AS query_count,
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM query_logs WHERE status = 'success'), 0), 2) AS percentage,
    ROUND(AVG(complexity_score)::numeric, 1) AS avg_score,
    ROUND(AVG(latency_ms)::numeric, 2) AS avg_latency_ms,
    ARRAY_AGG(DISTINCT provider) AS providers_used
FROM query_logs
WHERE status = 'success' AND complexity_category IS NOT NULL
GROUP BY complexity_category
ORDER BY 
    CASE complexity_category
        WHEN 'simple' THEN 1
        WHEN 'medium' THEN 2
        WHEN 'complex' THEN 3
    END;
