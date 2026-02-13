"""
ValueKit Trading Strategy
Warren Buffett Value Investing: Consensus Valuation + Moat Score

Main strategy implementation with multiple valuation methods
"""

import backtrader as bt
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.api.fmp_api import (
    get_balance_sheet,
    get_income_statement,
    get_cashflow_statement,
    get_key_metrics,
)
from .mos_calculator import MOSCalculator
from .moat_calculator import MoatCalculator
from .pbt_calculator import PBTCalculator
from .ten_cap_calculator import TenCapCalculator
from .trade_tracker import TradeTracker


class ValueKitStrategy(bt.Strategy):
    """
    ValueKit Value Investing Strategy

    Valuation: Consensus from DCF/PBT/TEN CAP (user selectable)
    Buy Signal:  MOS > 10% AND Moat Score > 30/50
    Sell Signal: MOS < -5% OR Moat Score < 20/50

    Portfolio:   Max 20 positions, Equal Weight
    Rebalancing: Quarterly
    """

    params = (
        # Valuation Methods
        ("use_dcf", True),  # Use DCF (MOS) valuation
        ("use_pbt", True),  # Use PBT valuation
        ("use_tencap", True),  # Use TEN CAP valuation
        # NOTE: CAGR is now calculated automatically for DCF and PBT
        # Thresholds
        ("mos_threshold", 10.0),  # Minimum MOS for buy (%)
        ("moat_threshold", 30.0),  # Minimum Moat Score for buy (0-50)
        ("sell_mos_threshold", -5.0),  # Sell if MOS falls below this
        ("sell_moat_threshold", 20.0),  # Sell if Moat falls below this
        # Portfolio Management
        ("max_positions", 20),  # Maximum number of positions
        ("rebalance_days", 90),  # Rebalance every 90 days (quarterly)
        ("printlog", True),  # Print logs
    )

    def __init__(self):
        """Initialize strategy"""
        self.order = None
        self.last_rebalance = None

        # Use persistent cache manager
        from backend.valuekit_ai.data.cache import get_cache_manager

        self.cache = get_cache_manager()

        # Initialize calculators and tracker
        self.mos_calc = MOSCalculator()
        self.moat_calc = MoatCalculator()
        self.pbt_calc = PBTCalculator()
        self.tencap_calc = TenCapCalculator()
        self.trade_tracker = TradeTracker(self)

        # Track portfolio values for metrics
        self.portfolio_values = []
        self.dates = []

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
                self.trade_tracker.handle_buy_execution(order, ticker, price, size)
            elif order.issell():
                self.trade_tracker.handle_sell_execution(order, ticker, price, size)

        self.order = None

    def get_fundamentals(self, ticker: str, force_refresh: bool = False):
        """
        Get fundamental data for ticker AS OF the current backtest date

        CRITICAL: Prevents look-ahead bias by accounting for reporting delays
        - Annual reports (10-K) are filed ~60-90 days after fiscal year end
        - Conservative approach: Assume available April 1st

        Example:
        - Backtest Date: 2020-03-15 → Use 2018 data (2019 not yet published)
        - Backtest Date: 2020-04-15 → Use 2019 data (2019 published)

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
        current_month = current_date.month

        # ========================================================================
        # PREVENT LOOK-AHEAD BIAS: Account for reporting delays
        # ========================================================================
        # Annual reports (10-K) are published ~60-90 days after fiscal year end
        # For calendar year companies (year end = Dec 31):
        # - Large Accelerated Filers: 60 days → End of February
        # - Most major companies file by end of February
        # Conservative cutoff: March 1st

        if current_month < 3:  # January, February
            # Q1 (Jan-Feb): Annual reports for previous year not yet available
            # Use data from 2 years ago
            max_year = current_year - 2
            self.log(
                f"📅 {current_year}-{current_month:02d}: Using {max_year} data (reporting lag)"
            )
        else:  # March onwards (month >= 3)
            # March-December: Previous year's annual report now available
            max_year = current_year - 1
            self.log(f"📅 {current_year}-{current_month:02d}: Using {max_year} data")

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

            # Debug output
            print(
                f"🔬 [{ticker}] {current_date} (month {current_month}) → Using {max_year} fundamentals"
            )

            return fundamentals

        except Exception as e:
            self.log(f"ERROR: Failed to get fundamentals for {ticker}: {e}")
            return None

    def calculate_cagr_for_ticker(self, ticker: str):
        """
        Calculate CAGR (Compound Annual Growth Rate) from historical fundamentals

        Uses backend/logic/cagr.py to compute average CAGR across multiple metrics

        Args:
            ticker: Stock ticker

        Returns:
            Float: CAGR as decimal (e.g., 0.15 for 15%) or 0.10 as fallback
        """
        try:
            # Get fundamentals data (already cached)
            fundamentals = self.get_fundamentals(ticker)
            if not fundamentals:
                self.log(f"WARNING: No fundamentals for CAGR calculation ({ticker})")
                return 0.10  # Fallback to 10%

            # Import CAGR logic
            from backend.logic.cagr import _mos_growth_estimate_auto
            from backend.api.fmp_api import get_year_data_by_range

            # Find data feed to get current year
            data_feed = None
            for data in self.datas:
                if data._name == ticker:
                    data_feed = data
                    break

            if data_feed is None:
                return 0.10

            current_year = data_feed.datetime.date(0).year
            max_year = current_year - 1  # Use previous year's data

            # Get historical data for CAGR calculation (5-year lookback)
            start_year = max_year - 5
            data, mos_input = get_year_data_by_range(
                ticker, start_year=start_year, years=5
            )

            if not mos_input:
                self.log(f"WARNING: No CAGR data for {ticker}, using 10% default")
                return 0.10

            # Calculate CAGR (5-year average)
            cagr_result = _mos_growth_estimate_auto(
                data_dict=mos_input,
                start_year=start_year,
                end_year=max_year,
                period_years=5,
                known_start_year=start_year,
                include_book=True,
                include_eps=True,
                include_revenue=True,
                include_cashflow=True,
                include_fcf=True,
            )

            # Get average CAGR
            avg_cagr_pct = cagr_result.get("avg", 10.0)  # Default 10% if missing
            avg_cagr = avg_cagr_pct / 100.0  # Convert to decimal

            # Sanity check: CAGR should be reasonable (-50% to +100%)
            if avg_cagr < -0.5 or avg_cagr > 1.0:
                self.log(
                    f"WARNING: Extreme CAGR {avg_cagr * 100:.1f}% for {ticker}, capping to 10%"
                )
                return 0.10

            self.log(f"📈 CAGR for {ticker}: {avg_cagr * 100:.1f}%")
            return avg_cagr

        except Exception as e:
            self.log(f"ERROR: CAGR calculation failed for {ticker}: {e}")
            return 0.10  # Safe fallback

    def calculate_margin_of_safety(self, ticker: str):
        """
        Calculate Margin of Safety using CONSENSUS from multiple valuation methods

        User can select which methods to use (DCF, PBT, TEN CAP)
        Fair Value = Average of selected methods
        MOS = (Fair Value - Current Price) / Fair Value * 100

        Args:
            ticker: Stock ticker

        Returns:
            Dict with consensus MOS data or None
        """
        valuations = []
        methods_used = []

        # Method 1: DCF (from MOS calculator)
        if self.params.use_dcf:
            try:
                dcf_result = self.mos_calc.calculate(self, ticker)
                if dcf_result:
                    valuations.append(
                        {
                            "method": "DCF",
                            "fair_value": dcf_result["fair_value"],
                            "buy_price": dcf_result["mos_price"],  # Price with 50% MOS
                        }
                    )
                    methods_used.append("DCF")
            except Exception as e:
                self.log(f"  DCF calculation failed for {ticker}: {e}")

        # Method 2: PBT (Payback Time)
        if self.params.use_pbt:
            try:
                pbt_result = self.pbt_calc.calculate(
                    self, ticker
                )  # ✅ No growth_rate param!
                if pbt_result:
                    valuations.append(
                        {
                            "method": "PBT",
                            "fair_value": pbt_result["fair_value"],
                            "buy_price": pbt_result["buy_price"],
                        }
                    )
                    methods_used.append("PBT")
            except Exception as e:
                self.log(f"  PBT calculation failed for {ticker}: {e}")

        # Method 3: TEN CAP (Owner Earnings)
        if self.params.use_tencap:
            try:
                tencap_result = self.tencap_calc.calculate(self, ticker)
                if tencap_result:
                    valuations.append(
                        {
                            "method": "TEN_CAP",
                            "fair_value": tencap_result["fair_value"],
                            "buy_price": tencap_result["buy_price"],
                        }
                    )
                    methods_used.append("TEN_CAP")
            except Exception as e:
                self.log(f"  TEN CAP calculation failed for {ticker}: {e}")

        # Need at least one successful method
        if not valuations:
            self.log(f"WARNING: No valuation methods available for {ticker}")
            return None

        # Calculate consensus (simple average)
        avg_fair_value = sum(v["fair_value"] for v in valuations) / len(valuations)
        avg_buy_price = sum(v["buy_price"] for v in valuations) / len(valuations)

        # Get current price from data feed
        current_price = None
        for data in self.datas:
            if data._name == ticker:
                current_price = float(data.close[0])
                break

        if current_price is None:
            return None

        # Calculate MOS percentage
        mos_percentage = ((avg_fair_value - current_price) / avg_fair_value) * 100

        # Determine recommendation
        if current_price <= avg_buy_price:
            recommendation = "STRONG BUY"
        elif current_price <= avg_fair_value:
            recommendation = "BUY"
        elif mos_percentage >= -5:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"

        return {
            "mos_percentage": mos_percentage,
            "current_price": current_price,
            "fair_value": avg_fair_value,
            "buy_price": avg_buy_price,
            "recommendation": recommendation,
            "methods_used": methods_used,
            "num_methods": len(valuations),
            "individual_valuations": valuations,  # For debugging
        }

    def calculate_moat_score(self, ticker: str):
        """
        Calculate Moat Score using MoatCalculator

        Args:
            ticker: Stock ticker

        Returns:
            Moat score (0-50) or None
        """
        return self.moat_calc.calculate(self, ticker)

    def should_buy(self, ticker: str):
        """
        Determine if we should buy this stock

        Args:
            ticker: Stock ticker

        Returns:
            True if buy signal, False otherwise
        """
        # Calculate Consensus MOS
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
            methods_str = "+".join(mos_data["methods_used"])
            self.log(
                f"BUY SIGNAL: {ticker} - "
                f"MOS: {mos_percentage:.1f}% ({methods_str}) "
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
        # Calculate current consensus metrics
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
            methods_str = "+".join(mos_data["methods_used"])
            self.log(
                f"SELL SIGNAL: {ticker} - "
                f"MOS: {mos_percentage:.1f}% ({methods_str}) "
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

        # Track portfolio value daily
        current_date = self.datas[0].datetime.date(0)
        current_value = self.broker.getvalue()
        self.portfolio_values.append(current_value)
        self.dates.append(current_date)

        # Check if we should rebalance (quarterly)
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
                            methods_str = "+".join(mos_data["methods_used"])
                            self.log(
                                f"  ❌ {ticker}: MOS {mos_pct:.1f}% ({methods_str}) "
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

        # Safety check for division by zero
        if debug_counter > 0:
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
        else:
            self.log(f"   ⚠️  Data Unavailable: {debug_data_fails}")
            self.log(f"   ❌ Failed MOS: {debug_mos_fails}")
            self.log(f"   ❌ Failed Moat: {debug_moat_fails}")
            self.log(f"   ✅ Passed Both: {debug_both_pass}")

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
            self.log("No buy opportunities found")
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
                methods_str = "+".join(mos_data["methods_used"])
                self.log(
                    f"BUY SIGNAL: {ticker} - "
                    f"MOS: {candidate['mos']:.1f}% ({methods_str}) "
                    f"(Fair: ${mos_data['fair_value']:.2f}, "
                    f"Current: ${price:.2f}), "
                    f"Moat: {candidate['moat']:.0f}/50"
                )
                self.log(f"BUY ORDER: {ticker} - {size} shares @ ${price:.2f}")
                self.buy(data=data, size=size)

    def stop(self):
        """Called when backtest ends"""

        # ========================================================================
        # FORCE CLOSE ALL OPEN POSITIONS AT MARKET CLOSE
        # ========================================================================
        self.log("=" * 70)
        self.log("END OF BACKTEST - FORCE CLOSING ALL OPEN POSITIONS")
        self.log("=" * 70)

        # Get last trading date and close all positions at last price
        last_date = self.datas[0].datetime.date(0)

        forced_closes = 0
        for data in self.datas:
            position = self.getposition(data)
            if position.size > 0:
                ticker = data._name
                current_price = data.close[0]

                self.log(
                    f"FORCE CLOSE: {ticker} - {position.size} shares @ ${current_price:.2f}"
                )

                # Manually close the position in trade tracker
                # This simulates selling at market close on the last day
                self.trade_tracker.handle_sell_execution(
                    order=None,  # No actual order object
                    ticker=ticker,
                    price=current_price,
                    size=position.size,
                    force_close=True,  # Flag to indicate this is a force close
                )

                forced_closes += 1

        if forced_closes > 0:
            self.log(f"\n⚠️  Force closed {forced_closes} open positions")
            self.log(
                "These positions are now included in Trade Log with exit price = last close\n"
            )

        # ========================================================================
        # STRATEGY PERFORMANCE SUMMARY
        # ========================================================================
        self.log("=" * 70)
        self.log("STRATEGY PERFORMANCE SUMMARY")
        self.log("=" * 70)

        # Get statistics from trade tracker
        stats = self.trade_tracker.get_statistics()

        if stats:
            self.log(f"Closed Trades: {stats['total_trades']}")
            self.log(f"Wins: {stats['wins']} ({stats['win_rate']:.1f}%)")
            self.log(f"Losses: {stats['losses']} ({100 - stats['win_rate']:.1f}%)")
            self.log("")
            self.log(f"Total Realized P&L: ${stats['total_pnl']:,.2f}")
            self.log(f"Average P&L per Trade: ${stats['avg_pnl']:,.2f}")
            self.log(f"Average Win: ${stats['avg_win']:,.2f}")
            self.log(f"Average Loss: ${stats['avg_loss']:,.2f}")

            if stats["profit_factor"]:
                self.log(f"Profit Factor: {stats['profit_factor']:.2f}")
        else:
            self.log("No closed trades")

        # Check for any remaining unrealized P&L (should be 0 now)
        unrealized = self.trade_tracker.get_unrealized_pnl()

        if unrealized["count"] > 0:
            self.log("")
            self.log(
                f"⚠️  WARNING: Still {unrealized['count']} open positions (this shouldn't happen!)"
            )

            for pos_info in unrealized["positions"]:
                self.log(
                    f"  {pos_info['ticker']}: {pos_info['size']} shares @ "
                    f"${pos_info['buy_price']:.2f} "
                    f"(Now: ${pos_info['current_price']:.2f}, "
                    f"Unrealized: ${pos_info['pnl']:,.2f})"
                )

            self.log(
                f"Total Unrealized P&L: ${unrealized['total_unrealized_pnl']:,.2f}"
            )

        self.log("")
        portfolio_value = self.broker.getvalue()
        starting_cash = self.broker.startingcash
        total_return = ((portfolio_value / starting_cash) - 1) * 100

        self.log(f"Final Portfolio Value: ${portfolio_value:,.2f}")
        self.log(f"Total Return: {total_return:.2f}%")
        self.log("=" * 70)


if __name__ == "__main__":
    print("ValueKit Strategy Module")
    print("Use this with scripts/run_valuekit.py")
