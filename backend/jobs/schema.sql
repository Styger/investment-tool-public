-- Screening Jobs Queue
CREATE TABLE IF NOT EXISTS screening_jobs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    
    -- Timestamps
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    
    -- Job Configuration
    strategy_id TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    universe_key TEXT NOT NULL,
    universe_name TEXT NOT NULL,
    parameters TEXT NOT NULL,  -- JSON: strategy parameters
    
    -- Results
    results TEXT,  -- JSON: screening results DataFrame
    error_message TEXT,
    
    -- Progress
    progress INTEGER DEFAULT 0,  -- 0-100
    stocks_processed INTEGER DEFAULT 0,
    stocks_total INTEGER DEFAULT 0,
    
    -- Metadata
    result_summary TEXT  -- JSON: {buy_count, hold_count, sell_count, avg_mos}
);

CREATE INDEX IF NOT EXISTS idx_screening_user_status ON screening_jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_screening_created ON screening_jobs(created_at DESC);