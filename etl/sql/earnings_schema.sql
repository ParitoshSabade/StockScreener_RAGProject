-- Single minimal table for transcript chunks with embeddings
-- No need to store full transcripts separately
CREATE TABLE IF NOT EXISTS transcript_chunks (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    speaker VARCHAR(100),
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure we only have latest transcript per company
    UNIQUE(ticker, chunk_index)
);

-- Indexes for fast searching
CREATE INDEX IF NOT EXISTS idx_transcript_chunks_ticker 
    ON transcript_chunks(ticker);

CREATE INDEX IF NOT EXISTS idx_transcript_chunks_vector 
    ON transcript_chunks USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Optional: Store metadata about latest transcript fetched
CREATE TABLE IF NOT EXISTS transcript_metadata (
    ticker VARCHAR(10) PRIMARY KEY,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL,
    report_date DATE NOT NULL,
    paragraph_count INTEGER,
    last_updated TIMESTAMP DEFAULT NOW()
);