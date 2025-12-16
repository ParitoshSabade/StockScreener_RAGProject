# 📊 NASDAQ-100 Stock Screener with RAG

<div align="center">

![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.31.0-red.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-API-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**An AI-powered financial analysis tool that combines structured financial data with unstructured documents using Retrieval-Augmented Generation (RAG)**

[Live Demo](https://stocks-screener-rag.streamlit.app/) • [Report Bug](https://github.com/ParitoshSabade/StockScreener_RAGProject/issues)

</div>

---

## 🌟 Features

### 🤖 Intelligent Query Classification
- Automatically determines if your question requires:
  - **Quantitative Analysis** (SQL queries on financial data)
  - **Qualitative Analysis** (Vector search on documents)
  - **Hybrid Analysis** (Combination of both)

### 📈 Comprehensive Financial Data
- **94 NASDAQ-100 companies** with complete financial statements
- Income statements, balance sheets, cash flow statements
- Pre-calculated financial ratios (ROE, ROA, profit margins, etc.)
- Data coverage: 2022 - November 2025

### 📄 Document Intelligence
- **10-K SEC Filings**: Business descriptions, risk factors, legal proceedings
- **Earnings Call Transcripts**: Q&A with management, strategic insights
- Semantic search across 3,818+ document chunks

### 💬 Natural Language Interface
Ask questions naturally:
- "What's Apple's revenue growth over the past 3 years?"
- "Which companies have ROE greater than 20%?"
- "What are Microsoft's main risk factors?"
- "Compare profit margins of Apple and Microsoft"

### ⚡ Advanced Features
- **Hybrid Search**: Combines quantitative metrics with qualitative insights
- **Smart Company Detection**: Automatically identifies mentioned companies
- **Rate Limiting**: 30 queries per day per user
- **Persistent Sessions**: Cookie-based session management
- **SQL Generation**: Automatic conversion of natural language to SQL

---

## 🏗️ Architecture
```
┌─────────────────┐
│  User Query     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Query Classifier       │
│  (GPT-4o-mini)          │
│  - Detects query type   │
│  - Extracts companies   │
└────────┬────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────┐   ┌──────┐
│ SQL │   │Vector│
│Query│   │Search│
└──┬──┘   └───┬──┘
   │          │
   ▼          ▼
┌──────────────────┐
│  Response Gen    │
│  (GPT-4o-mini)   │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│  Final Answer   │
└─────────────────┘
```

### RAG Pipeline Components

1. **Query Classifier**: Determines query type and extracts company mentions
2. **SQL Generator**: Converts natural language to PostgreSQL queries
3. **Vector Searcher**: Semantic search using OpenAI embeddings (text-embedding-3-small)
4. **Response Generator**: Synthesizes final answer from retrieved data

---

## 🛠️ Tech Stack

### Backend
- **Python 3.11+**: Core programming language
- **PostgreSQL**: Structured financial data storage
- **Supabase**: PostgreSQL hosting with pgvector extension
- **OpenAI API**: 
  - GPT-4o-mini for query classification and response generation
  - text-embedding-3-small for document embeddings

### Frontend
- **Streamlit**: Interactive web interface
- **Streamlit Cookies Manager**: Persistent session management

### Data Pipeline (ETL)
- **SimFin API**: Financial statements data
- **DefeatBeta API**: Earnings call transcripts
- **SEC EDGAR**: 10-K filings
- **LangChain**: Document processing and chunking

### Libraries
```
openai==1.12.0
streamlit==1.31.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
streamlit-cookies-manager==0.2.0
pandas==2.2.0
numpy==1.26.3
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+ with pgvector extension
- OpenAI API key
- Supabase account (or PostgreSQL instance)

### Installation

1. **Clone the repository**
```bash
   git clone https://github.com/ParitoshSabade/StockScreener_RAGProject.git
   cd StockScreener_RAGProject
```

2. **Create virtual environment**
```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
   pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
   cp .env.example .env
   # Edit .env with your credentials
```

5. **Configure `.env` file**
```bash
   # OpenAI API
   OPENAI_API_KEY=sk-proj-your-key-here

   # Database
   DB_HOST=your-supabase-host
   DB_PORT=6543  # Use 6543 for connection pooler, 5432 for direct
   DB_USER=postgres.your-project-ref
   DB_NAME=postgres
   DB_PASSWORD=your-password
   DB_SSLMODE=require
```

6. **Run the application**
```bash
   streamlit run app/streamlit_app.py
```

7. **Access the app**
```
   Open http://localhost:8501 in your browser
```

---

## 📊 Data Pipeline

### Initial Setup

1. **Load financial data**
```bash
   cd etl
   python load_financial_data.py
```

2. **Fetch and embed 10-K filings**
```bash
   python fetch_10k_filings.py
   python embed_10k_sections.py
```

3. **Fetch and embed earnings transcripts**
```bash
   python fetch_latest_transcripts.py
   python embed_transcripts.py
```

### Database Schema
```sql
-- Financial statements
companies, income_statement, balance_sheet, cash_flow, derived_ratios

-- Documents
tenk_sections, tenk_embeddings, transcript_chunks, transcript_metadata

-- User management
user_sessions, rate_limits
```

---

## 🎯 Usage Examples

### Quantitative Queries (SQL-based)
```
❓ "What's Apple's revenue in 2024?"
❓ "Show me the top 5 companies by profit margin"
❓ "Which companies have debt-to-equity ratio greater than 1?"
❓ "Compare revenue growth of Apple and Microsoft"
```

### Qualitative Queries (Document-based)
```
❓ "What are Tesla's main risk factors?"
❓ "Describe Microsoft's AI strategy"
❓ "What legal proceedings does Apple face?"
❓ "What did Nvidia's CEO say about AI demand in the latest earnings call?"
```

### Hybrid Queries (SQL + Documents)
```
❓ "How much did Nvidia grow? What are the main reasons?"
❓ "Which companies have the highest margins and what are their competitive advantages?"
❓ "Show me companies with strong financials and innovative products"
```

---

## 📁 Project Structure
```
StockScreener_RAGProject/
├── app/
│   ├── streamlit_app.py          # Main Streamlit application
│   └── src/
│       ├── auth/                  # Authentication & rate limiting
│       │   ├── user_session.py
│       │   └── rate_limiter.py
│       ├── rag/                   # RAG pipeline components
│       │   ├── orchestrator.py    # Main pipeline coordinator
│       │   ├── query_classifier.py
│       │   ├── sql_generator.py
│       │   ├── vector_searcher.py
│       │   └── response_generator.py
│       └── utils/                 # Utilities
│           ├── database.py
│           └── company_loader.py
├── etl/                           # Data pipeline
│   ├── load_financial_data.py
│   ├── fetch_10k_filings.py
│   ├── embed_10k_sections.py
│   ├── fetch_latest_transcripts.py
│   └── embed_transcripts.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Configuration

### Rate Limiting
```python
# Default: 30 queries per day per session
MAX_QUERIES_PER_DAY = 30
```

### Vector Search Thresholds
```python
# 10-K filings: 0.7 (company-specific), 0.5 (discovery)
# Transcripts: 0.5 (company-specific), 0.35 (discovery)
```

### SQL Generation
```python
# Model: gpt-4o-mini
# Temperature: 0.1
# Always uses fiscal_period = 'FY' for annual data
# balance_sheet and derived_ratios use latest quarter
```

### Response Generation
```python
# Model: gpt-4o-mini
# Temperature: 0.3
# Max tokens: 600 (qualitative), 800 (hybrid)
```

---

## 🌐 Deployment

### Streamlit Community Cloud (Free)

1. **Push to GitHub**
```bash
   git push origin master
```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Set main file: `app/streamlit_app.py`

3. **Configure Secrets**
   - Go to App Settings → Secrets
   - Add your environment variables in TOML format:
```toml
   OPENAI_API_KEY = "your-key"
   DB_HOST = "your-host"
   DB_PORT = "6543"
   DB_USER = "postgres.project-ref"
   DB_NAME = "postgres"
   DB_PASSWORD = "your-password"
   DB_SSLMODE = "require"
```

4. **Access your app**
```
   https://your-app.streamlit.app
```

---

## 📈 Performance

- **Database**: 142 MB / 500 MB used (358 MB available)
- **Documents**: 3,818 transcript chunks + 10-K embeddings
- **Response Time**: 2-5 seconds average
- **Concurrent Users**: Scales with Streamlit Community Cloud limits

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **SimFin** for financial data API
- **DefeatBeta** for earnings call transcripts
- **SEC EDGAR** for 10-K filings
- **OpenAI** for GPT-4 and embeddings
- **Supabase** for PostgreSQL hosting
- **Streamlit** for the amazing web framework

---

## 📧 Contact

**Paritosh Sabade** - [@ParitoshSabade](https://github.com/ParitoshSabade)

Project Link: [https://github.com/ParitoshSabade/StockScreener_RAGProject](https://github.com/ParitoshSabade/StockScreener_RAGProject)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ by Paritosh Sabade

</div>
