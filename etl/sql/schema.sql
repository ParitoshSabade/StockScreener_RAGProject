-- ============================================================================
-- NASDAQ-100 STOCK SCREENER DATABASE SCHEMA
-- ============================================================================

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- 1. COMPANIES TABLE
-- ============================================================================
CREATE TABLE companies (
    simfin_id INTEGER PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    isin VARCHAR(12),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_companies_ticker ON companies(ticker);

-- ============================================================================
-- 2. INCOME STATEMENT TABLE
-- ============================================================================
CREATE TABLE income_statement (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL REFERENCES companies(ticker) ON DELETE CASCADE,
    fiscal_period VARCHAR(10) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    report_date DATE NOT NULL,
    publish_date DATE,
    restated INTEGER,
    source TEXT,
    ttm INTEGER,
    value_check INTEGER,
    data_model INTEGER,
    revenue BIGINT,
    sales_services_revenue BIGINT,
    financing_revenue BIGINT,
    other_revenue BIGINT,
    cost_of_revenue BIGINT,
    cost_of_goods_services BIGINT,
    cost_of_financing_revenue BIGINT,
    cost_of_other_revenue BIGINT,
    gross_profit BIGINT,
    other_operating_income BIGINT,
    operating_expenses BIGINT,
    selling_general_administrative BIGINT,
    selling_marketing BIGINT,
    general_administrative BIGINT,
    research_development BIGINT,
    depreciation_amortization BIGINT,
    provision_for_doubtful_accounts BIGINT,
    other_operating_expense BIGINT,
    operating_income_loss BIGINT,
    non_operating_income_loss BIGINT,
    interest_expense_net BIGINT,
    interest_expense BIGINT,
    interest_income BIGINT,
    other_investment_income_loss BIGINT,
    foreign_exchange_gain_loss BIGINT,
    income_loss_from_affiliates BIGINT,
    other_non_operating_income_loss BIGINT,
    pretax_income_loss_adjusted BIGINT,
    abnormal_gains_losses BIGINT,
    acquired_in_process_rd BIGINT,
    merger_acquisition_expense BIGINT,
    abnormal_derivatives BIGINT,
    disposal_of_assets BIGINT,
    early_extinguishment_of_debt BIGINT,
    asset_write_down BIGINT,
    impairment_of_goodwill_intangibles BIGINT,
    sale_of_business BIGINT,
    legal_settlement BIGINT,
    restructuring_charges BIGINT,
    sale_of_unrealized_investments BIGINT,
    insurance_settlement BIGINT,
    other_abnormal_items BIGINT,
    pretax_income_loss BIGINT,
    income_tax_expense_benefit_net BIGINT,
    current_income_tax BIGINT,
    deferred_income_tax BIGINT,
    tax_allowance_credit BIGINT,
    income_loss_from_affiliates_net_of_taxes BIGINT,
    income_loss_from_continuing_operations BIGINT,
    net_extraordinary_gains_losses BIGINT,
    discontinued_operations BIGINT,
    xo_accounting_charges_other BIGINT,
    income_loss_including_minority_interest BIGINT,
    minority_interest BIGINT,
    net_income BIGINT,
    preferred_dividends BIGINT,
    other_adjustments BIGINT,
    net_income_available_to_common_shareholders BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, fiscal_period, fiscal_year, report_date)
);

CREATE INDEX idx_income_ticker ON income_statement(ticker);
CREATE INDEX idx_income_period ON income_statement(fiscal_period, fiscal_year);
CREATE INDEX idx_income_date ON income_statement(report_date DESC);

