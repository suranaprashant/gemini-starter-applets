import re
import pandas as pd # Though not used extensively in this initial version

def clean_numerical_value(value_str):
    """
    Cleans a string representation of a financial value.
    Removes '$', ','. Handles parentheses for negatives.
    Converts 'M' for millions, 'B' for billions.
    Returns float or None if conversion fails.
    """
    if not isinstance(value_str, str):
        return None

    value_str = value_str.strip()
    if not value_str or value_str.lower() in ['n/a', '-', 'none', '']:
        return None

    # Handle parentheses for negative numbers
    is_negative = False
    if value_str.startswith('(') and value_str.endswith(')'):
        is_negative = True
        value_str = value_str[1:-1]

    # Remove currency symbols and commas
    value_str = value_str.replace('$', '').replace(',', '')

    multiplier = 1
    if value_str.endswith('M'):
        multiplier = 1_000_000
        value_str = value_str[:-1]
    elif value_str.endswith('B'):
        multiplier = 1_000_000_000
        value_str = value_str[:-1]
    # Add K for thousands if necessary
    elif value_str.endswith('K'):
        multiplier = 1_000
        value_str = value_str[:-1]

    try:
        numerical_value = float(value_str)
        if is_negative:
            numerical_value *= -1
        return numerical_value * multiplier
    except ValueError:
        return None

