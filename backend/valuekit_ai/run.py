"""
ValueKit AI Analysis - Main Entry Point
Run complete investment analysis: Quantitative + Qualitative + AI Moat

Usage:
    python run.py AAPL
    python run.py AAPL --preset quant-only
    python run.py AAPL --no-brand --no-scale
"""

import sys
import argparse
from pathlib import Path

# Add root to path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from valuekit_integration import ValueKitAnalyzer
from analysis_config import (
    AnalysisConfig,
    quick_config,
    quantitative_only,
    qualitative_only,
)


def run_analysis(
    ticker: str,
    config: AnalysisConfig = None,
    growth_rate: float = None,
    year: int = 2024,
):
    """
    Run complete ValueKit AI analysis with config

    Args:
        ticker: Stock ticker symbol
        config: AnalysisConfig object with feature flags
        growth_rate: Manual growth rate (overrides config)
        year: Base year for calculations
    """

    if config is None:
        config = quick_config()

    print("\n" + "=" * 80)
    print("🚀 VALUEKIT AI INVESTMENT ANALYSIS")
    print("=" * 80)
    print(f"\nTicker: {ticker.upper()}")
    print(
        f"Mode: {'Auto-estimate growth' if config.auto_estimate_growth else 'Manual growth'}"
    )
    print(f"SEC Data: {'Reloading...' if config.load_sec_data else 'Using cache'}")

    # Show config
    print(f"\n📋 Analysis Components:")
    if config.run_mos or config.run_cagr:
        quant = []
        if config.run_mos:
            quant.append("MOS")
        if config.run_cagr:
            quant.append("CAGR")
        if config.run_profitability:
            quant.append("Profitability")
        print(f"  Quantitative: {', '.join(quant)}")

    if config.run_moat_analysis:
        moats = [m.replace("_", " ").title() for m in config.get_enabled_moats()]
        print(f"  Moats: {', '.join(moats) if moats else 'None'}")

    if config.run_red_flags:
        flags = [f.replace("_", " ").title() for f in config.get_enabled_red_flags()]
        print(f"  Red Flags: {', '.join(flags) if flags else 'None'}")

    try:
        # Initialize analyzer
        analyzer = ValueKitAnalyzer()

        # Run complete analysis with config
        result = analyzer.analyze_stock_complete(
            ticker=ticker,
            year=year,
            growth_rate=growth_rate,
            discount_rate=config.discount_rate,
            margin_of_safety=config.margin_of_safety,
            auto_estimate_growth=config.auto_estimate_growth,
            load_sec_data=config.load_sec_data,
            config=config,  # Pass config!
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
    if result.get("intrinsic_value"):
        mos = result["intrinsic_value"]
        print(f"\n💰 INTRINSIC VALUE (MARGIN OF SAFETY)")
        print(f"{'─' * 80}")
        print(f"Current Stock Price:  ${mos['Current Stock Price']:>10.2f}")
        print(f"Fair Value Today:     ${mos['Fair Value Today']:>10.2f}")
        print(f"MOS Price (50%):      ${mos['MOS Price']:>10.2f}")
        print(f"\nValuation: {mos['Price vs Fair Value']}")
        print(f"MOS Recommendation: {mos['Investment Recommendation']}")

    # Profitability Analysis
    if result.get("profitability_analysis"):
        prof = result["profitability_analysis"]

        print(f"\n📊 PROFITABILITY ANALYSIS")
        print(f"{'─' * 80}")

        # Return Ratios
        print(f"Return Ratios:")
        if prof.get("roe"):
            roe_emoji = (
                "🟢" if prof["roe"] > 0.20 else ("🟡" if prof["roe"] > 0.15 else "🔴")
            )
            print(
                f"  {roe_emoji} ROE (Return on Equity):    {prof['roe'] * 100:>6.1f}%"
            )

        if prof.get("roa"):
            roa_emoji = (
                "🟢" if prof["roa"] > 0.10 else ("🟡" if prof["roa"] > 0.07 else "🔴")
            )
            print(
                f"  {roa_emoji} ROA (Return on Assets):    {prof['roa'] * 100:>6.1f}%"
            )

        if prof.get("roic"):
            roic_emoji = (
                "🟢" if prof["roic"] > 0.15 else ("🟡" if prof["roic"] > 0.10 else "🔴")
            )
            print(
                f"  {roic_emoji} ROIC (Return on Inv. Cap): {prof['roic'] * 100:>6.1f}%"
            )

        # Profit Margins
        print(f"\nProfit Margins:")
        if prof.get("gross_margin"):
            print(f"     Gross Margin:     {prof['gross_margin'] * 100:>6.1f}%")
        if prof.get("operating_margin"):
            print(f"     Operating Margin: {prof['operating_margin'] * 100:>6.1f}%")
        if prof.get("net_margin"):
            nm_emoji = (
                "🟢"
                if prof["net_margin"] > 0.15
                else ("🟡" if prof["net_margin"] > 0.10 else "🔴")
            )
            print(f"  {nm_emoji} Net Margin:       {prof['net_margin'] * 100:>6.1f}%")

        # Efficiency
        print(f"\nEfficiency:")
        if prof.get("asset_turnover"):
            at_emoji = "🟢" if prof["asset_turnover"] > 1.0 else "🔴"
            print(f"  {at_emoji} Asset Turnover:    {prof['asset_turnover']:>6.2f}x")

    # AI Moat Analysis
    if result.get("ai_analysis"):
        ai = result["ai_analysis"]
        moat = ai.moat_analysis

        # Calculate display values
        num_moats = len(moat.moats)
        max_possible = num_moats * 10

        print(f"\n🏰 AI MOAT ANALYSIS")
        print(f"{'─' * 80}")
        print(
            f"Overall Moat Score:   {moat.overall_score}/{max_possible} ({num_moats} moats analyzed)"
        )
        print(f"Moat Strength:        {moat.moat_strength}")
        print(f"Competitive Position: {moat.competitive_position}")

        print(f"\nIndividual Moat Scores:")
        sorted_moats = sorted(
            moat.moats.items(), key=lambda x: x[1].score, reverse=True
        )
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
  python run.py AAPL                    # Quick analysis (default)
  python run.py AAPL --preset quant-only  # Only quantitative
  python run.py AAPL --no-brand --no-scale  # Skip certain moats
  python run.py AAPL --no-red-flags     # Skip red flag detection
        """,
    )

    parser.add_argument("ticker", type=str, help="Stock ticker symbol")

    # Preset configs
    parser.add_argument(
        "--preset",
        type=str,
        choices=["quick", "quant-only", "qual-only"],
        help="Analysis preset (quick=all, quant-only=numbers, qual-only=moats)",
    )

    # Toggle components
    parser.add_argument("--no-mos", action="store_true", help="Disable MOS calculation")
    parser.add_argument(
        "--no-cagr", action="store_true", help="Disable CAGR calculation"
    )
    parser.add_argument(
        "--no-profitability",
        action="store_true",
        help="Disable profitability analysis (ROE/ROA/ROIC/Margins)",
    )
    parser.add_argument(
        "--no-moats", action="store_true", help="Disable all moat analysis"
    )
    parser.add_argument(
        "--no-red-flags", action="store_true", help="Disable red flag detection"
    )

    # Individual moats
    parser.add_argument("--no-brand", action="store_true", help="Skip brand power moat")
    parser.add_argument(
        "--no-switching", action="store_true", help="Skip switching costs moat"
    )
    parser.add_argument(
        "--no-network", action="store_true", help="Skip network effects moat"
    )
    parser.add_argument(
        "--no-cost", action="store_true", help="Skip cost advantages moat"
    )
    parser.add_argument(
        "--no-scale", action="store_true", help="Skip efficient scale moat"
    )

    # Options
    parser.add_argument("--load-sec", action="store_true", help="Force reload SEC data")
    parser.add_argument("--growth", type=float, help="Manual growth rate")
    parser.add_argument(
        "--mos", type=float, default=0.50, help="Margin of safety (default: 0.50)"
    )
    parser.add_argument(
        "--discount", type=float, default=0.15, help="Discount rate (default: 0.15)"
    )
    parser.add_argument(
        "--year", type=int, default=2024, help="Base year (default: 2024)"
    )

    args = parser.parse_args()

    # Validate ticker
    ticker = args.ticker.upper()
    if len(ticker) < 1 or len(ticker) > 5:
        print(f"❌ Invalid ticker: {ticker}")
        sys.exit(1)

    # Build config
    if args.preset == "quant-only":
        config = quantitative_only()
    elif args.preset == "qual-only":
        config = qualitative_only()
    else:
        config = quick_config()

    # Apply toggles
    if args.no_mos:
        config.run_mos = False
    if args.no_cagr:
        config.run_cagr = False
    if args.no_profitability:
        config.run_profitability = False
    if args.no_moats:
        config.run_moat_analysis = False
    if args.no_red_flags:
        config.run_red_flags = False

    # Individual moat toggles
    if args.no_brand:
        config.run_brand_power = False
    if args.no_switching:
        config.run_switching_costs = False
    if args.no_network:
        config.run_network_effects = False
    if args.no_cost:
        config.run_cost_advantages = False
    if args.no_scale:
        config.run_efficient_scale = False

    # Other options
    config.load_sec_data = args.load_sec
    config.margin_of_safety = args.mos
    config.discount_rate = args.discount

    # Run analysis
    result = run_analysis(
        ticker=ticker,
        config=config,
        growth_rate=args.growth,
        year=args.year,
    )

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
