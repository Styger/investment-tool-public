"""
Live Market Screener
Screens S&P 500 stocks using saved strategy parameters
"""

from typing import Dict
import pandas as pd
from datetime import datetime

# Import backend logic DIRECTLY (not the calculator wrappers!)
from backend.logic.mos import calculate_mos_from_data
from backend.logic.pbt import calculate_pbt_with_comparison
from backend.logic.tencap import calculate_ten_cap_with_comparison
from backend.logic.cagr import get_cagr_for_screening

# Import FMP API functions
from backend.api.fmp_api import (
    get_current_price,
    get_income_statement,
    get_balance_sheet,
    get_cashflow_statement,
    get_key_metrics,
)


class Screener:
    """Screen stocks with saved strategy parameters"""

    @staticmethod
    def calculate_moat_score(ticker: str, fundamentals: Dict) -> float:
        """
        Calculate Economic Moat Score (0-50 points)
        Simplified version for screening
        """
        try:
            metrics = fundamentals.get("metrics", {})
            income = fundamentals.get("income", {})
            balance = fundamentals.get("balance", {})
            cashflow = fundamentals.get("cashflow", {})

            score = 0

            # ROE > 15% = strong (10 points)
            roe = metrics.get("roe", 0)
            if roe and roe > 0.15:
                score += 10
            elif roe and roe > 0.10:
                score += 5

            # ROIC > 15% = strong (10 points)
            roic = metrics.get("roic", 0)
            if roic and roic > 0.15:
                score += 10
            elif roic and roic > 0.10:
                score += 5

            # Operating Margin > 20% = strong (10 points)
            revenue = income.get("revenue", 0)
            operating_income = income.get("operatingIncome", 0)

            if revenue > 0:
                margin = operating_income / revenue
                if margin > 0.20:
                    score += 10
                elif margin > 0.10:
                    score += 5

            # Debt to Equity < 0.5 = strong (10 points)
            total_debt = balance.get("totalDebt", 0)
            total_equity = balance.get("totalStockholdersEquity", 1)

            if total_equity > 0:
                debt_ratio = total_debt / total_equity
                if debt_ratio < 0.5:
                    score += 10
                elif debt_ratio < 1.0:
                    score += 5

            # Free Cash Flow positive (10 points)
            fcf = cashflow.get("freeCashFlow", 0)
            if fcf > 0:
                score += 10

            return score

        except Exception:
            return 0

    @staticmethod
    def screen_market(
        strategy_params: Dict, universe_key: str = "sp500_top50"
    ) -> pd.DataFrame:
        """
        Screen stocks with strategy parameters

        Args:
            strategy_params: Strategy parameters dict with thresholds
            universe_key: Universe to screen (e.g., 'sp500_full', 'nasdaq100')

        Returns:
            DataFrame with screening results
        """
        # ✅ Get tickers from universe
        from backend.backtesting.universe.definitions import (
            get_universe,
            get_universe_info,
        )

        universe_info = get_universe_info(universe_key)
        tickers = universe_info["tickers"]
        universe_name = universe_info["name"]

        results = []
        current_year = datetime.now().year

        print(f"\n🔍 Screening {universe_name} ({len(tickers)} stocks)...")
        print(
            f"Strategy: MOS>{strategy_params['mos_threshold']}%, "
            f"Moat>{strategy_params['moat_threshold']}"
        )

        for i, ticker in enumerate(tickers, 1):  # ✅ Use tickers from universe!
            try:
                print(
                    f"  [{i}/{len(tickers)}] Analyzing {ticker}...",  # ✅ len(tickers)
                    end="",
                )

                # Get current price
                current_price = get_current_price(ticker)
                if not current_price:
                    print(" ⚠️  No price")
                    continue

                # Get fundamentals (latest)
                income = get_income_statement(ticker, limit=1)
                balance = get_balance_sheet(ticker, limit=1)
                cashflow = get_cashflow_statement(ticker, limit=1)
                metrics = get_key_metrics(ticker, limit=1)

                if not income or not balance or not cashflow or not metrics:
                    print(" ⚠️  No fundamentals")
                    continue

                fundamentals = {
                    "income": income[0],
                    "balance": balance[0],
                    "cashflow": cashflow[0],
                    "metrics": metrics[0],
                }

                # Get CAGR (5-year average)
                cagr = get_cagr_for_screening(ticker, period_years=5)

                # Calculate valuations
                fair_values = []

                # MOS
                if strategy_params.get("use_mos", True):
                    try:
                        mos_result = calculate_mos_from_data(
                            ticker=ticker,
                            current_price=current_price,
                            income_statement=income,
                            balance_sheet=balance,
                            cashflow=cashflow,
                            growth_rate=cagr,
                        )
                        if mos_result:
                            fair_values.append(mos_result["Fair Value Today"])
                    except Exception:
                        pass

                # PBT
                if strategy_params.get("use_pbt", True):
                    try:
                        pbt_result = calculate_pbt_with_comparison(
                            ticker, current_year - 1, cagr
                        )
                        if pbt_result:
                            fair_values.append(pbt_result["fair_value"])
                    except Exception:
                        pass

                # TEN CAP
                if strategy_params.get("use_tencap", True):
                    try:
                        tencap_result = calculate_ten_cap_with_comparison(
                            ticker, current_year - 1
                        )
                        if tencap_result:
                            fair_values.append(tencap_result["ten_cap_fair_value"])
                    except Exception:
                        pass

                if not fair_values:
                    print(" ⚠️  No valuation")
                    continue

                # Consensus fair value
                fair_value = sum(fair_values) / len(fair_values)

                # Calculate MOS
                mos_pct = ((fair_value - current_price) / fair_value) * 100

                # Calculate Moat
                moat_score = Screener.calculate_moat_score(ticker, fundamentals)

                # Determine signal
                buy_threshold = strategy_params.get("mos_threshold", 10.0)
                moat_buy_threshold = strategy_params.get("moat_threshold", 30.0)
                sell_mos_threshold = strategy_params.get("sell_mos_threshold", -5.0)
                sell_moat_threshold = strategy_params.get("sell_moat_threshold", 25.0)

                if mos_pct >= buy_threshold and moat_score >= moat_buy_threshold:
                    signal = "BUY"
                    print(f" 🟢 BUY (MOS: {mos_pct:.1f}%, Moat: {moat_score:.0f})")
                elif mos_pct < sell_mos_threshold or moat_score < sell_moat_threshold:
                    signal = "SELL"
                    print(f" 🔴 SELL (MOS: {mos_pct:.1f}%, Moat: {moat_score:.0f})")
                else:
                    signal = "HOLD"
                    print(f" 🟡 HOLD")

                results.append(
                    {
                        "Ticker": ticker,
                        "Signal": signal,
                        "Current Price": current_price,
                        "Fair Value": fair_value,
                        "MOS %": mos_pct,
                        "Moat Score": moat_score,
                        "Methods": len(fair_values),
                        "CAGR": cagr * 100,
                    }
                )

            except Exception as e:
                print(f" ❌ Error: {str(e)[:50]}")
                continue

        if not results:
            print("\n⚠️  No results found")
            return pd.DataFrame()

        df = pd.DataFrame(results)

        # Summary
        buy_count = len(df[df["Signal"] == "BUY"])
        hold_count = len(df[df["Signal"] == "HOLD"])
        sell_count = len(df[df["Signal"] == "SELL"])

        print(f"\n✅ Screening Complete!")
        print(f"   🟢 BUY: {buy_count}")
        print(f"   🟡 HOLD: {hold_count}")
        print(f"   🔴 SELL: {sell_count}")
        print(f"   Total: {len(df)}\n")

        return df
