"""
Vector Searcher - Semantic search through 10-K embeddings
"""
import logging
from typing import List, Dict, Optional
import psycopg2
from openai import OpenAI
import os
from dotenv import load_dotenv
from ..utils.database import get_db_connection
import streamlit as st

load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_API_KEY = ""
if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]


class VectorSearcher:
    """Performs semantic search on 10-K embeddings"""
    
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def search(
        self, 
        query: str, 
        tickers: Optional[List[str]] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.58
    ) -> List[Dict]:
        """
        Search for relevant 10-K chunks
        
        Args:
            query: User's search query
            tickers: Optional list of tickers to filter by
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)
        
        Returns:
            List of relevant chunks with metadata
        """
        try:
            # Generate query embedding
            logger.info(f"Generating embedding for query: {query[:50]}...")
            response = self.client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            query_embedding = response.data[0].embedding
            
            # Search database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Build params in correct order:
            # 1. embedding (for SELECT similarity calculation)
            # 2. tickers (for WHERE clause - optional)
            # 3. embedding (for ORDER BY)
            # 4. top_k (for LIMIT)
            
            ticker_filter = ""
            params = [query_embedding]
            
            if tickers:
                ticker_filter = "AND e.ticker = ANY(%s)"
                params.append(tickers)
            
            params.append(query_embedding)
            params.append(top_k)
            
            search_query = f"""
                SELECT 
                    e.ticker,
                    e.fiscal_year,
                    e.item_label,
                    e.chunk_text,
                    e.chunk_index,
                    s.item_description,
                    1 - (e.embedding <=> %s::vector) as similarity,
                    c.name as company_name
                FROM tenk_embeddings e
                JOIN tenk_sections s ON e.section_id = s.section_id
                JOIN companies c ON e.ticker = c.ticker
                WHERE 1=1 {ticker_filter}
                ORDER BY e.embedding <=> %s::vector
                LIMIT %s
            """
            
            cursor.execute(search_query, params)
            results = cursor.fetchall()
            
            # Format results
            chunks = []
            for row in results:
                similarity = row[6]
                if similarity >= similarity_threshold:
                    chunks.append({
                        "ticker": row[0],
                        "company_name": row[7],
                        "fiscal_year": row[1],
                        "item_label": row[2],
                        "chunk_text": row[3],
                        "chunk_index": row[4],
                        "item_description": row[5],
                        "similarity": round(similarity, 4)
                    })
            
            cursor.close()
            conn.close()
            
            logger.info(f"Found {len(chunks)} relevant chunks (threshold: {similarity_threshold})")
            return chunks
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def search_by_company(
        self,
        query: str,
        ticker: str,
        section_filter: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search within a specific company's 10-K
        
        Args:
            query: Search query
            ticker: Company ticker
            section_filter: Optional sections (e.g., ["Item 1A", "Item 7"])
            top_k: Number of results
        
        Returns:
            List of relevant chunks from that company
        """
        try:
            # Generate embedding
            response = self.client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            query_embedding = response.data[0].embedding
            
            # Build query
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Build params in correct order:
            # 1. embedding (for SELECT similarity calculation)
            # 2. ticker (for WHERE clause)
            # 3. section_filter (for WHERE clause - optional)
            # 4. embedding (for ORDER BY)
            # 5. top_k (for LIMIT)
            
            section_filter_sql = ""
            params = [query_embedding, ticker]
            
            if section_filter:
                section_filter_sql = "AND e.item_label = ANY(%s)"
                params.append(section_filter)
            
            params.append(query_embedding)
            params.append(top_k)
            
            search_query = f"""
                SELECT 
                    e.item_label,
                    e.chunk_text,
                    s.item_description,
                    1 - (e.embedding <=> %s::vector) as similarity,
                    c.name as company_name
                FROM tenk_embeddings e
                JOIN tenk_sections s ON e.section_id = s.section_id
                JOIN companies c ON e.ticker = c.ticker
                WHERE e.ticker = %s {section_filter_sql}
                ORDER BY e.embedding <=> %s::vector
                LIMIT %s
            """
            
            cursor.execute(search_query, params)
            results = cursor.fetchall()
            
            chunks = []
            for row in results:
                chunks.append({
                    "ticker": ticker,
                    "company_name": row[4],
                    "item_label": row[0],
                    "chunk_text": row[1],
                    "item_description": row[2],
                    "similarity": round(row[3], 4)
                })
            
            cursor.close()
            conn.close()
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error searching company {ticker}: {e}")
            return []
        
    def search_transcripts(
        self,
        query: str,
        tickers: Optional[List[str]] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.58
    ) -> List[Dict]:
        """
        Search earning call transcripts
        
        Args:
            query: Search query
            tickers: Optional list of tickers
            top_k: Number of results
            similarity_threshold: Minimum similarity
        
        Returns:
            List of relevant transcript chunks
        """
        try:
            # Generate embedding
            logger.info(f"Searching transcripts for: {query[:50]}...")
            response = self.client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            query_embedding = response.data[0].embedding
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Build query
            ticker_filter = ""
            params = [query_embedding]
            
            if tickers:
                ticker_filter = "AND t.ticker = ANY(%s)"
                params.append(tickers)
            
            params.append(query_embedding)
            params.append(top_k)
            
            search_query = f"""
                SELECT 
                    t.ticker,
                    t.fiscal_year,
                    t.fiscal_quarter,
                    t.chunk_text,
                    t.speaker,
                    1 - (t.embedding <=> %s::vector) as similarity,
                    c.name as company_name
                FROM transcript_chunks t
                JOIN companies c ON t.ticker = c.ticker
                WHERE 1=1 {ticker_filter}
                ORDER BY t.embedding <=> %s::vector
                LIMIT %s
            """
            
            cursor.execute(search_query, params)
            results = cursor.fetchall()
            
            chunks = []
            for row in results:
                similarity = row[5]
                if similarity >= similarity_threshold:
                    chunks.append({
                        "ticker": row[0],
                        "company_name": row[6],
                        "fiscal_year": row[1],
                        "fiscal_quarter": row[2],
                        "chunk_text": row[3],
                        "speaker": row[4],
                        "similarity": round(similarity, 4),
                        "source_type": "Earning Call",
                        "source_period": f"Q{row[2]} {row[1]}"
                    })
            
            cursor.close()
            conn.close()
            
            logger.info(f"Found {len(chunks)} relevant transcript chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error searching transcripts: {e}")
            return []
    
    def search_transcripts_by_company(
        self,
        query: str,
        ticker: str,
        top_k: int = 5,
        similarity_threshold: float = 0.58
    ) -> List[Dict]:
        """
        Search within a specific company's earning call transcripts
        
        Args:
            query: Search query
            ticker: Company ticker
            top_k: Number of results
            similarity_threshold: Minimum similarity (0.5 for conversational)
        
        Returns:
            List of relevant chunks from that company's transcripts
        """
        try:
            # Generate embedding
            logger.info(f"Searching {ticker} transcripts for: {query[:50]}...")
            response = self.client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            query_embedding = response.data[0].embedding
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            search_query = """
                SELECT 
                    t.ticker,
                    t.fiscal_year,
                    t.fiscal_quarter,
                    t.chunk_text,
                    t.speaker,
                    1 - (t.embedding <=> %s::vector) as similarity,
                    c.name as company_name
                FROM transcript_chunks t
                JOIN companies c ON t.ticker = c.ticker
                WHERE t.ticker = %s
                ORDER BY t.embedding <=> %s::vector
                LIMIT %s
            """
            
            params = [query_embedding, ticker, query_embedding, top_k]
            
            cursor.execute(search_query, params)
            results = cursor.fetchall()
            
            chunks = []
            for row in results:
                similarity = row[5]
                if similarity >= similarity_threshold:
                    chunks.append({
                        "ticker": row[0],
                        "company_name": row[6],
                        "fiscal_year": row[1],
                        "fiscal_quarter": row[2],
                        "chunk_text": row[3],
                        "speaker": row[4],
                        "similarity": round(similarity, 4),
                        "source_type": "Earning Call",
                        "source_period": f"Q{row[2]} {row[1]}"
                    })
            
            cursor.close()
            conn.close()
            
            logger.info(f"Found {len(chunks)} relevant transcript chunks for {ticker}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error searching {ticker} transcripts: {e}")
            return []

    def search_all_sources(
        self,
        query: str,
        tickers: Optional[List[str]] = None,
        top_k: int = 10,
        similarity_threshold_10k: float = 0.45,
        similarity_threshold_transcripts: float = 0.55,
        include_10k: bool = True,
        include_transcripts: bool = True
    ) -> List[Dict]:
        """
        Search across both 10-K filings and earning call transcripts
        Uses company-specific search when appropriate
        
        Args:
            query: Search query
            tickers: Optional list of tickers to filter
            top_k: Number of results per source
            similarity_threshold_10k: Minimum similarity for 10-K (0.7)
            similarity_threshold_transcripts: Minimum similarity for transcripts (0.5)
            include_10k: Whether to search 10-K filings
            include_transcripts: Whether to search transcripts
        
        Returns:
            Combined results from both sources
        """
        results = []
        
        # Determine if we're searching a single company
        single_company = len(tickers) == 1 if tickers else False
        
        # Search 10-K filings
        if include_10k:
            if single_company:
                # Company-specific 10-K search
                tenk_results = self.search_by_company(
                    query=query, 
                    ticker=tickers[0], 
                    top_k=top_k
                )
            else:
                # General or multi-company 10-K search
                tenk_results = self.search(
                    query=query, 
                    tickers=tickers, 
                    top_k=top_k, 
                    similarity_threshold=similarity_threshold_10k
                )
            
            for chunk in tenk_results:
                chunk['source_type'] = '10-K Filing'
                if 'source_period' not in chunk:
                    chunk['source_period'] = f"FY {chunk.get('fiscal_year', 'N/A')}"
            results.extend(tenk_results)
        
        # Search transcripts
        if include_transcripts:
            if single_company:
                # Company-specific transcript search
                transcript_results = self.search_transcripts_by_company(
                    query=query,
                    ticker=tickers[0],
                    top_k=top_k,
                    similarity_threshold=similarity_threshold_transcripts
                )
            else:
                # General or multi-company transcript search
                transcript_results = self.search_transcripts(
                    query=query,
                    tickers=tickers,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold_transcripts
                )
            
            results.extend(transcript_results)
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k * 2]
