import json # For pretty printing in main

# --- Helper functions (redefined here for now) ---
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
# --- End of Helper functions ---

class Recommender:
    def __init__(self, score_profile):
        self.score_profile = score_profile if score_profile else {}

    def _get_overall_score(self, category_scores_dict, score_key_part="overall_", default_score='Undetermined'):
        """
        Safely gets an 'overall_...' score from a category dictionary.
        Example: category_scores_dict = {'roe_score': 'Strong', 'overall_profitability_score': 'Strong'}
                 score_key_part = 'overall_profitability' -> returns 'Strong'
        It looks for keys that contain the score_key_part.
        """
        if not isinstance(category_scores_dict, dict):
            return default_score

        # Find the specific overall score key (e.g. 'overall_profitability_score')
        target_key = None
        for key in category_scores_dict.keys():
            if score_key_part in key and key.endswith("_score"):
                target_key = key
                break

        if target_key:
            return category_scores_dict.get(target_key, default_score)
        return default_score


    def generate_recommendation(self):
        if not self.score_profile or not safe_get(self.score_profile, ['scores']):
            return {
                'recommendation_tier': 'Undetermined',
                'rationale': 'Score profile is empty or missing critical score data.'
            }

        scores = safe_get(self.score_profile, ['scores'], {})
        qualitative = safe_get(self.score_profile, ['qualitative_assessment'], {})
        valuation_metrics = safe_get(self.score_profile, ['valuation_metrics'], {}) # Raw ratios like P/E

        # Extract overall scores for key categories
        # The _get_overall_score helper expects the full dictionary for that category
        prof_score = self._get_overall_score(safe_get(scores, ['profitability'], {}), 'overall_profitability')
        fh_score = self._get_overall_score(safe_get(scores, ['financial_health'], {}), 'overall_financial_health')
        cf_score = self._get_overall_score(safe_get(scores, ['cash_flow'], {}), 'overall_cash_flow')
        val_score = self._get_overall_score(safe_get(scores, ['valuation'], {}), 'overall_valuation') # This is the score of valuation (e.g. Strong if P/E is attractive)

        # Qualitative scores (direct access as their structure is simpler)
        moat_score = safe_get(qualitative, ['moat', 'moat_score'], 'Undetermined')
        mgmt_score = safe_get(qualitative, ['management', 'management_score'], 'Undetermined')

        # Tier 1: Prime Candidate
        # - Strong fundamentals (profitability, financial health, cash flow)
        # - Moat & Management are at least Moderate (ideally Strong, but placeholders are Undetermined)
        # - Valuation is 'Strong' (meaning attractive, e.g. low P/E) or 'Moderate' (fair)

        is_strong_fundamentals = (prof_score == "Strong" and
                                  fh_score == "Strong" and
                                  cf_score == "Strong")

        is_acceptable_qualitative = True # For now, as moat/mgmt are placeholders
        # if moat_score in ["Weak"] or mgmt_score in ["Weak"]: # Once implemented
        #     is_acceptable_qualitative = False

        is_good_valuation = val_score in ["Strong", "Moderate"]

        if is_strong_fundamentals and is_acceptable_qualitative and is_good_valuation:
            return {
                'recommendation_tier': "Tier 1: Prime Candidate",
                'rationale': f"Strong fundamentals (Profitability: {prof_score}, Financial Health: {fh_score}, Cash Flow: {cf_score}). "
                             f"Qualitative aspects (Moat: {moat_score}, Management: {mgmt_score}) are acceptable. "
                             f"Valuation ({val_score}) is attractive or fair."
            }

        # Tier 2: Interesting - Monitor
        # - Strong fundamentals but valuation is 'Weak' (Overvalued).
        # - OR Moderate overall fundamentals but valuation is 'Strong' (Attractive).

        is_moderate_fundamentals = (prof_score in ["Strong", "Moderate"] and
                                    fh_score in ["Strong", "Moderate"] and
                                    cf_score in ["Strong", "Moderate"]) and \
                                   not is_strong_fundamentals # Not already Tier 1 strong

        if is_strong_fundamentals and is_acceptable_qualitative and val_score == "Weak":
            return {
                'recommendation_tier': "Tier 2A: Monitor (Strong Co, High Price)",
                'rationale': f"Strong fundamentals (Profitability: {prof_score}, Financial Health: {fh_score}, Cash Flow: {cf_score}) "
                             f"but current valuation ({val_score}) appears high. Monitor for better entry point."
            }

        if is_moderate_fundamentals and is_acceptable_qualitative and val_score == "Strong":
             return {
                'recommendation_tier': "Tier 2B: Interesting (Fair Co, Good Price)",
                'rationale': f"Moderate fundamentals (Profitability: {prof_score}, Financial Health: {fh_score}, Cash Flow: {cf_score}) "
                             f"but current valuation ({val_score}) is attractive. Further due diligence needed on fundamental strength."
            }

        # Tier 3: Lower Priority / Caution
        # - One or more 'Weak' fundamental scores.
        # - OR Moderate fundamentals and valuation is 'Weak' (Overvalued) or 'Moderate' (Fair but not compelling).

        has_weak_fundamental = "Weak" in [prof_score, fh_score, cf_score]

        if has_weak_fundamental:
            return {
                'recommendation_tier': "Tier 3A: Caution (Weak Fundamentals)",
                'rationale': f"Weakness identified in core fundamentals (Profitability: {prof_score}, Financial Health: {fh_score}, Cash Flow: {cf_score}). "
                             f"Valuation: {val_score}. Proceed with caution, further investigation required."
            }

        if is_moderate_fundamentals and is_acceptable_qualitative and val_score in ["Weak", "Moderate"]:
            return {
                'recommendation_tier': "Tier 3B: Lower Priority (Fair Co, Fair/High Price)",
                'rationale': f"Moderate fundamentals (Profitability: {prof_score}, Financial Health: {fh_score}, Cash Flow: {cf_score}) "
                             f"with a valuation ({val_score}) that is not compelling. Lower priority for investment."
            }

        # Tier 4: Red Flagged / Undetermined
        # - Many 'Undetermined' scores, or critical data missing.
        has_undetermined_fundamental = "Undetermined" in [prof_score, fh_score, cf_score]
        if has_undetermined_fundamental:
             return {
                'recommendation_tier': "Tier 4: Undetermined (Incomplete Data)",
                'rationale': f"Key fundamental data is missing or undetermined (Profitability: {prof_score}, Financial Health: {fh_score}, Cash Flow: {cf_score}). "
                             f"Cannot make a reliable recommendation."
            }

        # Fallback for any other combinations not explicitly caught
        return {
            'recommendation_tier': "Tier X: Review Manually",
            'rationale': f"The company's profile does not fit standard tiers. "
                         f"Scores - Profitability: {prof_score}, Health: {fh_score}, Cash Flow: {cf_score}, Valuation: {val_score}. "
                         f"Qualitative - Moat: {moat_score}, Management: {mgmt_score}. Manual review needed."
        }


