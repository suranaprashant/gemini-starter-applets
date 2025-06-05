import pandas as pd # Optional, not strictly necessary for this implementation

def safe_get(data_dict, keys, default=None):
    """
    Safely get a value from a nested dictionary.
    `keys` should be a list or tuple of keys for nesting.
    """
    if not isinstance(data_dict, dict):
        return default
    temp_dict = data_dict
    for key in keys:
        if isinstance(temp_dict, dict) and key in temp_dict:
            temp_dict = temp_dict[key]
        else:
            return default
    return temp_dict

def safe_divide(numerator, denominator):
    """
    Safely divide two numbers. Returns None if denominator is zero or inputs are None.
    """
    if numerator is None or denominator is None or not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
        return None
    if denominator == 0:
        return None
    return numerator / denominator

class AnalysisEngine:
    def __init__(self, extracted_data):
        self.extracted_data = extracted_data if extracted_data else {}

    def calculate_profitability_ratios(self):
        ratios = {}

        # Get necessary values from extracted_data
        # Income Statement items
        total_revenue = safe_get(self.extracted_data, ['income_statement_extracted', 'total_revenue'])
        cogs = safe_get(self.extracted_data, ['income_statement_extracted', 'cost_of_revenue']) # Cost of Goods Sold
        operating_income = safe_get(self.extracted_data, ['income_statement_extracted', 'operating_income'])
        net_income = safe_get(self.extracted_data, ['income_statement_extracted', 'net_income'])

        # Balance Sheet items
        shareholder_equity = safe_get(self.extracted_data, ['balance_sheet_extracted', 'total_equity'])
        # Assuming 'total_debt' would be available or calculated separately if needed for ROIC.
        # For this simplified ROIC, let's assume it might be part of balance_sheet_extracted or needs to be added.
        # For now, if not directly available, ROIC might be None.
        # A more comprehensive 'total_debt' would sum short-term and long-term debt.
        total_debt = safe_get(self.extracted_data, ['balance_sheet_extracted', 'total_liabilities']) # Placeholder for total debt

        # Gross Profit Margin
        if total_revenue is not None and cogs is not None:
            gross_profit = total_revenue - cogs
            ratios['gross_profit_margin'] = safe_divide(gross_profit, total_revenue)
        else:
            ratios['gross_profit_margin'] = None

        # Operating Margin
        ratios['operating_margin'] = safe_divide(operating_income, total_revenue)

        # Net Profit Margin
        ratios['net_profit_margin'] = safe_divide(net_income, total_revenue)

        # Return on Equity (ROE)
        ratios['return_on_equity'] = safe_divide(net_income, shareholder_equity)

        # Return on Invested Capital (ROIC) - Simplified
        # ROIC = Net Income / (Shareholder's Equity + Total Debt)
        # This is a simplification. True invested capital can be more complex.
        if shareholder_equity is not None and total_debt is not None:
            invested_capital = shareholder_equity + total_debt
            ratios['return_on_invested_capital_simplified'] = safe_divide(net_income, invested_capital)
        else:
             ratios['return_on_invested_capital_simplified'] = None

        return ratios

    def calculate_financial_health_ratios(self):
        ratios = {}

        total_debt = safe_get(self.extracted_data, ['balance_sheet_extracted', 'total_liabilities']) # Using total liabilities as proxy for total debt
        shareholder_equity = safe_get(self.extracted_data, ['balance_sheet_extracted', 'total_equity'])
        current_assets = safe_get(self.extracted_data, ['balance_sheet_extracted', 'current_assets'])
        current_liabilities = safe_get(self.extracted_data, ['balance_sheet_extracted', 'current_liabilities'])

        # Debt-to-Equity Ratio
        ratios['debt_to_equity_ratio'] = safe_divide(total_debt, shareholder_equity)

        # Current Ratio
        ratios['current_ratio'] = safe_divide(current_assets, current_liabilities)

        return ratios

    def calculate_cash_flow_metrics(self):
        metrics = {}

        cash_flow_from_operations = safe_get(self.extracted_data, ['cash_flow_statement_extracted', 'cash_flow_from_operations'])
        capital_expenditures = safe_get(self.extracted_data, ['cash_flow_statement_extracted', 'capital_expenditures'])
        total_revenue = safe_get(self.extracted_data, ['income_statement_extracted', 'total_revenue'])
        net_income = safe_get(self.extracted_data, ['income_statement_extracted', 'net_income'])

        # Free Cash Flow (FCF)
        fcf = None
        if cash_flow_from_operations is not None and capital_expenditures is not None:
            # Capital expenditures might be negative (representing an inflow from sales of PP&E)
            # or positive (representing an outflow for purchases).
            # Typically, CapEx is shown as positive in statements when it's an expense.
            # If parsed CapEx is already negative for an expense, this works.
            # If parsed CapEx is positive for an expense, it should be subtracted.
            # Assuming capital_expenditures from extractor is positive if it's an expense.
            fcf = cash_flow_from_operations - capital_expenditures
        metrics['free_cash_flow'] = fcf

        # FCF Margin
        metrics['fcf_margin'] = safe_divide(fcf, total_revenue)

        # Net Income to FCF Conversion
        metrics['net_income_to_fcf_conversion'] = safe_divide(fcf, net_income)

        return metrics

    def analyze(self):
        if not self.extracted_data:
            return {"error": "Extracted data is empty. Cannot perform analysis."}

        analysis_output = self.extracted_data.copy() # Start with all original extracted data

        analysis_output['profitability_ratios'] = self.calculate_profitability_ratios()
        analysis_output['financial_health_ratios'] = self.calculate_financial_health_ratios()
        analysis_output['cash_flow_metrics'] = self.calculate_cash_flow_metrics()

        return analysis_output

