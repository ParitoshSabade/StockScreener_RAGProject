"""
RAG Orchestrator - Main pipeline coordinating all RAG components
"""
import logging
from typing import Dict, List
from .query_classifier import QueryClassifier
from .sql_generator import SQLGenerator
from .vector_searcher import VectorSearcher
from .response_generator import ResponseGenerator
from ..utils.company_loader import CompanyLoader

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """Main RAG pipeline orchestrator"""
    
    def __init__(self):
        self.classifier = QueryClassifier()
        self.sql_generator = SQLGenerator()
        self.vector_searcher = VectorSearcher()
        self.response_generator = ResponseGenerator()
        self.company_loader = CompanyLoader()
    
    def query(self, user_query: str) -> Dict:
        """
        Process a user query through the RAG pipeline
        
        Args:
            user_query: Natural language query from user
        
        Returns:
            Dict with answer, query_type, and metadata
        """
        try:
            logger.info(f"Processing query: {user_query}")
            
            # Step 1: Classify query
            classification = self.classifier.classify(user_query)
            query_type = classification['query_type']
            mentioned_companies = classification.get('mentioned_companies', [])
            mentioned_tickers = classification.get('mentioned_tickers', [])
            
            logger.info(f"Query type: {query_type}")
            logger.info(f"Mentioned companies: {mentioned_tickers}")
            
            # Step 2: Validate mentioned companies exist in our database
            validation_result = self._validate_companies(mentioned_tickers)
            if not validation_result['valid']:
                return validation_result['response']
            
            # Step 3: Route based on query type
            if query_type == "QUANTITATIVE":
                return self._handle_quantitative(user_query, mentioned_tickers)
            
            elif query_type == "QUALITATIVE":
                return self._handle_qualitative(user_query, mentioned_tickers)
            
            elif query_type == "HYBRID":
                return self._handle_hybrid(user_query, mentioned_tickers)
            
            else:
                return {
                    "success": False,
                    "answer": "I couldn't determine how to process your query. Could you try rephrasing?",
                    "query_type": "UNKNOWN"
                }
        
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}", exc_info=True)
            return self._handle_system_error(e)
    
    def _normalize_companies(self, tickers: List[str]) -> List[Dict]:
        """
        Convert tickers to company dicts with both ticker and name
        
        Args:
            tickers: List of ticker symbols (e.g., ["NVDA", "AAPL"])
        
        Returns:
            List of dicts with ticker and name (e.g., [{"ticker": "NVDA", "name": "NVIDIA CORP"}])
        """
        company_dicts = []
        
        if not tickers:
            return company_dicts
        
        # Get the company dictionary (ticker -> name mapping)
        all_companies = self.company_loader.get_company_dict()
        
        for ticker in tickers:
            if ticker in all_companies:
                company_dicts.append({
                    'ticker': ticker,
                    'name': all_companies[ticker]
                })
            else:
                # Fallback if company not found (shouldn't happen after validation)
                logger.warning(f"Company info not found for ticker: {ticker}")
                company_dicts.append({
                    'ticker': ticker,
                    'name': ticker  # Use ticker as name fallback
                })
        
        return company_dicts
    def _validate_companies(self, mentioned_tickers: list) -> Dict:
        """
        Validate that mentioned companies exist in our database
        
        Returns:
            Dict with 'valid' (bool) and optional 'response' (error message)
        """
        if not mentioned_tickers:
            return {'valid': True}
        
        # Get all valid tickers from database
        valid_companies = self.company_loader.get_company_dict()
        
        # Check which mentioned tickers are invalid
        invalid_tickers = [t for t in mentioned_tickers if t not in valid_companies]
        
        if invalid_tickers:
            invalid_names = ", ".join(invalid_tickers)
            
            # Suggest some valid companies
            examples = list(valid_companies.keys())[:5]
            examples_str = ", ".join([f"{valid_companies[t]} ({t})" for t in examples])
            
            return {
                'valid': False,
                'response': {
                    "success": False,
                    "answer": f"I don't have data for {invalid_names}. I only cover NASDAQ-100 companies.\n\nYou can ask about companies like: {examples_str}, and more.",
                    "query_type": "VALIDATION_FAILED",
                    "invalid_companies": invalid_tickers
                }
            }
        
        return {'valid': True}
    
    def _handle_quantitative(self, user_query: str, mentioned_tickers: list) -> Dict:
        """Handle quantitative queries (SQL only)"""
        logger.info("Handling QUANTITATIVE query")
        
        try:
            # Convert tickers to company dicts for SQL generator
            company_dicts = self._normalize_companies(mentioned_tickers)
            
            # Generate and execute SQL
            sql_result = self.sql_generator.query(user_query, company_dicts)
            
            if not sql_result['success']:
                return {
                    "success": False,
                    "answer": f"I had trouble retrieving the financial data. Please try rephrasing your question or asking about different metrics.\n\nError: {sql_result.get('error', 'Unknown error')}",
                    "query_type": "QUANTITATIVE",
                    "sql": sql_result.get('sql'),
                    "error_type": "SQL_EXECUTION_FAILED"
                }
            
            # Check if we got any results
            if not sql_result['data'] or sql_result['row_count'] == 0:
                return {
                    "success": False,
                    "answer": "I couldn't find any matching financial data for your query. Try asking about revenue, profit margins, total assets, or other financial metrics.",
                    "query_type": "QUANTITATIVE",
                    "sql": sql_result['sql'],
                    "error_type": "NO_DATA_FOUND"
                }
            
            # Generate natural language response
            answer = self.response_generator.generate_from_sql(
                user_query=user_query,
                sql_data=sql_result['data'],
                sql_query=sql_result['sql']
            )
            
            return {
                "success": True,
                "answer": answer,
                "query_type": "QUANTITATIVE",
                "sql": sql_result['sql'],
                "data": sql_result['data'],
                "row_count": sql_result['row_count']
            }
        
        except Exception as e:
            logger.error(f"Error in quantitative handling: {e}", exc_info=True)
            return {
                "success": False,
                "answer": "I encountered an error processing your financial data query. Please try rephrasing or simplifying your question.",
                "query_type": "QUANTITATIVE",
                "error_type": "PROCESSING_ERROR"
            }
    
    def _handle_qualitative(self, user_query: str, mentioned_tickers: list) -> Dict:
        """Handle qualitative queries (Vector search only)"""
        logger.info("Handling QUALITATIVE query")
        
        try:
            # Vector search with company filtering
            chunks = self._smart_vector_search(user_query, mentioned_tickers)
            
            if not chunks:
                # Different message based on whether company was specified
                if mentioned_tickers:
                    company_names = ", ".join(mentioned_tickers)
                    message = f"I couldn't find relevant information in the 10-K filings or transcripts for {company_names}. The company might not have filed a 10-K yet, or the information might not be in the sections I searched.\n\nTry asking about risks, business strategy, or legal proceedings."
                else:
                    message = "I couldn't find relevant information in the 10-K filings or transcripts. Try asking about specific topics like:\n- Risk factors\n- Business model and strategy\n- Legal proceedings\n- Market risks"
                
                return {
                    "success": False,
                    "answer": message,
                    "query_type": "QUALITATIVE",
                    "error_type": "NO_RELEVANT_INFO"
                }
            
            # Generate natural language response
            answer = self.response_generator.generate_from_vectors(
                user_query=user_query,
                chunks=chunks
            )
            
            # Build sources list (handle both 10-K and transcripts)
            sources = []
            for c in chunks[:5]:
                source = {
                    "company": c['company_name'],
                    "ticker": c['ticker'],
                    "source_type": c.get('source_type', '10-K Filing')
                }
                
                # Add section info based on source type
                if c.get('source_type') == 'Earning Call':
                    source['section'] = f"Q{c.get('fiscal_quarter')} {c.get('fiscal_year')} Earnings Call"
                    if c.get('speaker'):
                        source['speaker'] = c.get('speaker')
                else:
                    # 10-K filing
                    source['section'] = c.get('item_label', 'N/A')
                
                sources.append(source)
            
            return {
                "success": True,
                "answer": answer,
                "query_type": "QUALITATIVE",
                "sources": sources,
                "chunk_count": len(chunks)
            }
        
        except Exception as e:
            logger.error(f"Error in qualitative handling: {e}", exc_info=True)
            return {
                "success": False,
                "answer": "I encountered an error searching the filings and transcripts. Please try rephrasing your question.",
                "query_type": "QUALITATIVE",
                "error_type": "PROCESSING_ERROR"
            }
        
    def _handle_hybrid(self, user_query: str, mentioned_tickers: list) -> Dict:
        """Handle hybrid queries (SQL + Vector)"""
        logger.info("Handling HYBRID query")
        
        try:
            # Convert tickers to company dicts for SQL generator
            company_dicts = self._normalize_companies(mentioned_tickers)
            
            # SQL component
            sql_result = self.sql_generator.query(user_query, company_dicts)
            
            # Vector component
            chunks = self._smart_vector_search(user_query, mentioned_tickers)
            
            # Check if we have any results
            if not sql_result['success'] and not chunks:
                return {
                    "success": False,
                    "answer": "I couldn't find relevant information for your query. Try being more specific about the companies or metrics you're interested in.",
                    "query_type": "HYBRID",
                    "error_type": "NO_DATA"
                }
            
            # Generate combined response
            answer = self.response_generator.generate_hybrid_response(
                user_query=user_query,
                sql_data=sql_result.get('data', []),
                sql_query=sql_result.get('sql'),
                chunks=chunks
            )
            
            # Build sources list (handle both 10-K and transcripts)
            sources = []
            for c in chunks[:5]:
                source = {
                    "company": c['company_name'],
                    "ticker": c['ticker'],
                    "source_type": c.get('source_type', '10-K Filing')
                }
                
                # Add section info based on source type
                if c.get('source_type') == 'Earning Call':
                    source['section'] = f"Q{c.get('fiscal_quarter')} {c.get('fiscal_year')} Earnings Call"
                    if c.get('speaker'):
                        source['speaker'] = c.get('speaker')
                else:
                    # 10-K filing
                    source['section'] = c.get('item_label', 'N/A')
                
                sources.append(source)
            
            return {
                "success": True,
                "answer": answer,
                "query_type": "HYBRID",
                "sql": sql_result.get('sql'),
                "sql_data": sql_result.get('data', []),
                "sources": sources,
                "chunk_count": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error generating hybrid response: {e}", exc_info=True)
            return {
                "success": False,
                "answer": "I encountered an error processing your query. Please try rephrasing.",
                "query_type": "HYBRID",
                "error_type": "PROCESSING_ERROR"
            }
    
    def _smart_vector_search(self, query: str, mentioned_tickers: list) -> list:
        """
        Smart vector search across 10-K and transcripts
        
        Strategy:
        - If 1 company mentioned: Search only that company
        - If multiple companies: Search only those companies
        - If no companies: Search all companies (discovery)
        - Search BOTH 10-K and transcripts for richer results
        """
        
        try:
            if len(mentioned_tickers) == 1:
                # Single company - search both sources
                logger.info(f"Searching single company: {mentioned_tickers[0]}")
                chunks = self.vector_searcher.search_all_sources(
                    query=query,
                    tickers=mentioned_tickers,
                    top_k=5,
                    include_10k=True,
                    include_transcripts=True
                )
            
            elif len(mentioned_tickers) > 1:
                # Multiple companies
                logger.info(f"Searching multiple companies: {mentioned_tickers}")
                chunks = self.vector_searcher.search_all_sources(
                    query=query,
                    tickers=mentioned_tickers,
                    top_k=10,
                    include_10k=True,
                    include_transcripts=True
                )
            
            else:
                # No specific companies - search all
                logger.info("Searching all companies (discovery mode)")
                chunks = self.vector_searcher.search_all_sources(
                    query=query,
                    tickers=None,
                    top_k=10,
                    include_10k=True,
                    include_transcripts=True
                )
            
            return chunks
        
        except Exception as e:
            logger.error(f"Error in vector search: {e}", exc_info=True)
            return []

    def _handle_system_error(self, error: Exception) -> Dict:
        """
        Handle system-level errors with user-friendly messages
        
        This is a safety net for unexpected errors that slip through.
        Most common errors should be caught earlier in the pipeline.
        """
        error_str = str(error).lower()
        
        # OpenAI API Rate Limiting
        if 'rate limit' in error_str or '429' in error_str:
            return {
                "success": False,
                "answer": "The AI service is currently at capacity. Please try again in a few minutes.",
                "error_type": "RATE_LIMIT"
            }
        
        # OpenAI Quota Issues
        if 'quota' in error_str or 'insufficient_quota' in error_str:
            return {
                "success": False,
                "answer": "The AI service quota has been exceeded. Please contact support or try again later.",
                "error_type": "QUOTA_EXCEEDED"
            }
        
        # API Authentication Issues
        if 'api key' in error_str or '401' in error_str or 'authentication' in error_str:
            return {
                "success": False,
                "answer": "There's a configuration issue with the service. Please contact support.",
                "error_type": "API_KEY_ERROR"
            }
        
        # Database Connection Issues
        if 'connection' in error_str or 'database' in error_str or 'psycopg2' in error_str:
            return {
                "success": False,
                "answer": "I'm having trouble connecting to the database. Please try again in a moment.",
                "error_type": "DATABASE_ERROR"
            }
        
        # Network Timeouts
        if 'timeout' in error_str or 'timed out' in error_str:
            return {
                "success": False,
                "answer": "The request timed out. Please try again.",
                "error_type": "TIMEOUT_ERROR"
            }
        
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error in RAG pipeline: {error}", exc_info=True)
        
        return {
            "success": False,
            "answer": "Something unexpected happened. Please try again or rephrase your question. If the problem persists, please contact support.",
            "error_type": "UNEXPECTED_ERROR"
        }