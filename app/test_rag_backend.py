"""
Backend Testing Script - Test RAG components before UI integration
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from src.utils.database import get_db_connection, test_connection
from src.utils.company_loader import CompanyLoader
from src.rag.query_classifier import QueryClassifier
from src.rag.sql_generator import SQLGenerator
from src.rag.vector_searcher import VectorSearcher
from src.rag.response_generator import ResponseGenerator
from src.rag.orchestrator import RAGOrchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_separator(title=""):
    """Print a visual separator"""
    print("\n" + "="*80)
    if title:
        print(f" {title}")
        print("="*80)
    print()

def test_database_connection():
    """Test database connectivity"""
    print_separator("TEST 1: Database Connection")
    
    try:
        if test_connection():
            print("✅ Database connection successful!")
            
            # Test query
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM companies")
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            print(f"✅ Found {count} companies in database")
            return True
        else:
            print("❌ Database connection failed!")
            return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_company_loader():
    """Test company loading"""
    print_separator("TEST 2: Company Loader")
    
    try:
        loader = CompanyLoader()
        
        # Test loading companies as dict
        companies = loader.get_company_dict()
        print(f"✅ Loaded {len(companies)} companies")
        
        # Show sample
        sample = list(companies.items())[:5]
        print("\nSample companies:")
        for ticker, name in sample:
            print(f"  {ticker}: {name}")
        
        # Test loading as string (for LLM context)
        company_list = loader.load_companies()
        lines = company_list.split('\n')
        print(f"\n✅ Company list formatted: {len(lines)} lines")
        print(f"Sample: {lines[0]}")
        
        return True
    except Exception as e:
        print(f"❌ Company loader error: {e}")
        return False

def test_query_classifier():
    """Test query classification"""
    print_separator("TEST 3: Query Classifier")
    
    test_queries = [
        ("What's Apple's revenue?", "QUANTITATIVE"),
        ("What are Microsoft's main risks?", "QUALITATIVE"),
        ("Which profitable companies face AI risks?", "HYBRID"),
    ]
    
    try:
        classifier = QueryClassifier()
        
        for query, expected_type in test_queries:
            print(f"\nQuery: '{query}'")
            result = classifier.classify(query)
            
            print(f"  Type: {result['query_type']}")
            print(f"  Companies: {result.get('mentioned_tickers', [])}")
            print(f"  Expected: {expected_type}")
            
            if result['query_type'] == expected_type:
                print("  ✅ Correct classification")
            else:
                print(f"  ⚠️  Expected {expected_type}, got {result['query_type']}")
        
        return True
    except Exception as e:
        print(f"❌ Query classifier error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sql_generator():
    """Test SQL generation and execution"""
    print_separator("TEST 4: SQL Generator")
    
    test_query = "What is Apple's latest revenue?"
    
    try:
        sql_gen = SQLGenerator()
        
        print(f"Query: '{test_query}'")
        
        # Test SQL generation
        mentioned_companies = [{"name": "Apple Inc", "ticker": "AAPL"}]
        result = sql_gen.query(test_query, mentioned_companies)
        
        if result['success']:
            print(f"\n✅ SQL generated and executed successfully")
            print(f"SQL: {result['sql'][:100]}...")
            print(f"Rows returned: {result['row_count']}")
            
            if result['data']:
                print("\nSample data:")
                print(result['data'][0])
            
            return True
        else:
            print(f"❌ SQL execution failed: {result.get('error')}")
            print(f"SQL: {result.get('sql')}")
            return False
            
    except Exception as e:
        print(f"❌ SQL generator error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_searcher():
    """Test vector search"""
    print_separator("TEST 5: Vector Searcher")
    
    test_query = "What are the main business risks?"
    test_ticker = "AAPL"
    
    try:
        searcher = VectorSearcher()
        
        # Test company-specific search
        print(f"Query: '{test_query}'")
        print(f"Company: {test_ticker}")
        
        chunks = searcher.search_by_company(
            query=test_query,
            ticker=test_ticker,
            top_k=3
        )
        
        if chunks:
            print(f"\n✅ Found {len(chunks)} relevant chunks")
            
            print("\nTop result:")
            print(f"  Company: {chunks[0].get('company_name', 'N/A')}")
            print(f"  Section: {chunks[0]['item_label']}")
            print(f"  Similarity: {chunks[0]['similarity']}")
            print(f"  Text preview: {chunks[0]['chunk_text'][:200]}...")
            
            return True
        else:
            print("❌ No chunks found")
            return False
            
    except Exception as e:
        print(f"❌ Vector searcher error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_response_generator():
    """Test response generation"""
    print_separator("TEST 6: Response Generator")
    
    try:
        generator = ResponseGenerator()
        
        # Test SQL response generation
        print("Testing SQL response generation...")
        test_query = "What's Apple's revenue?"
        test_data = [
            {"ticker": "AAPL", "name": "Apple Inc", "revenue": 394328000000, "fiscal_year": 2022}
        ]
        
        answer = generator.generate_from_sql(
            user_query=test_query,
            sql_data=test_data,
            sql_query="SELECT * FROM income_statement WHERE ticker='AAPL'"
        )
        
        print(f"✅ Generated answer:")
        print(f"{answer[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Response generator error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_orchestrator():
    """Test full RAG pipeline"""
    print_separator("TEST 7: RAG Orchestrator (Full Pipeline)")
    
    test_queries = [
        "What is Apple's revenue?",
        "What are Microsoft's main risk factors?",
        "Tell me about Tesla",  # Should fail gracefully (not in NASDAQ-100)
    ]
    
    try:
        orchestrator = RAGOrchestrator()
        
        for query in test_queries:
            print(f"\n{'─'*60}")
            print(f"Query: '{query}'")
            print('─'*60)
            
            result = orchestrator.query(query)
            
            print(f"\nSuccess: {result['success']}")
            print(f"Type: {result.get('query_type', 'N/A')}")
            print(f"\nAnswer:\n{result['answer']}")
            
            if result['success']:
                print("\n✅ Query processed successfully")
            else:
                print(f"\n⚠️  Query failed (expected for invalid companies)")
                print(f"Error type: {result.get('error_type', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all backend tests"""
    print("\n" + "🚀 "*20)
    print("NASDAQ-100 Stock Screener - Backend Testing")
    print("🚀 "*20 + "\n")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Company Loader", test_company_loader),
        ("Query Classifier", test_query_classifier),
        ("SQL Generator", test_sql_generator),
        ("Vector Searcher", test_vector_searcher),
        ("Response Generator", test_response_generator),
        ("RAG Orchestrator", test_orchestrator),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results[name] = False
    
    # Summary
    print_separator("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{'='*80}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*80}\n")
    
    if passed == total:
        print("🎉 All tests passed! Backend is ready for Streamlit integration.")
        return True
    else:
        print("⚠️  Some tests failed. Please review errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)