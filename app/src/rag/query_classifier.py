"""
Query Classifier - Determines query type and routing strategy
"""
import logging
import json
from typing import Dict
from openai import OpenAI
import os
from dotenv import load_dotenv
from ..utils.company_loader import CompanyLoader
import streamlit as st

load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_API_KEY = ""
if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

class QueryClassifier:
    """Classifies user queries to determine routing strategy"""
    
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Load company list once
        self.company_list = CompanyLoader.load_companies()
    
    def _get_classification_prompt(self) -> str:
        """Build classification prompt with company list"""
        
        return f"""You are a query classifier for a NASDAQ-100 stock screening system.

        AVAILABLE COMPANIES:
        {self.company_list}

        You have access to two types of data:

        1. STRUCTURED DATA (SQL): Financial statements with numerical metrics
        - Income statements, balance sheets, cash flow statements
        - Financial ratios (margins, ROE, P/E, debt ratios)
        - Time series data (3 fiscal years + 4 quarters)

        2. TEXTUAL DATA (Vector Search): 10-K filing sections with qualitative information
        - Business description and strategy
        - Risk factors
        - Management discussion & analysis (MD&A)
        - Legal proceedings
        - Market risk disclosures

        Classify the query into ONE category:

        QUANTITATIVE: Asks for numerical metrics, financial calculations, comparisons
        Examples:
        - "Which companies have revenue over $100B?"
        - "Show me companies with ROE > 15%"
        - "Compare profit margins of Apple and Microsoft"
        - "What's Nvidia's revenue growth?"

        QUALITATIVE: Asks about business strategy, risks, operations, non-numerical info
        Examples:
        - "What are Apple's main risk factors?"
        - "Describe Microsoft's business model"
        - "What does Google say about AI?"
        - "What legal issues is Tesla facing?"

        HYBRID: Requires BOTH financial data AND qualitative context
        Examples:
        - "Which high-revenue companies face regulatory risks?"
        - "Show profitable companies with strong AI strategy"
        - "Companies with good margins but high legal risk?"

        IMPORTANT - Company Name Extraction:
        - Extract ANY mentioned companies from the query
        - Match company names to tickers using the AVAILABLE COMPANIES list above
        - Handle variations (e.g., "Apple" -> AAPL, "apple" -> AAPL, "Meta" or "Facebook" -> META)
        - Handle typos intelligently (e.g., "Nvida" -> NVDA)
        - If ticker mentioned directly (e.g., "AAPL"), use it

        Respond ONLY with valid JSON:
        {{
            "query_type": "QUANTITATIVE" | "QUALITATIVE" | "HYBRID",
            "reasoning": "Brief explanation",
            "mentioned_companies": [
                {{"name": "Apple Inc", "ticker": "AAPL"}},
                {{"name": "Nvidia Corporation", "ticker": "NVDA"}}
            ],
            "financial_metrics": ["revenue", "profit_margin"],
            "qualitative_aspects": ["risk_factors"]
        }}"""
    
    def classify(self, user_query: str) -> Dict:
        """
        Classify a user query
        
        Args:
            user_query: Natural language query from user
        
        Returns:
            Classification dict with query_type, reasoning, and extracted entities
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._get_classification_prompt()},
                    {"role": "user", "content": user_query}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            classification = json.loads(response.choices[0].message.content)
            
            # Extract tickers for convenience
            classification['mentioned_tickers'] = [
                c['ticker'] for c in classification.get('mentioned_companies', [])
            ]
            
            logger.info(f"Query classified as: {classification['query_type']}")
            logger.debug(f"Classification: {classification}")
            
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying query: {e}")
            # Default to HYBRID if classification fails
            return {
                "query_type": "HYBRID",
                "reasoning": "Classification failed, defaulting to hybrid search",
                "mentioned_companies": [],
                "mentioned_tickers": [],
                "financial_metrics": [],
                "qualitative_aspects": []
            }