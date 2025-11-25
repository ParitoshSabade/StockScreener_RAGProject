"""
SQL Generator - Converts natural language to SQL queries
"""
import logging
from typing import Dict, List
import psycopg2
from openai import OpenAI
import os
from dotenv import load_dotenv
from ..utils.database import get_db_connection
from ..utils.company_loader import CompanyLoader

load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class SQLGenerator:
    """Generates and executes SQL queries from natural language"""
    
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.company_list = CompanyLoader.load_companies()
    
    def _get_schema_context(self, mentioned_companies: List[Dict] = None) -> str:
        """Build schema context with company list"""
        
        context = f"""You are a SQL expert for a financial database with NASDAQ-100 stock data.

⚠️ CRITICAL SECURITY RULE ⚠️
ONLY GENERATE SELECT QUERIES. NEVER generate:
- INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE
- Any data modification or schema changes

AVAILABLE COMPANIES:
{self.company_list}

DATABASE SCHEMA:

1. companies
   Columns: simfin_id, ticker, name, currency, isin
   
2. income_statement  
   Columns: ticker, fiscal_period, fiscal_year, report_date, publish_date, restated, source, ttm, value_check, data_model,
   revenue, cost_of_revenue, gross_profit, 
   operating_expenses, operating_income_loss, 
   net_income, research_development, 
   selling_general_administrative, 
   interest_expense_net,
   income_tax_expense, 
   pretax_income_loss_adjusted
   
   ✅ HAS 'FY' DATA: Use fiscal_period = 'FY' for annual queries
   
3. balance_sheet
   Columns: ticker, fiscal_period, fiscal_year, report_date, publish_date, restated, source, ttm, value_check, data_model,
   
   ASSETS:
   - cash_cash_equivalents_short_term_investments, cash_cash_equivalents, short_term_investments
   - accounts_notes_receivable, accounts_receivable_net
   - inventories
   - other_short_term_assets, miscellaneous_short_term_assets
   - total_current_assets
   - property_plant_equipment_net
   - long_term_investments_receivables
   - other_long_term_assets, miscellaneous_long_term_assets
   - total_noncurrent_assets
   - total_assets
   
   LIABILITIES:
   - payables_accruals, accounts_payable
   - short_term_debt
   - other_short_term_liabilities, deferred_revenue_short_term, miscellaneous_short_term_liabilities
   - total_current_liabilities
   - long_term_debt
   - other_long_term_liabilities, miscellaneous_long_term_liabilities
   - total_noncurrent_liabilities
   - total_liabilities
   
   EQUITY:
   - share_capital_additional_paid_in_capital
   - retained_earnings
   - other_equity
   - equity_before_minority_interest
   - total_equity
   - total_liabilities_equity
   
   ❌ NO 'FY' DATA: Only quarterly (Q1-Q4). MUST use latest quarter CTE pattern!
   
4. cash_flow
   Columns: ticker, fiscal_period, fiscal_year, report_date, publish_date, restated, source, ttm, value_check, data_model,
   
   OPERATING:
   - net_income_starting_line
   - depreciation_amortization
   - non_cash_items
   - change_in_working_capital
   - cash_from_operating_activities
   
   INVESTING:
   - change_in_fixed_assets_intangibles
   - net_change_in_long_term_investment
   - other_investing_activities
   - cash_from_investing_activities
   
   FINANCING:
   - dividends_paid
   - cash_from_repayment_of_debt
   - cash_from_repurchase_of_equity
   - decrease_in_capital_stock
   - other_financing_activities
   - cash_from_financing_activities
   
   OTHER:
   - net_cash_before_disc_operations_and_fx
   - net_cash_before_fx
   - net_changes_in_cash
   
   ✅ HAS 'FY' DATA: Use fiscal_period = 'FY' for annual queries
   ⚠️ IMPORTANT: net_income is NOT in this table - it's in income_statement!

5. derived_ratios
   Columns: ticker, fiscal_period, fiscal_year, report_date, ttm, restated, data_model,
   
   PROFITABILITY:
   - gross_profit_margin, operating_margin
   - net_profit_margin, net_profit_margin_adjusted
   
   RETURNS:
   - return_on_equity, return_on_equity_adjusted
   - return_on_assets, return_on_assets_adjusted
   - return_on_invested_capital, return_on_invested_capital_adjusted
   - cash_return_on_invested_capital
   
   PER SHARE:
   - earnings_per_share_basic, earnings_per_share_diluted
   - sales_per_share, equity_per_share
   - free_cash_flow_per_share, dividends_per_share
   
   CASH FLOW:
   - ebitda, free_cash_flow
   - free_cash_flow_to_net_income, free_cash_flow_to_net_income_adjusted
   
   LEVERAGE & LIQUIDITY:
   - current_ratio, debt_ratio
   - total_debt, net_debt_to_ebitda, net_debt_to_ebit
   - liabilities_to_equity_ratio
   - dividend_payout_ratio
   
   OTHER:
   - piotroski_f_score
   - net_income_adjusted
   
   ❌ NO 'FY' DATA: Only quarterly (Q1-Q4). MUST use latest quarter CTE pattern!
   - ALL ratios and margins stored as DECIMALS (0.20 = 20%)
   - ALWAYS multiply by 100 when displaying: ROUND(value::numeric * 100, 2)

KEY FACTS:
- fiscal_period: 'FY' (fiscal year), 'Q1', 'Q2', 'Q3', 'Q4'
- Data availability: fiscal_year ranges from 2022-2025
- All financial values in company's currency (usually USD)

CRITICAL TABLE DATA STRUCTURE:
✅ Tables WITH 'FY' data:
   - income_statement: Use fiscal_period = 'FY' for annual
   - cash_flow: Use fiscal_period = 'FY' for annual

❌ Tables WITHOUT 'FY' data (quarterly only):
   - balance_sheet: Q1-Q4 only, use latest quarter CTE
   - derived_ratios: Q1-Q4 only, use latest quarter CTE

CRITICAL COLUMN LOCATIONS (avoid mistakes):
- net_income → income_statement (NOT in cash_flow!)
- cash_from_operating_activities → cash_flow
- total_assets, total_liabilities, long_term_debt → balance_sheet
- return_on_equity, profit margins, ratios → derived_ratios

When calculating cross-table ratios:
- Cashflow to profit: JOIN cash_flow.cash_from_operating_activities WITH income_statement.net_income
- Must join on: ticker, fiscal_year, AND fiscal_period
- For balance_sheet/derived_ratios: use latest quarter CTE first, then JOIN if needed

CRITICAL RULES FOR QUERY GENERATION:

1. FISCAL PERIOD SELECTION:
   - income_statement, cash_flow: Use fiscal_period = 'FY' for annual
   - balance_sheet, derived_ratios: Use latest quarter CTE (no 'FY' exists!)
   - NEVER use fiscal_period = 'FY' for balance_sheet or derived_ratios

2. LATEST QUARTER CTE PATTERN (for balance_sheet and derived_ratios):
   WITH latest_quarters AS (
       SELECT 
           *,
           ROW_NUMBER() OVER (
               PARTITION BY ticker 
               ORDER BY fiscal_year DESC, 
                        CASE fiscal_period 
                            WHEN 'Q4' THEN 4 
                            WHEN 'Q3' THEN 3 
                            WHEN 'Q2' THEN 2 
                            WHEN 'Q1' THEN 1 
                        END DESC
           ) as rn
       FROM [table_name]
       WHERE [metric] IS NOT NULL
   )
   SELECT ... FROM latest_quarters WHERE rn = 1

3. HANDLING NULL VALUES:
   - ALWAYS filter: WHERE metric IS NOT NULL
   - ALWAYS handle division by zero: NULLIF(denominator, 0)
   - Filter before CTE for better performance

4. MOST RECENT DATA (for income_statement and cash_flow):
   WHERE fiscal_period = 'FY'
     AND fiscal_year = (
         SELECT MAX(fiscal_year)
         FROM [table]
         WHERE ticker = main.ticker AND fiscal_period = 'FY'
     )

5. POSTGRESQL CRITICAL:
   - Cast before ROUND: ROUND(value::numeric, 2)
   - Cast before division: (new - old)::DECIMAL / NULLIF(old, 0)
   - Percentages from decimals: ROUND(decimal_value::numeric * 100, 2)

6. ALWAYS INCLUDE IN RESULTS:
   - ticker, name (join companies)
   - fiscal_year, fiscal_period (for context)
   - Calculated values AND their components
   - Use descriptive column names

EXAMPLES:

-- Top companies by revenue (income_statement has FY)
SELECT 
    c.ticker,
    c.name,
    i.revenue,
    i.fiscal_year
FROM companies c
JOIN income_statement i ON c.ticker = i.ticker
WHERE i.fiscal_period = 'FY'
  AND i.revenue IS NOT NULL
  AND i.fiscal_year = (
      SELECT MAX(fiscal_year)
      FROM income_statement
      WHERE ticker = i.ticker AND fiscal_period = 'FY'
  )
ORDER BY i.revenue DESC
LIMIT 10;

-- Top companies by total assets (balance_sheet has NO FY - use latest quarter)
WITH latest_quarters AS (
    SELECT 
        ticker,
        fiscal_year,
        fiscal_period,
        total_assets,
        ROW_NUMBER() OVER (
            PARTITION BY ticker 
            ORDER BY fiscal_year DESC, 
                     CASE fiscal_period 
                         WHEN 'Q4' THEN 4 
                         WHEN 'Q3' THEN 3 
                         WHEN 'Q2' THEN 2 
                         WHEN 'Q1' THEN 1 
                     END DESC
        ) as rn
    FROM balance_sheet
    WHERE total_assets IS NOT NULL
)
SELECT 
    c.ticker,
    c.name,
    lq.total_assets,
    lq.fiscal_period,
    lq.fiscal_year
FROM latest_quarters lq
JOIN companies c ON lq.ticker = c.ticker
WHERE lq.rn = 1
ORDER BY lq.total_assets DESC
LIMIT 10;

-- Top companies by ROE (derived_ratios has NO FY - use latest quarter)
WITH latest_quarters AS (
    SELECT 
        ticker,
        fiscal_year,
        fiscal_period,
        return_on_equity,
        ROW_NUMBER() OVER (
            PARTITION BY ticker 
            ORDER BY fiscal_year DESC, 
                     CASE fiscal_period 
                         WHEN 'Q4' THEN 4 
                         WHEN 'Q3' THEN 3 
                         WHEN 'Q2' THEN 2 
                         WHEN 'Q1' THEN 1 
                     END DESC
        ) as rn
    FROM derived_ratios
    WHERE return_on_equity IS NOT NULL
)
SELECT 
    c.ticker,
    c.name,
    ROUND(lq.return_on_equity::numeric * 100, 2) AS roe_percent,
    lq.fiscal_period,
    lq.fiscal_year
FROM latest_quarters lq
JOIN companies c ON lq.ticker = c.ticker
WHERE lq.rn = 1
ORDER BY lq.return_on_equity DESC
LIMIT 10;

-- Companies with ROE > 20% (derived_ratios - latest quarter)
WITH latest_quarters AS (
    SELECT 
        ticker,
        fiscal_year,
        fiscal_period,
        return_on_equity,
        ROW_NUMBER() OVER (
            PARTITION BY ticker 
            ORDER BY fiscal_year DESC, 
                     CASE fiscal_period 
                         WHEN 'Q4' THEN 4 
                         WHEN 'Q3' THEN 3 
                         WHEN 'Q2' THEN 2 
                         WHEN 'Q1' THEN 1 
                     END DESC
        ) as rn
    FROM derived_ratios
    WHERE return_on_equity IS NOT NULL
      AND return_on_equity > 0.20
)
SELECT 
    c.ticker,
    c.name,
    ROUND(lq.return_on_equity::numeric * 100, 2) AS roe_percent,
    lq.fiscal_period,
    lq.fiscal_year
FROM latest_quarters lq
JOIN companies c ON lq.ticker = c.ticker
WHERE lq.rn = 1
ORDER BY lq.return_on_equity DESC;

-- Cashflow to profit ratio (JOIN cash_flow + income_statement)
-- Both have FY data, so use fiscal_period = 'FY'
SELECT 
    c.ticker,
    c.name,
    cf.cash_from_operating_activities,
    i.net_income,
    ROUND((cf.cash_from_operating_activities::DECIMAL / NULLIF(i.net_income, 0)) * 100, 2) AS cashflow_to_profit_ratio,
    cf.fiscal_year
FROM cash_flow cf
JOIN income_statement i ON cf.ticker = i.ticker 
    AND cf.fiscal_year = i.fiscal_year 
    AND cf.fiscal_period = i.fiscal_period
JOIN companies c ON cf.ticker = c.ticker
WHERE cf.fiscal_period = 'FY'
  AND cf.cash_from_operating_activities IS NOT NULL
  AND i.net_income IS NOT NULL
  AND i.net_income > 0
  AND cf.fiscal_year = (
      SELECT MAX(fiscal_year)
      FROM cash_flow
      WHERE ticker = cf.ticker AND fiscal_period = 'FY'
  )
ORDER BY cashflow_to_profit_ratio DESC
LIMIT 5;

-- Revenue growth (income_statement - use CTE pattern)
WITH oldest_revenue AS (
    SELECT 
        ticker,
        fiscal_year,
        revenue,
        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY fiscal_year ASC) as rn
    FROM income_statement
    WHERE fiscal_period = 'FY' AND revenue IS NOT NULL
),
newest_revenue AS (
    SELECT 
        ticker,
        fiscal_year,
        revenue,
        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY fiscal_year DESC) as rn
    FROM income_statement
    WHERE fiscal_period = 'FY' AND revenue IS NOT NULL
)
SELECT 
    c.ticker,
    c.name,
    o.fiscal_year AS start_year,
    n.fiscal_year AS end_year,
    o.revenue AS start_revenue,
    n.revenue AS end_revenue,
    ROUND(((n.revenue - o.revenue)::DECIMAL / NULLIF(o.revenue, 0)) * 100, 2) AS total_growth_pct,
    n.fiscal_year - o.fiscal_year AS years_span
FROM companies c
JOIN oldest_revenue o ON c.ticker = o.ticker AND o.rn = 1
JOIN newest_revenue n ON c.ticker = n.ticker AND n.rn = 1
WHERE o.revenue > 0
ORDER BY total_growth_pct DESC
LIMIT 10;

-- Companies with highest debt (balance_sheet - use latest quarter)
WITH latest_quarters AS (
    SELECT 
        ticker,
        fiscal_year,
        fiscal_period,
        long_term_debt,
        ROW_NUMBER() OVER (
            PARTITION BY ticker 
            ORDER BY fiscal_year DESC, 
                     CASE fiscal_period 
                         WHEN 'Q4' THEN 4 
                         WHEN 'Q3' THEN 3 
                         WHEN 'Q2' THEN 2 
                         WHEN 'Q1' THEN 1 
                     END DESC
        ) as rn
    FROM balance_sheet
    WHERE long_term_debt IS NOT NULL
)
SELECT 
    c.ticker,
    c.name,
    lq.long_term_debt,
    lq.fiscal_period,
    lq.fiscal_year
FROM latest_quarters lq
JOIN companies c ON lq.ticker = c.ticker
WHERE lq.rn = 1
ORDER BY lq.long_term_debt DESC
LIMIT 5;

CRITICAL REMINDERS:
- ❌ NEVER use fiscal_period = 'FY' for balance_sheet or derived_ratios
- ✅ ALWAYS use latest quarter CTE for balance_sheet and derived_ratios
- ✅ ALWAYS filter NULL values before calculations
- ✅ ALWAYS cast to ::numeric before ROUND()
- ✅ ALWAYS include fiscal_period in results for clarity
- ✅ When JOINing tables, match on ticker, fiscal_year, AND fiscal_period
"""

        if mentioned_companies:
            company_info = ", ".join([
                f"{c['name']} ({c['ticker']})" 
                for c in mentioned_companies
            ])
            context += f"\n\nNOTE: User mentioned: {company_info}"
        
        context += "\n\nGenerate ONLY the SQL query, no explanations or markdown."
        
        return context
    
    def generate_sql(self, user_query: str, mentioned_companies: List[Dict] = None) -> Dict:
        """
        Generate SQL from natural language
        
        Args:
            user_query: Natural language query
            mentioned_companies: List of dicts with 'name' and 'ticker'
        
        Returns:
            Dict with 'sql' and 'explanation'
        """
        try:
            context = self._get_schema_context(mentioned_companies)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": f"Generate SQL for: {user_query}"}
                ],
                temperature=0.1
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up markdown code blocks
            if sql_query.startswith("```sql"):
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            elif sql_query.startswith("```"):
                sql_query = sql_query.replace("```", "").strip()
            
            logger.info(f"Generated SQL: {sql_query}...")
            
            return {
                "sql": sql_query,
                "explanation": "SQL query generated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return {
                "sql": None,
                "explanation": f"Error generating SQL: {str(e)}"
            }
    
    def execute_sql(self, sql_query: str) -> Dict:
        """
        Execute SQL query and return results
        
        Args:
            sql_query: SQL query to execute
        
        Returns:
            Dict with 'success', 'data', 'columns', 'error'
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            
            # Get results
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Format as list of dicts
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            cursor.close()
            conn.close()
            
            logger.info(f"SQL executed successfully: {len(data)} rows returned")
            
            return {
                "success": True,
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            return {
                "success": False,
                "data": [],
                "columns": [],
                "row_count": 0,
                "error": str(e)
            }
    
    def query(self, user_query: str, mentioned_companies: List[Dict] = None) -> Dict:
        """
        Generate and execute SQL in one step
        
        Args:
            user_query: Natural language query
            mentioned_companies: Optional list of mentioned companies
        
        Returns:
            Dict with SQL results and metadata
        """
        # Generate SQL
        sql_result = self.generate_sql(user_query, mentioned_companies)
        
        if not sql_result["sql"]:
            return {
                "success": False,
                "error": "Failed to generate SQL",
                "sql": None,
                "data": []
            }
        
        # Validate query safety
        if not self._validate_query_safety(sql_result["sql"]):
            logger.error(f"SECURITY: Unsafe query blocked")
            return {
                "success": False,
                "error": "Invalid query: Only SELECT statements are allowed",
                "sql": sql_result["sql"],
                "data": [],
                "row_count": 0
            }
        
        # Execute SQL
        exec_result = self.execute_sql(sql_result["sql"])
        
        return {
            "success": exec_result["success"],
            "sql": sql_result["sql"],
            "data": exec_result["data"],
            "columns": exec_result["columns"],
            "row_count": exec_result["row_count"],
            "error": exec_result["error"]
        }

    def _validate_query_safety(self, sql: str) -> bool:
        """
        Validate that query is a safe SELECT statement only
        
        Args:
            sql: SQL query string
        
        Returns:
            True if safe, False otherwise
        """
        sql_upper = sql.upper().strip()
        
        # Must start with SELECT or WITH
        if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
            logger.error(f"Query does not start with SELECT or WITH: {sql[:50]}")
            return False
        
        # Forbidden keywords
        forbidden = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 
            'TRUNCATE', 'CREATE', 'REPLACE', 'EXEC', 'EXECUTE'
        ]
        
        for keyword in forbidden:
            if keyword in sql_upper:
                logger.error(f"Forbidden keyword '{keyword}' found in query")
                return False
        
        # Check for multiple statements (semicolon not at end)
        semicolons = sql.count(';')
        if semicolons > 1:
            logger.error(f"Multiple statements detected (semicolons: {semicolons})")
            return False
        
        return True