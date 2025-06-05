# IMPORTANT: Replace "YOUR_API_KEY_HERE" with your actual Google API key.
# For production, manage API keys securely (e.g., environment variables).
GOOGLE_API_KEY = "YOUR_API_KEY_HERE"

# Configuration for Scoring Thresholds
# These are placeholders and should be refined based on investment strategy and market conditions.

SCORING_THRESHOLDS = {
    "profitability": {
        "roe_strong": 0.20,  # Return on Equity > 20% is Strong
        "roe_moderate": 0.15, # Return on Equity > 15% is Moderate
        "net_margin_strong": 0.15,  # Net Profit Margin > 15% is Strong
        "net_margin_moderate": 0.10, # Net Profit Margin > 10% is Moderate
        "operating_margin_strong": 0.20, # Operating Margin > 20% is Strong
        "operating_margin_moderate": 0.15, # Operating Margin > 15% is Moderate
        "gross_margin_strong": 0.40, # Gross Profit Margin > 40% is Strong
        "gross_margin_moderate": 0.30, # Gross Profit Margin > 30% is Moderate
    },
    "financial_health": {
        "debt_to_equity_low": 0.5,  # Debt-to-Equity < 0.5 is Low (Strong)
        "debt_to_equity_moderate": 1.0, # Debt-to-Equity < 1.0 is Moderate
        "current_ratio_strong": 2.0, # Current Ratio > 2.0 is Strong
        "current_ratio_moderate": 1.5, # Current Ratio > 1.5 is Moderate
    },
    "cash_flow": {
        "fcf_margin_strong": 0.10, # Free Cash Flow Margin > 10% is Strong
        "fcf_margin_moderate": 0.05, # Free Cash Flow Margin > 5% is Moderate
        "net_income_to_fcf_strong": 0.8, # FCF / Net Income > 80% is Strong
        "net_income_to_fcf_moderate": 0.6, # FCF / Net Income > 60% is Moderate
    },
    "valuation": { # Thresholds for considering a valuation attractive (lower is often better)
        "p_e_attractive": 15.0,
        "p_e_fair": 20.0,
        "p_b_attractive": 1.5,
        "p_b_fair": 2.5,
        "p_fcf_attractive": 15.0,
        "p_fcf_fair": 20.0,
    }
}
