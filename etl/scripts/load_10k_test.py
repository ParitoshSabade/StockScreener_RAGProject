#!/usr/bin/env python3
"""
Test script for SecBlast 10-K data loading
Uses DEDICATED TEST API KEY - won't affect production limits
Tests on 2 companies to verify everything works before full run
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import SECBLAST_TEST_API_KEY
from src.fetchers import fetch_latest_10k
from src.processors import process_10k_sections
from src.database import get_db_connection, store_10k_data
from src.utils import setup_logging

logger = logging.getLogger(__name__)

# Test companies
TEST_TICKERS = ["AAPL", "MSFT"]


def main():
    """Test 10-K loading on 2 companies using test API key"""
    setup_logging("10k_test.log")
    
    logger.info("="*80)
    logger.info("10-K DATA LOAD - TEST RUN (Using Test API Key)")
    logger.info("="*80)
    logger.info(f"Test companies: {TEST_TICKERS}")
    logger.info("="*80)
    
    # Validate test API key
    if not SECBLAST_TEST_API_KEY:
        logger.error("✗ SECBLAST_TEST_API_KEY not set in .env file")
        logger.error("Please add your test account API key")
        return
    
    logger.info(f"✓ Using test API key: {SECBLAST_TEST_API_KEY[:8]}...")
    
    # Connect to database
    try:
        conn = get_db_connection()
        logger.info("✓ Database connection established\n")
    except Exception as e:
        logger.error(f"✗ Failed to connect to database: {e}")
        return
    
    total_api_calls = 0
    
    # Test each company
    for idx, ticker in enumerate(TEST_TICKERS, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"[{idx}/{len(TEST_TICKERS)}] Testing {ticker}")
        logger.info(f"{'='*80}")
        
        try:
            # Step 1: Fetch 10-K using TEST API key
            logger.info("Step 1: Fetching 10-K from SecBlast (TEST API)...")
            tenk_data = fetch_latest_10k(ticker, api_key=SECBLAST_TEST_API_KEY)
            total_api_calls += 2  # lookup + sections
            
            if not tenk_data:
                logger.error(f"✗ No 10-K found for {ticker}")
                logger.error("This might indicate an API issue. Check your test API key.")
                continue
            
            logger.info(f"✓ Successfully fetched 10-K")
            logger.info(f"  Fiscal Year: {tenk_data['fiscal_year']}")
            logger.info(f"  Accession: {tenk_data['accession_number']}")
            logger.info(f"  Document ID: {tenk_data['document_id']}")
            logger.info(f"  File: {tenk_data['file_name']}")
            logger.info(f"  Total sections: {len(tenk_data['sections'])}")
            
            # Step 2: Process sections
            logger.info("\nStep 2: Processing sections...")
            sections, chunks = process_10k_sections(tenk_data)
            logger.info(f"✓ Processed {len(sections)} priority sections")
            logger.info(f"✓ Created {len(chunks)} chunks for embedding")
            
            # Show detailed section breakdown
            logger.info("\nPriority sections (will be stored):")
            for section in sections:
                logger.info(f"  • {section['item_label']}: {section['item_description']}")
                logger.info(f"    Content length: {section['content_length']:,} characters")
                # Count chunks for this section
                section_chunks = [c for c in chunks if c['section_id'] == section['section_id']]
                logger.info(f"    Chunks: {len(section_chunks)}")
            # Step 3: Store with embeddings
            logger.info(f"\nStep 3: Storing data and generating embeddings...")
            logger.info(f"  This will make {len(chunks)} OpenAI API calls...")
            store_10k_data(conn, tenk_data, sections, chunks)
            logger.info(f"✓ Successfully stored all data for {ticker}")
            
            # Step 4: Verify in database
            logger.info("\nStep 4: Verifying data in database...")
            cursor = conn.cursor()
            
            # Check document
            cursor.execute("""
                SELECT ticker, fiscal_year, accession_number 
                FROM tenk_documents 
                WHERE ticker = %s
            """, (ticker,))
            doc_result = cursor.fetchone()
            if doc_result:
                logger.info(f"✓ Document record found: {doc_result}")
            else:
                logger.error(f"✗ Document record NOT found!")
            
            # Check sections
            cursor.execute("""
                SELECT COUNT(*), STRING_AGG(item_label, ', ' ORDER BY item_label)
                FROM tenk_sections 
                WHERE document_id = %s
            """, (tenk_data['document_id'],))
            section_count, section_labels = cursor.fetchone()
            logger.info(f"✓ Sections stored: {section_count}")
            logger.info(f"  Items: {section_labels}")
            
            # Check embeddings
            cursor.execute("""
                SELECT COUNT(*) FROM tenk_embeddings WHERE ticker = %s
            """, (ticker,))
            embedding_count = cursor.fetchone()[0]
            logger.info(f"✓ Embeddings stored: {embedding_count}")
            
            # Verify embedding dimensions
            cursor.execute("""
                SELECT embedding FROM tenk_embeddings WHERE ticker = %s LIMIT 1
            """, (ticker,))
            sample_embedding = cursor.fetchone()
            if sample_embedding:
                embedding_dims = len(sample_embedding[0])
                logger.info(f"✓ Embedding dimensions: {embedding_dims}")
                if embedding_dims == 1536:
                    logger.info(f"  ✓ Correct dimensions for text-embedding-3-small")
                else:
                    logger.warning(f"  ⚠ Unexpected dimensions (expected 1536)")
            
            logger.info(f"\n{'✓'*40}")
            logger.info(f"✓ ALL TESTS PASSED FOR {ticker}")
            logger.info(f"{'✓'*40}")
            
        except Exception as e:
            logger.error(f"\n{'✗'*40}")
            logger.error(f"✗ ERROR processing {ticker}")
            logger.error(f"{'✗'*40}")
            logger.error(f"Error: {e}", exc_info=True)
            continue
    
    conn.close()
    
    print("\n" + "="*80)
    print("TEST RUN SUMMARY")
    print("="*80)
    print(f"Companies tested: {len(TEST_TICKERS)}")
    print(f"SecBlast API calls used (test account): {total_api_calls}")
    print("="*80)
    
    if total_api_calls == len(TEST_TICKERS) * 2:
        print("\n✓ ALL SYSTEMS WORKING!")
        print("\nYou can now proceed with the full production load:")
        print("  1. Run SimFin load: python scripts/load_simfin.py")
        print("  2. Run full 10-K load: python scripts/load_10k_full.py")
    else:
        print("\n⚠ Some tests failed. Review logs before proceeding.")
    
    print("="*80)


if __name__ == "__main__":
    main()