class DataExtractor:
    # Basic line item maps - these will need to be expanded significantly
    INCOME_STATEMENT_MAP = {
        "total_revenue": ["revenue", "total revenues", "sales", "total sales", "net revenue", "net sales"],
        "cost_of_revenue": ["cost of revenue", "cost of sales", "cost of goods sold"],
        "gross_profit": ["gross profit", "gross margin"],
        "operating_income": ["operating income", "income from operations", "operating earnings"],
        "net_income": ["net income", "net earnings", "net profit"],
    }

    BALANCE_SHEET_MAP = {
        "total_assets": ["total assets"],
        "total_liabilities": ["total liabilities"],
        "total_equity": ["total stockholders' equity", "total equity", "shareholders' equity"],
        "cash_and_cash_equivalents": ["cash and cash equivalents", "cash"],
        "current_assets": ["total current assets"],
        "current_liabilities": ["total current liabilities"],
    }

    CASH_FLOW_MAP = {
        "cash_flow_from_operations": ["net cash provided by operating activities", "cash flow from operating activities", "net cash from operations"],
        "capital_expenditures": ["capital expenditures", "purchase of property and equipment", "payments for property, plant and equipment"],
        "free_cash_flow": ["free cash flow"], # Typically calculated, not directly stated
    }

    def __init__(self, parsed_data):
        self.parsed_data = parsed_data if parsed_data else {}

    def _find_line_item_value(self, statement_data, item_keywords, statement_name="statement"):
        """
        Finds a specific line item in a parsed financial statement (list of lists).
        It tries to find the value in the next non-empty cell in the same row.
        If multiple value columns exist, it often prefers the first one (latest period).
        """
        if not statement_data or not isinstance(statement_data, list) or not item_keywords:
            return None

        # print(f"Debug: Searching for {item_keywords} in {statement_name}")

        for row_index, row in enumerate(statement_data):
            if not row or not isinstance(row, list) or not row[0]:
                continue

            description_cell = str(row[0]).lower().strip()
            # print(f"Debug: Row {row_index} Description: '{description_cell}'")


            for keyword in item_keywords:
                # Using regex for more flexible matching (e.g., whole word, case-insensitive)
                # \b for word boundary
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, description_cell):
                    # Keyword matched. Try to find a numerical value in the subsequent cells.
                    # print(f"Debug: Keyword '{keyword}' matched in '{description_cell}'")
                    for i in range(1, len(row)): # Start from the cell after description
                        value_str = row[i]
                        # print(f"Debug: Trying cell {i}: '{value_str}'")
                        cleaned_value = clean_numerical_value(value_str)
                        if cleaned_value is not None:
                            # print(f"Debug: Found and cleaned value: {cleaned_value}")
                            return cleaned_value
                    # print(f"Debug: Keyword matched for '{keyword}', but no parsable numeric value found in row: {row}")
                    return None # Found keyword but no value in that row that could be cleaned

        # print(f"Debug: Keywords {item_keywords} not found in {statement_name}")
        return None

    def process_income_statement(self):
        income_statement_data = self.parsed_data.get('income_statement')
        if not income_statement_data or not isinstance(income_statement_data, list):
            return {"error": "Income statement data not found or invalid format."}

        extracted_items = {}
        for key, keywords in self.INCOME_STATEMENT_MAP.items():
            value = self._find_line_item_value(income_statement_data, keywords, "Income Statement")
            extracted_items[key] = value

        return extracted_items

    def process_balance_sheet(self):
        balance_sheet_data = self.parsed_data.get('balance_sheet')
        if not balance_sheet_data or not isinstance(balance_sheet_data, list):
            return {"error": "Balance sheet data not found or invalid format."}

        extracted_items = {}
        for key, keywords in self.BALANCE_SHEET_MAP.items():
            value = self._find_line_item_value(balance_sheet_data, keywords, "Balance Sheet")
            extracted_items[key] = value

        return extracted_items


    def process_cash_flow_statement(self):
        cash_flow_data = self.parsed_data.get('cash_flow_statement')
        if not cash_flow_data or not isinstance(cash_flow_data, list):
            return {"error": "Cash flow statement data not found or invalid format."}

        extracted_items = {}
        for key, keywords in self.CASH_FLOW_MAP.items():
            value = self._find_line_item_value(cash_flow_data, keywords, "Cash Flow Statement")
            extracted_items[key] = value

        return extracted_items

    def extract_data(self):
        """
        Consolidates data from parsed sections and processed financial statements.
        """
        if not self.parsed_data:
            return {"error": "Parsed data is empty."}

        consolidated_data = {
            "ticker": self.parsed_data.get("ticker", "N/A"),
            "filing_type": self.parsed_data.get("filing_type", "N/A"),
            "period_of_report": self.parsed_data.get("period_of_report", "N/A"),
            "business_description_text": self.parsed_data.get('business_description', "Not found."),
            "md_and_a_text": self.parsed_data.get('md_and_a', "Not found."),
            "risk_factors_text": self.parsed_data.get('risk_factors', "Not found."),
            "income_statement_extracted": self.process_income_statement(),
            "balance_sheet_extracted": self.process_balance_sheet(),
            "cash_flow_statement_extracted": self.process_cash_flow_statement(),
        }
        return consolidated_data

