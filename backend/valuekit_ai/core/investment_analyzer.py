"""
Integrated Investment Analyzer
Combines Quantitative Metrics + Moat Analysis for final decision
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
from typing import Dict, Any, Optional
from dataclasses import dataclass
from backend.valuekit_ai.core.moat_analyzer import MoatAnalyzer, MoatAnalysis
from backend.valuekit_ai.config.analysis_config import AnalysisConfig


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
    mos_result: Optional[Dict[str, Any]] = None
    profitability_result: Optional[Dict[str, Any]] = None


class IntegratedAnalyzer:
    """
    Integrated Investment Analysis
    Combines Warren Buffett's moat analysis with quantitative value metrics
    """

    def __init__(self):
        self.moat_analyzer = MoatAnalyzer()

    def _calculate_quantitative_score(self, metrics: Dict[str, Any]) -> int:
        """
        Calculate quantitative score (0-100) from value metrics

        Expected metrics:
            - margin_of_safety: float (percentage)
            - roic: float (percentage)
            - fcf_yield: float (percentage, optional)
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
        roic_str = str(metrics.get("roic", "0%")).replace("%", "")
        if roic_str and roic_str.lower() != "none":
            roic = float(roic_str)
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

    def _combine_scores(
        self, quant_score: int, moat_analysis: MoatAnalysis
    ) -> InvestmentDecision:
        """Combine quantitative and qualitative scores into final decision"""

        # Calculate max possible moat score based on ENABLED moats
        num_enabled_moats = len(moat_analysis.moats)  # Anzahl der analyzed moats
        max_possible_moat_score = num_enabled_moats * 10  # Each moat max 10 points

        # Normalize moat score to 0-100 based on ACTUAL max possible
        moat_score = moat_analysis.overall_score
        if max_possible_moat_score > 0:
            moat_score_normalized = int((moat_score / max_possible_moat_score) * 100)
        else:
            moat_score_normalized = 0  # No moats analyzed

        # Weight: 60% quantitative, 40% moat
        overall = int((quant_score * 0.6) + (moat_score_normalized * 0.4))

        # Red flag penalty: 1 flag = -5, max penalty = -25
        red_flags = len(moat_analysis.red_flags)
        red_flag_penalty = min(25, red_flags * 5)
        overall = max(0, overall - red_flag_penalty)

        # Determine decision with moat strength consideration
        moat_strength = moat_analysis.moat_strength

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
            decision = "HOLD"
            confidence = "Medium" if red_flags <= 2 else "Low"
        else:
            decision = "PASS"
            confidence = "Low"

        # Generate reasoning
        reasoning = self._generate_reasoning(
            moat_analysis.ticker, quant_score, moat_analysis, decision
        )

        return InvestmentDecision(
            ticker=moat_analysis.ticker,
            decision=decision,
            confidence=confidence,
            quantitative_score=quant_score,
            qualitative_score=moat_score_normalized,
            overall_score=overall,
            reasoning=reasoning,
            moat_analysis=moat_analysis,
            quantitative_metrics={},  # Will be filled by caller
        )

    def analyze(
        self,
        ticker: str,
        quantitative_metrics: Dict,
        load_sec_data: bool = False,
        config: Optional["AnalysisConfig"] = None,
        mos_result: Optional[Dict] = None,
        profitability_result: Optional[Dict] = None,
    ) -> InvestmentDecision:
        """
        Run complete investment analysis

        Args:
            ticker: Stock ticker
            quantitative_metrics: Dict with MOS, ROIC, etc.
            load_sec_data: Whether to reload SEC data
            config: AnalysisConfig object (optional)
            mos_result: Complete MOS calculation result (optional)
            profitability_result: Complete profitability metrics (optional)

        Returns:
            InvestmentDecision with final recommendation
        """
        print(f"\n{'=' * 70}")
        print(f"🎯 INTEGRATED INVESTMENT ANALYSIS: {ticker.upper()}")
        print(f"{'=' * 70}\n")

        # Step 1: Load SEC Data
        print(
            f"📥 Step 1: {'Loading SEC data...' if load_sec_data else 'Using previously loaded SEC data...'}"
        )
        if load_sec_data:
            from backend.valuekit_ai.data_pipeline.load_sec_data import (
                load_company_data,
            )

            success = load_company_data(ticker)
            if not success:
                raise ValueError(f"Failed to load SEC data for {ticker}")

        # Step 2: Quantitative Score
        if config is None or config.run_mos or config.run_cagr:
            print(f"\n📊 Step 2: Calculating Quantitative Score...")
            quant_score = self._calculate_quantitative_score(quantitative_metrics)
            print(f"✅ Quantitative Score: {quant_score}/100")
            # Show breakdown
            mos = str(quantitative_metrics.get("margin_of_safety", "0%"))
            roic = str(quantitative_metrics.get("roic", "None"))
            print(f"   - Margin of Safety: {mos}")
            print(f"   - ROIC: {roic}")
        else:
            print(f"\n📊 Step 2: Calculating Quantitative Score: SKIPPED")
            quant_score = 0

        # Step 3: Moat Analysis (if enabled)
        if config is None or config.run_moat_analysis:
            print(f"\n🏰 Step 3: Analyzing Economic Moats...")
            moat_analysis = self.moat_analyzer.analyze_moats(ticker, config=config)
        else:
            print(f"\n🏰 Step 3: Economic Moats: SKIPPED")
            # Create empty moat analysis
            moat_analysis = MoatAnalysis(
                ticker=ticker,
                overall_score=0,
                moat_strength="None",
                moats={},
                red_flags=[],
                competitive_position="Not analyzed",
                recommendation="Not analyzed",
            )

        # Step 4: Combine scores
        print(f"\n⚖️  Step 4: Combining Quantitative + Qualitative...")
        decision = self._combine_scores(quant_score, moat_analysis)

        # Add quantitative metrics to result
        decision.quantitative_metrics = quantitative_metrics
        decision.mos_result = mos_result
        decision.profitability_result = profitability_result

        # Print decision
        self._print_decision(decision)

        return decision

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

        # Moat strength - SHOW ACTUAL DENOMINATOR!
        num_moats = len(moat.moats)
        max_score = num_moats * 10
        reasoning_parts.append(
            f"{moat.moat_strength} moat with score {moat.overall_score}/{max_score} ({num_moats} moats analyzed)"
        )

        # Best moats
        if moat.moats:
            top_moats = sorted(
                moat.moats.items(), key=lambda x: x[1].score, reverse=True
            )[:2]
            if top_moats and top_moats[0][1].score >= 7:
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
        num_moats = len(result.moat_analysis.moats)
        max_moat_score = num_moats * 10 if num_moats > 0 else 50
        print(
            f"Moat Strength:      {result.moat_analysis.moat_strength} ({result.moat_analysis.overall_score}/{max_moat_score})"
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
            # Skip zero/None values if component was disabled
            str_value = str(value)
            if not value or str_value in ["0", "0%", "0.00%", "None", "0.0"]:
                continue
            print(f"{key.replace('_', ' ').title():20s}: {value}")

        print(f"\n{'=' * 70}\n")


def quick_analysis(
    ticker: str, mos: float, roic: float, fcf_yield: float = None
) -> InvestmentDecision:
    """Quick analysis helper"""
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
