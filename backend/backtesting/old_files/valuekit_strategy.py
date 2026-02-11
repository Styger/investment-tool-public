"""
ValueKit Trading Strategy
Warren Buffett Value Investing: MOS + Moat Score
"""

import backtrader as bt
from datetime import datetime
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.logic.mos import calculate_mos_value_from_ticker
from backend.api.fmp_api import (
    get_balance_sheet,
    get_income_statement,
    get_cashflow_statement,
    get_key_metrics,
    get_current_price,
)


class ValueKitStrategy(bt.Strategy):
    """
    ValueKit Value Investing Strategy

    Buy Signal:  MOS > 10% AND Moat Score > 30/50
    Sell Signal: MOS < -5% OR Moat Score < 20/50

    Portfolio:   Max 20 positions, Equal Weight
    Rebalancing: Quarterly
    """

    params = (
        ("mos_threshold", 10.0),  # Minimum MOS for buy (%)
        ("moat_threshold", 30.0),  # Minimum Moat Score for buy (0-50)
        ("sell_mos_threshold", -5.0),  # Sell if MOS falls below this
        ("sell_moat_threshold", 20.0),  # Sell if Moat falls below this
        ("max_positions", 20),  # Maximum number of positions
        ("rebalance_days", 90),  # Rebalance every 90 days (quarterly)
        ("printlog", True),  # Print logs
    )

    def __init__(self):
        """Initialize strategy"""
        # Track positions
        self.order = None
        self.last_rebalance = None

        # Use persistent cache manager
        from backend.valuekit_ai.data.cache import get_cache_manager

        self.cache = get_cache_manager()

        # Manual trade tracking (more reliable than notify_trade!)
        self.open_positions = {}  # {ticker: {'price': float, 'size': int, 'date': str}}
        self.closed_trades = []  # List of completed trades

    @staticmethod
    def filter_by_year(data_list, max_year):
        """
        Filter financial data to only include years <= max_year

        Args:
            data_list: List of financial statements from FMP API
            max_year: Maximum year to include (inclusive)

        Returns:
            Filtered list with only historical data
        """
        if not data_list:
            return []

        filtered = []
        for item in data_list:
            date_str = item.get("date", "")
            if date_str:
                try:
                    # Extract year from date (format: "2018-12-31")
                    year = int(date_str.split("-")[0])
                    if year <= max_year:
                        filtered.append(item)
                except (ValueError, IndexError):
                    # Skip items with invalid dates
                    continue

        # Return max 5 years of historical data
        return filtered[:5]

    def log(self, txt, dt=None):
        """Logging function"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        """Called when order is executed"""
        if order.status in [order.Completed]:
            ticker = order.data._name
            price = order.executed.price
            size = abs(order.executed.size)

            if order.isbuy():
                self.log(f"BUY EXECUTED: {ticker} @ ${price:.2f} ({size} shares)")

                # Track position (handle multiple buys by averaging)
                if ticker in self.open_positions:
                    # Already have position - calculate new average price
                    old_info = self.open_positions[ticker]
                    old_price = old_info["buy_price"]
                    old_size = old_info["buy_size"]

                    # New weighted average
                    total_size = old_size + size
                    avg_price = (old_price * old_size + price * size) / total_size

                    self.open_positions[ticker] = {
                        "buy_price": avg_price,
                        "buy_size": total_size,
                        "buy_date": old_info["buy_date"],  # Keep first buy date
                        "total_sold": old_info.get("total_sold", 0),
                        "total_sell_value": old_info.get("total_sell_value", 0.0),
                    }

                    self.log(
                        f"  Updated position: {total_size} shares @ ${avg_price:.2f} (avg)"
                    )
                else:
                    # New position
                    date = self.datas[0].datetime.date(0).isoformat()
                    self.open_positions[ticker] = {
                        "buy_price": price,
                        "buy_size": size,
                        "buy_date": date,
                        "total_sold": 0,
                        "total_sell_value": 0.0,
                    }

            elif order.issell():
                if ticker in self.open_positions:
                    buy_info = self.open_positions[ticker]
                    buy_price = buy_info["buy_price"]

                    # Track this sell
                    buy_info["total_sold"] += size
                    buy_info["total_sell_value"] += price * size

                    # Check current position
                    position = self.getposition(order.data)

                    if position.size == 0:
                        # Position fully closed - calculate P&L
                        total_size = buy_info["total_sold"]
                        avg_sell_price = buy_info["total_sell_value"] / total_size
                        total_pnl = (avg_sell_price - buy_price) * total_size
                        pnl_pct = ((avg_sell_price - buy_price) / buy_price) * 100

                        # Store trade
                        self.closed_trades.append(
                            {
                                "ticker": ticker,
                                "buy_price": buy_price,
                                "sell_price": avg_sell_price,
                                "size": total_size,
                                "pnl": total_pnl,
                                "pnl_pct": pnl_pct,
                                "is_win": total_pnl > 0,
                                "buy_date": buy_info["buy_date"],
                                "sell_date": self.datas[0].datetime.date(0).isoformat(),
                            }
                        )

                        result = "✅ WIN" if total_pnl > 0 else "❌ LOSS"
                        self.log(
                            f"TRADE #{len(self.closed_trades)}: {ticker} CLOSED - "
                            f"{result} ${total_pnl:.2f} ({pnl_pct:+.1f}%) "
                            f"[{int(total_size)} shares: ${buy_price:.2f} → ${avg_sell_price:.2f}]"
                        )

                        del self.open_positions[ticker]
                    else:
                        # Partial sell
                        pnl = (price - buy_price) * size
                        result = "✅" if pnl > 0 else "❌"
                        self.log(
                            f"SELL EXECUTED: {ticker} @ ${price:.2f} ({size} shares) "
                            f"{result} ${pnl:.2f} [Partial: {position.size} remaining]"
                        )
                else:
                    # No tracking info - just log
                    self.log(
                        f"SELL EXECUTED: {ticker} @ ${price:.2f} ({size} shares) [No tracking]"
                    )

        self.order = None

    def get_fundamentals(self, ticker: str, force_refresh: bool = False):
        """
        Get fundamental data for ticker AS OF the current backtest date

        2-Layer Caching Architecture:
        - Layer 1 (fmp_api.py): Raw API responses (90 day TTL)
        - Layer 2 (this method): Filtered historical data (NEVER expires)

        Args:
            ticker: Stock ticker
            force_refresh: Force API call even if cached

        Returns:
            Dict with fundamental data or None (filtered to historical data only)
        """
        # Find the data feed for this ticker to get current date
        data_feed = None
        for data in self.datas:
            if data._name == ticker:
                data_feed = data
                break

        if data_feed is None:
            self.log(f"ERROR: No data feed found for {ticker}")
            return None

        # Get current backtest date
        current_date = data_feed.datetime.date(0)
        current_year = current_date.year

        # For fundamentals, we can only use data up to previous year
        # (annual reports are published with delay)
        max_year = current_year - 1

        # ========================================================================
        # LAYER 2 CACHE: Filtered historical fundamentals (NEVER EXPIRES!)
        # ========================================================================
        cache_key = f"{ticker}_fundamentals_year_{max_year}"

        if not force_refresh:
            # Try Layer 2 cache first (filtered data)
            cached_fundamentals = self.cache.get(cache_key, "historical_fundamentals")
            if cached_fundamentals is not None:
                self.log(f"✅ L2 Cache HIT: {ticker} (year {max_year})")
                return cached_fundamentals

        # Layer 2 miss - need to fetch and filter
        self.log(f"🔄 L2 Cache MISS: Fetching {ticker} (year {max_year})")

        try:
            # ====================================================================
            # LAYER 1 CACHE: Raw API responses (fmp_api.py handles this)
            # ====================================================================
            # These calls use Layer 1 cache automatically (90 day TTL)
            balance_sheet_all = get_balance_sheet(ticker, limit=10)
            income_stmt_all = get_income_statement(ticker, limit=10)
            cashflow_all = get_cashflow_statement(ticker, limit=10)
            metrics_all = get_key_metrics(ticker, limit=10)

            if not all([balance_sheet_all, income_stmt_all, cashflow_all, metrics_all]):
                self.log(f"WARNING: Incomplete fundamental data for {ticker}")
                return None

            # Filter to historical data only (fast operation - no I/O)
            balance_sheet = self.filter_by_year(balance_sheet_all, max_year)
            income_stmt = self.filter_by_year(income_stmt_all, max_year)
            cashflow = self.filter_by_year(cashflow_all, max_year)
            metrics = self.filter_by_year(metrics_all, max_year)

            if not all([balance_sheet, income_stmt, cashflow, metrics]):
                self.log(f"WARNING: No historical data for {ticker} up to {max_year}")
                return None

            fundamentals = {
                "balance_sheet": balance_sheet,
                "income_statement": income_stmt,
                "cashflow": cashflow,
                "key_metrics": metrics,
                "as_of_year": max_year,
            }

            # ====================================================================
            # SAVE TO LAYER 2 CACHE (historical_fundamentals - NEVER expires!)
            # ====================================================================
            self.cache.set(cache_key, "historical_fundamentals", fundamentals)
            self.log(f"💾 L2 Cached: {cache_key} (immutable - never expires)")

            return fundamentals

        except Exception as e:
            self.log(f"ERROR: Failed to get fundamentals for {ticker}: {e}")
            return None

    def calculate_margin_of_safety(self, ticker: str):
        """
        Calculate Margin of Safety for ticker using HISTORICAL price

        Args:
            ticker: Stock ticker

        Returns:
            Dict with MOS data or None
        """
        try:
            # Find the data feed for this ticker
            data_feed = None
            for data in self.datas:
                if data._name == ticker:
                    data_feed = data
                    break

            if data_feed is None:
                self.log(f"ERROR: No data feed found for {ticker}")
                return None

            # Get HISTORICAL price from current bar (CRITICAL!)
            historical_price = float(data_feed.close[0])

            # Get current year from backtest
            current_date = data_feed.datetime.date(0)
            year = current_date.year - 1  # Use previous year for annual data

            # Get fundamentals
            fundamentals = self.get_fundamentals(ticker)
            if not fundamentals:
                return None

            # Get EPS from income statement
            income_stmt = fundamentals["income_statement"]
            if not income_stmt or len(income_stmt) == 0:
                return None

            # Find EPS for the target year
            eps_now = None
            for stmt in income_stmt:
                stmt_date = stmt.get("date", "")
                if str(year) in stmt_date:
                    eps_now = stmt.get("eps", 0) or stmt.get("epsdiluted", 0)
                    break

            if not eps_now or eps_now <= 0:
                # Fallback to most recent EPS
                eps_now = income_stmt[0].get("eps", 0) or income_stmt[0].get(
                    "epsdiluted", 0
                )
                if not eps_now or eps_now <= 0:
                    return None

            # Calculate intrinsic value (same logic as mos.py)
            growth_rate = 0.10  # 10% default
            discount_rate = 0.15  # 15% discount

            eps_10y = eps_now * ((1 + growth_rate) ** 10)
            future_pe = growth_rate * 200
            future_value = eps_10y * future_pe
            fair_value = future_value / ((1 + discount_rate) ** 10)
            mos_price = fair_value * 0.50  # 50% MOS

            if fair_value <= 0:
                return None

            # Calculate MOS percentage using HISTORICAL price
            mos_percentage = ((fair_value - historical_price) / fair_value) * 100

            # Investment recommendation
            if historical_price <= mos_price:
                recommendation = "Strong Buy (Below MOS price)"
            elif historical_price <= fair_value:
                recommendation = "Buy (Below fair value)"
            elif historical_price <= fair_value * 1.1:
                recommendation = "Hold (Near fair value)"
            else:
                recommendation = "Avoid (Overvalued)"

            return {
                "mos_percentage": mos_percentage,
                "current_price": historical_price,  # HISTORICAL!
                "fair_value": fair_value,
                "mos_price": mos_price,
                "eps_now": eps_now,
                "recommendation": recommendation,
            }

        except Exception as e:
            self.log(f"ERROR: Failed to calculate MOS for {ticker}: {e}")
            return None

    def calculate_moat_score(self, ticker: str):
        """
        Calculate Moat Score for ticker

        Args:
            ticker: Stock ticker

        Returns:
            Moat score (0-50) or None
        """
        fundamentals = self.get_fundamentals(ticker)
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
            self.log(f"ERROR: Failed to calculate Moat for {ticker}: {e}")
            return None

    def should_buy(self, ticker: str):
        """
        Determine if we should buy this stock

        Args:
            ticker: Stock ticker

        Returns:
            True if buy signal, False otherwise
        """
        # Calculate MOS using real module
        mos_data = self.calculate_margin_of_safety(ticker)
        if mos_data is None:
            return False

        mos_percentage = mos_data["mos_percentage"]

        # Calculate Moat Score
        moat_score = self.calculate_moat_score(ticker)
        if moat_score is None:
            return False

        # Check thresholds
        buy_signal = (
            mos_percentage > self.params.mos_threshold
            and moat_score > self.params.moat_threshold
        )

        if buy_signal:
            self.log(
                f"BUY SIGNAL: {ticker} - "
                f"MOS: {mos_percentage:.1f}% "
                f"(Fair: ${mos_data['fair_value']:.2f}, "
                f"Current: ${mos_data['current_price']:.2f}), "
                f"Moat: {moat_score:.0f}/50"
            )

        return buy_signal

    def should_sell(self, ticker: str):
        """
        Determine if we should sell this stock

        Args:
            ticker: Stock ticker

        Returns:
            True if sell signal, False otherwise
        """
        # Calculate current metrics
        mos_data = self.calculate_margin_of_safety(ticker)
        moat_score = self.calculate_moat_score(ticker)

        if mos_data is None:
            # If we can't calculate MOS, be conservative and hold
            return False

        mos_percentage = mos_data["mos_percentage"]

        # Sell if either falls below threshold
        sell_signal = mos_percentage < self.params.sell_mos_threshold or (
            moat_score is not None and moat_score < self.params.sell_moat_threshold
        )

        if sell_signal:
            moat_display = f"{moat_score:.0f}/50" if moat_score else "N/A"
            self.log(
                f"SELL SIGNAL: {ticker} - "
                f"MOS: {mos_percentage:.1f}% "
                f"(Fair: ${mos_data['fair_value']:.2f}, "
                f"Current: ${mos_data['current_price']:.2f}), "
                f"Moat: {moat_display} "
                f"[{mos_data['recommendation']}]"
            )

        return sell_signal

    def next(self):
        """Called for each bar (trading day) - operates on all stocks"""

        # Only process on first data feed to avoid duplicates
        if len(self) != len(self.datas[0]):
            return

        # Check if we should rebalance (quarterly)
        current_date = self.datas[0].datetime.date(0)

        if self.last_rebalance is None:
            self.last_rebalance = current_date

        days_since_rebalance = (current_date - self.last_rebalance).days

        # Skip if not rebalance day (only check quarterly)
        if days_since_rebalance < self.params.rebalance_days:
            return

        self.log(f"--- REBALANCE DAY (Day {len(self)}) ---")
        self.last_rebalance = current_date

        # Evaluate ALL stocks
        buy_candidates = []
        sell_candidates = []

        # Debug counters
        debug_counter = 0
        debug_mos_fails = 0
        debug_moat_fails = 0
        debug_data_fails = 0
        debug_both_pass = 0

        for i, data in enumerate(self.datas):
            ticker = data._name
            position = self.getposition(data)

            # Check existing positions for sell signals
            if position.size > 0:
                if self.should_sell(ticker):
                    sell_candidates.append((data, ticker, position))
            else:
                # Count stocks evaluated
                debug_counter += 1

                # Check for buy signals
                mos_data = self.calculate_margin_of_safety(ticker)
                moat_score = self.calculate_moat_score(ticker)

                # Debug: Track failures
                if mos_data is None:
                    debug_data_fails += 1
                    if debug_data_fails <= 3:
                        self.log(f"  ⚠️  {ticker}: No MOS data available")
                elif moat_score is None:
                    debug_data_fails += 1
                    if debug_data_fails <= 3:
                        self.log(f"  ⚠️  {ticker}: No Moat data available")
                else:
                    mos_pct = mos_data["mos_percentage"]

                    # Track why stocks fail
                    mos_pass = mos_pct > self.params.mos_threshold
                    moat_pass = moat_score > self.params.moat_threshold

                    if not mos_pass:
                        debug_mos_fails += 1
                        if debug_mos_fails <= 5:
                            self.log(
                                f"  ❌ {ticker}: MOS {mos_pct:.1f}% "
                                f"(need >{self.params.mos_threshold}%) "
                                f"Fair=${mos_data['fair_value']:.2f} vs ${mos_data['current_price']:.2f}"
                            )

                    if not moat_pass:
                        debug_moat_fails += 1
                        if debug_moat_fails <= 5:
                            self.log(
                                f"  ❌ {ticker}: Moat {moat_score:.0f}/50 "
                                f"(need >{self.params.moat_threshold})"
                            )

                    if mos_pass and moat_pass:
                        debug_both_pass += 1
                        buy_candidates.append(
                            {
                                "data": data,
                                "ticker": ticker,
                                "mos": mos_pct,
                                "moat": moat_score,
                                "mos_data": mos_data,
                            }
                        )

        # Summary statistics
        self.log("=" * 50)
        self.log(f"📊 EVALUATION SUMMARY:")
        self.log(f"   Total Evaluated: {debug_counter} stocks")
        self.log(
            f"   ⚠️  Data Unavailable: {debug_data_fails} ({debug_data_fails / debug_counter * 100:.1f}%)"
        )
        self.log(
            f"   ❌ Failed MOS: {debug_mos_fails} ({debug_mos_fails / debug_counter * 100:.1f}%)"
        )
        self.log(
            f"   ❌ Failed Moat: {debug_moat_fails} ({debug_moat_fails / debug_counter * 100:.1f}%)"
        )
        self.log(
            f"   ✅ Passed Both: {debug_both_pass} ({debug_both_pass / debug_counter * 100:.1f}%)"
        )
        self.log(f"   🎯 Buy Candidates: {len(buy_candidates)}")
        self.log("=" * 50)

        # Execute sells first (free up capital)
        for data, ticker, position in sell_candidates:
            self.log(f"SELL ORDER: {ticker} ({position.size} shares)")
            # CRITICAL: Must specify size explicitly!
            self.sell(data=data, size=position.size, exectype=bt.Order.Market)

        # Count current positions
        current_positions = sum(1 for d in self.datas if self.getposition(d).size > 0)

        # Calculate available slots
        available_slots = self.params.max_positions - current_positions

        if available_slots <= 0:
            self.log(
                f"Portfolio full ({current_positions}/{self.params.max_positions})"
            )
            return

        # Sort buy candidates by MOS (best first)
        buy_candidates.sort(key=lambda x: x["mos"], reverse=True)

        # Limit to available slots
        buy_candidates = buy_candidates[:available_slots]

        if not buy_candidates:
            self.log("No buy opportunities found")
            return

        # Calculate position size (equal weight)
        cash = self.broker.getcash()
        positions_to_buy = len(buy_candidates)

        # Reserve cash for each position equally
        cash_per_position = cash / positions_to_buy

        # Execute buys
        for candidate in buy_candidates:
            data = candidate["data"]
            ticker = candidate["ticker"]
            price = data.close[0]
            mos_data = candidate["mos_data"]

            # Calculate shares to buy
            size = int(cash_per_position / price)

            if size > 0:
                self.log(
                    f"BUY SIGNAL: {ticker} - "
                    f"MOS: {candidate['mos']:.1f}% "
                    f"(Fair: ${mos_data['fair_value']:.2f}, "
                    f"Current: ${price:.2f}), "
                    f"Moat: {candidate['moat']:.0f}/50"
                )
                self.log(f"BUY ORDER: {ticker} - {size} shares @ ${price:.2f}")
                self.buy(data=data, size=size)

    def stop(self):
        """Called when backtest ends"""
        self.log("=" * 70)
        self.log("STRATEGY PERFORMANCE SUMMARY")
        self.log("=" * 70)

        # Calculate statistics from closed trades
        total_closed = len(self.closed_trades)

        if total_closed > 0:
            wins = sum(1 for t in self.closed_trades if t["is_win"])
            losses = total_closed - wins
            win_rate = (wins / total_closed) * 100

            total_pnl = sum(t["pnl"] for t in self.closed_trades)
            avg_pnl = total_pnl / total_closed

            winning_trades = [t for t in self.closed_trades if t["is_win"]]
            losing_trades = [t for t in self.closed_trades if not t["is_win"]]

            avg_win = (
                sum(t["pnl"] for t in winning_trades) / len(winning_trades)
                if winning_trades
                else 0
            )
            avg_loss = (
                sum(t["pnl"] for t in losing_trades) / len(losing_trades)
                if losing_trades
                else 0
            )

            self.log(f"Closed Trades: {total_closed}")
            self.log(f"Wins: {wins} ({win_rate:.1f}%)")
            self.log(f"Losses: {losses} ({100 - win_rate:.1f}%)")
            self.log("")
            self.log(f"Total Realized P&L: ${total_pnl:,.2f}")
            self.log(f"Average P&L per Trade: ${avg_pnl:,.2f}")
            self.log(f"Average Win: ${avg_win:,.2f}")
            self.log(f"Average Loss: ${avg_loss:,.2f}")

            if avg_loss != 0 and losses > 0:
                profit_factor = abs(avg_win * wins) / abs(avg_loss * losses)
                self.log(f"Profit Factor: {profit_factor:.2f}")
        else:
            self.log("No closed trades")

        # Check for open positions at end
        if self.open_positions:
            self.log("")
            self.log(f"⚠️  Open Positions at End: {len(self.open_positions)}")

            unrealized_pnl = 0
            for ticker, info in self.open_positions.items():
                # Get current price from data feed
                for data in self.datas:
                    if data._name == ticker:
                        current_price = float(data.close[0])
                        buy_price = info["buy_price"]
                        size = info["buy_size"]

                        position_pnl = (current_price - buy_price) * size
                        unrealized_pnl += position_pnl

                        self.log(
                            f"  {ticker}: {size} shares @ ${buy_price:.2f} "
                            f"(Now: ${current_price:.2f}, Unrealized: ${position_pnl:,.2f})"
                        )
                        break

            self.log(f"Total Unrealized P&L: ${unrealized_pnl:,.2f}")

        self.log("")
        portfolio_value = self.broker.getvalue()
        starting_cash = self.broker.startingcash
        total_return = ((portfolio_value / starting_cash) - 1) * 100

        self.log(f"Final Portfolio Value: ${portfolio_value:,.2f}")
        self.log(f"Total Return: {total_return:.2f}%")
        self.log("=" * 70)


if __name__ == "__main__":
    print("ValueKit Strategy Module")
    print("Use this with backtest_valuekit.py")
