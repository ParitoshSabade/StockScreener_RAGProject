import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# API Configuration
SIMFIN_API_KEY = os.getenv("SIMFIN_API_KEY")
SECBLAST_TEST_API_KEY = os.getenv("SECBLAST_TEST_API_KEY")  # NEW
SECBLAST_API_KEY_1 = os.getenv("SECBLAST_API_KEY_1")
SECBLAST_API_KEY_2 = os.getenv("SECBLAST_API_KEY_2")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SIMFIN_BASE_URL = "https://backend.simfin.com/api/v3"
SECBLAST_BASE_URL = "https://api.secblast.com/v1"

# Rate Limits
SIMFIN_RATE_LIMIT = float(os.getenv("SIMFIN_RATE_LIMIT", 2))  # req/sec
SECBLAST_DAILY_LIMIT_PER_KEY = int(os.getenv("SECBLAST_DAILY_LIMIT_PER_KEY", 95))

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "sslmode": os.getenv("DB_SSLMODE", "require")
}

# Processing Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 600))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", 100))

# 10-K Priority Sections
PRIORITY_SECTIONS = {
    "Item 1",   # Business
    "Item 1A",  # Risk Factors
    "Item 1B",  # Unresolved Staff Comments
    "Item 1C",  # Cybersecurity
    "Item 2",   # Properties
    "Item 3",   # Legal Proceedings
    "Item 5",   # Market for Registrant's Securities
    "Item 7",   # MD&A
    "Item 7A",  # Market Risk
}

# Initial Load Configuration
INITIAL_LOAD_START_DATE = "2023-01-01"

KEEP_FISCAL_YEARS = 3
KEEP_QUARTERS = 4