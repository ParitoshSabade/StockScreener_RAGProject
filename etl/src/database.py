"""
Database operations for storing financial data and 10-K documents
"""
import logging
import psycopg2
from psycopg2.extras import execute_values
from typing import Dict, List
from openai import OpenAI
from config.settings import DB_CONFIG, OPENAI_API_KEY, EMBEDDING_BATCH_SIZE
from src.column_mapping import map_record
logger = logging.getLogger(__name__)


def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise


def store_simfin_data(conn, company_data: Dict, statements: Dict):
    """
    Store company info and all financial statements
    
    Args:
        conn: Database connection
        company_data: Dict with company information
        statements: Dict with 'PL', 'BS', 'CF', 'DERIVED' statement data
    """
    cursor = conn.cursor()
    ticker = company_data["ticker"]
    
    try:
        # 1. Insert/Update company
        cursor.execute("""
            INSERT INTO companies (simfin_id, ticker, name, currency, isin)
            VALUES (%(simfin_id)s, %(ticker)s, %(name)s, %(currency)s, %(isin)s)
            ON CONFLICT (ticker) 
            DO UPDATE SET 
                name = EXCLUDED.name,
                currency = EXCLUDED.currency,
                isin = EXCLUDED.isin,
                updated_at = NOW()
        """, company_data)
        
        # 2. Insert Income Statement data
        if "PL" in statements:
            mapped_records = [map_record(r, "PL") for r in statements["PL"]]
            _store_income_statements(cursor, mapped_records)
        
        # 3. Insert Balance Sheet data
        if "BS" in statements:
            mapped_records = [map_record(r, "BS") for r in statements["BS"]]
            _store_balance_sheets(cursor, mapped_records)
        
        # 4. Insert Cash Flow data
        if "CF" in statements:
            mapped_records = [map_record(r, "CF") for r in statements["CF"]]
            _store_cash_flows(cursor, mapped_records)
        
        # 5. Insert Derived Ratios data
        if "DERIVED" in statements:
            mapped_records = [map_record(r, "DERIVED") for r in statements["DERIVED"]]
            _store_derived_ratios(cursor, mapped_records)
        
        conn.commit()
        logger.info(f"✓ Stored financial data for {ticker}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing SimFin data for {ticker}: {e}")
        raise

def _store_income_statements(cursor, records: List[Dict]):
    """Store income statement records using dynamic column insertion"""
    if not records:
        return
    
    for record in records:
        # Get all column names and values
        columns = list(record.keys())
        values = [record[col] for col in columns]
        
        # Build the INSERT statement dynamically
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        # Create conflict update clause (update all fields except unique constraints)
        update_fields = [f"{col} = EXCLUDED.{col}" for col in columns 
                        if col not in ['ticker', 'fiscal_period', 'fiscal_year', 'report_date']]
        update_str = ', '.join(update_fields) if update_fields else 'ticker = EXCLUDED.ticker'
        
        query = f"""
            INSERT INTO income_statement ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT (ticker, fiscal_period, fiscal_year, report_date)
            DO UPDATE SET {update_str}
        """
        
        cursor.execute(query, values)


def _store_balance_sheets(cursor, records: List[Dict]):
    """Store balance sheet records using dynamic column insertion"""
    if not records:
        return
    
    for record in records:
        columns = list(record.keys())
        values = [record[col] for col in columns]
        
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        update_fields = [f"{col} = EXCLUDED.{col}" for col in columns 
                        if col not in ['ticker', 'fiscal_period', 'fiscal_year', 'report_date']]
        update_str = ', '.join(update_fields) if update_fields else 'ticker = EXCLUDED.ticker'
        
        query = f"""
            INSERT INTO balance_sheet ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT (ticker, fiscal_period, fiscal_year, report_date)
            DO UPDATE SET {update_str}
        """
        
        cursor.execute(query, values)


def _store_cash_flows(cursor, records: List[Dict]):
    """Store cash flow records using dynamic column insertion"""
    if not records:
        return
    
    for record in records:
        columns = list(record.keys())
        values = [record[col] for col in columns]
        
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        update_fields = [f"{col} = EXCLUDED.{col}" for col in columns 
                        if col not in ['ticker', 'fiscal_period', 'fiscal_year', 'report_date']]
        update_str = ', '.join(update_fields) if update_fields else 'ticker = EXCLUDED.ticker'
        
        query = f"""
            INSERT INTO cash_flow ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT (ticker, fiscal_period, fiscal_year, report_date)
            DO UPDATE SET {update_str}
        """
        
        cursor.execute(query, values)



