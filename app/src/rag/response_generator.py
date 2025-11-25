"""
Response Generator - Synthesizes final answers from retrieved data
"""
import logging
from typing import Dict, List
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class ResponseGenerator:
    """Generates natural language responses from retrieved data"""
    
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def generate_from_sql(self, user_query: str, sql_data: List[Dict], sql_query: str) -> str:
        """
        Generate response from SQL query results
        
        Args:
            user_query: Original user query
            sql_data: SQL query results
            sql_query: The SQL query that was executed
        
        Returns:
            Natural language response
        """
        try:
            if not sql_data:
                return "I couldn't find any data matching your query."
            
            # Format SQL results
            data_summary = f"Found {len(sql_data)} results:\n"
            for i, row in enumerate(sql_data[:10], 1):  # Limit to 10 for context
                data_summary += f"{i}. {row}\n"
            
            if len(sql_data) > 10:
                data_summary += f"... and {len(sql_data) - 10} more results"
            
            prompt = f"""Based on the following data from a financial database, answer the user's question clearly and concisely.

            User Question: {user_query}

            Data Retrieved:
            {data_summary}

            Instructions:
            - Answer in natural language
            - Be specific with numbers and company names
            - ALWAYS include the calculated values (growth rates, percentages, averages, etc.)
            - - Ratio/margin values are already in percentage format - add % symbol (e.g., "23.5%", "45.2%")
            - Format large numbers with commas (e.g., $123,456,789)
            - If multiple companies, present as a numbered list or table
            - Highlight the key metric that was calculated
            - Keep it concise but complete
            - Don't mention the SQL query or technical details
            - Do NOT use asterisks, bold, or other markdown syntax

            Example good answer format:
            "Here are the top 5 companies by revenue growth in 2024:
            1. Company A - 45.2% growth ($100B → $145B)
            2. Company B - 32.1% growth ($50B → $66B)
            ..."
            """

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a financial analyst providing clear, accurate answers with specific numbers and calculations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            answer = response.choices[0].message.content
            logger.info("Generated response from SQL data")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating response from SQL: {e}")
            return "I encountered an error generating the response."
    
    def generate_from_vectors(self, user_query: str, chunks: List[Dict]) -> str:
        """
        Generate response from vector search results (10-K + Transcripts)
        
        Args:
            user_query: Original user query
            chunks: Retrieved chunks from 10-K and/or transcripts
        
        Returns:
            Natural language response
        """
        try:
            if not chunks:
                return "I couldn't find relevant information in the 10-K filings or transcripts for your query."
            
            # Format chunks for context (handle both 10-K and transcripts)
            context = ""
            for i, chunk in enumerate(chunks[:5], 1):  # Top 5 chunks
                source_type = chunk.get('source_type', '10-K Filing')
                company = chunk.get('company_name', 'Unknown')
                
                if source_type == 'Earning Call':
                    # Transcript chunk
                    period = f"Q{chunk.get('fiscal_quarter')} {chunk.get('fiscal_year')}"
                    speaker = chunk.get('speaker', 'Speaker')
                    context += f"\n[Source {i}: {company} - {period} Earnings Call - {speaker}]\n"
                else:
                    # 10-K chunk
                    section = chunk.get('item_label', 'Section')
                    context += f"\n[Source {i}: {company} - 10-K {section}]\n"
                
                context += f"{chunk['chunk_text']}\n"
            
            prompt = f"""Based on the following excerpts from 10-K filings and earnings call transcripts, answer the user's question.

            User Question: {user_query}

            Relevant Information:
            {context}

            Instructions:
            - Answer based ONLY on the information provided
            - Cite which company and source (10-K section or earnings call) the information comes from
            - Be specific and factual
            - If information is from an earnings call, you can mention what executives said
            - If information is incomplete, acknowledge it
            - Keep response focused and concise
            - Do NOT use asterisks, bold, or other markdown syntax"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a financial analyst providing accurate answers based on 10-K filings and earnings call transcripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            answer = response.choices[0].message.content
            logger.info("Generated response from vector search")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating response from vectors: {e}")
            return "I encountered an error generating the response."
    
    def generate_hybrid_response(
    self,
    user_query: str,
    sql_data: List[Dict],
    sql_query: str,
    chunks: List[Dict]
) -> str:
        """
        Generate response combining SQL and vector search results
        
        Args:
            user_query: Original user query
            sql_data: SQL query results
            sql_query: The SQL query executed
            chunks: Vector search chunks (10-K + transcripts)  
        
        Returns:
            Natural language response
        """
        try:
            # Format SQL data
            sql_summary = ""
            if sql_data:
                sql_summary = f"SQL Results ({len(sql_data)} rows):\n"
                for i, row in enumerate(sql_data[:5], 1):
                    sql_summary += f"{i}. {row}\n"
            
            # Format vector chunks (handle both 10-K and transcripts) 
            vector_summary = ""
            if chunks:
                vector_summary = f"\nAdditional Context from Filings and Transcripts:\n"
                for i, chunk in enumerate(chunks[:3], 1):
                    source_type = chunk.get('source_type', '10-K Filing')
                    company = chunk.get('company_name', 'Unknown')
                    
                    if source_type == 'Earning Call':
                        period = f"Q{chunk.get('fiscal_quarter')} {chunk.get('fiscal_year')}"
                        speaker = chunk.get('speaker', 'Speaker')
                        vector_summary += f"\n[{company} - {period} Earnings Call - {speaker}]\n"
                    else:
                        section = chunk.get('item_label', 'Section')
                        vector_summary += f"\n[{company} - 10-K {section}]\n"
                    
                    vector_summary += f"{chunk['chunk_text'][:300]}...\n"
            
            prompt = f"""Based on the following quantitative data and qualitative information, provide a comprehensive answer.

                User Question: {user_query}

                {sql_summary}

                {vector_summary}

                Instructions:
                - Combine insights from both the quantitative data and qualitative context
                - Start with the key numbers/companies from SQL results
                - Add strategic/qualitative insights from the filings/transcripts
                - Be specific and cite sources (company names, earnings calls, 10-K sections)
                - Format numbers clearly (use %, commas for large numbers)
                - Keep response focused and well-structured
                - Do NOT use asterisks, bold, or other markdown syntax
                """

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a financial analyst providing comprehensive answers combining quantitative and qualitative analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            answer = response.choices[0].message.content
            logger.info("Generated hybrid response")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating hybrid response: {e}")
            return "I encountered an error generating the response."