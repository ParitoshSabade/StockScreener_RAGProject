"""
Chunk and Embed Earning Call Transcripts
Storage-efficient: Smart chunking, batch processing
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import psycopg2
from utils.database import get_db_connection

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


def smart_chunk_transcript(paragraphs: list, target_chunks: int = 30) -> list:
    """
    Smart chunking: Combine paragraphs to create ~30 chunks per transcript
    
    Args:
        paragraphs: List of paragraph dicts with 'speaker' and 'content'
        target_chunks: Target number of chunks (default 30 for storage efficiency)
    
    Returns:
        List of chunk dicts with combined text
    """
    if not paragraphs:
        return []
    
    total_paragraphs = len(paragraphs)
    paragraphs_per_chunk = max(1, total_paragraphs // target_chunks)
    
    chunks = []
    current_chunk = []
    current_speakers = []
    
    for i, para in enumerate(paragraphs):
        current_chunk.append(f"[{para['speaker']}]: {para['content']}")
        current_speakers.append(para['speaker'])
        
        # Create chunk when we hit target size or end of paragraphs
        if len(current_chunk) >= paragraphs_per_chunk or i == total_paragraphs - 1:
            chunk_text = "\n\n".join(current_chunk)
            
            # Primary speaker (most common in this chunk)
            primary_speaker = max(set(current_speakers), key=current_speakers.count)
            
            chunks.append({
                'text': chunk_text,
                'speaker': primary_speaker,
                'paragraph_count': len(current_chunk)
            })
            
            current_chunk = []
            current_speakers = []
    
    logger.info(f"Created {len(chunks)} chunks from {total_paragraphs} paragraphs")
    return chunks


def generate_embeddings_batch(texts: list, batch_size: int = 100) -> list:
    """
    Generate embeddings in batches
    
    Args:
        texts: List of text strings
        batch_size: Number of texts per API call
    
    Returns:
        List of embedding vectors
    """
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        try:
            response = client.embeddings.create(
                input=batch,
                model="text-embedding-3-small"
            )
            
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)
            
            logger.info(f"Generated embeddings for batch {i//batch_size + 1} ({len(batch)} texts)")
            
        except Exception as e:
            logger.error(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
            # Return None for failed batch
            all_embeddings.extend([None] * len(batch))
    
    return all_embeddings


def save_chunks_to_db(ticker: str, fiscal_year: int, fiscal_quarter: int, 
                      chunks: list, embeddings: list):
    """
    Save chunks with embeddings to database
    
    Args:
        ticker: Company ticker
        fiscal_year: Fiscal year
        fiscal_quarter: Fiscal quarter
        chunks: List of chunk dicts
        embeddings: List of embedding vectors
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding is None:
                logger.warning(f"Skipping chunk {i} - no embedding")
                continue
            
            cursor.execute("""
                INSERT INTO transcript_chunks 
                (ticker, fiscal_year, fiscal_quarter, chunk_index, chunk_text, speaker, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, chunk_index) 
                DO UPDATE SET
                    fiscal_year = EXCLUDED.fiscal_year,
                    fiscal_quarter = EXCLUDED.fiscal_quarter,
                    chunk_text = EXCLUDED.chunk_text,
                    speaker = EXCLUDED.speaker,
                    embedding = EXCLUDED.embedding
            """, (
                ticker,
                fiscal_year,
                fiscal_quarter,
                i,
                chunk['text'],
                chunk['speaker'],
                embedding
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Saved {len(chunks)} chunks for {ticker}")
        
    except Exception as e:
        logger.error(f"Error saving chunks: {e}")


def process_transcript(transcript_data: dict):
    """
    Process a single transcript: chunk and embed
    
    Args:
        transcript_data: Dict with ticker, fiscal info, and paragraphs
    """
    ticker = transcript_data['ticker']
    fiscal_year = transcript_data['fiscal_year']
    fiscal_quarter = transcript_data['fiscal_quarter']
    paragraphs = transcript_data['paragraphs']
    
    logger.info(f"Processing {ticker} Q{fiscal_quarter} {fiscal_year}")
    
    # Smart chunking
    chunks = smart_chunk_transcript(paragraphs, target_chunks=30)
    
    if not chunks:
        logger.warning(f"No chunks created for {ticker}")
        return
    
    # Generate embeddings
    texts = [chunk['text'] for chunk in chunks]
    embeddings = generate_embeddings_batch(texts, batch_size=100)
    
    # Save to database
    save_chunks_to_db(ticker, fiscal_year, fiscal_quarter, chunks, embeddings)


def embed_all_transcripts():
    """Process all fetched transcripts"""
    logger.info("="*80)
    logger.info("Chunking and Embedding Transcripts")
    logger.info("="*80)
    
    # Load transcript data from fetch step
    input_file = Path(__file__).parent / 'transcript_data.json'
    
    if not input_file.exists():
        logger.error(f"❌ File not found: {input_file}")
        logger.error("Run fetch_latest_transcripts.py first!")
        return
    
    with open(input_file, 'r') as f:
        transcripts = json.load(f)
    
    logger.info(f"Found {len(transcripts)} transcripts to process\n")
    
    for i, transcript_data in enumerate(transcripts, 1):
        logger.info(f"[{i}/{len(transcripts)}] {transcript_data['ticker']}")
        process_transcript(transcript_data)
    
    logger.info("\n" + "="*80)
    logger.info("EMBEDDING COMPLETE")
    logger.info("="*80)
    
    # Check final storage
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM transcript_chunks")
        total_chunks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT ticker) FROM transcript_chunks")
        total_companies = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        logger.info(f"📊 Final Stats:")
        logger.info(f"   Total chunks: {total_chunks:,}")
        logger.info(f"   Companies: {total_companies}")
        logger.info(f"   Avg chunks per company: {total_chunks // total_companies if total_companies > 0 else 0}")
        
    except Exception as e:
        logger.error(f"Error checking stats: {e}")


if __name__ == "__main__":
    embed_all_transcripts()