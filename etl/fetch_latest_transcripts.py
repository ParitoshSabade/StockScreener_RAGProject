"""
Fetch Latest Earning Call Transcript for each NASDAQ-100 Company
Storage-efficient: Only fetches the most recent transcript per company
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from defeatbeta_api.data.ticker import Ticker
import psycopg2
from datetime import datetime
import time
from utils.database import get_db_connection
from utils.company_loader import CompanyLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_latest_transcript(ticker_symbol: str) -> dict:
    """
    Fetch only the latest earning call transcript for a ticker
    
    Returns:
        Dict with transcript data or None
    """
    try:
        logger.info(f"Fetching latest transcript for {ticker_symbol}...")
        ticker = Ticker(ticker_symbol)
        transcripts_obj = ticker.earning_call_transcripts()
        
        # Get list of all transcripts
        transcripts_list = transcripts_obj.get_transcripts_list()
        
        if transcripts_list.empty:
            logger.warning(f"❌ No transcripts found for {ticker_symbol}")
            return None
        
        # Get the most recent (last row)
        latest = transcripts_list.iloc[-1]
        fiscal_year = int(latest['fiscal_year'])
        fiscal_quarter = int(latest['fiscal_quarter'])
        report_date = latest['report_date']
        
        logger.info(f"Found: Q{fiscal_quarter} {fiscal_year} ({report_date})")
        
        # Fetch actual content
        transcript_df = transcripts_obj.get_transcript(fiscal_year, fiscal_quarter)
        
        if transcript_df.empty:
            logger.warning(f"❌ Transcript content empty for {ticker_symbol}")
            return None
        
        # Combine paragraphs with speaker labels
        paragraphs = []
        for _, row in transcript_df.iterrows():
            paragraphs.append({
                'speaker': row['speaker'],
                'content': row['content'],
                'paragraph_number': int(row['paragraph_number'])
            })
        
        logger.info(f"✅ {ticker_symbol}: {len(paragraphs)} paragraphs, {len(transcript_df['speaker'].unique())} speakers")
        
        return {
            'ticker': ticker_symbol,
            'fiscal_year': fiscal_year,
            'fiscal_quarter': fiscal_quarter,
            'report_date': str(report_date),
            'paragraphs': paragraphs
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching {ticker_symbol}: {e}")
        return None


def save_metadata(transcript_data: dict):
    """Save transcript metadata (small tracking table)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO transcript_metadata 
            (ticker, fiscal_year, fiscal_quarter, report_date, paragraph_count)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ticker) 
            DO UPDATE SET 
                fiscal_year = EXCLUDED.fiscal_year,
                fiscal_quarter = EXCLUDED.fiscal_quarter,
                report_date = EXCLUDED.report_date,
                paragraph_count = EXCLUDED.paragraph_count,
                last_updated = NOW()
        """, (
            transcript_data['ticker'],
            transcript_data['fiscal_year'],
            transcript_data['fiscal_quarter'],
            transcript_data['report_date'],
            len(transcript_data['paragraphs'])
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")


def clear_old_transcript_data(ticker: str):
    """Delete old transcript data for a ticker before inserting new"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM transcript_chunks WHERE ticker = %s", (ticker,))
        deleted = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if deleted > 0:
            logger.info(f"Cleared {deleted} old chunks for {ticker}")
        
    except Exception as e:
        logger.error(f"Error clearing old data: {e}")


def fetch_all_latest_transcripts():
    """Fetch latest transcript for all companies"""
    logger.info("="*80)
    logger.info("Fetching Latest Transcripts for NASDAQ-100 Companies")
    logger.info("="*80)
    
    # Get all companies
    loader = CompanyLoader()
    companies = loader.get_company_dict()
    
    logger.info(f"Found {len(companies)} companies to process\n")
    
    success_count = 0
    failed_tickers = []
    results = []
    
    for i, ticker in enumerate(companies.keys(), 1):
        logger.info(f"[{i}/{len(companies)}] {ticker}")
        
        try:
            # Fetch latest transcript
            transcript_data = fetch_latest_transcript(ticker)
            
            if transcript_data:
                # Clear old data for this ticker
                clear_old_transcript_data(ticker)
                
                # Save metadata
                save_metadata(transcript_data)
                
                # Store for embedding (next step)
                results.append(transcript_data)
                success_count += 1
            else:
                failed_tickers.append(ticker)
            
            # Rate limiting - be nice to API
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ {ticker}: {e}")
            failed_tickers.append(ticker)
            time.sleep(2)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("FETCH SUMMARY")
    logger.info("="*80)
    logger.info(f"Total companies: {len(companies)}")
    logger.info(f"✅ Successful: {success_count}")
    logger.info(f"❌ Failed: {len(failed_tickers)}")
    
    if failed_tickers:
        logger.info(f"\nFailed tickers: {', '.join(failed_tickers[:20])}")
        if len(failed_tickers) > 20:
            logger.info(f"... and {len(failed_tickers) - 20} more")
    
    # Save results to temp file for embedding step
    import json
    output_file = Path(__file__).parent / 'transcript_data.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📁 Saved {len(results)} transcripts to: {output_file}")
    logger.info("="*80)
    
    return results


if __name__ == "__main__":
    fetch_all_latest_transcripts()