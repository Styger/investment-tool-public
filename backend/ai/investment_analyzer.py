"""
Integrated Investment Analyzer
Combines Quantitative Metrics + Moat Analysis for final decision
"""

from typing import Dict, Any
from dataclasses import dataclass
from moat_analyzer import MoatAnalyzer, MoatAnalysis
from load_sec_data import load_company_data


@dataclass
class InvestmentDecision:
    """Final investment decision"""

    ticker: str
    decision: str  # "STRONG BUY", "BUY", "HOLD", "PASS"
    confidence: str  # "High", "Medium", "Low"
    quantitative_score: int  # 0-100
    qualitative_score: int  # 0-100 (moat score normalized)
    overall_score: int  # 0-100
    reasoning: str
    moat_analysis: MoatAnalysis
    quantitative_metrics: Dict[str, Any]


class IntegratedAnalyzer:
    """
    Integrated Investment Analysis
    Combines Warren Buffett's moat analysis with quantitative value metrics
    """

    def __init__(self):
        self.moat_analyzer = MoatAnalyzer()

    def calculate_quantitative_score(self, metrics: Dict[str, Any]) -> int:
        """
        Calculate quantitative score (0-100) from value metrics

        Expected metrics:
            - margin_of_safety: float (percentage)
            - roic: float (percentage)
            - fcf_yield: float (percentage, optional)
            - debt_to_equity: float (optional)
        """
        score = 0

        # Margin of Safety (0-40 points)
        mos = float(str(metrics.get("margin_of_safety", "0%")).replace("%", ""))
        if mos >= 25:
            score += 40
        elif mos >= 15:
            score += 30
        elif mos >= 10:
            score += 20
        elif mos >= 5:
            score += 10

        # ROIC (0-40 points)
        roic = float(str(metrics.get("roic", "0%")).replace("%", ""))
        if roic >= 30:
            score += 40
        elif roic >= 20:
            score += 30
        elif roic >= 15:
            score += 20
        elif roic >= 10:
            score += 10

        # FCF Yield (0-20 points)
        if "fcf_yield" in metrics:
            fcf = float(str(metrics["fcf_yield"]).replace("%", ""))
            if fcf >= 8:
                score += 20
            elif fcf >= 5:
                score += 15
            elif fcf >= 3:
                score += 10
            elif fcf >= 1:
                score += 5

        return min(100, score)

    def combine_scores(
        self, quant_score: int, moat_score: int, red_flags: int
    ) -> tuple:
        """
        Combine quantitative and qualitative scores

        Returns:
            (overall_score, decision, confidence)
        """
        # Moat score is 0-50, normalize to 0-100
        moat_score_normalized = (moat_score / 50) * 100

        # Weight: 60% quantitative, 40% moat
        # Quantitative numbers are more reliable
        overall = int((quant_score * 0.6) + (moat_score_normalized * 0.4))

        # Reduced red flag penalty (was too harsh)
        # 1 flag = -5, 2 flags = -10, 3 flags = -15, 4 flags = -20
        red_flag_penalty = min(25, red_flags * 5)
        overall = max(0, overall - red_flag_penalty)

        # Determine decision with moat strength consideration
        # Wide moat companies get more leeway (threshold adjusted for confidence weighting)
        moat_strength = (
            "Wide" if moat_score >= 33 else ("Narrow" if moat_score >= 18 else "None")
        )

        if overall >= 80 and red_flags == 0:
            decision = "STRONG BUY"
            confidence = "High"
        elif overall >= 70 and red_flags <= 1:
            decision = "BUY"
            confidence = "High" if red_flags == 0 else "Medium"
        elif overall >= 60:
            decision = "BUY"
            confidence = "Medium"
        elif overall >= 50 or (moat_strength == "Wide" and overall >= 45):
            # Wide moat companies: allow HOLD down to 45
            decision = "HOLD"
            confidence = "Medium" if red_flags <= 2 else "Low"
        else:
            decision = "PASS"
            confidence = "Low"

        return overall, decision, confidence

    def analyze(
        self,
        ticker: str,
        quantitative_metrics: Dict[str, Any],
        load_sec_data: bool = True,
    ) -> InvestmentDecision:
        """
        Complete integrated analysis

        Args:
            ticker: Stock ticker
            quantitative_metrics: Your ValueKit calculations
            load_sec_data: Whether to load SEC data (set False if already loaded)

        Returns:
            InvestmentDecision with recommendation
        """
        print(f"\n{'=' * 70}")
        print(f"🎯 INTEGRATED INVESTMENT ANALYSIS: {ticker}")
        print(f"{'=' * 70}\n")

        # Step 1: Load SEC data into RAG (if needed)
        if load_sec_data:
            print("📥 Step 1: Loading SEC 10-K data into RAG...")
            load_result = load_company_data(ticker)

            if load_result["status"] != "success":
                raise ValueError(
                    f"Failed to load SEC data: {load_result.get('message')}"
                )

            print(f"✅ Loaded {load_result['documents_added']} documents")
        else:
            print("📥 Step 1: Using previously loaded SEC data...")

        # Step 2: Calculate quantitative score
        print("\n📊 Step 2: Calculating Quantitative Score...")
        quant_score = self.calculate_quantitative_score(quantitative_metrics)
        print(f"✅ Quantitative Score: {quant_score}/100")
        print(f"   - Margin of Safety: {quantitative_metrics.get('margin_of_safety')}")
        print(f"   - ROIC: {quantitative_metrics.get('roic')}")
        if "fcf_yield" in quantitative_metrics:
            print(f"   - FCF Yield: {quantitative_metrics.get('fcf_yield')}")

        # Step 3: Analyze moats
        print("\n🏰 Step 3: Analyzing Economic Moats...")
        moat_analysis = self.moat_analyzer.analyze_company_moat(ticker)

        # Step 4: Combine scores
        print("\n⚖️  Step 4: Combining Quantitative + Qualitative...")
        overall, decision, confidence = self.combine_scores(
            quant_score, moat_analysis.overall_score, len(moat_analysis.red_flags)
        )

        # Step 5: Generate reasoning
        reasoning = self._generate_reasoning(
            ticker, quant_score, moat_analysis, decision
        )

        result = InvestmentDecision(
            ticker=ticker,
            decision=decision,
            confidence=confidence,
            quantitative_score=quant_score,
            qualitative_score=int((moat_analysis.overall_score / 50) * 100),
            overall_score=overall,
            reasoning=reasoning,
            moat_analysis=moat_analysis,
            quantitative_metrics=quantitative_metrics,
        )

        self._print_decision(result)

        return result

    def _generate_reasoning(
        self, ticker: str, quant_score: int, moat: MoatAnalysis, decision: str
    ) -> str:
        """Generate human-readable reasoning"""

        reasoning_parts = []

        # Quantitative strength
        if quant_score >= 80:
            reasoning_parts.append(
                f"Excellent quantitative metrics (Score: {quant_score}/100)"
            )
        elif quant_score >= 60:
            reasoning_parts.append(
                f"Good quantitative metrics (Score: {quant_score}/100)"
            )
        else:
            reasoning_parts.append(
                f"Weak quantitative metrics (Score: {quant_score}/100)"
            )

        # Moat strength
        reasoning_parts.append(
            f"{moat.moat_strength} moat with score {moat.overall_score}/50"
        )

        # Best moats
        top_moats = sorted(moat.moats.items(), key=lambda x: x[1].score, reverse=True)[
            :2
        ]

        if top_moats[0][1].score >= 7:
            moat_names = [m[1].name for m in top_moats if m[1].score >= 7]
            reasoning_parts.append(f"Strong in: {', '.join(moat_names)}")

        # Red flags
        if moat.red_flags:
            reasoning_parts.append(f"⚠️ {len(moat.red_flags)} red flag(s) identified")
        else:
            reasoning_parts.append("✅ No significant red flags")

        # Competitive position
        reasoning_parts.append(f"Position: {moat.competitive_position}")

        return ". ".join(reasoning_parts) + "."

    def _print_decision(self, result: InvestmentDecision):
        """Print final investment decision"""

        print("\n" + "=" * 70)
        print(f"🎯 FINAL INVESTMENT DECISION: {result.ticker}")
        print("=" * 70)

        # Decision with emoji
        emoji = {"STRONG BUY": "🚀", "BUY": "✅", "HOLD": "⏸️", "PASS": "❌"}.get(
            result.decision, ""
        )

        print(f"\n{emoji} DECISION: {result.decision}")
        print(f"📊 Confidence: {result.confidence}")
        print(f"🎯 Overall Score: {result.overall_score}/100")

        print(f"\n{'─' * 70}")
        print("SCORE BREAKDOWN")
        print(f"{'─' * 70}")
        print(f"Quantitative Score: {result.quantitative_score}/100 (60% weight)")
        print(f"Qualitative Score:  {result.qualitative_score}/100 (40% weight)")
        print(
            f"Moat Strength:      {result.moat_analysis.moat_strength} ({result.moat_analysis.overall_score}/50)"
        )
        print(f"Red Flags:          {len(result.moat_analysis.red_flags)}")

        print(f"\n{'─' * 70}")
        print("REASONING")
        print(f"{'─' * 70}")
        print(result.reasoning)

        print(f"\n{'─' * 70}")
        print("KEY METRICS")
        print(f"{'─' * 70}")
        for key, value in result.quantitative_metrics.items():
            print(f"{key.replace('_', ' ').title():20s}: {value}")

        print(f"\n{'=' * 70}\n")


def quick_analysis(
    ticker: str, mos: float, roic: float, fcf_yield: float = None
) -> InvestmentDecision:
    """
    Quick analysis helper

    Usage:
        result = quick_analysis("AAPL", mos=15.2, roic=45.2, fcf_yield=3.8)
        print(result.decision)
    """
    analyzer = IntegratedAnalyzer()

    metrics = {"margin_of_safety": f"{mos}%", "roic": f"{roic}%"}

    if fcf_yield:
        metrics["fcf_yield"] = f"{fcf_yield}%"

    return analyzer.analyze(ticker, metrics)


if __name__ == "__main__":
    # Example usage
    ticker = "AAPL"

    quantitative_metrics = {
        "margin_of_safety": "15.2%",
        "roic": "45.2%",
        "fcf_yield": "3.8%",
    }

    analyzer = IntegratedAnalyzer()
    decision = analyzer.analyze(ticker, quantitative_metrics, load_sec_data=False)

    print(f"\n✅ Analysis complete!")
    print(f"Decision: {decision.decision}")
    print(f"Overall Score: {decision.overall_score}/100")
