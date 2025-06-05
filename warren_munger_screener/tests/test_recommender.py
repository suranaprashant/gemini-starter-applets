import unittest
import json # For printing complex dicts
from ..app.recommender.recommender import Recommender

class TestRecommender(unittest.TestCase):
    def setUp(self):
        # Profile 1: Tier 1 - Strong fundamentals, Good Valuation
        self.profile_tier1 = {
            "ticker": "PRIME", "scores": {
                "profitability": {"overall_profitability_score": "Strong"},
                "financial_health": {"overall_financial_health_score": "Strong"},
                "cash_flow": {"overall_cash_flow_score": "Strong"},
                "valuation": {"overall_valuation_score": "Strong"}
            }, "qualitative_assessment": {
                "moat": {"moat_score": "Moderate"}, "management": {"management_score": "Moderate"}
            }}

        # Profile 2: Tier 2A - Strong fundamentals, Overvalued
        self.profile_tier2a = {
            "ticker": "GOODCO_HIGHPRICE", "scores": {
                "profitability": {"overall_profitability_score": "Strong"},
                "financial_health": {"overall_financial_health_score": "Strong"},
                "cash_flow": {"overall_cash_flow_score": "Strong"},
                "valuation": {"overall_valuation_score": "Weak"}
            }, "qualitative_assessment": {
                "moat": {"moat_score": "Strong"}, "management": {"management_score": "Strong"}
            }}

        # Profile 3: Tier 2B - Moderate fundamentals, Attractive Valuation
        self.profile_tier2b = {
            "ticker": "FAIRCO_GOODPRICE", "scores": {
                "profitability": {"overall_profitability_score": "Moderate"},
                "financial_health": {"overall_financial_health_score": "Moderate"},
                "cash_flow": {"overall_cash_flow_score": "Strong"},
                "valuation": {"overall_valuation_score": "Strong"}
            }, "qualitative_assessment": {
                "moat": {"moat_score": "Moderate"}, "management": {"management_score": "Moderate"}
            }}

        # Profile 4: Tier 3A - Weak fundamentals
        self.profile_tier3a = {
            "ticker": "WEAKFUND", "scores": {
                "profitability": {"overall_profitability_score": "Weak"},
                "financial_health": {"overall_financial_health_score": "Moderate"},
                "cash_flow": {"overall_cash_flow_score": "Strong"},
                "valuation": {"overall_valuation_score": "Moderate"}
            }, "qualitative_assessment": {
                "moat": {"moat_score": "Undetermined"}, "management": {"management_score": "Undetermined"}
            }}

        # Profile 5: Tier 3B - Moderate fundamentals, Fair/High Price
        self.profile_tier3b_fair_price = { # Moderate val
            "ticker": "FAIRCO_FAIRPRICE", "scores": {
                "profitability": {"overall_profitability_score": "Moderate"},
                "financial_health": {"overall_financial_health_score": "Moderate"},
                "cash_flow": {"overall_cash_flow_score": "Moderate"},
                "valuation": {"overall_valuation_score": "Moderate"}
            }, "qualitative_assessment": {
                "moat": {"moat_score": "Moderate"}, "management": {"management_score": "Moderate"}
            }}
        self.profile_tier3b_high_price = { # Weak val
            "ticker": "FAIRCO_HIGHPRICE", "scores": {
                "profitability": {"overall_profitability_score": "Moderate"},
                "financial_health": {"overall_financial_health_score": "Moderate"},
                "cash_flow": {"overall_cash_flow_score": "Moderate"},
                "valuation": {"overall_valuation_score": "Weak"}
            }, "qualitative_assessment": {
                "moat": {"moat_score": "Moderate"}, "management": {"management_score": "Moderate"}
            }}


        # Profile 6: Tier 4 - Undetermined fundamentals
        self.profile_tier4 = {
            "ticker": "UNKNOWN", "scores": {
                "profitability": {"overall_profitability_score": "Undetermined"},
                "financial_health": {"overall_financial_health_score": "Strong"},
                "cash_flow": {"overall_cash_flow_score": "Moderate"},
                "valuation": {"overall_valuation_score": "Moderate"}
            }, "qualitative_assessment": {
                "moat": {"moat_score": "Undetermined"}, "management": {"management_score": "Undetermined"}
            }}

        self.profile_empty = {}
        self.profile_no_scores_key = {"ticker": "NOSCORES"}


    def test_recommender_initialization(self):
        recommender = Recommender(self.profile_tier1)
        self.assertEqual(recommender.score_profile["ticker"], "PRIME")

    def test_tier1_recommendation(self):
        recommender = Recommender(self.profile_tier1)
        rec = recommender.generate_recommendation()
        self.assertEqual(rec['recommendation_tier'], "Tier 1: Prime Candidate")
        self.assertIn("Strong fundamentals", rec['rationale'])
        self.assertIn("attractive or fair", rec['rationale'])

    def test_tier2a_recommendation(self):
        recommender = Recommender(self.profile_tier2a)
        rec = recommender.generate_recommendation()
        self.assertEqual(rec['recommendation_tier'], "Tier 2A: Monitor (Strong Co, High Price)")
        self.assertIn("Strong fundamentals", rec['rationale'])
        self.assertIn("valuation appears high", rec['rationale'])

    def test_tier2b_recommendation(self):
        recommender = Recommender(self.profile_tier2b)
        rec = recommender.generate_recommendation()
        self.assertEqual(rec['recommendation_tier'], "Tier 2B: Interesting (Fair Co, Good Price)")
        self.assertIn("Moderate fundamentals", rec['rationale'])
        self.assertIn("valuation is attractive", rec['rationale'])

    def test_tier3a_recommendation(self):
        recommender = Recommender(self.profile_tier3a)
        rec = recommender.generate_recommendation()
        self.assertEqual(rec['recommendation_tier'], "Tier 3A: Caution (Weak Fundamentals)")
        self.assertIn("Weakness identified", rec['rationale'])

    def test_tier3b_recommendation(self):
        # Test with Moderate valuation
        recommender_fair = Recommender(self.profile_tier3b_fair_price)
        rec_fair = recommender_fair.generate_recommendation()
        self.assertEqual(rec_fair['recommendation_tier'], "Tier 3B: Lower Priority (Fair Co, Fair/High Price)")
        self.assertIn("Moderate fundamentals", rec_fair['rationale'])
        self.assertIn("valuation that is not compelling", rec_fair['rationale'])

        # Test with Weak valuation
        recommender_high = Recommender(self.profile_tier3b_high_price)
        rec_high = recommender_high.generate_recommendation()
        self.assertEqual(rec_high['recommendation_tier'], "Tier 3B: Lower Priority (Fair Co, Fair/High Price)")
        self.assertIn("Moderate fundamentals", rec_high['rationale'])
        self.assertIn("valuation that is not compelling", rec_high['rationale'])


    def test_tier4_recommendation(self):
        recommender = Recommender(self.profile_tier4)
        rec = recommender.generate_recommendation()
        self.assertEqual(rec['recommendation_tier'], "Tier 4: Undetermined (Incomplete Data)")
        self.assertIn("Key fundamental data is missing", rec['rationale'])

    def test_empty_and_malformed_profile(self):
        recommender_empty = Recommender(self.profile_empty)
        rec_empty = recommender_empty.generate_recommendation()
        self.assertEqual(rec_empty['recommendation_tier'], "Undetermined")
        self.assertIn("Score profile is empty", rec_empty['rationale'])

        recommender_no_scores = Recommender(self.profile_no_scores_key)
        rec_no_scores = recommender_no_scores.generate_recommendation()
        self.assertEqual(rec_no_scores['recommendation_tier'], "Undetermined")
        self.assertIn("missing critical score data", rec_no_scores['rationale'])

    # Add more test methods for:
    # - Specific edge cases in score combinations.
    # - Impact of 'Undetermined' qualitative scores once they are actively used in logic.
    # - Testing the _get_overall_score helper more directly if its logic becomes complex.

if __name__ == '__main__':
    unittest.main()
```
