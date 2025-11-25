"""
Database utilities for RAG application
"""
import os
import logging
import psycopg2
from typing import Optional
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def get_env_var(key, default=None):
    """Get environment variable from .env or Streamlit secrets"""
    if hasattr(st, 'secrets') and key in st.secrets:
        return st.secrets[key]
    return os.getenv(key, default)

def get_db_connection():
    """
    Create and return a database connection
    
    Returns:
        Database connection object
    """
    database_url = get_env_var("DATABASE_URL")
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


def test_connection() -> bool:
    """
    Test database connection
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False