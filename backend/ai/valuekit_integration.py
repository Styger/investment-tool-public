"""
ValueKit Integration Module
Connects existing ValueKit formulas (MOS, CAGR) with AI Moat Analysis
"""

import sys
from pathlib import Path
from typing import Dict, Optional

# Add root to path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.logic.mos import calculate_mos_value_from_ticker
from backend.logic.cagr import _mos_growth_estimate_auto
from backend.api import fmp_api
from backend.ai.investment_analyzer import IntegratedAnalyzer


class ValueKitAnalyzer:
    """
    Integrated ValueKit Analysis
    Combines quantitative formulas with qualitative AI analysis
    """

    def __init__(self):
        self.ai_analyzer = IntegratedAnalyzer()

    def estimate_growth_rate(
        self,
        ticker: str,
        period_years: int = 5,
        end_year: int = 2024,
        include_book: bool = True,
        include_eps: bool = True,
        include_revenue: bool = True,
        include_cashflow: bool = True,
    ) -> Dict[str, float]:
        """
        Estimate growth rate using CAGR analysis

        Args:
            ticker: Stock ticker
            period_years: Period for CAGR calculation (default 5 years)
            end_year: End year for calculation
            include_book: Include book value in calculation
            include_eps: Include EPS in calculation
            include_revenue: Include revenue in calculation
            include_cashflow: Include cashflow in calculation

        Returns:
            Dict with CAGR metrics and average growth rate
        """
        start_year = end_year - period_years

        # Fetch data from FMP
        data, mos_input = fmp_api.get_year_data_by_range(
            ticker, start_year, years=period_years
        )

        if not data or not mos_input:
            raise ValueError(f"No data available for {ticker}")

        # Calculate CAGR
        growth_metrics = _mos_growth_estimate_auto(
            data_dict=mos_input,
            start_year=start_year,
            end_year=end_year,
            period_years=period_years,
            known_start_year=start_year,
            include_book=include_book,
            include_eps=include_eps,
            include_revenue=include_revenue,
            include_cashflow=include_cashflow,
        )

        # Convert average from percentage to decimal
        avg_growth = growth_metrics.get("avg", 0) / 100

        return {
            "avg_growth_rate": avg_growth,
            "book_cagr": growth_metrics.get("book", 0),
            "eps_cagr": growth_metrics.get("eps", 0),
            "revenue_cagr": growth_metrics.get("revenue", 0),
            "cashflow_cagr": growth_metrics.get("cashflow", 0),
            "period_years": period_years,
            "start_year": start_year,
            "end_year": end_year,
        }

    def calculate_intrinsic_value(
        self,
        ticker: str,
        year: int = 2024,
        growth_rate: Optional[float] = None,
        discount_rate: float = 0.15,
        margin_of_safety: float = 0.50,
        auto_estimate_growth: bool = True,
    ) -> Dict:
        """
        Calculate intrinsic value using MOS formula

        Args:
            ticker: Stock ticker
            year: Base year for calculation
            growth_rate: Manual growth rate (if None, auto-estimate from CAGR)
            discount_rate: Discount rate (default 15%)
            margin_of_safety: Safety margin (default 50%)
            auto_estimate_growth: Automatically estimate growth from historical data

        Returns:
            Dict with MOS calculation results including current price comparison
        """
        # Auto-estimate growth rate if not provided
        if growth_rate is None and auto_estimate_growth:
            print(f"📊 Auto-estimating growth rate for {ticker}...")
            growth_data = self.estimate_growth_rate(ticker)
            growth_rate = growth_data["avg_growth_rate"]
            print(
                f"   Estimated growth rate: {growth_rate * 100:.2f}% (based on {growth_data['period_years']}y CAGR)"
            )
        elif growth_rate is None:
            # Default fallback
            growth_rate = 0.10
            print(f"   Using default growth rate: {growth_rate * 100:.2f}%")

        # Calculate MOS
        mos_result = calculate_mos_value_from_ticker(
            ticker=ticker,
            year=year,
            growth_rate=growth_rate,
            discount_rate=discount_rate,
            margin_of_safety=margin_of_safety,
        )

        return mos_result

    def analyze_stock_complete(
        self,
        ticker: str,
        year: int = 2024,
        growth_rate: Optional[float] = None,
        discount_rate: float = 0.15,
        margin_of_safety: float = 0.50,
        auto_estimate_growth: bool = True,
        load_sec_data: bool = False,
    ) -> Dict:
        """
        Complete stock analysis: Quantitative (MOS, CAGR) + Qualitative (Moat)

        Args:
            ticker: Stock ticker
            year: Base year
            growth_rate: Manual growth rate (None for auto-estimate)
            discount_rate: Discount rate
            margin_of_safety: Safety margin
            auto_estimate_growth: Auto-estimate growth from CAGR
            load_sec_data: Whether to reload SEC data (False if already cached)

        Returns:
            Complete analysis with investment decision
        """
        print(f"\n{'=' * 70}")
        print(f"🎯 VALUEKIT COMPLETE ANALYSIS: {ticker.upper()}")
        print(f"{'=' * 70}\n")

        # Step 1: Calculate Growth Rate (CAGR)
        if growth_rate is None and auto_estimate_growth:
            growth_data = self.estimate_growth_rate(ticker)
            growth_rate = growth_data["avg_growth_rate"]

            print(f"📈 Growth Rate Analysis (CAGR):")
            print(f"   Period: {growth_data['start_year']}-{growth_data['end_year']}")
            print(f"   Book Value CAGR: {growth_data['book_cagr']:.2f}%")
            print(f"   EPS CAGR: {growth_data['eps_cagr']:.2f}%")
            print(f"   Revenue CAGR: {growth_data['revenue_cagr']:.2f}%")
            print(f"   Cashflow CAGR: {growth_data['cashflow_cagr']:.2f}%")
            print(f"   → Average Growth: {growth_rate * 100:.2f}%\n")

        # Step 2: Calculate Intrinsic Value (MOS)
        print(f"💰 Intrinsic Value Calculation (MOS):")
        mos_result = self.calculate_intrinsic_value(
            ticker=ticker,
            year=year,
            growth_rate=growth_rate,
            discount_rate=discount_rate,
            margin_of_safety=margin_of_safety,
            auto_estimate_growth=False,  # Already calculated above
        )

        print(f"   Current Price: ${mos_result['Current Stock Price']:.2f}")
        print(f"   Fair Value: ${mos_result['Fair Value Today']:.2f}")
        print(f"   MOS Price: ${mos_result['MOS Price']:.2f}")
        print(f"   {mos_result['Price vs Fair Value']}")
        print(f"   → {mos_result['Investment Recommendation']}\n")

        # Calculate margin of safety percentage
        fair_value = mos_result["Fair Value Today"]
        current_price = mos_result["Current Stock Price"]

        if fair_value > 0 and current_price > 0:
            actual_mos = ((fair_value - current_price) / fair_value) * 100
        else:
            actual_mos = 0

        # Step 3: Prepare metrics for AI Analysis
        # Note: We don't have ROIC calculated yet - would need separate module
        # For now, use growth rate as proxy for quality
        quantitative_metrics = {
            "margin_of_safety": f"{actual_mos:.2f}%",
            "growth_rate": f"{growth_rate * 100:.2f}%",
            "current_price": current_price,
            "fair_value": fair_value,
            "mos_price": mos_result["MOS Price"],
            "discount_rate": f"{discount_rate * 100:.0f}%",
            # TODO: Add ROIC when profitability.py is integrated
        }

        # Step 4: AI Moat Analysis
        print(f"🏰 AI Moat Analysis:")
        ai_decision = self.ai_analyzer.analyze(
            ticker=ticker,
            quantitative_metrics=quantitative_metrics,
            load_sec_data=load_sec_data,
        )

        # Step 5: Combine Results
        final_rec = self._reconcile_recommendations(
            mos_result["Investment Recommendation"],
            ai_decision.decision,
            ai_decision.moat_analysis.moat_strength,
        )

        return {
            "ticker": ticker.upper(),
            "growth_analysis": growth_data if auto_estimate_growth else None,
            "intrinsic_value": mos_result,
            "ai_analysis": ai_decision,
            "final_recommendation": final_rec,
        }

    def _reconcile_recommendations(
        self, mos_rec: str, ai_rec: str, moat_strength: str
    ) -> str:
        """
        Reconcile MOS recommendation with AI moat recommendation

        Logic:
        - Overvalued (MOS) + Wide Moat (AI) → HOLD (wait for better price)
        - Overvalued (MOS) + Weak Moat (AI) → PASS
        - If both say BUY → STRONG BUY
        - If MOS says BUY but AI says HOLD → BUY (with caution)
        """
        mos_upper = mos_rec.upper()
        ai_upper = ai_rec.upper()

        # Stock is overvalued per MOS
        if "AVOID" in mos_upper or "OVERVALUED" in mos_upper:
            if moat_strength == "Wide":
                return (
                    "HOLD - Quality company (Wide moat) but wait for better entry price"
                )
            elif moat_strength == "Narrow":
                return "PASS - Overvalued with only narrow competitive advantages"
            else:
                return "PASS - Overvalued without strong moat"

        # MOS says Strong Buy (likely due to extreme undervaluation)
        if "STRONG BUY" in mos_upper:
            if "BUY" in ai_upper or "STRONG BUY" in ai_upper:
                return "STRONG BUY - Excellent value with quality moat"
            elif "HOLD" in ai_upper or moat_strength == "Narrow":
                return "BUY - Excellent value but monitor competitive position"
            else:
                return "HOLD - Attractive valuation but weak competitive moat"

        # Both bullish
        if "BUY" in mos_upper and "STRONG BUY" in ai_upper:
            return "STRONG BUY - Excellent quantitative + qualitative"
        elif "BUY" in mos_upper and "BUY" in ai_upper:
            return "BUY - Good value with solid moat"

        # MOS bullish, AI cautious
        elif "BUY" in mos_upper and "HOLD" in ai_upper:
            return "BUY (with caution) - Good value but moat concerns"
        elif "BUY" in mos_upper and "PASS" in ai_upper:
            return "HOLD - Good value but significant red flags"

        # MOS cautious
        elif "HOLD" in mos_upper:
            if "BUY" in ai_upper:
                return "HOLD - Fair value but strong moat, monitor for entry"
            else:
                return "HOLD - Fairly valued, monitor"

        # Default
        return f"See details: MOS={mos_rec}, AI={ai_rec}"


def quick_analysis(ticker: str) -> Dict:
    """
    Quick analysis with defaults

    Usage:
        result = quick_analysis("AAPL")
        print(result['final_recommendation'])
    """
    analyzer = ValueKitAnalyzer()
    return analyzer.analyze_stock_complete(
        ticker=ticker,
        auto_estimate_growth=True,
        load_sec_data=False,  # Assume SEC data already loaded
    )


if __name__ == "__main__":
    # Example usage
    ticker = "AAPL"

    analyzer = ValueKitAnalyzer()

    # Full analysis
    result = analyzer.analyze_stock_complete(
        ticker=ticker, auto_estimate_growth=True, load_sec_data=False
    )

    print(f"\n{'=' * 70}")
    print(f"FINAL RECOMMENDATION: {result['final_recommendation']}")
    print(f"{'=' * 70}\n")