if __name__ == '__main__':
    sample_profiles = []

    # Profile 1: Tier 1 - Strong fundamentals, Good Valuation
    sample_profiles.append({
        "ticker": "PRIME", "period_of_report": "2023-12-31",
        "scores": {
            "profitability": {"overall_profitability_score": "Strong"},
            "financial_health": {"overall_financial_health_score": "Strong"},
            "cash_flow": {"overall_cash_flow_score": "Strong"},
            "valuation": {"overall_valuation_score": "Strong"} # Attractive P/E, P/B
        },
        "qualitative_assessment": {
            "moat": {"moat_score": "Moderate"}, # Placeholder
            "management": {"management_score": "Moderate"} # Placeholder
        },
        "valuation_metrics": {"p_e": 12.0, "p_b": 1.2}
    })

    # Profile 2: Tier 2A - Strong fundamentals, Overvalued
    sample_profiles.append({
        "ticker": "GOODCO_HIGHPRICE", "period_of_report": "2023-12-31",
        "scores": {
            "profitability": {"overall_profitability_score": "Strong"},
            "financial_health": {"overall_financial_health_score": "Strong"},
            "cash_flow": {"overall_cash_flow_score": "Strong"},
            "valuation": {"overall_valuation_score": "Weak"} # e.g. P/E > 30
        },
        "qualitative_assessment": {"moat": {"moat_score": "Strong"}, "management": {"management_score": "Strong"}},
        "valuation_metrics": {"p_e": 35.0, "p_b": 4.0}
    })

    # Profile 3: Tier 2B - Moderate fundamentals, Attractive Valuation
    sample_profiles.append({
        "ticker": "FAIRCO_GOODPRICE", "period_of_report": "2023-12-31",
        "scores": {
            "profitability": {"overall_profitability_score": "Moderate"},
            "financial_health": {"overall_financial_health_score": "Moderate"},
            "cash_flow": {"overall_cash_flow_score": "Strong"}, # One strong can still be overall moderate
            "valuation": {"overall_valuation_score": "Strong"}
        },
        "qualitative_assessment": {"moat": {"moat_score": "Moderate"}, "management": {"management_score": "Moderate"}},
        "valuation_metrics": {"p_e": 10.0, "p_b": 1.0}
    })

    # Profile 4: Tier 3A - Weak fundamentals
    sample_profiles.append({
        "ticker": "WEAKFUND", "period_of_report": "2023-12-31",
        "scores": {
            "profitability": {"overall_profitability_score": "Weak"},
            "financial_health": {"overall_financial_health_score": "Moderate"},
            "cash_flow": {"overall_cash_flow_score": "Strong"},
            "valuation": {"overall_valuation_score": "Moderate"}
        },
        "qualitative_assessment": {"moat": {"moat_score": "Undetermined"}, "management": {"management_score": "Undetermined"}},
        "valuation_metrics": {"p_e": 18.0, "p_b": 2.0}
    })

    # Profile 5: Tier 3B - Moderate fundamentals, Fair/High Price
    sample_profiles.append({
        "ticker": "FAIRCO_FAIRPRICE", "period_of_report": "2023-12-31",
        "scores": {
            "profitability": {"overall_profitability_score": "Moderate"},
            "financial_health": {"overall_financial_health_score": "Moderate"},
            "cash_flow": {"overall_cash_flow_score": "Moderate"},
            "valuation": {"overall_valuation_score": "Moderate"} # Fair valuation
        },
        "qualitative_assessment": {"moat": {"moat_score": "Moderate"}, "management": {"management_score": "Moderate"}},
        "valuation_metrics": {"p_e": 22.0, "p_b": 2.2}
    })


    # Profile 6: Tier 4 - Undetermined fundamentals
    sample_profiles.append({
        "ticker": "UNKNOWN", "period_of_report": "2023-12-31",
        "scores": {
            "profitability": {"overall_profitability_score": "Undetermined"},
            "financial_health": {"overall_financial_health_score": "Strong"},
            "cash_flow": {"overall_cash_flow_score": "Moderate"},
            "valuation": {"overall_valuation_score": "Moderate"}
        },
        "qualitative_assessment": {"moat": {"moat_score": "Undetermined"}, "management": {"management_score": "Undetermined"}},
        "valuation_metrics": {}
    })

    # Profile 7: Empty score profile
    sample_profiles.append({})

    # Profile 8: Missing scores structure
    sample_profiles.append({"ticker": "NOSCORES"})


    for i, profile in enumerate(sample_profiles):
        print(f"\n--- Recommending for Profile {i+1} ({profile.get('ticker', 'N/A')}) ---")
        # print("Input Profile:")
        # print(json.dumps(profile, indent=2)) # Print the input for clarity

        recommender = Recommender(profile)
        recommendation = recommender.generate_recommendation()
        print("Recommendation Output:")
        print(json.dumps(recommendation, indent=2))

```
