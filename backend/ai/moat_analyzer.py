"""
Moat Analysis System - Warren Buffett's 5 Economic Moats
Analyzes competitive advantages from SEC 10-K filings using RAG
"""

from typing import Dict, List, Any
from rag_service import get_rag_service
from dataclasses import dataclass


@dataclass
class MoatScore:
    """Individual moat scoring"""

    name: str
    score: int  # 0-10
    evidence: List[str]
    confidence: str  # "High", "Medium", "Low"


@dataclass
class MoatAnalysis:
    """Complete moat analysis result"""

    ticker: str
    overall_score: int  # 0-50 (sum of all moats)
    moat_strength: str  # "None", "Narrow", "Wide"
    moats: Dict[str, MoatScore]
    red_flags: List[str]
    competitive_position: str
    recommendation: str


class MoatAnalyzer:
    """Analyze economic moats from SEC filings using RAG"""

    # Buffett's 5 Economic Moats
    MOAT_TYPES = {
        "brand_power": {
            "name": "Brand Power & Intangible Assets",
            "indicators": [
                "brand recognition",
                "brand value",
                "customer loyalty",
                "pricing power",
                "premium pricing",
                "brand equity",
                "trademarks",
                "patents",
                "intellectual property",
                "reputation",
                "trust",
                "consumer preference",
            ],
            "query_template": "What evidence exists of {ticker}'s brand strength, pricing power, and intangible assets? Look for customer loyalty, brand recognition, and ability to charge premium prices.",
        },
        "switching_costs": {
            "name": "Switching Costs",
            "indicators": [
                "customer retention",
                "switching costs",
                "lock-in",
                "integration costs",
                "training costs",
                "migration difficulty",
                "long-term contracts",
                "sticky products",
                "ecosystem",
                "data migration",
                "compatibility",
                "learning curve",
            ],
            "query_template": "What switching costs or customer lock-in mechanisms does {ticker} have? Look for high customer retention, long-term contracts, integration complexity, or ecosystem effects.",
        },
        "network_effects": {
            "name": "Network Effects",
            "indicators": [
                "network effects",
                "platform",
                "marketplace",
                "two-sided market",
                "user base",
                "viral growth",
                "peer-to-peer",
                "social network",
                "increasing returns",
                "critical mass",
                "dominant platform",
                "ecosystem",
            ],
            "query_template": "Does {ticker} benefit from network effects where value increases with more users? Look for platform dynamics, marketplace effects, or viral growth mechanisms.",
        },
        "cost_advantages": {
            "name": "Cost Advantages",
            "indicators": [
                "economies of scale",
                "cost leadership",
                "operating leverage",
                "proprietary technology",
                "efficient operations",
                "supply chain",
                "vertical integration",
                "manufacturing advantages",
                "distribution network",
                "procurement power",
                "bargaining power",
                "cost structure",
            ],
            "query_template": "What cost advantages does {ticker} have over competitors? Look for economies of scale, proprietary processes, vertical integration, or superior operational efficiency.",
        },
        "efficient_scale": {
            "name": "Efficient Scale",
            "indicators": [
                "market saturation",
                "limited competition",
                "regulated market",
                "high barriers to entry",
                "capital requirements",
                "regulatory barriers",
                "geographic monopoly",
                "local dominance",
                "infrastructure",
                "licenses",
                "permits",
                "exclusive rights",
            ],
            "query_template": "Does {ticker} operate in a market with efficient scale where new entry is difficult? Look for high barriers to entry, regulatory protection, or geographic/infrastructure advantages.",
        },
    }

    RED_FLAG_CATEGORIES = {
        "regulatory_risk": {
            "keywords": [
                "regulatory investigation",
                "compliance violation",
                "lawsuit",
                "antitrust",
                "regulatory scrutiny",
                "litigation",
                "government investigation",
                "enforcement action",
                "penalty",
                "settlement",
                "regulatory change",
                "unfavorable regulation",
            ],
            "query": "What regulatory risks, legal issues, or compliance concerns face {ticker}?",
        },
        "competitive_threats": {
            "keywords": [
                "intense competition",
                "price competition",
                "market share loss",
                "new entrants",
                "disruption",
                "commoditization",
                "competitive pressure",
                "margin compression",
                "substitutes",
                "technology disruption",
                "innovation threats",
            ],
            "query": "What competitive threats or market disruptions could impact {ticker}?",
        },
        "management_issues": {
            "keywords": [
                "management turnover",
                "executive departure",
                "governance",
                "related party transaction",
                "conflict of interest",
                "board issues",
                "compensation concerns",
                "insider trading",
            ],
            "query": "Are there any management, governance, or insider-related concerns for {ticker}?",
        },
        "financial_stress": {
            "keywords": [
                "liquidity concerns",
                "debt covenant",
                "refinancing risk",
                "going concern",
                "impairment",
                "restructuring",
                "cash flow issues",
                "working capital deficit",
                "credit rating downgrade",
            ],
            "query": "Are there any financial stress indicators or liquidity concerns for {ticker}?",
        },
    }

    def __init__(self):
        self.rag = get_rag_service()

    def analyze_single_moat(
        self, ticker: str, moat_key: str, moat_config: Dict
    ) -> MoatScore:
        """
        Analyze a single moat type

        Returns:
            MoatScore with 0-10 rating
        """
        # Create explicit prompt to avoid meta-commentary
        base_query = moat_config["query_template"].format(ticker=ticker)
        full_query = f"{base_query} Provide specific evidence from the SEC filings only. Do not mention data gaps, limitations, or inability to analyze. Focus only on what IS present in the documents."

        # Get RAG analysis
        result = self.rag.analyze_with_rag(
            query=full_query, quantitative_data={"ticker": ticker}
        )

        if result["status"] != "success":
            return MoatScore(
                name=moat_config["name"],
                score=0,
                evidence=["Analysis failed"],
                confidence="Low",
            )

        analysis_text = result["analysis"].lower()

        # Count indicator mentions
        indicator_count = sum(
            1
            for indicator in moat_config["indicators"]
            if indicator.lower() in analysis_text
        )

        # Extract evidence (first 3 relevant sentences)
        evidence = self._extract_evidence(result["analysis"], moat_config["indicators"])

        # Calculate score (0-10)
        # Based on: indicator frequency, evidence strength, source count
        base_score = min(10, (indicator_count / len(moat_config["indicators"])) * 20)
        source_bonus = min(2, len(result.get("sources", [])) / 3)
        evidence_bonus = min(2, len(evidence))

        score = int(min(10, base_score + source_bonus + evidence_bonus))

        # Determine confidence and apply ceiling
        if len(result.get("sources", [])) >= 3 and indicator_count >= 3:
            confidence = "High"
            confidence_ceiling = 10  # Can score up to 10
        elif len(result.get("sources", [])) >= 2 and indicator_count >= 2:
            confidence = "Medium"
            confidence_ceiling = 8  # Can score up to 8
        else:
            confidence = "Low"
            confidence_ceiling = 5  # Can score up to 5 max

        # Apply confidence ceiling - cap the score
        final_score = min(score, confidence_ceiling)

        return MoatScore(
            name=moat_config["name"],
            score=final_score,  # Now confidence-capped!
            evidence=evidence[:3],  # Top 3 pieces of evidence
            confidence=confidence,
        )

    def detect_red_flags(self, ticker: str) -> List[str]:
        """
        Detect red flags from SEC filings

        Returns:
            List of red flag descriptions
        """
        red_flags = []

        for category, config in self.RED_FLAG_CATEGORIES.items():
            query = config["query"].format(ticker=ticker)

            # Add explicit instruction to only report SERIOUS red flags
            full_query = f"{query} Only report SERIOUS concerns that would materially impact investment decisions. Do not report normal business risks or competitive dynamics that all companies face. Be specific about material risks only."

            result = self.rag.analyze_with_rag(
                query=full_query, quantitative_data={"ticker": ticker}
            )

            if result["status"] == "success":
                analysis_text = result["analysis"].lower()

                # First check: Does the analysis actually report concerns?
                # If it says "no issues" or "cannot identify", skip
                no_issue_patterns = [
                    "no specific",
                    "cannot identify",
                    "do not discuss",
                    "does not discuss",
                    "not mentioned",
                    "no evidence of",
                    "filings do not contain",
                    "unable to identify",
                    "no serious",
                    "no material",
                    "no significant",
                    "there are no",
                    "does not face",
                    "not identified",
                    "no indicators",
                    "no concerns",
                    "no issues",
                ]

                # Check if the response is actually saying "no problems found"
                has_negative_finding = any(
                    pattern in analysis_text for pattern in no_issue_patterns
                )

                # Additional check: look for affirmative problem statements
                problem_statements = [
                    "faces",
                    "experiencing",
                    "has been",
                    "is subject to",
                    "ongoing",
                    "under investigation",
                    "charged with",
                    "violated",
                    "failed to",
                    "defaulted",
                ]

                has_positive_finding = any(
                    stmt in analysis_text for stmt in problem_statements
                )

                # Only proceed if we have actual problems, not just keyword matches
                if has_negative_finding and not has_positive_finding:
                    continue  # Skip this category - analysis says "no issues found"

                # More stringent keyword matching - need multiple indicators
                found_keywords = [
                    kw for kw in config["keywords"] if kw.lower() in analysis_text
                ]

                # Only flag if:
                # 1. Multiple keywords found (not just one)
                # 2. Contains severity indicators
                severity_indicators = [
                    "significant",
                    "material",
                    "substantial",
                    "severe",
                    "ongoing investigation",
                    "major litigation",
                    "faces charges",
                    "regulatory action",
                    "substantial fines",
                    "criminal",
                ]

                has_severity = any(ind in analysis_text for ind in severity_indicators)

                # Require at least 2 keywords OR 1 keyword + severity indicator
                if (len(found_keywords) >= 2) or (
                    len(found_keywords) >= 1 and has_severity
                ):
                    # Extract the concerning part
                    flag_description = self._extract_red_flag(
                        result["analysis"], category, found_keywords
                    )
                    if flag_description and len(flag_description) > 50:
                        red_flags.append(flag_description)

        return red_flags

    def analyze_company_moat(self, ticker: str) -> MoatAnalysis:
        """
        Complete moat analysis for a company

        Returns:
            MoatAnalysis with scores, red flags, and recommendation
        """
        print(f"\n🏰 Analyzing Economic Moats for {ticker}...")
        print("=" * 70)

        # Analyze each moat
        moat_scores = {}
        for moat_key, moat_config in self.MOAT_TYPES.items():
            print(f"\n📊 Analyzing: {moat_config['name']}...")
            score = self.analyze_single_moat(ticker, moat_key, moat_config)
            moat_scores[moat_key] = score
            print(f"   Score: {score.score}/10 (Confidence: {score.confidence})")
            if score.evidence:
                print(f"   Evidence: {score.evidence[0][:100]}...")

        # Calculate overall score
        overall_score = sum(s.score for s in moat_scores.values())

        # Determine moat strength (adjusted thresholds for confidence weighting)
        # Wide: 33+ (was 35+, adjusted for low confidence penalties)
        # Narrow: 18+ (was 20+)
        if overall_score >= 33:
            moat_strength = "Wide"
        elif overall_score >= 18:
            moat_strength = "Narrow"
        else:
            moat_strength = "None"

        # Detect red flags
        print(f"\n🚩 Detecting Red Flags...")
        red_flags = self.detect_red_flags(ticker)
        print(f"   Found {len(red_flags)} red flags")

        # Determine competitive position
        competitive_position = self._assess_competitive_position(
            overall_score, moat_scores, red_flags
        )

        # Generate recommendation
        recommendation = self._generate_recommendation(
            overall_score, moat_strength, red_flags
        )

        return MoatAnalysis(
            ticker=ticker,
            overall_score=overall_score,
            moat_strength=moat_strength,
            moats=moat_scores,
            red_flags=red_flags,
            competitive_position=competitive_position,
            recommendation=recommendation,
        )

    def _extract_evidence(self, text: str, indicators: List[str]) -> List[str]:
        """Extract sentences containing moat indicators"""
        # Split by periods and newlines
        sentences = []
        for line in text.split("\n"):
            sentences.extend(line.split("."))

        evidence = []

        # Very aggressive filter for meta-commentary
        skip_patterns = [
            "quantitative",
            "qualitative",
            "analysis",
            "limitation",
            "critical",
            "data gap",
            "insufficient",
            "cannot",
            "disclaimer",
            "note:",
            "important:",
            "context",
            "however,",
            "as a",
            "i must",
            "i cannot",
            "based on the provided",
            "the provided",
            "excerpts",
            "limited scope",
            "limited insight",
            "review",
            "##",
            "**important**",
            "**note**",
            "**critical**",
        ]

        for sentence in sentences:
            sentence_lower = sentence.lower().strip()

            # Skip very short sentences
            if len(sentence_lower) < 30:
                continue

            # Skip if contains meta-commentary
            if any(pattern in sentence_lower for pattern in skip_patterns):
                continue

            # Skip if starts with markdown headers or asterisks
            if sentence.strip().startswith("#") or sentence.strip().startswith("**"):
                continue

            # Check for moat indicators
            if any(ind.lower() in sentence_lower for ind in indicators):
                clean = sentence.strip()
                # Final check: must contain actual content words
                content_words = [
                    "company",
                    "product",
                    "customer",
                    "market",
                    "business",
                    "service",
                ]
                if any(word in clean.lower() for word in content_words):
                    evidence.append(clean)

        return evidence[:5]  # Return top 5

    def _extract_red_flag(self, text: str, category: str, keywords: List[str]) -> str:
        """Extract red flag description from analysis"""
        sentences = text.split(".")

        # Exclude patterns that indicate NO red flag found
        exclude_patterns = [
            "cannot identify",
            "do not discuss",
            "does not discuss",
            "no specific",
            "no evidence",
            "not mentioned",
            "filings do not",
            "i cannot",
            "unable to identify",
        ]

        for sentence in sentences:
            sentence_lower = sentence.lower().strip()

            # Skip if it's actually saying "no red flag found"
            if any(pattern in sentence_lower for pattern in exclude_patterns):
                continue

            # Check if contains red flag keywords
            if any(kw.lower() in sentence_lower for kw in keywords):
                clean = sentence.strip()
                if len(clean) > 30:
                    return f"{category.replace('_', ' ').title()}: {clean}"

        return None

    def _assess_competitive_position(
        self,
        overall_score: int,
        moat_scores: Dict[str, MoatScore],
        red_flags: List[str],
    ) -> str:
        """Assess overall competitive position"""

        # Adjusted thresholds to account for confidence weighting
        if overall_score >= 33 and len(red_flags) == 0:
            return "Dominant market position with multiple sustainable competitive advantages"
        elif overall_score >= 33:
            return "Strong competitive position but facing some challenges"
        elif overall_score >= 23 and len(red_flags) <= 1:
            return "Solid competitive position with moderate advantages"
        elif overall_score >= 13:
            return "Competitive but without strong moats"
        else:
            return "Weak competitive position - commodity-like business"

    def _generate_recommendation(
        self, overall_score: int, moat_strength: str, red_flags: List[str]
    ) -> str:
        """Generate moat-based investment recommendation"""

        if moat_strength == "Wide" and len(red_flags) == 0:
            return "STRONG BUY - Wide moat, no significant red flags"
        elif moat_strength == "Wide" and len(red_flags) <= 1:
            return "BUY - Wide moat, monitor identified risks"
        elif moat_strength == "Narrow" and len(red_flags) == 0:
            return "BUY - Narrow moat, suitable for quality investors"
        elif moat_strength == "Narrow":
            return "HOLD - Narrow moat with concerns, wait for better entry"
        elif len(red_flags) >= 2:
            return "PASS - Insufficient moat with multiple red flags"
        else:
            return "PASS - No sustainable competitive advantage"

    def print_analysis(self, analysis: MoatAnalysis):
        """Pretty print moat analysis"""

        print("\n" + "=" * 70)
        print(f"🏰 MOAT ANALYSIS: {analysis.ticker}")
        print("=" * 70)

        print(f"\n📊 Overall Moat Score: {analysis.overall_score}/50")
        print(f"💪 Moat Strength: {analysis.moat_strength}")
        print(f"🎯 Competitive Position: {analysis.competitive_position}")

        print(f"\n{'─' * 70}")
        print("INDIVIDUAL MOAT SCORES")
        print(f"{'─' * 70}")

        for moat_key, score in analysis.moats.items():
            print(f"\n{score.name}:")
            print(f"  Score: {score.score}/10 ({score.confidence} confidence)")
            if score.evidence:
                print(f"  Evidence:")
                for ev in score.evidence[:2]:
                    print(f"    • {ev[:150]}...")

        if analysis.red_flags:
            print(f"\n{'─' * 70}")
            print(f"🚩 RED FLAGS ({len(analysis.red_flags)})")
            print(f"{'─' * 70}")
            for i, flag in enumerate(analysis.red_flags, 1):
                print(f"{i}. {flag}")
        else:
            print(f"\n✅ No significant red flags detected")

        print(f"\n{'─' * 70}")
        print(f"💡 RECOMMENDATION: {analysis.recommendation}")
        print(f"{'─' * 70}\n")


def analyze_moat(ticker: str) -> MoatAnalysis:
    """
    Convenience function to analyze moat

    Usage:
        from moat_analyzer import analyze_moat
        analysis = analyze_moat("AAPL")
        print(analysis.overall_score)
    """
    analyzer = MoatAnalyzer()
    return analyzer.analyze_company_moat(ticker)


if __name__ == "__main__":
    # Example usage
    ticker = "AAPL"

    analyzer = MoatAnalyzer()
    analysis = analyzer.analyze_company_moat(ticker)
    analyzer.print_analysis(analysis)
