"""
Moat Analysis System - Warren Buffett's 5 Economic Moats
Analyzes competitive advantages from SEC 10-K filings using RAG
"""

from typing import Dict, List, Optional
from backend.valuekit_ai.rag.rag_service import get_rag_service
from dataclasses import dataclass
from backend.valuekit_ai.config.analysis_config import (
    AnalysisConfig,
)
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


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
        self.moat_types = self.MOAT_TYPES

    def analyze_single_moat(
        self, ticker: str, moat_key: str, moat_config: Dict
    ) -> MoatScore:
        """Analyze a single moat type - Returns MoatScore with 0-10 rating"""

        base_query = moat_config["query_template"].format(ticker=ticker)
        full_query = f"{base_query} Provide specific evidence from the SEC filings only. Do not mention data gaps, limitations, or inability to analyze. Focus only on what IS present in the documents."

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
        indicator_count = sum(
            1
            for indicator in moat_config["indicators"]
            if indicator.lower() in analysis_text
        )

        evidence = self._extract_evidence(result["analysis"], moat_config["indicators"])

        # Calculate score
        base_score = min(10, (indicator_count / len(moat_config["indicators"])) * 20)
        source_bonus = min(2, len(result.get("sources", [])) / 3)
        evidence_bonus = min(2, len(evidence))
        score = int(min(10, base_score + source_bonus + evidence_bonus))

        # Confidence ceiling
        if len(result.get("sources", [])) >= 3 and indicator_count >= 3:
            confidence, confidence_ceiling = "High", 10
        elif len(result.get("sources", [])) >= 2 and indicator_count >= 2:
            confidence, confidence_ceiling = "Medium", 8
        else:
            confidence, confidence_ceiling = "Low", 5

        final_score = min(score, confidence_ceiling)

        return MoatScore(
            name=moat_config["name"],
            score=final_score,
            evidence=evidence[:3],
            confidence=confidence,
        )

    def detect_red_flags(
        self, ticker: str, enabled_categories: List[str] = None
    ) -> List[str]:
        """Detect red flags - only checks enabled categories"""

        if enabled_categories is None:
            enabled_categories = list(self.RED_FLAG_CATEGORIES.keys())

        red_flags = []

        for category in enabled_categories:
            if category not in self.RED_FLAG_CATEGORIES:
                continue

            config = self.RED_FLAG_CATEGORIES[category]
            query = config["query"].format(ticker=ticker)
            full_query = f"{query} Only report SERIOUS concerns that would materially impact investment decisions. Do not report normal business risks or competitive dynamics that all companies face. Be specific about material risks only."

            result = self.rag.analyze_with_rag(
                query=full_query, quantitative_data={"ticker": ticker}
            )

            if result["status"] == "success":
                analysis_text = result["analysis"].lower()

                # Check for "no issues" patterns
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

                has_negative_finding = any(
                    pattern in analysis_text for pattern in no_issue_patterns
                )

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

                if has_negative_finding and not has_positive_finding:
                    continue

                found_keywords = [
                    kw for kw in config["keywords"] if kw.lower() in analysis_text
                ]

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

                if (len(found_keywords) >= 2) or (
                    len(found_keywords) >= 1 and has_severity
                ):
                    flag_description = self._extract_red_flag(
                        result["analysis"], category, found_keywords
                    )
                    if flag_description and len(flag_description) > 50:
                        red_flags.append(flag_description)

        return red_flags

    def analyze_moats(
        self, ticker: str, config: Optional["AnalysisConfig"] = None
    ) -> MoatAnalysis:
        """
        Complete moat analysis with config support

        Args:
            ticker: Stock ticker
            config: AnalysisConfig with enabled/disabled features

        Returns:
            MoatAnalysis result
        """
        print(f"\n🏰 Analyzing Economic Moats for {ticker.upper()}...")
        print("=" * 70 + "\n")

        # Get enabled moats and flags from config
        if config:
            enabled_moats = config.get_enabled_moats()
            enabled_flags = (
                config.get_enabled_red_flags() if config.run_red_flags else []
            )
        else:
            # All enabled by default
            enabled_moats = list(self.MOAT_TYPES.keys())
            enabled_flags = list(self.RED_FLAG_CATEGORIES.keys())

        moat_scores = {}

        # Analyze only enabled moats
        for moat_type, moat_config in self.MOAT_TYPES.items():
            if moat_type in enabled_moats:
                print(f"📊 Analyzing: {moat_config['name']}...")
                score = self.analyze_single_moat(ticker, moat_type, moat_config)
                moat_scores[moat_type] = score
                print(f"   Score: {score.score}/10 (Confidence: {score.confidence})")
            else:
                print(f"⏭️  Skipping: {moat_config['name']}")

        # Calculate overall score (only from analyzed moats)
        overall_score = sum(s.score for s in moat_scores.values())

        # Determine moat strength DYNAMICALLY based on enabled moats
        num_enabled_moats = len(moat_scores)
        max_possible_score = num_enabled_moats * 10

        if max_possible_score > 0:
            # Calculate as percentage of max possible
            score_percentage = overall_score / max_possible_score

            if score_percentage >= 0.66:  # 66%+ → Wide
                moat_strength = "Wide"
            elif score_percentage >= 0.36:  # 36%+ → Narrow
                moat_strength = "Narrow"
            else:
                moat_strength = "None"
        else:
            # No moats analyzed
            moat_strength = "None"

        # Red flags (if enabled)
        red_flags = []
        if config is None or config.run_red_flags:
            print(f"\n🚩 Detecting Red Flags...")
            red_flags = self.detect_red_flags(ticker, enabled_flags)
            print(f"   Found {len(red_flags)} red flags")
        else:
            print(f"\n🚩 Red Flag Detection: SKIPPED")

        # Assess position
        competitive_position = self._assess_competitive_position(
            overall_score, moat_scores, red_flags
        )

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
        sentences = []
        for line in text.split("\n"):
            sentences.extend(line.split("."))

        evidence = []
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
            if len(sentence_lower) < 30:
                continue
            if any(pattern in sentence_lower for pattern in skip_patterns):
                continue
            if sentence.strip().startswith("#") or sentence.strip().startswith("**"):
                continue
            if any(ind.lower() in sentence_lower for ind in indicators):
                clean = sentence.strip()
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

        return evidence[:5]

    def _extract_red_flag(self, text: str, category: str, keywords: List[str]) -> str:
        """Extract red flag description from analysis"""
        sentences = text.split(".")
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
            if any(pattern in sentence_lower for pattern in exclude_patterns):
                continue
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

        # Calculate as percentage of max possible
        num_moats = len(moat_scores)
        max_possible = num_moats * 10

        if max_possible == 0:
            return "Not analyzed"

        score_percentage = overall_score / max_possible

        # Use percentage-based thresholds
        if score_percentage >= 0.66 and len(red_flags) == 0:
            return "Dominant market position with multiple sustainable competitive advantages"
        elif score_percentage >= 0.66:
            return "Strong competitive position but facing some challenges"
        elif score_percentage >= 0.50 and len(red_flags) <= 1:
            return "Solid competitive position with moderate advantages"
        elif score_percentage >= 0.36:
            return "Competitive but with limited moats"  # Changed!
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

    # Keep backward compatibility
    def analyze_company_moat(self, ticker: str) -> MoatAnalysis:
        """Backward compatible - analyze all moats"""
        return self.analyze_moats(ticker, config=None)


def analyze_moat(ticker: str) -> MoatAnalysis:
    """Convenience function"""
    analyzer = MoatAnalyzer()
    return analyzer.analyze_moats(ticker)
