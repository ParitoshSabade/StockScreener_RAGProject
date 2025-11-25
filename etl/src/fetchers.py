"""
API data fetching functions for SimFin and SecBlast
"""
import time
import requests
import logging
from typing import Dict, List, Optional
from config.settings import (
    SIMFIN_API_KEY, SIMFIN_BASE_URL, SIMFIN_RATE_LIMIT,
    SECBLAST_API_KEY_1, SECBLAST_BASE_URL
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, calls_per_second: float):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
    
    def wait(self):
        """Wait if necessary to respect rate limit"""
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


# Initialize rate limiter for SimFin
simfin_limiter = RateLimiter(SIMFIN_RATE_LIMIT)

def fetch_simfin_data(ticker: str, start_date: str) -> Optional[Dict]:
    """
    Fetch all financial statements for a company from SimFin
    
    Args:
        ticker: Company ticker symbol
        start_date: Start date in YYYY-MM-DD format
    
    Returns:
        Dict with company data and statements, or None if error
    """
    simfin_limiter.wait()
    
    url = f"{SIMFIN_BASE_URL}/companies/statements/verbose"  # Changed to verbose
    params = {
        "ticker": ticker,
        "statements": "PL,BS,CF,DERIVED",
        "period": "FY,Q1,Q2,Q3,Q4",
        "start": start_date
    }
    headers = {
        "Authorization": SIMFIN_API_KEY,
        "accept": "application/json"
    }
    
    try:
        logger.info(f"Fetching SimFin data for {ticker}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data or len(data) == 0:
            logger.warning(f"No SimFin data found for {ticker}")
            return None
        
        logger.info(f"✓ Fetched SimFin data for {ticker}")
        return data[0]  # Return first element (company data)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching SimFin data for {ticker}: {e}")
        return None

def fetch_latest_10k(ticker: str, api_key: str = None) -> Optional[Dict]:
    """
    Fetch the most recent 10-K filing for a company from SecBlast
    
    Args:
        ticker: Company ticker symbol
        api_key: Optional SecBlast API key (defaults to SECBLAST_API_KEY_1)
    
    Returns:
        Dict with 10-K document and sections, or None if error/not found
    """
    # Use provided API key or default to first production key
    if api_key is None:
        api_key = SECBLAST_API_KEY_1
    
    try:
        logger.info(f"Looking up latest 10-K for {ticker}")
        lookup_url = f"{SECBLAST_BASE_URL}/lookup"
        lookup_params = {
            "api_key": api_key,
            "tickers": ticker,
            "form_types": "10-K",
            "limit": 1
        }
        
        lookup_response = requests.get(lookup_url, params=lookup_params, timeout=30)
        lookup_response.raise_for_status()
        lookup_data = lookup_response.json()
        
        if lookup_data.get("response_details", {}).get("filings_found", 0) == 0:
            logger.warning(f"No 10-K found for {ticker}")
            return None
        
        filing = lookup_data["filings"][0]
        document_id = None
        doc_metadata = None
        
        for doc in filing.get("documents", []):
            if doc["form_type"] == "10-K" and doc["description"] == "10-K":
                document_id = doc["document_id"]
                doc_metadata = doc
                break
        
        if not document_id:
            logger.warning(f"No 10-K document found in filing for {ticker}")
            return None
        
        logger.info(f"Fetching 10-K sections for {ticker} (document: {document_id})")
        sections_url = f"{SECBLAST_BASE_URL}/document_sections"
        sections_params = {
            "api_key": api_key,
            "document_id": document_id,
            "strip_html": "true"
        }
        
        sections_response = requests.get(sections_url, params=sections_params, timeout=60)
        sections_response.raise_for_status()
        sections_data = sections_response.json()
        
        fiscal_year = _extract_fiscal_year(doc_metadata["file_name"])
        
        result = {
            "ticker": ticker,
            "accession_number": filing["accnum"],
            "document_id": document_id,
            "file_name": doc_metadata["file_name"],
            "size": doc_metadata["size"],
            "fiscal_year": fiscal_year,
            "sections": sections_data.get("sections", [])
        }
        
        logger.info(f"✓ Fetched 10-K for {ticker} (FY{fiscal_year}, {len(result['sections'])} sections)")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching 10-K for {ticker}: {e}")
        return None


def _extract_fiscal_year(filename: str) -> Optional[int]:
    """
    Extract fiscal year from filename like 'aapl-20250927.htm'
    
    Args:
        filename: SEC filing filename
    
    Returns:
        Fiscal year as integer, or None if not found
    """
    import re
    match = re.search(r'(\d{4})\d{4}', filename)
    if match:
        return int(match.group(1))
    return None