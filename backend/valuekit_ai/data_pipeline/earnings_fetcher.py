"""
FMP Earnings Call Transcripts Fetcher
Fetches earnings call transcripts for moat analysis
"""

import requests
from typing import Dict, List, Optional
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.api.fmp_api import get_api_key


class EarningsTranscriptFetcher:
    """Fetch earnings call transcripts from FMP API"""

    def __init__(self):
        self.api_key = get_api_key()
        self.base_url = "https://financialmodelingprep.com/api/v3"

    def get_latest_transcripts(
        self, ticker: str, limit: int = 4
    ) -> List[Dict[str, any]]:
        """
        Get latest earnings call transcripts

        Args:
            ticker: Stock ticker
            limit: Number of transcripts to fetch (default 4 = last 4 quarters)

        Returns:
            List of transcript data
        """
        print(f"  → Fetching earnings transcripts for {ticker}...")

        url = f"{self.base_url}/earning_call_transcript/{ticker}"
        params = {"apikey": self.api_key, "limit": limit}

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not data:
                print(f"  ⚠️  No transcripts found for {ticker}")
                return []

            print(f"  ✅ Found {len(data)} transcript(s)")
            return data

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error fetching transcripts: {e}")
            return []

    def extract_moat_relevant_sections(self, transcript_text: str) -> str:
        """
        Extract sections most relevant for moat analysis

        Focuses on:
        - Competitive positioning
        - Pricing power
        - Customer retention
        - Market share
        - Innovation/R&D

        Args:
            transcript_text: Full transcript text

        Returns:
            Filtered transcript with moat-relevant content
        """
        # Keywords that indicate moat-relevant discussion
        moat_keywords = [
            "competition",
            "competitive",
            "market share",
            "pricing power",
            "price increase",
            "margin",
            "customer retention",
            "churn",
            "switching cost",
            "brand",
            "loyalty",
            "network effect",
            "platform",
            "ecosystem",
            "moat",
            "advantage",
            "differentiation",
            "proprietary",
            "patent",
            "innovation",
            "r&d",
            "research and development",
            "barrier to entry",
        ]

        # Split into sentences/paragraphs
        lines = transcript_text.split("\n")

        relevant_sections = []
        context_buffer = []  # Keep some context around relevant sections

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Check if line contains moat keywords
            if any(keyword in line_lower for keyword in moat_keywords):
                # Add context: previous 2 lines + current + next 2 lines
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = "\n".join(lines[start:end])

                if context not in relevant_sections:
                    relevant_sections.append(context)

        if relevant_sections:
            filtered_text = "\n\n---\n\n".join(relevant_sections)
            print(
                f"     Filtered to {len(filtered_text):,} chars (from {len(transcript_text):,})"
            )
            return filtered_text
        else:
            # If no specific sections found, return full transcript (truncated)
            print(f"     No specific moat sections found, using full transcript")
            return transcript_text[:50000]  # Limit to 50k chars

    def parse_transcript_metadata(self, transcript: Dict) -> Dict[str, str]:
        """
        Parse transcript metadata from FMP response

        Args:
            transcript: Raw transcript dict from FMP API

        Returns:
            Cleaned metadata dict
        """
        return {
            "ticker": transcript.get("symbol", ""),
            "date": transcript.get("date", ""),
            "quarter": str(transcript.get("quarter", "")),
            "year": str(transcript.get("year", "")),
            "document_type": "earnings_call",
            "source": "FMP",
        }


def fetch_and_prepare_for_rag(
    ticker: str, limit: int = 4, filter_moat_content: bool = True
) -> List[Dict[str, any]]:
    """
    Fetch earnings transcripts and prepare for RAG ingestion
    Follows same pattern as sec_fetcher.py

    Args:
        ticker: Stock ticker
        limit: Number of transcripts (default 4 quarters)
        filter_moat_content: Whether to filter for moat-relevant sections

    Returns:
        List of documents ready for RAG in format:
        [
            {
                'text': str,
                'metadata': {
                    'ticker': str,
                    'document_type': 'earnings_call',
                    'date': str,
                    'quarter': str,
                    'year': str
                }
            }
        ]
    """
    fetcher = EarningsTranscriptFetcher()

    # Get transcripts from FMP
    raw_transcripts = fetcher.get_latest_transcripts(ticker, limit)

    if not raw_transcripts:
        return []

    documents = []

    for transcript in raw_transcripts:
        content = transcript.get("content", "")

        if not content:
            print(
                f"  ⚠️  Empty transcript for Q{transcript.get('quarter')} {transcript.get('year')}"
            )
            continue

        # Optional: Filter for moat-relevant content
        if filter_moat_content:
            content = fetcher.extract_moat_relevant_sections(content)

        # Parse metadata
        metadata = fetcher.parse_transcript_metadata(transcript)

        # Add to documents list
        documents.append({"text": content, "metadata": metadata})

        print(
            f"  ✅ Prepared: Q{metadata['quarter']} {metadata['year']} ({len(content):,} chars)"
        )

    return documents


def test_fetcher(ticker: str = "AAPL"):
    """Test the earnings fetcher"""
    print(f"\n{'=' * 70}")
    print(f"Testing Earnings Transcript Fetcher for {ticker}")
    print(f"{'=' * 70}\n")

    docs = fetch_and_prepare_for_rag(ticker, limit=2)

    print(f"\n{'=' * 70}")
    print(f"RESULT: Found {len(docs)} transcripts\n")

    for i, doc in enumerate(docs, 1):
        meta = doc["metadata"]
        print(f"{i}. Earnings Call Q{meta['quarter']} {meta['year']}")
        print(f"   Date: {meta['date']}")
        print(f"   Length: {len(doc['text']):,} characters")
        print(f"   Preview: {doc['text'][:300]}...")
        print()


if __name__ == "__main__":
    # Test the fetcher
    test_fetcher("AAPL")
