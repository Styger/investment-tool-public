"""
Historical Data Download Script
Download and cache historical price data for backtesting
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import time

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.backtesting.stock_universe import get_universe
from backend.backtesting.backtest_poc import fetch_fmp_historical_data
from backend.valuekit_ai.data.cache import get_cache_manager


class HistoricalDataDownloader:
    """Download historical data for multiple stocks"""

    def __init__(self, from_date: datetime, to_date: datetime):
        """
        Initialize downloader

        Args:
            from_date: Start date
            to_date: End date
        """
        self.from_date = from_date
        self.to_date = to_date
        self.cache = get_cache_manager()

        # Results tracking
        self.successful = []
        self.failed = []
        self.skipped = []

    def download_ticker(self, ticker: str, retry: int = 3) -> bool:
        """
        Download data for single ticker with retry logic

        Args:
            ticker: Stock ticker
            retry: Number of retries on failure

        Returns:
            True if successful, False otherwise
        """
        # Check if already cached
        cache_key = f"{ticker}_historical_{self.from_date.date()}_{self.to_date.date()}"

        cached_data = self.cache.get(cache_key, "historical_prices")
        if cached_data is not None:
            print(f"   ✅ {ticker}: Already cached")
            self.skipped.append(ticker)
            return True

        # Download with retry
        for attempt in range(retry):
            try:
                print(f"   📥 {ticker}: Downloading... (attempt {attempt + 1}/{retry})")

                df = fetch_fmp_historical_data(ticker, self.from_date, self.to_date)

                if df is None or len(df) == 0:
                    print(f"   ⚠️  {ticker}: No data returned")
                    continue

                # Cache the data
                self.cache.set(cache_key, "historical_prices", df)

                print(f"   ✅ {ticker}: Success ({len(df)} days)")
                self.successful.append(ticker)
                return True

            except Exception as e:
                print(f"   ❌ {ticker}: Error - {str(e)}")
                if attempt < retry - 1:
                    time.sleep(2)  # Wait before retry
                    continue
                else:
                    self.failed.append(ticker)
                    return False

        return False

    def download_universe(self, universe: List[str], delay: float = 0.5) -> Dict:
        """
        Download data for entire universe

        Args:
            universe: List of tickers
            delay: Delay between requests (seconds) to avoid rate limits

        Returns:
            Summary dict
        """
        print("=" * 70)
        print(f"HISTORICAL DATA DOWNLOAD")
        print(f"Period: {self.from_date.date()} to {self.to_date.date()}")
        print(f"Stocks: {len(universe)}")
        print("=" * 70)

        start_time = time.time()

        for i, ticker in enumerate(universe, 1):
            print(f"\n[{i}/{len(universe)}] Processing {ticker}...")

            self.download_ticker(ticker)

            # Delay to avoid rate limits (except for last ticker)
            if i < len(universe):
                time.sleep(delay)

        elapsed = time.time() - start_time

        # Summary
        print("\n" + "=" * 70)
        print("DOWNLOAD SUMMARY")
        print("=" * 70)
        print(f"✅ Successful: {len(self.successful)}")
        print(f"⏭️  Skipped (cached): {len(self.skipped)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"⏱️  Time: {elapsed:.1f}s")
        print("=" * 70)

        if self.failed:
            print(f"\n❌ Failed tickers: {', '.join(self.failed)}")

        return {
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "total_time": elapsed,
        }


def download_for_backtesting(
    universe_name: str = "test_10", from_year: int = 2015, to_year: int = 2025
):
    """
    Convenient function to download data for backtesting

    Args:
        universe_name: Name of universe ('test_5', 'test_10', 'sp_100', 'russell_100')
        from_year: Start year
        to_year: End year
    """
    # Get universe
    universe = get_universe(universe_name)

    # Create dates
    from_date = datetime(from_year, 1, 1)
    to_date = datetime(to_year, 12, 31)

    # Download
    downloader = HistoricalDataDownloader(from_date, to_date)
    results = downloader.download_universe(universe)

    return results


if __name__ == "__main__":
    # Test with small universe first
    print("Testing with TEST_UNIVERSE_5...")
    results = download_for_backtesting(
        universe_name="test_5", from_year=2020, to_year=2023
    )

    print(f"\n✅ Download complete!")
    print(f"Cache stats: {get_cache_manager().get_stats()}")
