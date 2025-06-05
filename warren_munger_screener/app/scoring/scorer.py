import os # For potential future use, not strictly needed now
from ..config import SCORING_THRESHOLDS # Assuming this import works based on directory structure

# --- Helper functions (redefined here for now to avoid import complexities) ---
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
    Safely divide two numbers. Returns None if denominator is zero or inputs are None or not numeric.
    """
    if numerator is None or denominator is None or \
       not isinstance(numerator, (int, float)) or \
       not isinstance(denominator, (int, float)):
        return None
    if denominator == 0:
        return None
    return numerator / denominator
# --- End of Helper functions ---

class Scorer:
    def __init__(self, analyzed_data, config=None):
        self.analyzed_data = analyzed_data if analyzed_data else {}
        self.config = config if config else SCORING_THRESHOLDS

    def _score_metric(self, value, strong_threshold, moderate_threshold, lower_is_better=False):
        if value is None:
            return "Undetermined"

        if not isinstance(value, (int, float)):
             return "Invalid Data" # Should ideally be caught earlier

        if lower_is_better:
            if value <= strong_threshold:
                return "Strong"
            elif value <= moderate_threshold:
                return "Moderate"
            else:
                return "Weak"
        else: # Higher is better
            if value >= strong_threshold:
                return "Strong"
            elif value >= moderate_threshold:
                return "Moderate"
            else:
                return "Weak"

    def _calculate_overall_score(self, scores_dict):
        """
        Calculates an overall score based on individual metric scores.
        Simple approach: returns the most conservative score (Weak > Moderate > Strong).
        If any is "Undetermined" or "Invalid Data", overall is "Undetermined".
        """
        if not scores_dict:
            return "Undetermined"

        scores_list = [score for score in scores_dict.values() if isinstance(score, str)]

        if not scores_list:
            return "Undetermined"

        if "Invalid Data" in scores_list or "Undetermined" in scores_list:
            # Prioritize showing if data is bad or missing for a component
            if "Invalid Data" in scores_list: return "Invalid Data"
            return "Undetermined"

        if "Weak" in scores_list:
            return "Weak"
        if "Moderate" in scores_list:
            return "Moderate"
        if "Strong" in scores_list:
            return "Strong"
        return "Undetermined" # Should not be reached if scores_list is populated


    def score_profitability(self):
        scores = {}
        profitability_ratios = safe_get(self.analyzed_data, ['profitability_ratios'], {})
        thresholds = safe_get(self.config, ['profitability'], {})

        roe = safe_get(profitability_ratios, ['return_on_equity'])
        scores['roe_score'] = self._score_metric(
            roe,
            safe_get(thresholds, ['roe_strong']),
            safe_get(thresholds, ['roe_moderate'])
        )

        net_margin = safe_get(profitability_ratios, ['net_profit_margin'])
        scores['net_margin_score'] = self._score_metric(
            net_margin,
            safe_get(thresholds, ['net_margin_strong']),
            safe_get(thresholds, ['net_margin_moderate'])
        )

        op_margin = safe_get(profitability_ratios, ['operating_margin'])
        scores['operating_margin_score'] = self._score_metric(
            op_margin,
            safe_get(thresholds, ['operating_margin_strong']),
            safe_get(thresholds, ['operating_margin_moderate'])
        )

        gross_margin = safe_get(profitability_ratios, ['gross_profit_margin'])
        scores['gross_margin_score'] = self._score_metric(
            gross_margin,
            safe_get(thresholds, ['gross_margin_strong']),
            safe_get(thresholds, ['gross_margin_moderate'])
        )

        scores['overall_profitability_score'] = self._calculate_overall_score({
            'roe': scores['roe_score'],
            'net_margin': scores['net_margin_score'],
            'operating_margin': scores['operating_margin_score'],
            'gross_margin': scores['gross_margin_score'],
        })
        return scores

    def score_financial_health(self):
        scores = {}
        health_ratios = safe_get(self.analyzed_data, ['financial_health_ratios'], {})
        thresholds = safe_get(self.config, ['financial_health'], {})

        debt_to_equity = safe_get(health_ratios, ['debt_to_equity_ratio'])
        scores['debt_to_equity_score'] = self._score_metric(
            debt_to_equity,
            safe_get(thresholds, ['debt_to_equity_low']), # Strong threshold for D/E (lower is better)
            safe_get(thresholds, ['debt_to_equity_moderate']), # Moderate threshold for D/E
            lower_is_better=True
        )

        current_ratio = safe_get(health_ratios, ['current_ratio'])
        scores['current_ratio_score'] = self._score_metric(
            current_ratio,
            safe_get(thresholds, ['current_ratio_strong']),
            safe_get(thresholds, ['current_ratio_moderate'])
        )

        scores['overall_financial_health_score'] = self._calculate_overall_score({
            'debt_to_equity': scores['debt_to_equity_score'],
            'current_ratio': scores['current_ratio_score'],
        })
        return scores

    def score_cash_flow(self):
        scores = {}
        cash_flow_metrics = safe_get(self.analyzed_data, ['cash_flow_metrics'], {})
        thresholds = safe_get(self.config, ['cash_flow'], {})

        fcf_margin = safe_get(cash_flow_metrics, ['fcf_margin'])
        scores['fcf_margin_score'] = self._score_metric(
            fcf_margin,
            safe_get(thresholds, ['fcf_margin_strong']),
            safe_get(thresholds, ['fcf_margin_moderate'])
        )

        net_income_to_fcf = safe_get(cash_flow_metrics, ['net_income_to_fcf_conversion'])
        scores['net_income_to_fcf_score'] = self._score_metric(
            net_income_to_fcf,
            safe_get(thresholds, ['net_income_to_fcf_strong']),
            safe_get(thresholds, ['net_income_to_fcf_moderate'])
        )

        scores['overall_cash_flow_score'] = self._calculate_overall_score({
             'fcf_margin': scores['fcf_margin_score'],
             'net_income_to_fcf': scores['net_income_to_fcf_score'],
        })
        return scores

    def score_qualitative_moat(self):
        # Placeholder for future implementation (e.g., using LLM analysis of text sections)
        return {'moat_score': 'Undetermined', 'moat_analysis': 'Qualitative moat analysis not yet implemented.'}

    def score_qualitative_management(self):
        # Placeholder for future implementation
        return {'management_score': 'Undetermined', 'management_analysis': 'Qualitative management analysis not yet implemented.'}

    def calculate_valuation_ratios(self, current_stock_price):
        valuation = {}
        if current_stock_price is None or current_stock_price <= 0:
            return {
                'p_e': None, 'p_b': None, 'p_fcf': None,
                'eps': None, 'book_value_per_share': None, 'fcf_per_share': None,
                'valuation_notes': "Current stock price not provided or invalid."
            }

        # EPS: net_income / shares_outstanding
        # BVPS: total_equity / shares_outstanding
        # FCFPS: free_cash_flow / shares_outstanding

        net_income = safe_get(self.analyzed_data, ['income_statement_extracted', 'net_income'])
        total_equity = safe_get(self.analyzed_data, ['balance_sheet_extracted', 'total_equity'])
        free_cash_flow = safe_get(self.analyzed_data, ['cash_flow_metrics', 'free_cash_flow'])

        # SHARES_OUTSTANDING needs to be part of analyzed_data.
        # Assuming it's added by DataExtractor or passed in. For now, let's add a placeholder here.
        # In a real scenario, DataExtractor should attempt to find this.
        shares_outstanding = safe_get(self.analyzed_data, ['shares_outstanding'])
        if shares_outstanding is None: # Fallback if not in analyzed_data directly
             shares_outstanding = safe_get(self.analyzed_data, ["income_statement_extracted",'shares_outstanding_basic']) or \
                                  safe_get(self.analyzed_data, ["income_statement_extracted",'shares_outstanding_diluted'])


        eps = safe_divide(net_income, shares_outstanding)
        book_value_per_share = safe_divide(total_equity, shares_outstanding)
        fcf_per_share = safe_divide(free_cash_flow, shares_outstanding)

        valuation['eps'] = eps
        valuation['book_value_per_share'] = book_value_per_share
        valuation['fcf_per_share'] = fcf_per_share

        valuation['p_e'] = safe_divide(current_stock_price, eps) if eps is not None and eps != 0 else None # Avoid division by zero for EPS=0
        valuation['p_b'] = safe_divide(current_stock_price, book_value_per_share) if book_value_per_share is not None and book_value_per_share != 0 else None
        valuation['p_fcf'] = safe_divide(current_stock_price, fcf_per_share) if fcf_per_share is not None and fcf_per_share != 0 else None

        if shares_outstanding is None:
            valuation['valuation_notes'] = "Shares outstanding not found, cannot calculate per-share ratios."
            valuation['p_e'] = valuation['p_b'] = valuation['p_fcf'] = None # Ensure these are None if shares missing

        return valuation

    def score_valuation(self, valuation_ratios):
        scores = {}
        thresholds = safe_get(self.config, ['valuation'], {})

        pe_ratio = safe_get(valuation_ratios, ['p_e'])
        scores['p_e_score'] = self._score_metric(
            pe_ratio,
            safe_get(thresholds, ['p_e_attractive']),
            safe_get(thresholds, ['p_e_fair']),
            lower_is_better=True
        )

        pb_ratio = safe_get(valuation_ratios, ['p_b'])
        scores['p_b_score'] = self._score_metric(
            pb_ratio,
            safe_get(thresholds, ['p_b_attractive']),
            safe_get(thresholds, ['p_b_fair']),
            lower_is_better=True
        )

        pfcf_ratio = safe_get(valuation_ratios, ['p_fcf'])
        scores['p_fcf_score'] = self._score_metric(
            pfcf_ratio,
            safe_get(thresholds, ['p_fcf_attractive']),
            safe_get(thresholds, ['p_fcf_fair']),
            lower_is_better=True
        )
        scores['overall_valuation_score'] = self._calculate_overall_score({
            'p_e': scores['p_e_score'],
            'p_b': scores['p_b_score'],
            'p_fcf': scores['p_fcf_score'],
        })
        return scores


    def generate_score_profile(self, current_stock_price=None):
        score_profile = {
            "ticker": safe_get(self.analyzed_data, ['ticker'], "N/A"),
            "period_of_report": safe_get(self.analyzed_data, ['period_of_report'], "N/A"),
            "scores": {},
            "qualitative_assessment": {},
            "valuation_metrics": {}
        }

        score_profile['scores']['profitability'] = self.score_profitability()
        score_profile['scores']['financial_health'] = self.score_financial_health()
        score_profile['scores']['cash_flow'] = self.score_cash_flow()

        score_profile['qualitative_assessment']['moat'] = self.score_qualitative_moat()
        score_profile['qualitative_assessment']['management'] = self.score_qualitative_management()

        if current_stock_price is not None:
            valuation_ratios = self.calculate_valuation_ratios(current_stock_price)
            score_profile['valuation_metrics'] = valuation_ratios
            score_profile['scores']['valuation'] = self.score_valuation(valuation_ratios)
        else:
            score_profile['valuation_metrics'] = {'notes': "Current stock price not provided for valuation."}
            score_profile['scores']['valuation'] = {'overall_valuation_score': 'Undetermined', 'notes': "Valuation not performed."}

        # Consolidate overall scores for a final summary
        final_summary_scores = {
            'profitability': score_profile['scores']['profitability']['overall_profitability_score'],
            'financial_health': score_profile['scores']['financial_health']['overall_financial_health_score'],
            'cash_flow': score_profile['scores']['cash_flow']['overall_cash_flow_score'],
            'valuation': score_profile['scores']['valuation']['overall_valuation_score'],
            'moat': score_profile['qualitative_assessment']['moat']['moat_score'],
            'management': score_profile['qualitative_assessment']['management']['management_score'],
        }
        score_profile['final_overall_score'] = self._calculate_overall_score(final_summary_scores)


        return score_profile

if __name__ == '__main__':
    # Sample analyzed_data (output from AnalysisEngine)
    sample_analyzed_data_strong = {
        "ticker": "STRONGCO",
        "period_of_report": "2023-12-31",
        "shares_outstanding": 100_000_000, # Added for valuation
        "income_statement_extracted": {"net_income": 25_000_000},
        "balance_sheet_extracted": {"total_equity": 100_000_000},
        "profitability_ratios": {
            "return_on_equity": 0.25, # Strong
            "net_profit_margin": 0.20, # Strong
            "operating_margin": 0.25, # Strong
            "gross_profit_margin": 0.50, # Strong
        },
        "financial_health_ratios": {
            "debt_to_equity_ratio": 0.4, # Strong (Low)
            "current_ratio": 2.5 # Strong
        },
        "cash_flow_metrics": {
            "fcf_margin": 0.15, # Strong
            "net_income_to_fcf_conversion": 0.9, # Strong
            "free_cash_flow": 22_500_000 # net_income * 0.9
        }
    }

    sample_analyzed_data_moderate = {
        "ticker": "MODERATECO",
        "period_of_report": "2023-12-31",
        "shares_outstanding": 50_000_000,
        "income_statement_extracted": {"net_income": 8_000_000},
        "balance_sheet_extracted": {"total_equity": 50_000_000},
        "profitability_ratios": {
            "return_on_equity": 0.16, # Moderate
            "net_profit_margin": 0.12, # Moderate
            "operating_margin": 0.17, # Moderate
            "gross_profit_margin": 0.35, # Moderate
        },
        "financial_health_ratios": {
            "debt_to_equity_ratio": 0.8, # Moderate
            "current_ratio": 1.7 # Moderate
        },
        "cash_flow_metrics": {
            "fcf_margin": 0.07, # Moderate
            "net_income_to_fcf_conversion": 0.7, # Moderate
            "free_cash_flow": 5_600_000
        }
    }

    sample_analyzed_data_weak_or_missing = {
        "ticker": "WEAKCO",
        "period_of_report": "2023-12-31",
        "shares_outstanding": 20_000_000,
        "income_statement_extracted": {"net_income": 1_000_000}, # Low net income
        "balance_sheet_extracted": {"total_equity": 20_000_000}, # Low equity base
        "profitability_ratios": {
            "return_on_equity": 0.05, # Weak
            "net_profit_margin": 0.03, # Weak
            "operating_margin": None, # Undetermined
            "gross_profit_margin": 0.10, # Weak
        },
        "financial_health_ratios": {
            "debt_to_equity_ratio": 2.5, # Weak
            "current_ratio": 0.8 # Weak
        },
        "cash_flow_metrics": {
            "fcf_margin": -0.02, # Weak
            "net_income_to_fcf_conversion": None, # Undetermined due to missing FCF or NI
            "free_cash_flow": -400_000
        }
    }

    current_stock_price_strongco = 30.0
    current_stock_price_moderateco = 10.0
    current_stock_price_weakco = 5.0

    print("--- Scoring Strong Company (STRONGCO) ---")
    scorer_strong = Scorer(sample_analyzed_data_strong)
    profile_strong = scorer_strong.generate_score_profile(current_stock_price=current_stock_price_strongco)
    import json # For pretty printing the dict
    print(json.dumps(profile_strong, indent=2))

    print("\n--- Scoring Moderate Company (MODERATECO) ---")
    scorer_moderate = Scorer(sample_analyzed_data_moderate)
    profile_moderate = scorer_moderate.generate_score_profile(current_stock_price=current_stock_price_moderateco)
    print(json.dumps(profile_moderate, indent=2))

    print("\n--- Scoring Weak/Missing Data Company (WEAKCO) ---")
    scorer_weak = Scorer(sample_analyzed_data_weak_or_missing)
    profile_weak = scorer_weak.generate_score_profile(current_stock_price=current_stock_price_weakco)
    print(json.dumps(profile_weak, indent=2))

    print("\n--- Scoring Weak/Missing Data Company (WEAKCO) - No Stock Price ---")
    profile_weak_no_price = scorer_weak.generate_score_profile() # No stock price
    print(json.dumps(profile_weak_no_price, indent=2))

    print("\n--- Scoring Empty Analyzed Data ---")
    scorer_empty = Scorer({})
    profile_empty = scorer_empty.generate_score_profile()
    print(json.dumps(profile_empty, indent=2))

    # Test case where shares_outstanding is missing
    sample_no_shares = sample_analyzed_data_strong.copy()
    del sample_no_shares['shares_outstanding']
    print("\n--- Scoring Strong Company (STRONGCO) - No Shares Outstanding ---")
    scorer_no_shares = Scorer(sample_no_shares)
    profile_no_shares = scorer_no_shares.generate_score_profile(current_stock_price=current_stock_price_strongco)
    print(json.dumps(profile_no_shares, indent=2))

```
