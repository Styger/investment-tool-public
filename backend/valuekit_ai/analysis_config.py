"""
Analysis Configuration System
Toggle which components to include in analysis
"""

from dataclasses import dataclass
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


@dataclass
class AnalysisConfig:
    """Configuration for analysis components"""

    # Quantitative
    run_mos: bool = True
    run_cagr: bool = True
    run_roic: bool = False

    # Moats
    run_moat_analysis: bool = True
    run_brand_power: bool = True
    run_switching_costs: bool = True
    run_network_effects: bool = True
    run_cost_advantages: bool = True
    run_efficient_scale: bool = True

    # Red Flags
    run_red_flags: bool = True
    run_regulatory_risk: bool = True
    run_competitive_threats: bool = True
    run_management_issues: bool = True
    run_financial_stress: bool = True

    # Options
    load_sec_data: bool = False
    auto_estimate_growth: bool = True
    margin_of_safety: float = 0.50
    discount_rate: float = 0.15

    def get_enabled_moats(self):
        """Returns list of enabled moats"""
        moats = []
        if self.run_brand_power:
            moats.append("brand_power")
        if self.run_switching_costs:
            moats.append("switching_costs")
        if self.run_network_effects:
            moats.append("network_effects")
        if self.run_cost_advantages:
            moats.append("cost_advantages")
        if self.run_efficient_scale:
            moats.append("efficient_scale")
        return moats

    def get_enabled_red_flags(self):
        """Returns list of enabled red flag categories"""
        flags = []
        if self.run_regulatory_risk:
            flags.append("regulatory_risk")
        if self.run_competitive_threats:
            flags.append("competitive_threats")
        if self.run_management_issues:
            flags.append("management_issues")
        if self.run_financial_stress:
            flags.append("financial_stress")
        return flags


# Presets
def quick_config():
    """Quick - all enabled"""
    return AnalysisConfig()


def quantitative_only():
    """Only numbers, no moats"""
    return AnalysisConfig(run_moat_analysis=False, run_red_flags=False)


def qualitative_only():
    """Only moats, no numbers"""
    return AnalysisConfig(run_mos=False, run_cagr=False)
