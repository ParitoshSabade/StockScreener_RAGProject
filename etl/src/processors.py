"""
Data processing and transformation functions
"""
import logging
import tiktoken
from typing import Dict, List, Tuple
from config.settings import (
    CHUNK_SIZE, CHUNK_OVERLAP, PRIORITY_SECTIONS
)

logger = logging.getLogger(__name__)


def process_simfin_data(raw_data: Dict) -> Tuple[Dict, Dict]:
    """
    Transform SimFin verbose JSON into records for database
    
    Args:
        raw_data: Raw response from SimFin API (verbose format)
    
    Returns:
        Tuple of (company_data, statements)
        - company_data: Dict with company info
        - statements: Dict with keys 'PL', 'BS', 'CF', 'DERIVED' containing lists of records
    """
    company_data = {
        "simfin_id": raw_data["id"],
        "ticker": raw_data["ticker"],
        "name": raw_data["name"],
        "currency": raw_data.get("currency", "USD"),
        "isin": raw_data.get("isin")
    }
    
    statements = {}
    for stmt in raw_data.get("statements", []):
        stmt_type = stmt["statement"]  # PL, BS, CF, DERIVED
        data_rows = stmt["data"]  
        
        # Add ticker to each record
        records = []
        for row in data_rows:
            row["ticker"] = company_data["ticker"]  # Add ticker field
            records.append(row)
        
        statements[stmt_type] = records
    
    logger.info(f"Processed SimFin data for {company_data['ticker']}: "
                f"PL={len(statements.get('PL', []))}, "
                f"BS={len(statements.get('BS', []))}, "
                f"CF={len(statements.get('CF', []))}, "
                f"DERIVED={len(statements.get('DERIVED', []))}")
    
    return company_data, statements


def process_10k_sections(document_data: Dict) -> Tuple[List[Dict], List[Dict]]:
    """
    Process 10-K sections: filter priority sections and create chunks
    
    Args:
        document_data: Dict with ticker, fiscal_year, and sections list
    
    Returns:
        Tuple of (priority_sections, chunks_for_embedding)
    """
    ticker = document_data["ticker"]
    fiscal_year = document_data["fiscal_year"]
    
    encoding = tiktoken.encoding_for_model("gpt-4")
    
    priority_sections = []
    chunks_for_embedding = []
    
    for section in document_data.get("sections", []):
        if section["item_label"] not in PRIORITY_SECTIONS:
            continue
        
        section_data = {
            "section_id": section["id"],
            "document_id": section["document_id"],
            "item_label": section["item_label"],
            "item_description": section["item_description"],
            "content": section["content"],
            "content_length": len(section["content"])
        }
        priority_sections.append(section_data)
        
        chunks = _chunk_text(
            text=section["content"],
            section_id=section["id"],
            ticker=ticker,
            fiscal_year=fiscal_year,
            item_label=section["item_label"],
            encoding=encoding
        )
        chunks_for_embedding.extend(chunks)
    
    logger.info(f"Processed 10-K for {ticker}: "
                f"{len(priority_sections)} sections, {len(chunks_for_embedding)} chunks")
    
    return priority_sections, chunks_for_embedding


def _chunk_text(text: str, section_id: str, ticker: str, fiscal_year: int, 
                item_label: str, encoding) -> List[Dict]:
    """
    Split text into overlapping chunks based on token count
    
    Args:
        text: Text to chunk
        section_id: Section identifier
        ticker: Company ticker
        fiscal_year: Fiscal year
        item_label: Item label (e.g., "Item 1")
        encoding: tiktoken encoding
    
    Returns:
        List of chunk dictionaries
    """
    tokens = encoding.encode(text)
    chunks = []
    
    start = 0
    chunk_index = 0
    
    while start < len(tokens):
        end = start + CHUNK_SIZE
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        
        chunks.append({
            "section_id": section_id,
            "chunk_index": chunk_index,
            "chunk_text": chunk_text,
            "ticker": ticker,
            "fiscal_year": fiscal_year,
            "item_label": item_label
        })
        
        chunk_index += 1
        start = end - CHUNK_OVERLAP  # Overlap for context
    
    return chunks