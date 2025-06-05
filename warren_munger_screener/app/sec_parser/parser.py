import os
import re
from bs4 import BeautifulSoup

class SECParser:
    def __init__(self, ticker, filing_path):
        self.ticker = ticker
        self.filing_path = filing_path
        self.soup = None

    def load_filing(self):
        """
        Reads the content of the HTML file and parses it with BeautifulSoup.
        """
        try:
            with open(self.filing_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.soup = BeautifulSoup(content, 'lxml')
            return True
        except FileNotFoundError:
            print(f"Error: File not found at {self.filing_path}")
            return False
        except Exception as e:
            print(f"Error loading or parsing file {self.filing_path}: {e}")
            return False

    def extract_text_section(self, section_keywords):
        """
        Extracts text content of a section based on keywords in headings.
        This is a very basic implementation and will need improvement.
        """
        if not self.soup:
            return None

        # Try to find headings (h1, h2, h3, h4, h5, h6) containing the keywords
        for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for header in self.soup.find_all(tag_name):
                header_text = header.get_text(strip=True).lower()
                if any(keyword.lower() in header_text for keyword in section_keywords):
                    # Found a potential header, now try to get subsequent text.
                    # This is naive: it takes all text in subsequent siblings until another header.
                    content = []
                    for sibling in header.find_next_siblings():
                        if sibling.name and sibling.name.startswith('h') and sibling.name[1].isdigit():
                            break  # Stop if we hit another major heading
                        if sibling.name == 'p' or sibling.name == 'div': # Common tags for text
                             # Get text, try to clean it up a bit
                            text = sibling.get_text(separator=' ', strip=True)
                            if text:
                                content.append(text)
                        elif sibling.string and sibling.string.strip(): # Text nodes
                            content.append(sibling.string.strip())

                    if content:
                        return "\n".join(content)
        return "Section not found or content extraction failed."

    def extract_financial_statements(self):
        """
        Attempts to find tables representing financial statements.
        This is a very basic placeholder.
        """
        if not self.soup:
            return None, None, None

        income_statement_table = None
        balance_sheet_table = None
        cash_flow_table = None

        # Keywords to identify financial statement tables
        income_keywords = ["income statement", "statement of earnings", "statement of operations"]
        balance_keywords = ["balance sheet", "statement of financial position"]
        cash_flow_keywords = ["cash flow statement", "statement of cash flows"]

        tables_data = {"income_statement": [], "balance_sheet": [], "cash_flow_statement": []}

        for table in self.soup.find_all('table'):
            # Look for titles in preceding siblings or within the table itself (e.g., in a <caption> or <thead>)
            caption_or_header_text = ""
            if table.caption:
                caption_or_header_text += table.caption.get_text(strip=True).lower()

            # Check few previous siblings for headings
            for prev_sibling in table.find_previous_siblings(limit=5):
                if prev_sibling.name and prev_sibling.name.startswith('h') and prev_sibling.name[1].isdigit():
                    caption_or_header_text += prev_sibling.get_text(strip=True).lower()
                    break
                if prev_sibling.name == 'p' and prev_sibling.b: # Often titles are in bold paragraphs
                     caption_or_header_text += prev_sibling.b.get_text(strip=True).lower()
                     break

            # Also check text directly before the table
            text_before_table = ""
            for i in range(1, 4): # Check up to 3 previous non-table, non-empty text nodes or specific tags
                prev = table.find_previous_sibling()
                if prev:
                    if prev.name == 'table': break
                    if prev.get_text(strip=True):
                        text_before_table = prev.get_text(strip=True).lower() + " " + text_before_table
                        if any(kw in text_before_table for kw in income_keywords + balance_keywords + cash_flow_keywords):
                            break
                    table = prev # move to the previous sibling to continue search upwards
                else:
                    break
            caption_or_header_text += text_before_table


            rows_list = []
            for row in table.find_all('tr'):
                cols = [ele.get_text(strip=True) for ele in row.find_all(['td', 'th'])]
                if any(cols): # Only add if row is not entirely empty
                    rows_list.append(cols)

            if not rows_list:
                continue

            current_table_type = None
            if any(keyword in caption_or_header_text for keyword in income_keywords):
                current_table_type = "income_statement"
            elif any(keyword in caption_or_header_text for keyword in balance_keywords):
                current_table_type = "balance_sheet"
            elif any(keyword in caption_or_header_text for keyword in cash_flow_keywords):
                current_table_type = "cash_flow_statement"

            if current_table_type and not tables_data[current_table_type]: # Take the first match for now
                tables_data[current_table_type] = rows_list


        return tables_data["income_statement"], tables_data["balance_sheet"], tables_data["cash_flow_statement"]

    def parse(self):
        """
        Main method to parse the filing.
        """
        if not self.load_filing():
            return None # Or raise an exception

        if not self.soup:
            return {"error": "BeautifulSoup object not initialized."}

        business_description = self.extract_text_section(["Business", "Overview"])
        md_and_a = self.extract_text_section(["Management's Discussion and Analysis", "MD&A"])
        risk_factors = self.extract_text_section(["Risk Factors"])

        income_statement, balance_sheet, cash_flow_statement = self.extract_financial_statements()

        # Placeholder for other data like filing_type, period_date
        # These would likely need more sophisticated regex or pattern matching on the document.
        filing_type = "Unknown" # e.g. 10-K, 10-Q
        period_of_report = "Unknown" # e.g. 2023-12-31

        # Try to find filing type and period from common patterns (very basic)
        # This is highly unreliable and just a placeholder
        if self.soup.title:
            title_text = self.soup.title.string.lower()
            if "10-k" in title_text:
                filing_type = "10-K"
            elif "10-q" in title_text:
                filing_type = "10-Q"

        # Search for common date patterns for period of report (extremely naive)
        # Example: "For the fiscal year ended December 31, 2023" or "For the quarterly period ended September 30, 2023"
        date_patterns = [
            r"for the fiscal year ended\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            r"for the quarterly period ended\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            r"period ended\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})"
        ]
        text_content_for_dates = self.soup.get_text()[:5000] # Search in first 5000 chars
        for pattern in date_patterns:
            match = re.search(pattern, text_content_for_dates, re.IGNORECASE)
            if match:
                period_of_report = match.group(1)
                break


        return {
            "ticker": self.ticker,
            "filing_path": self.filing_path,
            "filing_type": filing_type,
            "period_of_report": period_of_report,
            "business_description": business_description,
            "md_and_a": md_and_a,
            "risk_factors": risk_factors,
            "income_statement": income_statement if income_statement else "Not found or extraction failed.",
            "balance_sheet": balance_sheet if balance_sheet else "Not found or extraction failed.",
            "cash_flow_statement": cash_flow_statement if cash_flow_statement else "Not found or extraction failed.",
        }

if __name__ == '__main__':
    # This is for example usage/testing and will not be part of the module's production code.
    # To run this, you would need to:
    # 1. Create a dummy HTML file, e.g., "dummy_10k.html"
    # 2. Put some sample HTML structure in it, especially with headings and tables.

    # Create a dummy HTML file for testing
    dummy_html_content = """
    <html>
    <head><title>Test Company 10-K Filing</title></head>
    <body>
        <h1>Item 1. Business</h1>
        <p>This is the business description paragraph 1.</p>
        <p>This is the business description paragraph 2.</p>
        <h2>Another section</h2>
        <p>Some other text</p>
        <h1>Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations</h1>
        <p>This is the MD&A section.</p>
        <div>This is more MD&A in a div.</div>
        <h1>Item 1A. Risk Factors</h1>
        <p>These are the risk factors.</p>

        <h2>CONSOLIDATED STATEMENTS OF INCOME</h2>
        <table>
            <caption>Consolidated Statements of Earnings</caption>
            <tr><th>Revenue</th><th>2023</th><th>2022</th></tr>
            <tr><td>Net Sales</td><td>1000</td><td>900</td></tr>
            <tr><td>Cost of Sales</td><td>600</td><td>500</td></tr>
            <tr><td>Gross Profit</td><td>400</td><td>400</td></tr>
        </table>

        <p><b>Consolidated Balance Sheets</b></p>
        <table>
            <tr><th>Assets</th><th>2023</th><th>2022</th></tr>
            <tr><td>Cash</td><td>100</td><td>150</td></tr>
            <tr><td>Accounts Receivable</td><td>200</td><td>180</td></tr>
        </table>

        <p><b>CONSOLIDATED STATEMENTS OF CASH FLOWS</b></p>
        <table>
            <tr><th>Operating Activities</th><th>2023</th><th>2022</th></tr>
            <tr><td>Net Income</td><td>50</td><td>40</td></tr>
            <tr><td>Depreciation</td><td>10</td><td>8</td></tr>
        </table>
    </body>
    </html>
    """
    dummy_file_path = "dummy_10k.html"
    with open(dummy_file_path, 'w', encoding='utf-8') as f:
        f.write(dummy_html_content)

    print(f"Attempting to parse dummy file: {dummy_file_path}")
    # Note: Ticker is just a placeholder here
    parser = SECParser(ticker="DUMMY", filing_path=dummy_file_path)
    data = parser.parse()

    if data:
        print("\n--- Parsed Data ---")
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"{key}: {value[:100]}...")
            elif isinstance(value, list) and value:
                 print(f"{key}: {value[0] if value else 'Empty list'} ... (showing first item if list)")
            else:
                print(f"{key}: {value}")
        print("--- End of Parsed Data ---")
    else:
        print("Parsing failed.")

    # Clean up the dummy file
    if os.path.exists(dummy_file_path):
        os.remove(dummy_file_path)
        print(f"\nCleaned up dummy file: {dummy_file_path}")
