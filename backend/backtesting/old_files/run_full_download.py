"""
Full Universe Download Script
Interactive script to download large stock universes
"""

import sys
from pathlib import Path
from datetime import datetime

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.backtesting.download_historical_data import download_for_backtesting
from backend.backtesting.data_validator import validate_downloaded_data


def main():
    print("=" * 70)
    print("VALUEKIT BACKTESTING - FULL DATA DOWNLOAD")
    print("=" * 70)
    print()

    # Configuration
    print("📋 Configuration:")
    print("   Universe: SP_100 (100 stocks)")
    print("   Period: 2020-01-01 to 2023-12-31")
    print("   Strategy: Download missing, skip cached")
    print()

    # Confirmation
    response = input("Ready to start? (yes/no): ").strip().lower()

    if response != "yes":
        print("❌ Cancelled by user")
        return

    print("\n" + "=" * 70)
    print("PHASE 1: DOWNLOADING DATA")
    print("=" * 70)

    # Download
    results = download_for_backtesting(
        universe_name="sp_100", from_year=2020, to_year=2023
    )

    print("\n" + "=" * 70)
    print("PHASE 2: VALIDATING DATA")
    print("=" * 70)

    # Validate
    validation = validate_downloaded_data(
        universe_name="sp_100", from_year=2020, to_year=2023
    )

    # Final Summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Downloaded: {len(results['successful'])} stocks")
    print(f"Cached (skipped): {len(results['skipped'])} stocks")
    print(f"Failed: {len(results['failed'])} stocks")
    print(f"Validation Pass Rate: {validation['success_rate']:.1f}%")
    print("=" * 70)

    if validation["success_rate"] >= 95:
        print("\n🎉 MILESTONE 2 COMPLETE!")
        print("✅ 100 stocks ready for backtesting")
        print("✅ Data quality validated")
        print("✅ Ready for Milestone 3: ValueKit Strategy")
    elif validation["success_rate"] >= 90:
        print("\n👍 Download mostly successful")
        print("⚠️  Some minor issues - check validation report")
    else:
        print("\n⚠️  Some issues detected")
        print("📄 Check validation report for details")
        if results["failed"]:
            print(f"\n🔄 To retry failed stocks, run download again")


if __name__ == "__main__":
    main()
