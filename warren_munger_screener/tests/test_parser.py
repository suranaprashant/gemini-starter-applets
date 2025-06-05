import unittest
import os
from ..app.sec_parser.parser import SECParser # Adjusted path

class TestSECParser(unittest.TestCase):
    def setUp(self):
        # Setup code, e.g., path to a dummy test filing for actual parsing tests
        self.dummy_html_content = """
        <html><head><title>Test 10-K</title></head>
        <body>
            <h1>Item 1. Business</h1><p>This is business.</p>
            <h1>Item 7. Management's Discussion and Analysis</h1><p>This is MD&A.</p>
        </body></html>
        """
        self.dummy_file_path = "test_dummy_filing.html"
        with open(self.dummy_file_path, 'w', encoding='utf-8') as f:
            f.write(self.dummy_html_content)
        # print(f"TestSECParser setUp: Created dummy file {self.dummy_file_path}")


    def tearDown(self):
        # Clean up dummy files
        if os.path.exists(self.dummy_file_path):
            os.remove(self.dummy_file_path)
            # print(f"TestSECParser tearDown: Removed dummy file {self.dummy_file_path}")

    def test_parser_initialization(self):
        # Test basic initialization of the parser
        parser = SECParser(ticker="DUMMY", filing_path=self.dummy_file_path)
        self.assertEqual(parser.ticker, "DUMMY")
        self.assertEqual(parser.filing_path, self.dummy_file_path)
        self.assertIsNone(parser.soup) # Soup should be None before load_filing

    def test_load_filing_success(self):
        # Test successful loading and parsing of a filing
        parser = SECParser(ticker="DUMMY", filing_path=self.dummy_file_path)
        self.assertTrue(parser.load_filing())
        self.assertIsNotNone(parser.soup)
        self.assertEqual(parser.soup.title.string, "Test 10-K")

    def test_load_filing_not_found(self):
        # Test handling of a non-existent file
        parser = SECParser(ticker="DUMMY", filing_path="non_existent_file.html")
        self.assertFalse(parser.load_filing()) # Should return False
        self.assertIsNone(parser.soup)

    # Add more test methods for:
    # - extract_text_section (various sections, section not found, complex structures)
    # - extract_financial_statements (mocked soup, finding different table formats)
    # - parse method orchestrating the calls and returning the correct dictionary structure
    # - Test with malformed HTML if robust parsing is expected.
    # - Test extraction of filing_type and period_of_report.

if __name__ == '__main__':
    unittest.main()
```