-- ============================================================================
-- 3. BALANCE SHEET TABLE
-- ============================================================================
CREATE TABLE balance_sheet (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL REFERENCES companies(ticker) ON DELETE CASCADE,
    fiscal_period VARCHAR(10) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    report_date DATE NOT NULL,
    publish_date DATE,
    restated INTEGER,
    source TEXT,
    ttm INTEGER,
    value_check INTEGER,
    data_model INTEGER,
    cash_cash_equivalents_short_term_investments BIGINT,
    cash_cash_equivalents BIGINT,
    short_term_investments BIGINT,
    accounts_notes_receivable BIGINT,
    accounts_receivable_net BIGINT,
    notes_receivable_net BIGINT,
    unbilled_revenues BIGINT,
    inventories BIGINT,
    raw_materials BIGINT,
    work_in_process BIGINT,
    finished_goods BIGINT,
    other_inventory BIGINT,
    other_short_term_assets BIGINT,
    prepaid_expenses BIGINT,
    derivative_hedging_assets_short_term BIGINT,
    assets_held_for_sale BIGINT,
    deferred_tax_assets_short_term BIGINT,
    income_taxes_receivable BIGINT,
    discontinued_operations_short_term BIGINT,
    miscellaneous_short_term_assets BIGINT,
    total_current_assets BIGINT,
    property_plant_equipment_net BIGINT,
    property_plant_equipment BIGINT,
    accumulated_depreciation BIGINT,
    long_term_investments_receivables BIGINT,
    long_term_investments BIGINT,
    long_term_marketable_securities BIGINT,
    long_term_receivables BIGINT,
    other_long_term_assets BIGINT,
    intangible_assets BIGINT,
    goodwill BIGINT,
    other_intangible_assets BIGINT,
    prepaid_expense BIGINT,
    deferred_tax_assets_long_term BIGINT,
    derivative_hedging_assets_long_term BIGINT,
    prepaid_pension_costs BIGINT,
    discontinued_operations_long_term BIGINT,
    investments_in_affiliates BIGINT,
    miscellaneous_long_term_assets BIGINT,
    total_noncurrent_assets BIGINT,
    total_assets BIGINT,
    payables_accruals BIGINT,
    accounts_payable BIGINT,
    accrued_taxes BIGINT,
    interest_dividends_payable BIGINT,
    other_payables_accruals BIGINT,
    short_term_debt BIGINT,
    short_term_borrowings BIGINT,
    short_term_capital_leases BIGINT,
    current_portion_of_long_term_debt BIGINT,
    other_short_term_liabilities BIGINT,
    deferred_revenue_short_term BIGINT,
    liabilities_from_derivatives_hedging_short_term BIGINT,
    deferred_tax_liabilities_short_term BIGINT,
    liabilities_from_discontinued_operations_short_term BIGINT,
    miscellaneous_short_term_liabilities BIGINT,
    total_current_liabilities BIGINT,
    long_term_debt BIGINT,
    long_term_borrowings BIGINT,
    long_term_capital_leases BIGINT,
    other_long_term_liabilities BIGINT,
    accrued_liabilities BIGINT,
    pension_liabilities BIGINT,
    pensions BIGINT,
    other_post_retirement_benefits BIGINT,
    deferred_compensation BIGINT,
    deferred_revenue_long_term BIGINT,
    deferred_tax_liabilities_long_term BIGINT,
    liabilities_from_derivatives_hedging_long_term BIGINT,
    liabilities_from_discontinued_operations_long_term BIGINT,
    miscellaneous_long_term_liabilities BIGINT,
    total_noncurrent_liabilities BIGINT,
    total_liabilities BIGINT,
    preferred_equity BIGINT,
    share_capital_additional_paid_in_capital BIGINT,
    common_stock BIGINT,
    additional_paid_in_capital BIGINT,
    other_share_capital BIGINT,
    treasury_stock BIGINT,
    retained_earnings BIGINT,
    other_equity BIGINT,
    equity_before_minority_interest BIGINT,
    minority_interest BIGINT,
    total_equity BIGINT,
    total_liabilities_equity BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, fiscal_period, fiscal_year, report_date)
);

CREATE INDEX idx_balance_ticker ON balance_sheet(ticker);
CREATE INDEX idx_balance_period ON balance_sheet(fiscal_period, fiscal_year);
CREATE INDEX idx_balance_date ON balance_sheet(report_date DESC);

