-- ============================================================================
-- ANALYTICS QUERIES
-- Run these in Supabase SQL Editor when you want to check usage
-- ============================================================================

-- 1. Total unique users today
SELECT COUNT(DISTINCT session_id) as unique_users_today
FROM session_quota
WHERE usage_date = CURRENT_DATE;

-- 2. Total queries today
SELECT SUM(query_count) as total_queries_today
FROM session_quota
WHERE usage_date = CURRENT_DATE;

-- 3. Active users last 7 days
SELECT 
    usage_date,
    COUNT(DISTINCT session_id) as unique_users,
    SUM(query_count) as total_queries
FROM session_quota
WHERE usage_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY usage_date
ORDER BY usage_date DESC;

-- 4. Weekly summary
SELECT 
    COUNT(DISTINCT session_id) as unique_users,
    SUM(query_count) as total_queries,
    ROUND(AVG(query_count), 1) as avg_per_user,
    MAX(query_count) as max_queries_by_one_user
FROM session_quota
WHERE usage_date >= CURRENT_DATE - INTERVAL '7 days';

-- 5. Power users approaching limit today
SELECT 
    session_id,
    query_count,
    30 - query_count as remaining
FROM session_quota
WHERE usage_date = CURRENT_DATE
  AND query_count >= 25
ORDER BY query_count DESC;

-- 6. Check for IP quota abuse
SELECT 
    ip_hash,
    query_count,
    1000 - query_count as remaining
FROM ip_quota
WHERE usage_date = CURRENT_DATE
  AND query_count > 500
ORDER BY query_count DESC;

-- 7. Daily trend (last 30 days)
SELECT 
    usage_date,
    COUNT(DISTINCT session_id) as users,
    SUM(query_count) as queries
FROM session_quota
WHERE usage_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY usage_date
ORDER BY usage_date DESC;

-- 8. Cleanup old data (run monthly)
DELETE FROM session_quota WHERE usage_date < CURRENT_DATE - INTERVAL '90 days';
DELETE FROM ip_quota WHERE usage_date < CURRENT_DATE - INTERVAL '90 days';
DELETE FROM user_sessions WHERE last_seen < CURRENT_DATE - INTERVAL '180 days';