"""
ValueKit AI Analysis - Main Entry Point
Run complete investment analysis: Quantitative + Qualitative + AI Moat

Usage:
    python run.py AAPL
    python run.py AAPL --load-sec  # Force reload SEC data
    python run.py AAPL --no-growth-estimate  # Manual growth rate
"""

import sys
import argparse
from pathlib import Path

# Add root to path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from valuekit_integration import ValueKitAnalyzer


def run_analysis(
    ticker: str,
    load_sec_data: bool = False,
    auto_estimate_growth: bool = True,
    growth_rate: float = None,
    margin_of_safety: float = 0.50,
    discount_rate: float = 0.15,
    year: int = 2024,
):
    """
    Run complete ValueKit AI analysis

    Args:
        ticker: Stock ticker symbol
        load_sec_data: Force reload SEC 10-K data
        auto_estimate_growth: Auto-estimate growth from CAGR
        growth_rate: Manual growth rate (overrides auto-estimate)
        margin_of_safety: Safety margin (default 50%)
        discount_rate: Discount rate (default 15%)
        year: Base year for calculations
    """

    print("\n" + "=" * 80)
    print("🚀 VALUEKIT AI INVESTMENT ANALYSIS")
    print("=" * 80)
    print(f"\nTicker: {ticker.upper()}")
    print(
        f"Mode: {'Auto-estimate growth' if auto_estimate_growth else 'Manual growth'}"
    )
    print(f"SEC Data: {'Reloading...' if load_sec_data else 'Using cache'}")

    try:
        # Initialize analyzer
        analyzer = ValueKitAnalyzer()

        # Run complete analysis
        result = analyzer.analyze_stock_complete(
            ticker=ticker,
            year=year,
            growth_rate=growth_rate,
            discount_rate=discount_rate,
            margin_of_safety=margin_of_safety,
            auto_estimate_growth=auto_estimate_growth,
            load_sec_data=load_sec_data,
        )

        # Print detailed results
        _print_results(result)

        return result

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return None


def _print_results(result: dict):
    """Print formatted analysis results"""

    print("\n" + "=" * 80)
    print("📊 ANALYSIS RESULTS")
    print("=" * 80)

    # Growth Analysis
    if result.get("growth_analysis"):
        growth = result["growth_analysis"]
        print(f"\n📈 GROWTH RATE ANALYSIS (CAGR)")
        print(f"{'─' * 80}")
        print(
            f"Period: {growth['start_year']}-{growth['end_year']} ({growth['period_years']} years)"
        )
        print(f"\nMetric CAGRs:")
        print(f"  Book Value:    {growth['book_cagr']:>6.2f}%")
        print(f"  EPS:           {growth['eps_cagr']:>6.2f}%")
        print(f"  Revenue:       {growth['revenue_cagr']:>6.2f}%")
        print(f"  Cashflow:      {growth['cashflow_cagr']:>6.2f}%")
        print(f"  ──────────────────────")
        print(f"  Average:       {growth['avg_growth_rate'] * 100:>6.2f}%")

    # Intrinsic Value
    mos = result["intrinsic_value"]
    print(f"\n💰 INTRINSIC VALUE (MARGIN OF SAFETY)")
    print(f"{'─' * 80}")
    print(f"Current Stock Price:  ${mos['Current Stock Price']:>10.2f}")
    print(f"Fair Value Today:     ${mos['Fair Value Today']:>10.2f}")
    print(f"MOS Price (50%):      ${mos['MOS Price']:>10.2f}")
    print(f"\nValuation: {mos['Price vs Fair Value']}")
    print(f"MOS Recommendation: {mos['Investment Recommendation']}")

    # AI Moat Analysis
    ai = result["ai_analysis"]
    moat = ai.moat_analysis

    print(f"\n🏰 AI MOAT ANALYSIS")
    print(f"{'─' * 80}")
    print(f"Overall Moat Score:   {moat.overall_score}/50")
    print(f"Moat Strength:        {moat.moat_strength}")
    print(f"Competitive Position: {moat.competitive_position}")

    print(f"\nIndividual Moat Scores:")
    sorted_moats = sorted(moat.moats.items(), key=lambda x: x[1].score, reverse=True)
    for i, (key, m) in enumerate(sorted_moats, 1):
        emoji = "🟢" if m.score >= 7 else ("🟡" if m.score >= 4 else "🔴")
        print(
            f"  {i}. {emoji} {m.name:30s} {m.score:>2}/10 ({m.confidence} confidence)"
        )

    if moat.red_flags:
        print(f"\n🚩 RED FLAGS ({len(moat.red_flags)}):")
        for i, flag in enumerate(moat.red_flags, 1):
            print(f"  {i}. {flag[:100]}...")
    else:
        print(f"\n✅ No significant red flags detected")

    # AI Decision
    print(f"\n🤖 AI INVESTMENT DECISION")
    print(f"{'─' * 80}")
    print(f"Decision:       {ai.decision}")
    print(f"Confidence:     {ai.confidence}")
    print(f"Overall Score:  {ai.overall_score}/100")
    print(f"\nScore Breakdown:")
    print(f"  Quantitative:  {ai.quantitative_score}/100 (60% weight)")
    print(f"  Qualitative:   {ai.qualitative_score}/100 (40% weight)")
    print(
        f"  Red Flag Penalty: -{ai.overall_score - int((ai.quantitative_score * 0.6 + ai.qualitative_score * 0.4))}"
    )

    # Final Recommendation
    print(f"\n🎯 FINAL RECOMMENDATION")
    print(f"{'─' * 80}")
    print(f"\n  {result['final_recommendation']}")

    print(f"\n{'=' * 80}\n")


def main():
    """Main entry point with CLI arguments"""

    parser = argparse.ArgumentParser(
        description="ValueKit AI Investment Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py AAPL                    # Quick analysis
  python run.py AAPL --load-sec         # Force reload SEC data
  python run.py MSFT --growth 0.12      # Manual growth rate (12%)
  python run.py GOOGL --mos 0.30        # 30% margin of safety
        """,
    )

    parser.add_argument(
        "ticker", type=str, help="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"
    )

    parser.add_argument(
        "--load-sec",
        action="store_true",
        help="Force reload SEC 10-K data (default: use cache)",
    )

    parser.add_argument(
        "--no-growth-estimate",
        action="store_true",
        help="Disable auto growth rate estimation",
    )

    parser.add_argument(
        "--growth", type=float, help="Manual growth rate (e.g., 0.12 for 12%%)"
    )

    parser.add_argument(
        "--mos",
        type=float,
        default=0.50,
        help="Margin of safety (default: 0.50 = 50%%)",
    )

    parser.add_argument(
        "--discount",
        type=float,
        default=0.15,
        help="Discount rate (default: 0.15 = 15%%)",
    )

    parser.add_argument(
        "--year",
        type=int,
        default=2024,
        help="Base year for calculations (default: 2024)",
    )

    args = parser.parse_args()

    # Validate ticker
    ticker = args.ticker.upper()
    if len(ticker) < 1 or len(ticker) > 5:
        print(f"❌ Invalid ticker: {ticker}")
        sys.exit(1)

    # Run analysis
    result = run_analysis(
        ticker=ticker,
        load_sec_data=args.load_sec,
        auto_estimate_growth=not args.no_growth_estimate,
        growth_rate=args.growth,
        margin_of_safety=args.mos,
        discount_rate=args.discount,
        year=args.year,
    )

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