-- ============================================================================
-- 4. CASH FLOW TABLE
-- ============================================================================
CREATE TABLE cash_flow (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL REFERENCES companies(ticker) ON DELETE CASCADE,
    fiscal_period VARCHAR(10) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    report_date DATE NOT NULL,
    publish_date DATE,
    restated INTEGER,
    source TEXT,
    ttm INTEGER,
    value_check INTEGER,
    data_model INTEGER,
    net_income_starting_line BIGINT,
    net_income BIGINT,
    net_income_from_discontinued_operations BIGINT,
    other_adjustments BIGINT,
    depreciation_amortization BIGINT,
    non_cash_items BIGINT,
    stock_based_compensation BIGINT,
    deferred_income_taxes BIGINT,
    other_non_cash_adjustments BIGINT,
    change_in_working_capital BIGINT,
    increase_decrease_in_accounts_receivable BIGINT,
    increase_decrease_in_inventories BIGINT,
    increase_decrease_in_accounts_payable BIGINT,
    increase_decrease_in_other BIGINT,
    net_cash_from_discontinued_operations_operating BIGINT,
    cash_from_operating_activities BIGINT,
    change_in_fixed_assets_intangibles BIGINT,
    disposition_of_fixed_assets_intangibles BIGINT,
    disposition_of_fixed_assets BIGINT,
    disposition_of_intangible_assets BIGINT,
    acquisition_of_fixed_assets_intangibles BIGINT,
    purchase_of_fixed_assets BIGINT,
    acquisition_of_intangible_assets BIGINT,
    other_change_in_fixed_assets_intangibles BIGINT,
    net_change_in_long_term_investment BIGINT,
    decrease_in_long_term_investment BIGINT,
    increase_in_long_term_investment BIGINT,
    net_cash_from_acquisitions_divestitures BIGINT,
    net_cash_from_divestitures BIGINT,
    cash_for_acquisition_of_subsidiaries BIGINT,
    cash_for_joint_ventures BIGINT,
    net_cash_from_other_acquisitions BIGINT,
    other_investing_activities BIGINT,
    net_cash_from_discontinued_operations_investing BIGINT,
    cash_from_investing_activities BIGINT,
    dividends_paid BIGINT,
    cash_from_repayment_of_debt BIGINT,
    cash_from_repayment_of_short_term_debt_net BIGINT,
    cash_from_repayment_of_long_term_debt_net BIGINT,
    repayments_of_long_term_debt BIGINT,
    cash_from_long_term_debt BIGINT,
    cash_from_repurchase_of_equity BIGINT,
    increase_in_capital_stock BIGINT,
    decrease_in_capital_stock BIGINT,
    other_financing_activities BIGINT,
    net_cash_from_discontinued_operations_financing BIGINT,
    cash_from_financing_activities BIGINT,
    net_cash_before_disc_operations_and_fx BIGINT,
    change_in_cash_from_disc_operations_and_other BIGINT,
    net_cash_before_fx BIGINT,
    effect_of_foreign_exchange_rates BIGINT,
    net_changes_in_cash BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, fiscal_period, fiscal_year, report_date)
);

CREATE INDEX idx_cashflow_ticker ON cash_flow(ticker);
CREATE INDEX idx_cashflow_period ON cash_flow(fiscal_period, fiscal_year);
CREATE INDEX idx_cashflow_date ON cash_flow(report_date DESC);

-- ============================================================================
-- 5. DERIVED RATIOS TABLE
-- ============================================================================
CREATE TABLE derived_ratios (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL REFERENCES companies(ticker) ON DELETE CASCADE,
    fiscal_period VARCHAR(10) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    report_date DATE NOT NULL,
    ttm INTEGER,
    restated INTEGER,
    data_model INTEGER,
    gross_profit_margin DOUBLE PRECISION,
    operating_margin DOUBLE PRECISION,
    net_profit_margin DOUBLE PRECISION,
    net_profit_margin_adjusted DOUBLE PRECISION,
    return_on_equity DOUBLE PRECISION,
    return_on_equity_adjusted DOUBLE PRECISION,
    return_on_assets DOUBLE PRECISION,
    return_on_assets_adjusted DOUBLE PRECISION,
    return_on_invested_capital DOUBLE PRECISION,
    return_on_invested_capital_adjusted DOUBLE PRECISION,
    cash_return_on_invested_capital DOUBLE PRECISION,
    earnings_per_share_basic DOUBLE PRECISION,
    earnings_per_share_diluted DOUBLE PRECISION,
    sales_per_share DOUBLE PRECISION,
    equity_per_share DOUBLE PRECISION,
    free_cash_flow_per_share DOUBLE PRECISION,
    dividends_per_share DOUBLE PRECISION,
    ebitda BIGINT,
    free_cash_flow BIGINT,
    free_cash_flow_to_net_income DOUBLE PRECISION,
    free_cash_flow_to_net_income_adjusted DOUBLE PRECISION,
    dividend_payout_ratio DOUBLE PRECISION,
    current_ratio DOUBLE PRECISION,
    debt_ratio DOUBLE PRECISION,
    total_debt BIGINT,
    net_debt_to_ebitda DOUBLE PRECISION,
    net_debt_to_ebit DOUBLE PRECISION,
    liabilities_to_equity_ratio DOUBLE PRECISION,
    piotroski_f_score DOUBLE PRECISION,
    net_income_adjusted BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, fiscal_period, fiscal_year, report_date)
);