if __name__ == '__main__':
    # Sample parsed_data mimicking SECParser output
    sample_parsed_data = {
        "ticker": "SAMPLE",
        "filing_path": "dummy_path/sample_10k.html",
        "filing_type": "10-K",
        "period_of_report": "December 31, 2023",
        "business_description": "This is a sample business description...",
        "md_and_a": "This is a sample MD&A section...",
        "risk_factors": "These are sample risk factors...",
        "income_statement": [
            ["Description", "2023", "2022"],
            ["Total Revenue", "$1,000.5M", "$900M"],
            ["Cost of Revenue", "600M", "500M"],
            ["Gross Profit", "400.5M", "400M"],
            ["Operating Expenses", "150M", "140M"],
            ["Net Income", "(50.25M)", "$60M"] # Negative value example
        ],
        "balance_sheet": [
            ["Description", "Dec 31, 2023", "Dec 31, 2022"],
            ["Total Assets", "2,000B", "1,800B"],
            ["Total Liabilities", "1,200B", "1,100B"],
            ["Total Stockholders' Equity", "800B", "700B"]
        ],
        "cash_flow_statement": [
            ["Description", "Year Ended Dec 31, 2023"],
            ["Net cash provided by operating activities", "120M"],
            ["Capital Expenditures", "(30M)"], # Negative value
            ["Other stuff", "10"] # No M or B
        ],
    }

    print("--- Testing clean_numerical_value ---")
    test_values = ["$1,000.5M", "(50.25M)", "600B", "N/A", "-", "  ", "123.45K", "(100)"]
    for tv in test_values:
        print(f"'{tv}' -> {clean_numerical_value(tv)}")
    print("--- End clean_numerical_value Test ---\n")

    extractor = DataExtractor(sample_parsed_data)
    extracted_data = extractor.extract_data()

    print("\n--- Extracted Data ---")
    for key, value in extracted_data.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {str(value)[:200] + '...' if isinstance(value, str) and len(value) > 200 else value}")
    print("--- End of Extracted Data ---")

    print("\n--- Testing with missing/invalid data ---")
    extractor_empty = DataExtractor({})
    print(f"Empty parsed data: {extractor_empty.extract_data()}")

    extractor_no_income = DataExtractor({"ticker": "NOINC"})
    print(f"No income statement: {extractor_no_income.extract_data()['income_statement_extracted']}")

    extractor_malformed_income = DataExtractor({
        "ticker": "BADINC",
        "income_statement": "This is not a list"
    })
    print(f"Malformed income statement: {extractor_malformed_income.extract_data()['income_statement_extracted']}")

    extractor_income_no_match = DataExtractor({
        "ticker": "NOMATCH",
        "income_statement": [["Random data", "123"], ["More random", "456"]]
    })
    no_match_result = extractor_income_no_match.extract_data()['income_statement_extracted']
    print(f"Income statement no match: {no_match_result}")


    # Test _find_line_item_value more directly
    print("\n--- Direct test of _find_line_item_value ---")
    test_statement = [
            ["Description", "2023", "2022"],
            ["Total Sales", "$1,000.5M", "$900M"],
            ["  Net Income (Loss) ", "  (50.25M)  ", "$60M"]
        ]
    keywords_revenue = DataExtractor.INCOME_STATEMENT_MAP["total_revenue"]
    keywords_net_income = DataExtractor.INCOME_STATEMENT_MAP["net_income"]

    found_revenue = extractor._find_line_item_value(test_statement, keywords_revenue, "Test Revenue")
    print(f"Searching for {keywords_revenue}, Found: {found_revenue}")

    found_net_income = extractor._find_line_item_value(test_statement, keywords_net_income, "Test Net Income")
    print(f"Searching for {keywords_net_income}, Found: {found_net_income}")

    keywords_fake = ["non existent item"]
    found_fake = extractor._find_line_item_value(test_statement, keywords_fake, "Test Fake")
    print(f"Searching for {keywords_fake}, Found: {found_fake}")

    # Test with a row that has keyword but no valid number
    test_statement_no_num = [["Net Income", "See Note 1"]]
    found_no_num = extractor._find_line_item_value(test_statement_no_num, keywords_net_income, "Test No Num")
    print(f"Searching for {keywords_net_income} in data with no number, Found: {found_no_num}")

    # Test with a row that has keyword but empty string as number
    test_statement_empty_str_num = [["Net Income", ""]]
    found_empty_str_num = extractor._find_line_item_value(test_statement_empty_str_num, keywords_net_income, "Test Empty Str Num")
    print(f"Searching for {keywords_net_income} in data with empty string number, Found: {found_empty_str_num}")

    # Test with only description, no value columns
    test_statement_only_desc = [["Net Income"]]
    found_only_desc = extractor._find_line_item_value(test_statement_only_desc, keywords_net_income, "Test Only Desc")
    print(f"Searching for {keywords_net_income} in data with only description, Found: {found_only_desc}")

    print("--- End of Direct _find_line_item_value Test ---")
