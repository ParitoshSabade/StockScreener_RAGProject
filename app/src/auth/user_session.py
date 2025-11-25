"""
User Session Management
"""
import logging
from datetime import datetime
from typing import Optional, Dict
import psycopg2
from ..utils.database import get_db_connection

logger = logging.getLogger(__name__)


class UserSession:
    """Manages user session data"""
    
    @staticmethod
    def create_session(session_id: str, ip_address: str) -> bool:
        """
        Create a new user session
        
        Args:
            session_id: Unique session identifier
            ip_address: User's IP address
        
        Returns:
            True if successful
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            today = datetime.now().date()
            
            cursor.execute("""
                INSERT INTO user_sessions (session_id, ip_address, query_count, last_query_date, last_query_timestamp)
                VALUES (%s, %s, 0, %s, NOW())
                ON CONFLICT (session_id, last_query_date) DO NOTHING
            """, (session_id, ip_address, today))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Created session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    @staticmethod
    def get_session_info(session_id: str) -> Optional[Dict]:
        """
        Get session information
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dict with session info or None
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            today = datetime.now().date()
            
            cursor.execute("""
                SELECT session_id, ip_address, query_count, last_query_date, last_query_timestamp
                FROM user_sessions
                WHERE session_id = %s AND last_query_date = %s
            """, (session_id, today))
            
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return {
                    'session_id': result[0],
                    'ip_address': result[1],
                    'query_count': result[2],
                    'last_query_date': result[3],
                    'last_query_timestamp': result[4]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None