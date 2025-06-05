import unittest
from ..app.data_extractor.extractor import DataExtractor, clean_numerical_value

class TestDataExtractor(unittest.TestCase):
    def setUp(self):
        # Sample parsed_data mimicking SECParser output
        self.sample_parsed_data = {
            "ticker": "SAMPLE",
            "filing_type": "10-K",
            "period_of_report": "December 31, 2023",
            "business_description": "Sample business description.",
            "md_and_a": "Sample MD&A.",
            "risk_factors": "Sample risk factors.",
            "income_statement": [
                ["Description", "2023", "2022"],
                ["Total Revenue", "$1,000.5M", "$900M"],
                ["Net Income", "(50.25M)", "$60M"]
            ],
            "balance_sheet": [
                ["Description", "Dec 31, 2023"],
                ["Total Assets", "2,000B"],
                ["Total Liabilities", "1,200B"]
            ],
            "cash_flow_statement": [
                ["Description", "Year Ended Dec 31, 2023"],
                ["Net cash provided by operating activities", "120M"]
            ],
        }
        self.extractor = DataExtractor(self.sample_parsed_data)

    def test_clean_numerical_value(self):
        self.assertEqual(clean_numerical_value("$1,000.5M"), 1000500000.0)
        self.assertEqual(clean_numerical_value("(50.25M)"), -50250000.0)
        self.assertEqual(clean_numerical_value("600B"), 600000000000.0)
        self.assertEqual(clean_numerical_value("123.45K"), 123450.0)
        self.assertEqual(clean_numerical_value("(100)"), -100.0)
        self.assertIsNone(clean_numerical_value("N/A"))
        self.assertIsNone(clean_numerical_value("-"))
        self.assertIsNone(clean_numerical_value("Invalid"))
        self.assertIsNone(clean_numerical_value(None)) # Test with None input
        self.assertIsNone(clean_numerical_value("  ")) # Test with empty string

    def test_extractor_initialization(self):
        self.assertEqual(self.extractor.parsed_data["ticker"], "SAMPLE")

    def test_process_income_statement(self):
        income_data = self.extractor.process_income_statement()
        self.assertEqual(income_data.get("total_revenue"), 1000500000.0)
        self.assertEqual(income_data.get("net_income"), -50250000.0)
        # Test for a key that should not be found
        self.assertIsNone(income_data.get("operating_income"))

    def test_process_balance_sheet(self):
        balance_sheet_data = self.extractor.process_balance_sheet()
        self.assertEqual(balance_sheet_data.get("total_assets"), 2000000000000.0)
        self.assertEqual(balance_sheet_data.get("total_liabilities"), 1200000000000.0)
        self.assertIsNone(balance_sheet_data.get("total_equity"))

    def test_process_cash_flow_statement(self):
        cash_flow_data = self.extractor.process_cash_flow_statement()
        self.assertEqual(cash_flow_data.get("cash_flow_from_operations"), 120000000.0)
        self.assertIsNone(cash_flow_data.get("capital_expenditures"))

    def test_extract_data_structure(self):
        extracted_data = self.extractor.extract_data()
        self.assertIn("ticker", extracted_data)
        self.assertIn("income_statement_extracted", extracted_data)
        self.assertIn("balance_sheet_extracted", extracted_data)
        self.assertIn("cash_flow_statement_extracted", extracted_data)
        self.assertEqual(extracted_data["income_statement_extracted"].get("total_revenue"), 1000500000.0)

    def test_find_line_item_value_variations(self):
        # Test with slight variations in naming and table structure
        test_statement = [
            ["  Total Sales  ", " $123.45 M "],
            ["Net earnings (loss)", " ( 10.0 B )"],
            ["  Random item not in map  ", "500K"]
        ]
        # Assuming "total_revenue" maps to "total sales" and "net_income" to "net earnings"
        revenue = self.extractor._find_line_item_value(test_statement, DataExtractor.INCOME_STATEMENT_MAP["total_revenue"], "Test IS")
        net_income = self.extractor._find_line_item_value(test_statement, DataExtractor.INCOME_STATEMENT_MAP["net_income"], "Test IS")

        self.assertEqual(revenue, 123450000.0)
        self.assertEqual(net_income, -10000000000.0)

    def test_empty_or_malformed_parsed_data(self):
        empty_extractor = DataExtractor({})
        self.assertEqual(empty_extractor.extract_data().get("ticker"), "N/A") # Should handle gracefully
        self.assertIsInstance(empty_extractor.extract_data().get("income_statement_extracted"), dict)

        malformed_extractor = DataExtractor({"income_statement": "not a list"})
        # Current implementation of process_income_statement returns an error dict
        self.assertIn("error", malformed_extractor.process_income_statement())


    # Add more test methods for:
    # - Handling of various table structures in _find_line_item_value.
    # - More comprehensive testing of all items in the maps.
    # - Cases with multiple value columns (e.g., ensuring it picks the correct period if specified).
    # - Line items that are sums of other items (future functionality).
    # - Impact of different encodings or special characters if files were read by parser.

if __name__ == '__main__':
    unittest.main()
```
