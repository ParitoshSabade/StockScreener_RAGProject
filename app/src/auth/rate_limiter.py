"""
Rate Limiter - Controls query limits per user session and IP
"""
import logging
from datetime import datetime, timedelta
from typing import Dict
import psycopg2
from ..utils.database import get_db_connection

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting for user queries"""
    
    # Limits
    SESSION_DAILY_LIMIT = 30  # 30 queries per session per day
    IP_DAILY_LIMIT = 1000     # 1000 queries per IP per day
    
    @staticmethod
    def check_and_increment(session_id: str, ip_address: str) -> Dict:
        """
        Check rate limits and increment counter if allowed
        
        Args:
            session_id: User session ID
            ip_address: User IP address
        
        Returns:
            Dict with 'allowed' (bool), 'limit_type' (str), and counts
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get today's date
            today = datetime.now().date()
            
            # Check session limit
            cursor.execute("""
                SELECT query_count FROM user_sessions
                WHERE session_id = %s AND last_query_date = %s
            """, (session_id, today))
            
            session_result = cursor.fetchone()
            session_count = session_result[0] if session_result else 0
            
            # Check IP limit
            cursor.execute("""
                SELECT SUM(query_count) FROM user_sessions
                WHERE ip_address = %s AND last_query_date = %s
            """, (ip_address, today))
            
            ip_result = cursor.fetchone()
            ip_count = ip_result[0] if ip_result and ip_result[0] else 0
            
            # Check if limits exceeded
            if session_count >= RateLimiter.SESSION_DAILY_LIMIT:
                cursor.close()
                conn.close()
                return {
                    'allowed': False,
                    'limit_type': 'session',
                    'session_count': session_count,
                    'ip_count': ip_count
                }
            
            if ip_count >= RateLimiter.IP_DAILY_LIMIT:
                cursor.close()
                conn.close()
                return {
                    'allowed': False,
                    'limit_type': 'ip',
                    'session_count': session_count,
                    'ip_count': ip_count
                }
            
            # Increment counter
            if session_result:
                # Update existing session
                cursor.execute("""
                    UPDATE user_sessions
                    SET query_count = query_count + 1,
                        last_query_timestamp = NOW()
                    WHERE session_id = %s AND last_query_date = %s
                """, (session_id, today))
            else:
                # Create new session for today
                cursor.execute("""
                    INSERT INTO user_sessions (session_id, ip_address, query_count, last_query_date, last_query_timestamp)
                    VALUES (%s, %s, 1, %s, NOW())
                    ON CONFLICT (session_id, last_query_date) 
                    DO UPDATE SET 
                        query_count = user_sessions.query_count + 1,
                        last_query_timestamp = NOW()
                """, (session_id, ip_address, today))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                'allowed': True,
                'limit_type': None,
                'session_count': session_count + 1,
                'ip_count': ip_count + 1
            }
            
        except Exception as e:
            logger.error(f"Error in rate limiting: {e}")
            # On error, allow the query (fail open)
            return {
                'allowed': True,
                'limit_type': None,
                'session_count': 0,
                'ip_count': 0
            }
    
    @staticmethod
    def get_usage_stats(session_id: str) -> Dict:
        """
        Get usage statistics for a session
        
        Args:
            session_id: User session ID
        
        Returns:
            Dict with usage statistics
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            today = datetime.now().date()
            
            cursor.execute("""
                SELECT query_count, last_query_timestamp
                FROM user_sessions
                WHERE session_id = %s AND last_query_date = %s
            """, (session_id, today))
            
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return {
                    'queries_today': result[0],
                    'queries_remaining': max(0, RateLimiter.SESSION_DAILY_LIMIT - result[0]),
                    'last_query': result[1],
                    'daily_limit': RateLimiter.SESSION_DAILY_LIMIT
                }
            else:
                return {
                    'queries_today': 0,
                    'queries_remaining': RateLimiter.SESSION_DAILY_LIMIT,
                    'last_query': None,
                    'daily_limit': RateLimiter.SESSION_DAILY_LIMIT
                }
                
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return {
                'queries_today': 0,
                'queries_remaining': RateLimiter.SESSION_DAILY_LIMIT,
                'last_query': None,
                'daily_limit': RateLimiter.SESSION_DAILY_LIMIT
            }
    
    @staticmethod
    def reset_session(session_id: str) -> bool:
        """
        Reset a session's query count (admin function)
        
        Args:
            session_id: Session ID to reset
        
        Returns:
            True if successful
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            today = datetime.now().date()
            
            cursor.execute("""
                DELETE FROM user_sessions
                WHERE session_id = %s AND last_query_date = %s
            """, (session_id, today))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error resetting session: {e}")
            return False