"""
Economic Moat Score Calculator
Measures competitive advantage through financial metrics
"""


class MoatCalculator:
    """Calculate Economic Moat Score (0-50 points)"""

    @staticmethod
    def calculate(strategy, ticker: str):
        """
        Calculate Moat Score for ticker

        Args:
            strategy: Parent strategy instance
            ticker: Stock ticker

        Returns:
            Moat score (0-50) or None
        """
        fundamentals = strategy.get_fundamentals(ticker)
        if not fundamentals:
            return None

        try:
            # Simplified moat scoring based on key metrics
            metrics = fundamentals["key_metrics"][0]

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
            income = fundamentals["income_statement"][0]
            revenue = income.get("revenue", 0)
            operating_income = income.get("operatingIncome", 0)

            if revenue > 0:
                margin = operating_income / revenue
                if margin > 0.20:
                    score += 10
                elif margin > 0.10:
                    score += 5

            # Debt to Equity < 0.5 = strong balance sheet (10 points)
            balance = fundamentals["balance_sheet"][0]
            total_debt = balance.get("totalDebt", 0)
            total_equity = balance.get("totalStockholdersEquity", 1)

            if total_equity > 0:
                debt_ratio = total_debt / total_equity
                if debt_ratio < 0.5:
                    score += 10
                elif debt_ratio < 1.0:
                    score += 5

            # Free Cash Flow positive (10 points)
            cashflow_data = fundamentals["cashflow"][0]
            fcf = cashflow_data.get("freeCashFlow", 0)

            if fcf > 0:
                score += 10

            return score

        except Exception as e:
            strategy.log(f"ERROR: Failed to calculate Moat for {ticker}: {e}")
            return None