if __name__ == '__main__':
    sample_extracted_data_full = {
        "ticker": "SAMPLE",
        "filing_type": "10-K",
        "period_of_report": "December 31, 2023",
        "income_statement_extracted": {
            "total_revenue": 1000000.0,
            "cost_of_revenue": 600000.0,
            "operating_income": 250000.0,
            "net_income": 150000.0,
        },
        "balance_sheet_extracted": {
            "total_assets": 2000000.0,
            "total_liabilities": 800000.0, # Proxy for total_debt
            "total_equity": 1200000.0,
            "current_assets": 500000.0,
            "current_liabilities": 200000.0,
        },
        "cash_flow_statement_extracted": {
            "cash_flow_from_operations": 200000.0,
            "capital_expenditures": 50000.0, # Assuming positive means expense
        }
    }

    sample_extracted_data_missing = {
        "ticker": "MISSING",
        "income_statement_extracted": {
            "total_revenue": 1000000.0,
            # "net_income": None, # Missing net_income
        },
        "balance_sheet_extracted": {
            "total_equity": 0.0, # Zero equity for testing zero denominator
        },
        "cash_flow_statement_extracted": {
            "cash_flow_from_operations": 50000.0
            # capital_expenditures is missing
        }
    }

    sample_extracted_data_partial_cogs = {
        "ticker": "PARTIAL",
        "income_statement_extracted": {
            "total_revenue": 1000000.0,
            # cost_of_revenue is missing
            "operating_income": 250000.0,
            "net_income": 150000.0,
        },
        "balance_sheet_extracted": {
            "total_liabilities": 800000.0,
            "total_equity": 1200000.0,
            "current_assets": 500000.0,
            "current_liabilities": 200000.0,
        },
        "cash_flow_statement_extracted": {
            "cash_flow_from_operations": 200000.0,
            "capital_expenditures": 50000.0,
        }
    }


    print("--- Analysis for Full Data ---")
    engine_full = AnalysisEngine(sample_extracted_data_full)
    analysis_full = engine_full.analyze()
    for key, value in analysis_full.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")

    print("\n--- Analysis for Missing/Zero Data ---")
    engine_missing = AnalysisEngine(sample_extracted_data_missing)
    analysis_missing = engine_missing.analyze()
    for key, value in analysis_missing.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")

    print("\n--- Analysis for Partial COGS Data ---")
    engine_partial_cogs = AnalysisEngine(sample_extracted_data_partial_cogs)
    analysis_partial_cogs = engine_partial_cogs.analyze()
    for key, value in analysis_partial_cogs.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")

    print("\n--- Analysis for Empty Data ---")
    engine_empty = AnalysisEngine({})
    analysis_empty = engine_empty.analyze()
    print(analysis_empty)

    print("\n--- Testing safe_get ---")
    test_dict_safe_get = {"a": {"b": {"c": 10}}}
    print(f"safe_get(test_dict_safe_get, ['a', 'b', 'c']): {safe_get(test_dict_safe_get, ['a', 'b', 'c'])}") # Expected: 10
    print(f"safe_get(test_dict_safe_get, ['a', 'x', 'c']): {safe_get(test_dict_safe_get, ['a', 'x', 'c'])}") # Expected: None
    print(f"safe_get(test_dict_safe_get, ['a', 'b']): {safe_get(test_dict_safe_get, ['a', 'b'])}") # Expected: {'c': 10}
    print(f"safe_get(None, ['a']): {safe_get(None, ['a'])}") # Expected: None
    print(f"safe_get({{}}, ['a']): {safe_get({}, ['a'])}") # Expected: None


    print("\n--- Testing safe_divide ---")
    print(f"safe_divide(10, 2): {safe_divide(10,2)}") # Expected: 5.0
    print(f"safe_divide(10, 0): {safe_divide(10,0)}") # Expected: None
    print(f"safe_divide(None, 2): {safe_divide(None,2)}") # Expected: None
    print(f"safe_divide(10, None): {safe_divide(10,None)}") # Expected: None
    print(f"safe_divide(0, 5): {safe_divide(0,5)}") # Expected: 0.0

```
