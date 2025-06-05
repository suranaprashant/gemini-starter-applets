import unittest
from ..app.analysis_engine.engine import AnalysisEngine, safe_get, safe_divide

class TestAnalysisEngine(unittest.TestCase):
    def setUp(self):
        self.sample_extracted_data_full = {
            "ticker": "SAMPLE",
            "income_statement_extracted": {
                "total_revenue": 1000000.0, "cost_of_revenue": 600000.0,
                "operating_income": 250000.0, "net_income": 150000.0,
            },
            "balance_sheet_extracted": {
                "total_liabilities": 800000.0, "total_equity": 1200000.0,
                "current_assets": 500000.0, "current_liabilities": 200000.0,
            },
            "cash_flow_statement_extracted": {
                "cash_flow_from_operations": 200000.0, "capital_expenditures": 50000.0,
            }
        }
        self.engine_full = AnalysisEngine(self.sample_extracted_data_full)

        self.sample_extracted_data_missing = {
            "ticker": "MISSING",
            "income_statement_extracted": {"total_revenue": 1000000.0},
            "balance_sheet_extracted": {"total_equity": 0.0}, # For zero denominator test
            "cash_flow_statement_extracted": {}
        }
        self.engine_missing = AnalysisEngine(self.sample_extracted_data_missing)

    def test_safe_get_and_safe_divide(self):
        # Test safe_get
        self.assertEqual(safe_get(self.sample_extracted_data_full, ['income_statement_extracted', 'total_revenue']), 1000000.0)
        self.assertIsNone(safe_get(self.sample_extracted_data_full, ['income_statement_extracted', 'non_existent_key']))
        self.assertEqual(safe_get(self.sample_extracted_data_full, ['non_existent_top_key'], default="default"), "default")

        # Test safe_divide
        self.assertEqual(safe_divide(10, 2), 5.0)
        self.assertIsNone(safe_divide(10, 0))
        self.assertIsNone(safe_divide(None, 2))
        self.assertIsNone(safe_divide(10, None))
        self.assertIsNone(safe_divide("a", 2)) # Non-numeric

    def test_engine_initialization(self):
        self.assertEqual(self.engine_full.extracted_data["ticker"], "SAMPLE")

    def test_calculate_profitability_ratios_full(self):
        ratios = self.engine_full.calculate_profitability_ratios()
        self.assertAlmostEqual(ratios['gross_profit_margin'], 0.4)  # (1M - 0.6M) / 1M
        self.assertAlmostEqual(ratios['operating_margin'], 0.25)    # 0.25M / 1M
        self.assertAlmostEqual(ratios['net_profit_margin'], 0.15)   # 0.15M / 1M
        self.assertAlmostEqual(ratios['return_on_equity'], 0.125)   # 0.15M / 1.2M
        # Simplified ROIC = 150k / (1.2M + 0.8M) = 150k / 2M = 0.075
        self.assertAlmostEqual(ratios['return_on_invested_capital_simplified'], 0.075)

    def test_calculate_profitability_ratios_missing(self):
        ratios = self.engine_missing.calculate_profitability_ratios()
        self.assertIsNone(ratios['gross_profit_margin']) # Missing cogs, net_income etc.
        self.assertIsNone(ratios['operating_margin'])
        self.assertIsNone(ratios['net_profit_margin'])
        self.assertIsNone(ratios['return_on_equity']) # net_income missing, equity is 0
        self.assertIsNone(ratios['return_on_invested_capital_simplified'])

    def test_calculate_financial_health_ratios_full(self):
        ratios = self.engine_full.calculate_financial_health_ratios()
        self.assertAlmostEqual(ratios['debt_to_equity_ratio'], 800000.0 / 1200000.0) # 0.8M / 1.2M
        self.assertAlmostEqual(ratios['current_ratio'], 500000.0 / 200000.0) # 0.5M / 0.2M

    def test_calculate_financial_health_ratios_missing_or_zero(self):
        ratios_missing = self.engine_missing.calculate_financial_health_ratios()
        self.assertIsNone(ratios_missing['debt_to_equity_ratio']) # total_liabilities missing, equity is 0
        self.assertIsNone(ratios_missing['current_ratio']) # current assets/liabilities missing

        # Test zero equity specifically for debt_to_equity
        data_zero_equity = {"balance_sheet_extracted": {"total_liabilities": 100.0, "total_equity": 0.0}}
        engine_zero_equity = AnalysisEngine(data_zero_equity)
        ratios_zero_eq = engine_zero_equity.calculate_financial_health_ratios()
        self.assertIsNone(ratios_zero_eq['debt_to_equity_ratio'])


    def test_calculate_cash_flow_metrics_full(self):
        metrics = self.engine_full.calculate_cash_flow_metrics()
        # FCF = 200k - 50k = 150k
        self.assertEqual(metrics['free_cash_flow'], 150000.0)
        # FCF Margin = 150k / 1M = 0.15
        self.assertAlmostEqual(metrics['fcf_margin'], 0.15)
        # NI to FCF = 150k / 150k = 1.0
        self.assertAlmostEqual(metrics['net_income_to_fcf_conversion'], 1.0)

    def test_calculate_cash_flow_metrics_missing(self):
        metrics = self.engine_missing.calculate_cash_flow_metrics()
        self.assertIsNone(metrics['free_cash_flow']) # CFO or CapEx missing
        self.assertIsNone(metrics['fcf_margin'])
        self.assertIsNone(metrics['net_income_to_fcf_conversion']) # Net income also missing

    def test_analyze_method(self):
        analysis_output = self.engine_full.analyze()
        self.assertIn('profitability_ratios', analysis_output)
        self.assertIn('financial_health_ratios', analysis_output)
        self.assertIn('cash_flow_metrics', analysis_output)
        self.assertEqual(analysis_output['ticker'], "SAMPLE")
        self.assertAlmostEqual(analysis_output['profitability_ratios']['net_profit_margin'], 0.15)

    def test_analyze_with_empty_data(self):
        engine_empty = AnalysisEngine({})
        analysis_output = engine_empty.analyze()
        self.assertIn("error", analysis_output)
        self.assertEqual(analysis_output["error"], "Extracted data is empty. Cannot perform analysis.")

    # Add more test methods for:
    # - Edge cases for each ratio (e.g., zero revenue, zero equity). (Some covered)
    # - Different combinations of missing data for each calculation method.
    # - Ensuring that the 'analyze' method correctly copies original data.

if __name__ == '__main__':
    unittest.main()
```