def _store_derived_ratios(cursor, records: List[Dict]):
    """Store derived ratios records using dynamic column insertion"""
    if not records:
        return
    
    for record in records:
        columns = list(record.keys())
        values = [record[col] for col in columns]
        
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        update_fields = [f"{col} = EXCLUDED.{col}" for col in columns 
                        if col not in ['ticker', 'fiscal_period', 'fiscal_year', 'report_date']]
        update_str = ', '.join(update_fields) if update_fields else 'ticker = EXCLUDED.ticker'
        
        query = f"""
            INSERT INTO derived_ratios ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT (ticker, fiscal_period, fiscal_year, report_date)
            DO UPDATE SET {update_str}
        """
        
        cursor.execute(query, values)


def store_10k_data(conn, document_data: Dict, sections: List[Dict], chunks: List[Dict]):
    """
    Store 10-K document, sections, and generate embeddings
    
    Args:
        conn: Database connection
        document_data: Document metadata
        sections: List of priority section data
        chunks: List of text chunks to embed
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    cursor = conn.cursor()
    ticker = document_data["ticker"]
    
    try:
        # 1. Insert/Update document metadata
        cursor.execute("""
            INSERT INTO tenk_documents (
                ticker, accession_number, document_id, form_type,
                fiscal_year, file_name, document_size
            ) VALUES (%s, %s, %s, '10-K', %s, %s, %s)
            ON CONFLICT (ticker) 
            DO UPDATE SET 
                accession_number = EXCLUDED.accession_number,
                document_id = EXCLUDED.document_id,
                fiscal_year = EXCLUDED.fiscal_year,
                file_name = EXCLUDED.file_name,
                document_size = EXCLUDED.document_size,
                updated_at = NOW()
        """, (
            ticker,
            document_data["accession_number"],
            document_data["document_id"],
            document_data["fiscal_year"],
            document_data["file_name"],
            document_data["size"]
        ))
        
        # Get the actual document_id that's stored (in case of conflict)
        cursor.execute("""
            SELECT document_id FROM tenk_documents WHERE ticker = %s
        """, (ticker,))
        stored_doc_id = cursor.fetchone()[0]
        
        # 2. Delete old sections and embeddings (CASCADE will handle embeddings)
        cursor.execute("""
            DELETE FROM tenk_sections WHERE document_id = %s
        """, (stored_doc_id,))
        
        # 3. Insert priority sections
        for section in sections:
            cursor.execute("""
                INSERT INTO tenk_sections (
                    document_id, section_id, item_label, 
                    item_description, content, content_length
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                stored_doc_id,
                section["section_id"],
                section["item_label"],
                section["item_description"],
                section["content"],
                section["content_length"]
            ))
        
        # 4. Generate and insert embeddings in batches
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        for i in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
            batch = chunks[i:i + EMBEDDING_BATCH_SIZE]
            texts = [chunk["chunk_text"] for chunk in batch]
            
            # Generate embeddings
            response = client.embeddings.create(
                input=texts,
                model="text-embedding-3-small"
            )
            
            # Insert embeddings
            for chunk, embedding_obj in zip(batch, response.data):
                cursor.execute("""
                    INSERT INTO tenk_embeddings (
                        section_id, chunk_index, chunk_text, embedding,
                        ticker, fiscal_year, item_label
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    chunk["section_id"],
                    chunk["chunk_index"],
                    chunk["chunk_text"],
                    embedding_obj.embedding,
                    chunk["ticker"],
                    chunk["fiscal_year"],
                    chunk["item_label"]
                ))
            
            logger.info(f"  Embedded batch {i//EMBEDDING_BATCH_SIZE + 1}/{(len(chunks)-1)//EMBEDDING_BATCH_SIZE + 1}")
        
        conn.commit()
        logger.info(f"✓ Stored 10-K for {ticker}: {len(sections)} sections, {len(chunks)} chunks")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing 10-K data for {ticker}: {e}")
        raise