"""
NASDAQ-100 Stock Screener - Streamlit UI
"""
import streamlit as st
import sys
from pathlib import Path
import logging
from datetime import datetime
import uuid
from streamlit_cookies_manager import EncryptedCookieManager

sys.path.insert(0, str(Path(__file__).parent))

from src.rag.orchestrator import RAGOrchestrator
from src.auth.user_session import UserSession
from src.auth.rate_limiter import RateLimiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="NASDAQ-100 Stock Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

cookies = EncryptedCookieManager(
    prefix="nasdaq_screener_",
    password="RandomJoker123"  
)

if not cookies.ready():
    st.stop()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .query-type-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.5rem 0;
    }
    .quantitative {
        background-color: #e3f2fd;
        color: #1976d2;
    }
    .qualitative {
        background-color: #f3e5f5;
        color: #7b1fa2;
    }
    .hybrid {
        background-color: #fff3e0;
        color: #f57c00;
    }
    .source-box {
        background-color: #f5f5f5;
        border-left: 3px solid #1f77b4;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        color: #000000;
    }
    .error-box {
        background-color: #ffebee;
        border-left: 3px solid #d32f2f;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
        color: #000000;
    }
    .success-box {
        background-color: #e8f5e9;
        border-left: 3px solid #388e3c;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
        color: #000000;
    }
    .stTextInput > div > div > input {
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'session_id' not in cookies:
        # First time user - create new session ID
        session_id = str(uuid.uuid4())
        cookies['session_id'] = session_id
        cookies.save()
        logger.info(f"Created new persistent session: {session_id}")
    else:
        session_id = cookies['session_id']
        logger.info(f"Retrieved existing session: {session_id}")
    
    # Store in session state for easy access
    st.session_state.session_id = session_id
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = RAGOrchestrator()
    
    if 'queries_today' not in st.session_state:
        usage = RateLimiter.get_usage_stats(session_id)
        st.session_state.queries_today = usage['queries_today']


def get_client_ip():
    """Get client IP address (for rate limiting)"""
    # In production with proper deployment, use real IP
    # For now, use a placeholder
    return "127.0.0.1"

def display_header():
    """Display app header"""
    st.markdown('<h1 class="main-header">📊 NASDAQ-100 Stock Screener</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ask questions about NASDAQ-100 companies using natural language</p>', unsafe_allow_html=True)

def display_sidebar():
    """Display sidebar with info and stats"""
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This AI-powered screener helps you analyze NASDAQ-100 companies using:
        - 📈 **Financial data** (income statements, balance sheets, ratios)
        - 📄 **10-K filings** (business info, risks, strategy)
        - 📄 **Earnings Call Transcripts (Q&A with management)**
        """)
        
        st.divider()
        
        # Usage stats
        st.header("📊 Usage")
        queries_used = st.session_state.queries_today
        queries_left = max(0, 30 - queries_used)
        
        st.metric("Queries Today", f"{queries_used} / 30")
        st.progress(queries_used / 30)
        
        if queries_left <= 5:
            st.warning(f"⚠️ Only {queries_left} queries left today!")
        
        st.divider()
        
        # Query history
        if st.session_state.query_history:
            st.header("📝 Recent Queries")
            for i, item in enumerate(reversed(st.session_state.query_history[-5:]), 1):
                with st.expander(f"{i}. {item['query'][:40]}..."):
                    st.write(f"**Type:** {item['type']}")
                    st.write(f"**Time:** {item['timestamp']}")

def display_query_result(result: dict, query: str):
    """Display query result with formatting"""
    
    # Query type badge
    query_type = result.get('query_type', 'UNKNOWN')
    badge_class = query_type.lower()
    st.markdown(
        f'<div class="query-type-badge {badge_class}">{query_type}</div>',
        unsafe_allow_html=True
    )
    
    # Success or error
    if result['success']:
        st.markdown(f'<div class="success-box">✅ <strong>Answer:</strong></div>', unsafe_allow_html=True)
        st.markdown(result['answer'])
        
        # Show sources for qualitative queries
        if query_type == 'QUALITATIVE' and 'sources' in result:
            with st.expander("📚 Sources"):
                for i, source in enumerate(result['sources'], 1):
                    st.markdown(f"""
                    <div class="source-box">
                        <strong>Source {i}:</strong> {source['company']} ({source['ticker']}) - {source['section']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Show SQL for quantitative queries
        if query_type in ['QUANTITATIVE', 'HYBRID'] and 'sql' in result and result['sql']:
            with st.expander("🔍 SQL Query"):
                st.code(result['sql'], language='sql')
        
        # Show metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            if 'row_count' in result:
                st.metric("Data Rows", result['row_count'])
        with col2:
            if 'chunk_count' in result:
                st.metric("Documents", result['chunk_count'])
        with col3:
            st.metric("Query Type", query_type)
    
    else:
        # Error
        st.markdown(
            f'<div class="error-box">❌ <strong>Error:</strong> {result["answer"]}</div>',
            unsafe_allow_html=True
        )
        
        if 'error_type' in result:
            st.caption(f"Error type: {result['error_type']}")

def process_query(query: str):
    """Process user query"""
    
    # Rate limiting
    session_id = st.session_state.session_id
    ip_address = get_client_ip()
    
    rate_check = RateLimiter.check_and_increment(session_id, ip_address)
    
    if not rate_check['allowed']:
        if rate_check['limit_type'] == 'session':
            st.error("🎯 **You've reached your daily limit of 30 queries!**\n\n"
                    "Your quota resets tomorrow. Thanks for using the screener!")
        elif rate_check['limit_type'] == 'ip':
            st.error("⚠️ **Daily query limit reached for this network.**\n\n"
                    "This typically happens when multiple users share the same connection. "
                    "Please try again tomorrow.")
        return
    
    # Update counter
    st.session_state.queries_today = rate_check['session_count']
    
    # Process query
    with st.spinner("🔍 Analyzing your query..."):
        try:
            result = st.session_state.orchestrator.query(query)
            
            # Add to history
            st.session_state.query_history.append({
                'query': query,
                'type': result.get('query_type', 'UNKNOWN'),
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'success': result['success']
            })
            
            # Display result
            display_query_result(result, query)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            st.error(f"An unexpected error occurred: {str(e)}\n\nPlease try again or rephrase your question.")

def main():
    """Main app function"""
    
    # Initialize
    init_session_state()
    
    # Display UI
    display_header()
    display_sidebar()
    
    # Example queries
    with st.expander("💡 Example Queries", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Financial Queries:**")
            if st.button("What's Apple's revenue?", key="ex1"):
                st.session_state.auto_query = "What's Apple's revenue?"
                st.rerun()
            if st.button("Companies with ROE > 20%", key="ex2"):
                st.session_state.auto_query = "Which companies have return on equity greater than 20%?"
                st.rerun()
            if st.button("Compare AAPL vs MSFT margins", key="ex3"):
                st.session_state.auto_query = "Compare profit margins of Apple and Microsoft"
                st.rerun()
        
        with col2:
            st.markdown("**Business Queries:**")
            if st.button("Microsoft's risk factors", key="ex4"):
                st.session_state.auto_query = "What are Microsoft's main risk factors?"
                st.rerun()
            if st.button("Companies investing in AI", key="ex5"):
                st.session_state.auto_query = "Which companies are investing heavily in AI?"
                st.rerun()
            if st.button("Tesla's business model", key="ex6"):
                st.session_state.auto_query = "Describe Tesla's business model"
                st.rerun()

    # Check if we need to auto-execute a query
    auto_execute = 'auto_query' in st.session_state

    # Query input with form (enables Enter key submission)
    with st.form(key="query_form", clear_on_submit=False):
        # Pre-fill with auto_query if it exists
        default_query = st.session_state.get('auto_query', '')
        
        query = st.text_input(
            "Ask a question:",
            placeholder="e.g., What's Apple's revenue? or Which companies have high profit margins?",
            value=default_query,
            key="query_input"
        )
        
        # Submit button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            submit = st.form_submit_button("🔍 Search", type="primary", use_container_width=True)

    # Clear auto_query from session state after use
    if 'auto_query' in st.session_state:
        del st.session_state.auto_query

    # Process query (triggered by Enter key, button click, or auto-execute)
    if (submit or auto_execute) and query:
        process_query(query)
    elif submit and not query:
        st.warning("⚠️ Please enter a question!")
        
    # Footer
    st.divider()
    st.caption("💡 Tip: You can ask about financial metrics, business strategy, risks, and more!")
    st.caption("📊 Data covers 94 NASDAQ-100 companies with latest financial statements, 10-K filings and Earnings call transcripts.")
    st.caption("📊 Covers data from 2022 to Nov 2025")
if __name__ == "__main__":
    main()