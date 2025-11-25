-- ============================================================================
-- RATE LIMITING & USER TRACKING
-- Tables for RAG application rate limiting (session + IP hybrid)
-- ============================================================================

-- Track user sessions (anonymous)
CREATE TABLE user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_sessions_last_seen ON user_sessions(last_seen);

-- Session-based daily quota (30 queries/day per session)
CREATE TABLE session_quota (
    session_id VARCHAR(255) NOT NULL,
    usage_date DATE NOT NULL,
    query_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (session_id, usage_date)
);

CREATE INDEX idx_session_quota_date ON session_quota(usage_date);
CREATE INDEX idx_session_quota_session ON session_quota(session_id, usage_date);

-- IP-based daily quota (1000 queries/day per IP)
CREATE TABLE ip_quota (
    ip_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash of IP address
    usage_date DATE NOT NULL,
    query_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (ip_hash, usage_date)
);

CREATE INDEX idx_ip_quota_date ON ip_quota(usage_date);
CREATE INDEX idx_ip_quota_hash ON ip_quota(ip_hash, usage_date);

-- Comments
COMMENT ON TABLE user_sessions IS 'Anonymous user session tracking';
COMMENT ON TABLE session_quota IS 'Daily query quota per session (30/day)';
COMMENT ON TABLE ip_quota IS 'Daily query quota per IP address (1000/day)';