import unittest
import json # For comparing complex dicts if needed, or just for printing
from ..app.scoring.scorer import Scorer
from ..app.config import SCORING_THRESHOLDS # To verify against default config

class TestScorer(unittest.TestCase):
    def setUp(self):
        self.sample_analyzed_data_strong = {
            "ticker": "STRONGCO", "period_of_report": "2023-12-31",
            "shares_outstanding": 100_000_000,
            "income_statement_extracted": {"net_income": 25_000_000},
            "balance_sheet_extracted": {"total_equity": 100_000_000},
            "profitability_ratios": {
                "return_on_equity": 0.25, "net_profit_margin": 0.20,
                "operating_margin": 0.22, "gross_profit_margin": 0.50,
            },
            "financial_health_ratios": {
                "debt_to_equity_ratio": 0.4, "current_ratio": 2.5,
            },
            "cash_flow_metrics": {
                "fcf_margin": 0.15, "net_income_to_fcf_conversion": 0.9,
                "free_cash_flow": 22_500_000
            }
        }
        self.scorer_strong = Scorer(self.sample_analyzed_data_strong)

        self.sample_analyzed_data_weak = {
            "ticker": "WEAKCO", "period_of_report": "2023-12-31",
            "shares_outstanding": 50_000_000,
            "income_statement_extracted": {"net_income": 1_000_000},
            "balance_sheet_extracted": {"total_equity": 20_000_000},
            "profitability_ratios": {
                "return_on_equity": 0.05, "net_profit_margin": 0.03,
                "operating_margin": 0.06, "gross_profit_margin": 0.10,
            },
            "financial_health_ratios": {
                "debt_to_equity_ratio": 2.5, "current_ratio": 0.8,
            },
            "cash_flow_metrics": {
                "fcf_margin": -0.02, "net_income_to_fcf_conversion": 0.1,
                 "free_cash_flow": 100_000
            }
        }
        self.scorer_weak = Scorer(self.sample_analyzed_data_weak)

        self.sample_analyzed_data_mixed = {
            "ticker": "MIXEDCO", "period_of_report": "2023-12-31",
            "shares_outstanding": 70_000_000,
             "income_statement_extracted": {"net_income": 10_000_000},
            "balance_sheet_extracted": {"total_equity": 60_000_000},
            "profitability_ratios": { # Moderate ROE, Strong Net Margin
                "return_on_equity": SCORING_THRESHOLDS["profitability"]["roe_moderate"] + 0.01,
                "net_profit_margin": SCORING_THRESHOLDS["profitability"]["net_margin_strong"] + 0.01,
                "operating_margin": None, # Undetermined
                "gross_profit_margin": SCORING_THRESHOLDS["profitability"]["gross_margin_moderate"] - 0.01 # Weak
            },
            "financial_health_ratios": { # Strong D/E, Weak Current Ratio
                "debt_to_equity_ratio": SCORING_THRESHOLDS["financial_health"]["debt_to_equity_low"] - 0.1,
                "current_ratio": SCORING_THRESHOLDS["financial_health"]["current_ratio_moderate"] - 0.1,
            },
            "cash_flow_metrics": { # Undetermined FCF Margin, Moderate NI to FCF
                "fcf_margin": None,
                "net_income_to_fcf_conversion": SCORING_THRESHOLDS["cash_flow"]["net_income_to_fcf_moderate"] + 0.01,
                "free_cash_flow": 6_000_000
            }
        }
        self.scorer_mixed = Scorer(self.sample_analyzed_data_mixed)


    def test_scorer_initialization(self):
        self.assertEqual(self.scorer_strong.analyzed_data["ticker"], "STRONGCO")
        self.assertEqual(self.scorer_strong.config, SCORING_THRESHOLDS) # Check if default config is loaded

    def test_score_metric_helper(self):
        # Higher is better
        self.assertEqual(self.scorer_strong._score_metric(0.25, 0.20, 0.15), "Strong")
        self.assertEqual(self.scorer_strong._score_metric(0.18, 0.20, 0.15), "Moderate")
        self.assertEqual(self.scorer_strong._score_metric(0.10, 0.20, 0.15), "Weak")
        self.assertEqual(self.scorer_strong._score_metric(None, 0.20, 0.15), "Undetermined")
        self.assertEqual(self.scorer_strong._score_metric("invalid", 0.20, 0.15), "Invalid Data")


        # Lower is better
        self.assertEqual(self.scorer_strong._score_metric(0.4, 0.5, 1.0, lower_is_better=True), "Strong")
        self.assertEqual(self.scorer_strong._score_metric(0.7, 0.5, 1.0, lower_is_better=True), "Moderate")
        self.assertEqual(self.scorer_strong._score_metric(1.2, 0.5, 1.0, lower_is_better=True), "Weak")

    def test_score_profitability(self):
        scores_strong = self.scorer_strong.score_profitability()
        self.assertEqual(scores_strong['roe_score'], "Strong")
        self.assertEqual(scores_strong['net_margin_score'], "Strong")
        self.assertEqual(scores_strong['overall_profitability_score'], "Strong")

        scores_weak = self.scorer_weak.score_profitability()
        self.assertEqual(scores_weak['roe_score'], "Weak")
        self.assertEqual(scores_weak['net_margin_score'], "Weak")
        self.assertEqual(scores_weak['overall_profitability_score'], "Weak")

        scores_mixed = self.scorer_mixed.score_profitability()
        self.assertEqual(scores_mixed['roe_score'], "Moderate")
        self.assertEqual(scores_mixed['net_margin_score'], "Strong")
        self.assertEqual(scores_mixed['operating_margin_score'], "Undetermined")
        self.assertEqual(scores_mixed['gross_margin_score'], "Weak")
        self.assertEqual(scores_mixed['overall_profitability_score'], "Undetermined") # Undetermined because one component is Undetermined, then Weak takes precedence.

    def test_score_financial_health(self):
        scores_strong = self.scorer_strong.score_financial_health()
        self.assertEqual(scores_strong['debt_to_equity_score'], "Strong")
        self.assertEqual(scores_strong['current_ratio_score'], "Strong")
        self.assertEqual(scores_strong['overall_financial_health_score'], "Strong")

        scores_weak = self.scorer_weak.score_financial_health()
        self.assertEqual(scores_weak['debt_to_equity_score'], "Weak")
        self.assertEqual(scores_weak['current_ratio_score'], "Weak")
        self.assertEqual(scores_weak['overall_financial_health_score'], "Weak")

        scores_mixed = self.scorer_mixed.score_financial_health()
        self.assertEqual(scores_mixed['debt_to_equity_score'], "Strong")
        self.assertEqual(scores_mixed['current_ratio_score'], "Weak")
        self.assertEqual(scores_mixed['overall_financial_health_score'], "Weak")


    def test_score_cash_flow(self):
        scores_strong = self.scorer_strong.score_cash_flow()
        self.assertEqual(scores_strong['fcf_margin_score'], "Strong")
        self.assertEqual(scores_strong['net_income_to_fcf_score'], "Strong")
        self.assertEqual(scores_strong['overall_cash_flow_score'], "Strong")

        scores_weak = self.scorer_weak.score_cash_flow()
        self.assertEqual(scores_weak['fcf_margin_score'], "Weak")
        self.assertEqual(scores_weak['net_income_to_fcf_score'], "Weak") # 0.1 is weak
        self.assertEqual(scores_weak['overall_cash_flow_score'], "Weak")

        scores_mixed = self.scorer_mixed.score_cash_flow()
        self.assertEqual(scores_mixed['fcf_margin_score'], "Undetermined")
        self.assertEqual(scores_mixed['net_income_to_fcf_score'], "Moderate")
        self.assertEqual(scores_mixed['overall_cash_flow_score'], "Undetermined")


    def test_calculate_valuation_ratios(self):
        # StrongCo: NI=25M, Equity=100M, FCF=22.5M, Shares=100M. Price=30
        # EPS = 0.25, BVPS = 1.0, FCFPS = 0.225
        # P/E = 30/0.25 = 120, P/B = 30/1 = 30, P/FCF = 30/0.225 = 133.33
        valuation_strong = self.scorer_strong.calculate_valuation_ratios(current_stock_price=30.0)
        self.assertAlmostEqual(valuation_strong['eps'], 0.25)
        self.assertAlmostEqual(valuation_strong['book_value_per_share'], 1.0)
        self.assertAlmostEqual(valuation_strong['fcf_per_share'], 0.225)
        self.assertAlmostEqual(valuation_strong['p_e'], 120.0)
        self.assertAlmostEqual(valuation_strong['p_b'], 30.0)
        self.assertAlmostEqual(valuation_strong['p_fcf'], 30.0 / 0.225)

        # Test no stock price
        valuation_no_price = self.scorer_strong.calculate_valuation_ratios(current_stock_price=None)
        self.assertIsNone(valuation_no_price['p_e'])
        self.assertIn("Current stock price not provided", valuation_no_price['valuation_notes'])

        # Test missing shares_outstanding
        data_no_shares = self.sample_analyzed_data_strong.copy()
        del data_no_shares['shares_outstanding'] # remove direct key
        # check if it can fallback to income_statement_extracted if needed (not set up here)
        # for now, assume it will be None
        scorer_no_shares = Scorer(data_no_shares)
        valuation_no_shares = scorer_no_shares.calculate_valuation_ratios(current_stock_price=30.0)
        self.assertIsNone(valuation_no_shares['eps'])
        self.assertIsNone(valuation_no_shares['p_e'])
        self.assertIn("Shares outstanding not found", valuation_no_shares['valuation_notes'])


    def test_score_valuation(self):
        # Using STRONGCO's valuation: P/E=120, P/B=30, P/FCF=133.33 - these are all Weak (high)
        valuation_ratios_high = {'p_e': 120.0, 'p_b': 30.0, 'p_fcf': 133.33}
        valuation_scores_high = self.scorer_strong.score_valuation(valuation_ratios_high)
        self.assertEqual(valuation_scores_high['p_e_score'], "Weak")
        self.assertEqual(valuation_scores_high['p_b_score'], "Weak")
        self.assertEqual(valuation_scores_high['p_fcf_score'], "Weak")
        self.assertEqual(valuation_scores_high['overall_valuation_score'], "Weak")

        # Attractive valuation
        valuation_ratios_low = {'p_e': 10.0, 'p_b': 1.0, 'p_fcf': 12.0} # Strong scores
        valuation_scores_low = self.scorer_strong.score_valuation(valuation_ratios_low)
        self.assertEqual(valuation_scores_low['p_e_score'], "Strong")
        self.assertEqual(valuation_scores_low['p_b_score'], "Strong")
        self.assertEqual(valuation_scores_low['p_fcf_score'], "Strong")
        self.assertEqual(valuation_scores_low['overall_valuation_score'], "Strong")

        # Undetermined valuation
        valuation_ratios_undetermined = {'p_e': None, 'p_b': 1.0, 'p_fcf': 12.0}
        valuation_scores_undetermined = self.scorer_strong.score_valuation(valuation_ratios_undetermined)
        self.assertEqual(valuation_scores_undetermined['p_e_score'], "Undetermined")
        self.assertEqual(valuation_scores_undetermined['overall_valuation_score'], "Undetermined")


    def test_generate_score_profile(self):
        profile = self.scorer_strong.generate_score_profile(current_stock_price=30.0)
        self.assertEqual(profile['ticker'], "STRONGCO")
        self.assertIn('profitability', profile['scores'])
        self.assertIn('valuation_metrics', profile)
        self.assertEqual(profile['scores']['profitability']['overall_profitability_score'], "Strong")
        # Valuation for STRONGCO with price 30 was WEAK as P/E etc were high
        self.assertEqual(profile['scores']['valuation']['overall_valuation_score'], "Weak")
        self.assertEqual(profile['final_overall_score'], "Weak") # Weak valuation makes overall weak

        profile_no_price = self.scorer_strong.generate_score_profile() # No stock price
        self.assertEqual(profile_no_price['scores']['valuation']['overall_valuation_score'], "Undetermined")
        self.assertIn("not provided", profile_no_price['valuation_metrics']['notes'])
        self.assertEqual(profile_no_price['final_overall_score'], "Undetermined") # Undetermined valuation

    # Add more test methods for:
    # - Qualitative scoring once implemented.
    # - More granular tests for _calculate_overall_score logic.
    # - Testing with custom config passed to Scorer.
    # - Behavior when specific ratios are missing from input analyzed_data.

if __name__ == '__main__':
    unittest.main()
```
