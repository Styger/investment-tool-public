"""
Data Validator for Backtesting
Validates downloaded historical data quality
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.valuekit_ai.data.cache import get_cache_manager
from backend.backtesting.stock_universe import get_universe


class DataValidator:
    """Validate historical data quality"""

    def __init__(self):
        self.cache = get_cache_manager()
        self.validation_results = []

    def validate_ticker(
        self,
        ticker: str,
        from_date: datetime,
        to_date: datetime,
        min_days: int = 200,  # Minimum ~1 year of trading days
    ) -> Dict:
        """
        Validate data for single ticker

        Args:
            ticker: Stock ticker
            from_date: Expected start date
            to_date: Expected end date
            min_days: Minimum number of trading days required

        Returns:
            Validation result dict
        """
        result = {
            "ticker": ticker,
            "status": "UNKNOWN",
            "issues": [],
            "warnings": [],
            "days_count": 0,
            "missing_days": 0,
            "date_range": None,
        }

        # Check if data exists in cache
        cache_key = f"{ticker}_historical_{from_date.date()}_{to_date.date()}"
        df = self.cache.get(cache_key, "historical_prices")

        if df is None:
            result["status"] = "MISSING"
            result["issues"].append("No data in cache")
            return result

        # Check if DataFrame is valid
        if not isinstance(df, pd.DataFrame):
            result["status"] = "INVALID"
            result["issues"].append("Data is not a valid DataFrame")
            return result

        if len(df) == 0:
            result["status"] = "EMPTY"
            result["issues"].append("DataFrame is empty")
            return result

        # Basic stats
        result["days_count"] = len(df)
        result["date_range"] = (df.index.min().date(), df.index.max().date())

        # Check minimum days
        if len(df) < min_days:
            result["warnings"].append(f"Only {len(df)} days (expected >{min_days})")

        # Check required columns
        required_columns = ["open", "high", "low", "close", "volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            result["issues"].append(f"Missing columns: {', '.join(missing_columns)}")

        # Check for NaN values
        if df.isnull().any().any():
            nan_columns = df.columns[df.isnull().any()].tolist()
            result["warnings"].append(
                f"Contains NaN values in: {', '.join(nan_columns)}"
            )

        # Check for zeros in price columns
        price_columns = ["open", "high", "low", "close"]
        for col in price_columns:
            if col in df.columns and (df[col] == 0).any():
                result["warnings"].append(f"Contains zero values in {col}")

        # Check date gaps (only weekdays, account for holidays)
        if len(df) > 1:
            date_diffs = df.index.to_series().diff()
            # Gap > 7 days is suspicious (even with holidays)
            large_gaps = date_diffs[date_diffs > timedelta(days=7)]

            if len(large_gaps) > 0:
                result["warnings"].append(f"Found {len(large_gaps)} gaps >7 days")

        # Check date range coverage
        actual_start = df.index.min()
        actual_end = df.index.max()

        # Allow 5 days tolerance (holidays, weekends)
        if (from_date - actual_start).days > 5:
            result["warnings"].append(
                f"Start date mismatch: expected {from_date.date()}, got {actual_start.date()}"
            )

        if (actual_end - to_date).days > 5:
            result["warnings"].append(
                f"End date mismatch: expected {to_date.date()}, got {actual_end.date()}"
            )

        # Determine overall status
        if result["issues"]:
            result["status"] = "FAILED"
        elif result["warnings"]:
            result["status"] = "WARNING"
        else:
            result["status"] = "PASSED"

        return result

    def validate_universe(
        self, universe: List[str], from_date: datetime, to_date: datetime
    ) -> Dict:
        """
        Validate entire stock universe

        Args:
            universe: List of tickers
            from_date: Expected start date
            to_date: Expected end date

        Returns:
            Summary dict with all results
        """
        print("=" * 70)
        print("DATA VALIDATION")
        print(f"Period: {from_date.date()} to {to_date.date()}")
        print(f"Stocks: {len(universe)}")
        print("=" * 70)

        passed = []
        warnings_list = []
        failed = []

        for i, ticker in enumerate(universe, 1):
            print(f"\n[{i}/{len(universe)}] Validating {ticker}...", end=" ")

            result = self.validate_ticker(ticker, from_date, to_date)
            self.validation_results.append(result)

            if result["status"] == "PASSED":
                print(f"✅ PASSED ({result['days_count']} days)")
                passed.append(ticker)
            elif result["status"] == "WARNING":
                print(f"⚠️  WARNING ({result['days_count']} days)")
                warnings_list.append(ticker)
                for warning in result["warnings"]:
                    print(f"      - {warning}")
            else:
                print(f"❌ FAILED")
                failed.append(ticker)
                for issue in result["issues"]:
                    print(f"      - {issue}")

        # Summary
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        print(f"✅ Passed: {len(passed)}")
        print(f"⚠️  Warnings: {len(warnings_list)}")
        print(f"❌ Failed: {len(failed)}")
        print(f"📊 Total: {len(universe)}")
        print("=" * 70)

        if failed:
            print(f"\n❌ Failed tickers: {', '.join(failed)}")

        if warnings_list:
            print(f"\n⚠️  Warning tickers: {', '.join(warnings_list)}")

        # Success rate
        success_rate = (len(passed) / len(universe)) * 100
        print(f"\n📈 Success Rate: {success_rate:.1f}%")

        return {
            "passed": passed,
            "warnings": warnings_list,
            "failed": failed,
            "success_rate": success_rate,
            "details": self.validation_results,
        }

    def generate_report(self, output_file: Optional[str] = None):
        """
        Generate detailed validation report

        Args:
            output_file: Optional file path to save report
        """
        if not self.validation_results:
            print("No validation results available")
            return

        report = []
        report.append("=" * 70)
        report.append("DETAILED VALIDATION REPORT")
        report.append("=" * 70)
        report.append("")

        for result in self.validation_results:
            ticker = result["ticker"]
            status = result["status"]

            # Status emoji
            emoji = {
                "PASSED": "✅",
                "WARNING": "⚠️",
                "FAILED": "❌",
                "MISSING": "🚫",
                "INVALID": "⛔",
                "EMPTY": "📭",
            }.get(status, "❓")

            report.append(f"{emoji} {ticker} - {status}")

            if result["days_count"] > 0:
                report.append(f"   Days: {result['days_count']}")
                report.append(
                    f"   Range: {result['date_range'][0]} to {result['date_range'][1]}"
                )

            if result["issues"]:
                report.append("   Issues:")
                for issue in result["issues"]:
                    report.append(f"      - {issue}")

            if result["warnings"]:
                report.append("   Warnings:")
                for warning in result["warnings"]:
                    report.append(f"      - {warning}")

            report.append("")

        report_text = "\n".join(report)

        # Print to console
        print(report_text)

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_text)

            print(f"\n💾 Report saved to: {output_path}")


def validate_downloaded_data(
    universe_name: str = "test_5", from_year: int = 2020, to_year: int = 2023
):
    """
    Convenient function to validate downloaded data

    Args:
        universe_name: Name of universe to validate
        from_year: Start year
        to_year: End year
    """
    # Get universe
    universe = get_universe(universe_name)

    # Create dates
    from_date = datetime(from_year, 1, 1)
    to_date = datetime(to_year, 12, 31)

    # Validate
    validator = DataValidator()
    results = validator.validate_universe(universe, from_date, to_date)

    # Generate detailed report
    report_file = f"backend/backtesting/results/validation_report_{universe_name}.txt"
    validator.generate_report(report_file)

    return results


if __name__ == "__main__":
    # Validate TEST_UNIVERSE_5 (that we downloaded earlier)
    print("Validating TEST_UNIVERSE_5...\n")

    results = validate_downloaded_data(
        universe_name="test_5", from_year=2020, to_year=2023
    )

    print(f"\n✅ Validation complete!")

    # Print quick stats
    if results["success_rate"] == 100:
        print("🎉 All data passed validation!")
    elif results["success_rate"] >= 90:
        print("👍 Most data passed validation")
    else:
        print("⚠️  Some issues found - check report")
