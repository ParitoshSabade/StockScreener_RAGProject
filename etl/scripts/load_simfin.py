#!/usr/bin/env python3
"""
Load SimFin financial data for all NASDAQ-100 companies
3 FY + 4 quarters for each company
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import INITIAL_LOAD_START_DATE
from config.nasdaq100_tickers import NASDAQ100_TICKERS
from src.fetchers import fetch_simfin_data
from src.processors import process_simfin_data
from src.database import get_db_connection, store_simfin_data
from src.utils import setup_logging

logger = logging.getLogger(__name__)


def check_simfin_exists(conn, ticker: str) -> bool:
    """Check if SimFin data already exists for a ticker"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT EXISTS(
            SELECT 1 FROM income_statement WHERE ticker = %s
        )
    """, (ticker,))
    return cursor.fetchone()[0]


def main(force_reload: bool = False):
    """Load SimFin data for all NASDAQ-100 companies"""
    setup_logging("simfin_load.log")
    
    logger.info("="*80)
    logger.info("SIMFIN DATA LOAD")
    logger.info("="*80)
    logger.info(f"Companies to process: {len(NASDAQ100_TICKERS)}")
    logger.info(f"Start date: {INITIAL_LOAD_START_DATE}")
    logger.info(f"Force reload: {force_reload}")
    logger.info("="*80)
    
    try:
        conn = get_db_connection()
        logger.info("✓ Database connection established\n")
    except Exception as e:
        logger.error(f"✗ Failed to connect to database: {e}")
        return
    
    stats = {
        "success": 0,
        "skipped": 0,
        "failed": 0,
        "no_data": 0
    }
    
    # Process each company
    for idx, ticker in enumerate(NASDAQ100_TICKERS, 1):
        logger.info(f"[{idx}/{len(NASDAQ100_TICKERS)}] {ticker}")
        
        try:
            # Check if already exists
            if not force_reload and check_simfin_exists(conn, ticker):
                logger.info(f"  ⊙ Data already exists, skipping...")
                stats["skipped"] += 1
                continue
            
            # Fetch data
            logger.info(f"  → Fetching from SimFin...")
            simfin_raw = fetch_simfin_data(ticker, INITIAL_LOAD_START_DATE)
            
            if not simfin_raw:
                logger.warning(f"  ⚠ No data available")
                stats["no_data"] += 1
                continue
            
            # Process and store
            logger.info(f"  → Processing and storing...")
            company_data, statements = process_simfin_data(simfin_raw)
            store_simfin_data(conn, company_data, statements)
            
            stats["success"] += 1
            logger.info(f"  ✓ Success\n")
            
        except Exception as e:
            logger.error(f"  ✗ Error: {e}\n")
            stats["failed"] += 1
            continue
    
    conn.close()
    
    print("\n" + "="*80)
    print("SIMFIN LOAD SUMMARY")
    print("="*80)
    print(f"Total companies: {len(NASDAQ100_TICKERS)}")
    print(f"✓ Successfully loaded: {stats['success']}")
    print(f"⊙ Already existed (skipped): {stats['skipped']}")
    print(f"⚠ No data available: {stats['no_data']}")
    print(f"✗ Failed: {stats['failed']}")
    print("="*80)
    
    if stats["success"] + stats["skipped"] == len(NASDAQ100_TICKERS):
        logger.info("\n✓ All SimFin data loaded successfully!")
    else:
        logger.warning(f"\n⚠ {len(NASDAQ100_TICKERS) - stats['success'] - stats['skipped']} companies missing data")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load SimFin data")
    parser.add_argument(
        "--force-reload", 
        action="store_true",
        help="Force reload all data, even if it already exists"
    )
    
    args = parser.parse_args()
    main(force_reload=args.force_reload)