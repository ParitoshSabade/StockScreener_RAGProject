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
def get_env_var(key):
    """Get environment variable from .env or Streamlit secrets"""
    # Try Streamlit secrets first (for deployment)
    if hasattr(st, 'secrets') and key in st.secrets:
        return st.secrets[key]
    # Fallback to environment variable (for local dev)
    return os.getenv(key)

# Database configuration
DB_CONFIG = {
    "host": get_env_var("DB_HOST"),
    "port": int(get_env_var("DB_PORT", 5432)),
    "dbname": get_env_var("DB_NAME"),
    "user": get_env_var("DB_USER"),
    "password": get_env_var("DB_PASSWORD"),
    "sslmode": get_env_var("DB_SSLMODE", "require")
}


def get_db_connection():
    """
    Create and return a database connection
    
    Returns:
        Database connection object
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
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