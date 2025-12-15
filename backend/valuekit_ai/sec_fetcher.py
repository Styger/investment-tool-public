"""
SEC Edgar Data Fetcher - Using sec-edgar-downloader library
Reliable way to fetch 10-K filings
"""

from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup
import os
import re
from typing import Dict, List, Optional
from pathlib import Path
import shutil
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class SECEdgarFetcher:
    """Fetch financial documents from SEC Edgar using reliable library"""

    def __init__(
        self, company_name: str = "ValueKit", email: str = "jonas@valuekit.com"
    ):
        """
        Initialize SEC Edgar fetcher

        Args:
            company_name: Your company name
            email: Contact email (required by SEC)
        """
        # Store current directory and create data directory
        self.original_dir = Path.cwd()

        # Hard-code path to backend/ai/data/sec-filings
        # This ensures files are always saved in the correct location
        self.data_dir = self.original_dir / "backend" / "ai" / "data" / "sec-filings"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        print(f"  📁 SEC files will be saved to: {self.data_dir}")

        # Initialize downloader
        self.dl = Downloader(company_name, email)
        self.temp_dir = Path("./sec_temp")

    def cleanup_temp(self):
        """Clean up temporary download directory"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def get_latest_10k_file(self, ticker: str) -> Optional[Path]:
        """
        Download latest 10-K and return file path

        Args:
            ticker: Stock ticker

        Returns:
            Path to downloaded file or None
        """
        try:
            print(f"     Calling downloader API...")

            # Download to current directory (creates sec-edgar-filings/ in cwd)
            self.dl.get("10-K", ticker, limit=1)

            print(f"     Looking for downloaded files...")

            # Files are downloaded to: sec-edgar-filings/TICKER/10-K/...
            # Just read from there directly instead of moving
            search_dir = Path("sec-edgar-filings") / ticker / "10-K"

            if not search_dir.exists():
                print(f"  ❌ Download directory not found: {search_dir}")
                return None

            print(f"     Found directory: {search_dir}")

            # Find the most recent filing
            filing_dirs = sorted(search_dir.iterdir(), reverse=True)
            if not filing_dirs:
                print(f"  ❌ No filings found in {search_dir}")
                return None

            print(f"     Found {len(filing_dirs)} filing(s)")

            # Look for primary document (usually primary-document.html or filing-details.html)
            latest_dir = filing_dirs[0]
            print(f"     Latest filing dir: {latest_dir.name}")

            # Try to find the main document file
            # sec-edgar-downloader downloads .txt files, not .html
            txt_files = list(latest_dir.glob("*.txt"))

            if not txt_files:
                # Fallback: try HTML files
                html_files = list(latest_dir.glob("*.htm*"))
                if not html_files:
                    print(f"  ❌ No TXT or HTML files found in {latest_dir}")
                    # List what we actually have
                    all_files = list(latest_dir.glob("*"))
                    print(f"     Files found: {[f.name for f in all_files]}")
                    return None
                txt_files = html_files

            print(f"     Found {len(txt_files)} document file(s)")

            # Usually the file named "full-submission.txt" is what we want
            # Otherwise, take the largest file
            main_file = None
            for f in txt_files:
                if "full-submission" in f.name.lower():
                    main_file = f
                    break

            if not main_file:
                main_file = max(txt_files, key=lambda f: f.stat().st_size)

            print(
                f"     Selected file: {main_file.name} ({main_file.stat().st_size:,} bytes)"
            )

            return main_file

        except Exception as e:
            print(f"  ❌ Error downloading 10-K: {e}")
            import traceback

            traceback.print_exc()
            return None

    def extract_text_from_html(self, file_path: Path) -> str:
        """
        Extract clean text from HTML filing

        Args:
            file_path: Path to HTML file

        Returns:
            Cleaned text
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            print(f"  ❌ Error extracting text: {e}")
            return ""

    def extract_section(
        self, text: str, section_patterns: List[str], end_patterns: List[str]
    ) -> Optional[str]:
        """
        Extract a specific section from filing text

        Args:
            text: Full filing text
            section_patterns: Regex patterns to find section start
            end_patterns: Regex patterns to find section end

        Returns:
            Extracted section text or None
        """
        text_upper = text.upper()

        # Find start
        start_pos = -1
        for pattern in section_patterns:
            match = re.search(pattern, text_upper)
            if match:
                start_pos = match.start()
                break

        if start_pos == -1:
            return None

        # Find end
        end_pos = len(text)
        for pattern in end_patterns:
            match = re.search(
                pattern, text_upper[start_pos + 100 :]
            )  # Skip ahead a bit
            if match:
                end_pos = start_pos + 100 + match.start()
                break

        # Extract and clean
        section = text[start_pos:end_pos]

        # Limit length
        if len(section) > 20000:
            section = section[:20000] + "\n\n[Section truncated for length]"

        return section

    def get_latest_10k(self, ticker: str) -> Optional[Dict]:
        """
        Get latest 10-K with extracted sections

        Args:
            ticker: Stock ticker

        Returns:
            Dict with sections or None
        """
        print(f"  → Downloading 10-K for {ticker}...")

        file_path = self.get_latest_10k_file(ticker)

        if not file_path:
            return None

        print(f"  ✅ Downloaded to: {file_path.name}")
        print(f"  → Extracting text...")

        full_text = self.extract_text_from_html(file_path)

        if not full_text:
            return None

        print(f"  ✅ Extracted {len(full_text):,} characters")
        print(f"  → Parsing sections...")

        sections = {}

        # Item 1: Business
        sections["business"] = self.extract_section(
            full_text,
            [
                r"ITEM\s+1[\.\:\-\s]+BUSINESS",
                r"ITEM\s+1\b(?!\s*A)",  # Item 1 but not Item 1A
            ],
            [r"ITEM\s+1A", r"ITEM\s+2\b"],
        )

        # Item 1A: Risk Factors
        sections["risk_factors"] = self.extract_section(
            full_text,
            [r"ITEM\s+1A[\.\:\-\s]+RISK\s+FACTORS", r"ITEM\s+1A\b"],
            [r"ITEM\s+1B", r"ITEM\s+2\b"],
        )

        # Item 7: MD&A
        sections["mda"] = self.extract_section(
            full_text,
            [
                r"ITEM\s+7[\.\:\-\s]+MANAGEMENT",
                r"ITEM\s+7\b(?!\s*A)",
            ],
            [r"ITEM\s+7A", r"ITEM\s+8\b"],
        )

        found_sections = [k for k, v in sections.items() if v]
        print(
            f"  ✅ Extracted {len(found_sections)} sections: {', '.join(found_sections)}"
        )

        # Get filing date from directory name
        filing_date = (
            file_path.parent.name.split("-")[0]
            if "-" in file_path.parent.name
            else "unknown"
        )

        return {
            "ticker": ticker,
            "filing_date": filing_date,
            "file_path": str(file_path),
            "sections": sections,
        }


