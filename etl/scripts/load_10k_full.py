#!/usr/bin/env python3
"""
Full 10-K data load for all NASDAQ-100 companies
Uses dual SecBlast API keys to process all 100 companies in one day
API Key 1: Companies 1-50 (100 requests)
API Key 2: Companies 51-100 (100 requests)
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    SECBLAST_API_KEY_1, SECBLAST_API_KEY_2, 
    SECBLAST_DAILY_LIMIT_PER_KEY
)
from config.nasdaq100_tickers import NASDAQ100_TICKERS
from src.fetchers import fetch_latest_10k
from src.processors import process_10k_sections
from src.database import get_db_connection, store_10k_data
from src.utils import setup_logging

logger = logging.getLogger(__name__)


def check_10k_exists(conn, ticker: str) -> bool:
    """Check if 10-K data already exists for a ticker"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT EXISTS(
            SELECT 1 FROM tenk_documents WHERE ticker = %s
        )
    """, (ticker,))
    return cursor.fetchone()[0]


def main(force_reload: bool = False, start_from: int = 0):
    """
    Load 10-K data for all NASDAQ-100 companies
    
    Args:
        force_reload: If True, reload data even if it exists
        start_from: Index to start from (0-based, for resuming)
    """
    setup_logging("10k_full_load.log")
    
    logger.info("="*80)
    logger.info("10-K DATA LOAD - FULL RUN")
    logger.info("="*80)
    logger.info(f"Total companies: {len(NASDAQ100_TICKERS)}")
    logger.info(f"API Key 1: Companies 1-50 ({SECBLAST_DAILY_LIMIT_PER_KEY} calls limit)")
    logger.info(f"API Key 2: Companies 51-100 ({SECBLAST_DAILY_LIMIT_PER_KEY} calls limit)")
    logger.info(f"Force reload: {force_reload}")
    logger.info(f"Starting from company index: {start_from}")
    logger.info("="*80)
    
    # Validate API keys
    if not SECBLAST_API_KEY_1 or not SECBLAST_API_KEY_2:
        logger.error("✗ Both SECBLAST_API_KEY_1 and SECBLAST_API_KEY_2 must be set in .env")
        return
    
    try:
        conn = get_db_connection()
        logger.info("✓ Database connection established\n")
    except Exception as e:
        logger.error(f"✗ Failed to connect to database: {e}")
        return
    
    stats = {
        "key1_success": 0,
        "key1_calls": 0,
        "key2_success": 0,
        "key2_calls": 0,
        "skipped": 0,
        "failed": 0,
        "no_data": 0
    }
    
    for idx, ticker in enumerate(NASDAQ100_TICKERS[start_from:], start_from):
        actual_idx = idx + 1  # 1-based for display
        logger.info(f"\n{'='*80}")
        logger.info(f"[{actual_idx}/{len(NASDAQ100_TICKERS)}] {ticker}")
        logger.info(f"{'='*80}")
        
        try:
            # Check if already exists
            if not force_reload and check_10k_exists(conn, ticker):
                logger.info(f"  ⊙ Data already exists, skipping...")
                stats["skipped"] += 1
                continue
            
            # Determine which API key to use (split at company 50)
            if actual_idx <= 50:
                api_key = SECBLAST_API_KEY_1
                key_name = "Key 1"
                current_calls = stats["key1_calls"]
                call_limit = SECBLAST_DAILY_LIMIT_PER_KEY
            else:
                api_key = SECBLAST_API_KEY_2
                key_name = "Key 2"
                current_calls = stats["key2_calls"]
                call_limit = SECBLAST_DAILY_LIMIT_PER_KEY
            
            # Check rate limit for this key
            if current_calls >= call_limit:
                logger.error(f"  ✗ {key_name} rate limit reached ({call_limit} calls)")
                logger.error(f"  Stopping at company {actual_idx}")
                break
            
            logger.info(f"  Using {key_name} (calls: {current_calls}/{call_limit})")
            
            # Fetch 10-K
            logger.info(f"  → Fetching 10-K from SecBlast...")
            tenk_data = fetch_latest_10k(ticker, api_key=api_key)
            
            # Update call counter
            if actual_idx <= 50:
                stats["key1_calls"] += 2 
            else:
                stats["key2_calls"] += 2
            
            if not tenk_data:
                logger.warning(f"  ⚠ No 10-K found")
                stats["no_data"] += 1
                continue
            
            logger.info(f"  → Found FY{tenk_data['fiscal_year']} 10-K")
            
            # Process sections
            logger.info(f"  → Processing sections...")
            sections, chunks = process_10k_sections(tenk_data)
            logger.info(f"    {len(sections)} sections, {len(chunks)} chunks")
            
            # Store with embeddings
            logger.info(f"  → Storing data and generating embeddings...")
            store_10k_data(conn, tenk_data, sections, chunks)
            
            if actual_idx <= 50:
                stats["key1_success"] += 1
            else:
                stats["key2_success"] += 1
            
            logger.info(f"  ✓ Success")
            
        except Exception as e:
            logger.error(f"  ✗ Error: {e}", exc_info=True)
            stats["failed"] += 1
            continue
        
        # Progress update every 10 companies
        if actual_idx % 10 == 0:
            logger.info(f"\n{'─'*80}")
            logger.info(f"Progress Update: {actual_idx}/{len(NASDAQ100_TICKERS)}")
            logger.info(f"Key 1: {stats['key1_success']} success, {stats['key1_calls']}/{SECBLAST_DAILY_LIMIT_PER_KEY} calls")
            logger.info(f"Key 2: {stats['key2_success']} success, {stats['key2_calls']}/{SECBLAST_DAILY_LIMIT_PER_KEY} calls")
            logger.info(f"{'─'*80}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("10-K LOAD SUMMARY")
    print("="*80)
    print(f"Total companies: {len(NASDAQ100_TICKERS)}")
    print(f"\nAPI Key 1 (Companies 1-50):")
    print(f"  ✓ Successfully loaded: {stats['key1_success']}")
    print(f"  📊 API calls used: {stats['key1_calls']}/{SECBLAST_DAILY_LIMIT_PER_KEY}")
    print(f"\nAPI Key 2 (Companies 51-100):")
    print(f"  ✓ Successfully loaded: {stats['key2_success']}")
    print(f"  📊 API calls used: {stats['key2_calls']}/{SECBLAST_DAILY_LIMIT_PER_KEY}")
    print(f"\n⊙ Already existed (skipped): {stats['skipped']}")
    print(f"⚠ No data available: {stats['no_data']}")
    print(f"✗ Failed: {stats['failed']}")
    print("="*80)
    
    total_success = stats['key1_success'] + stats['key2_success'] + stats['skipped']
    if total_success == len(NASDAQ100_TICKERS):
        logger.info("\n✓ All 10-K data loaded successfully!")
    else:
        logger.warning(f"\n⚠ {len(NASDAQ100_TICKERS) - total_success} companies missing 10-K data")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load 10-K data with dual API keys")
    parser.add_argument(
        "--force-reload", 
        action="store_true",
        help="Force reload all data, even if it already exists"
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=0,
        help="Start from this company index (0-based, for resuming)"
    )
    
    args = parser.parse_args()
    main(force_reload=args.force_reload, start_from=args.start_from)