CREATE INDEX idx_ratios_ticker ON derived_ratios(ticker);
CREATE INDEX idx_ratios_period ON derived_ratios(fiscal_period, fiscal_year);
CREATE INDEX idx_ratios_date ON derived_ratios(report_date DESC);

-- ============================================================================
-- 6. 10-K DOCUMENTS TABLE
-- ============================================================================
CREATE TABLE tenk_documents (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL REFERENCES companies(ticker) ON DELETE CASCADE,
    accession_number VARCHAR(50) NOT NULL UNIQUE,
    document_id VARCHAR(100) NOT NULL UNIQUE,
    form_type VARCHAR(10) DEFAULT '10-K',
    fiscal_year INTEGER NOT NULL,
    filing_date DATE,
    document_size INTEGER,
    file_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker)
);

CREATE INDEX idx_tenk_ticker ON tenk_documents(ticker);
CREATE INDEX idx_tenk_fiscal_year ON tenk_documents(fiscal_year DESC);

-- ============================================================================
-- 7. 10-K SECTIONS TABLE (Only priority sections)
-- ============================================================================
CREATE TABLE tenk_sections (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL REFERENCES tenk_documents(document_id) ON DELETE CASCADE,
    section_id VARCHAR(150) NOT NULL UNIQUE,
    item_label VARCHAR(50) NOT NULL,
    item_description TEXT,
    content TEXT NOT NULL,
    content_length INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    CHECK (item_label IN ('Item 1', 'Item 1A', 'Item 1B', 'Item 1C', 
                          'Item 2', 'Item 3', 'Item 5', 'Item 7', 'Item 7A'))
);

CREATE INDEX idx_tenk_sections_document ON tenk_sections(document_id);
CREATE INDEX idx_tenk_sections_item ON tenk_sections(item_label);

-- ============================================================================
-- 8. 10-K EMBEDDINGS TABLE (pgvector)
-- ============================================================================
CREATE TABLE tenk_embeddings (
    id SERIAL PRIMARY KEY,
    section_id VARCHAR(150) NOT NULL REFERENCES tenk_sections(section_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1536),
    ticker VARCHAR(10) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    item_label VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(section_id, chunk_index)
);

CREATE INDEX idx_tenk_embeddings_section ON tenk_embeddings(section_id);
CREATE INDEX idx_tenk_embeddings_ticker ON tenk_embeddings(ticker, fiscal_year);
CREATE INDEX idx_tenk_embeddings_item ON tenk_embeddings(item_label);

-- Vector similarity search index (cosine distance)
CREATE INDEX idx_tenk_embeddings_vector ON tenk_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- GRANTS (Optional - for additional security)
-- ============================================================================
-- If you want to create a separate read-only user later, you can use:
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE companies IS 'NASDAQ-100 companies master list';
COMMENT ON TABLE income_statement IS 'Income statement data from SimFin';
COMMENT ON TABLE balance_sheet IS 'Balance sheet data from SimFin';
COMMENT ON TABLE cash_flow IS 'Cash flow statement data from SimFin';
COMMENT ON TABLE derived_ratios IS 'Financial ratios and metrics from SimFin';
COMMENT ON TABLE tenk_documents IS 'Latest 10-K filing metadata';
COMMENT ON TABLE tenk_sections IS 'Priority sections from 10-K filings';
COMMENT ON TABLE tenk_embeddings IS 'Vector embeddings for semantic search';