"""
Company Loader - Load company list from database
"""
import logging
import psycopg2
from typing import Dict
from .database import get_db_connection

logger = logging.getLogger(__name__)


class CompanyLoader:
    """Loads company ticker-name mapping from database"""
    
    _cache = None
    
    @classmethod
    def load_companies(cls) -> str:
        """
        Load all companies and format as string for LLM context
        
        Returns:
            Formatted string like "AAPL: Apple Inc\nMSFT: Microsoft Corporation\n..."
        """
        if cls._cache is not None:
            return cls._cache
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ticker, name 
                FROM companies 
                ORDER BY ticker
            """)
            
            companies = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Format as "TICKER: Company Name"
            company_list = "\n".join([
                f"{ticker}: {name}" 
                for ticker, name in companies
            ])
            
            cls._cache = company_list
            logger.info(f"Loaded {len(companies)} companies for LLM context")
            
            return company_list
            
        except Exception as e:
            logger.error(f"Error loading companies: {e}")
            return ""
    
    @classmethod
    def get_company_dict(cls) -> Dict[str, str]:
        """
        Get companies as dict for programmatic access
        
        Returns:
            Dict mapping ticker -> name
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT ticker, name FROM companies")
            companies = dict(cursor.fetchall())
            
            cursor.close()
            conn.close()
            
            return companies
            
        except Exception as e:
            logger.error(f"Error loading companies: {e}")
            return {}