def fetch_and_prepare_for_rag(ticker: str) -> List[Dict[str, any]]:
    """
    Fetch SEC data and prepare it for RAG ingestion

    Args:
        ticker: Stock ticker

    Returns:
        List of documents ready for RAG
    """
    fetcher = SECEdgarFetcher()

    try:
        # Get latest 10-K with extracted sections
        filing_data = fetcher.get_latest_10k(ticker)

        if not filing_data:
            return []

        documents = []

        # Create a document for each extracted section
        section_names = {
            "business": "Business Description",
            "risk_factors": "Risk Factors",
            "mda": "Management Discussion & Analysis",
        }

        for section_key, section_text in filing_data["sections"].items():
            if section_text:
                documents.append(
                    {
                        "text": section_text,
                        "metadata": {
                            "company": ticker,
                            "ticker": ticker,
                            "document_type": "10-K",
                            "section": section_key,
                            "section_name": section_names.get(section_key, section_key),
                            "date": filing_data["filing_date"],
                        },
                    }
                )

        return documents

    finally:
        # Cleanup (optional - comment out if you want to keep files)
        # fetcher.cleanup_temp()
        pass


if __name__ == "__main__":
    # Test the fetcher
    ticker = "AAPL"
    print(f"Fetching SEC data for {ticker}...")
    print("=" * 60)

    docs = fetch_and_prepare_for_rag(ticker)

    print("\n" + "=" * 60)
    print(f"RESULT: Found {len(docs)} documents\n")

    for i, doc in enumerate(docs, 1):
        print(f"{i}. {doc['metadata']['section_name']}")
        print(f"   Date: {doc['metadata']['date']}")
        print(f"   Length: {len(doc['text']):,} characters")
        print(f"   Preview: {doc['text'][:200]}...")
        print()

    print("\n💡 Files downloaded to: sec-edgar-filings/")
    print("   (You can delete this folder after testing)")
