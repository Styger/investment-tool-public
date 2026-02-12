"""
Trade Tracking & P&L Calculation
Handles order execution, position tracking, and trade statistics
"""


class TradeTracker:
    """
    Track trades and calculate P&L

    Backtrader's notify_trade() is unreliable in multi-stock strategies,
    so we manually track positions in notify_order()
    """

    def __init__(self, strategy):
        """
        Initialize trade tracker

        Args:
            strategy: Parent strategy instance (for logging, getposition)
        """
        self.strategy = strategy
        self.open_positions = {}  # {ticker: {'buy_price': float, 'size': int, ...}}
        self.closed_trades = []  # List of completed trades

    def handle_buy_execution(self, order, ticker, price, size):
        """
        Handle buy order execution

        Args:
            order: Backtrader order object
            ticker: Stock ticker
            price: Buy price
            size: Number of shares bought
        """
        # Get buy date as datetime.date object (NOT string!)
        buy_date = order.data.datetime.date(0)

        self.strategy.log(f"BUY EXECUTED: {ticker} @ ${price:.2f} ({size} shares)")

        # Track position (handle multiple buys by averaging)
        if ticker in self.open_positions:
            # Already have position - calculate new average price
            old_info = self.open_positions[ticker]
            old_price = old_info["buy_price"]
            old_size = old_info["size"]

            # New weighted average
            total_size = old_size + size
            avg_price = (old_price * old_size + price * size) / total_size

            self.open_positions[ticker] = {
                "buy_price": avg_price,
                "size": total_size,
                "buy_date": old_info["buy_date"],  # Keep first buy date (datetime.date)
            }

            self.strategy.log(
                f"  Updated position: {total_size} shares @ ${avg_price:.2f} (avg)"
            )
        else:
            # New position - store as datetime.date object
            self.open_positions[ticker] = {
                "buy_price": price,
                "size": size,
                "buy_date": buy_date,  # ✅ datetime.date object
            }

            self.strategy.log(
                f"TRADE OPENED: {ticker} - {size} shares @ ${price:.2f} on {buy_date}"
            )

    def handle_sell_execution(self, order, ticker, price, size, force_close=False):
        """
        Handle sell order execution

        Args:
            order: Backtrader order object (can be None for force close)
            ticker: Stock ticker
            price: Sell price
            size: Number of shares sold
            force_close: True if this is a forced close at end of backtest
        """
        if ticker not in self.open_positions or size <= 0:
            return

        position = self.open_positions[ticker]

        # Calculate P&L
        buy_price = position["buy_price"]
        pnl = (price - buy_price) * size

        # Get sell date as datetime.date object
        if order is not None:
            sell_date = order.data.datetime.date(0)
        else:
            # Force close - use last available date from strategy
            sell_date = self.strategy.datas[0].datetime.date(0)

        # Get buy date (already a datetime.date object)
        buy_date = position["buy_date"]

        # Calculate hold time (both are datetime.date objects now)
        hold_days = (sell_date - buy_date).days

        # Determine if win or loss
        is_win = pnl > 0

        # Create closed trade record
        closed_trade = {
            "ticker": ticker,
            "buy_date": buy_date,  # datetime.date object
            "sell_date": sell_date,  # datetime.date object
            "buy_price": buy_price,
            "sell_price": price,
            "size": size,
            "pnl": pnl,
            "hold_days": hold_days,
            "is_win": is_win,
            "force_closed": force_close,
        }

        self.closed_trades.append(closed_trade)

        # Remove from open positions
        del self.open_positions[ticker]

        # Log the trade
        status = "FORCE CLOSED" if force_close else "CLOSED"
        win_loss = "WIN" if is_win else "LOSS"
        self.strategy.log(
            f"TRADE {status} ({win_loss}): {ticker} - "
            f"Buy: ${buy_price:.2f} ({buy_date}) → "
            f"Sell: ${price:.2f} ({sell_date}) | "
            f"P&L: ${pnl:,.2f} ({hold_days} days)"
        )

    def get_statistics(self):
        """
        Calculate trading statistics from closed trades

        Returns:
            Dict with statistics or None if no trades
        """
        if not self.closed_trades:
            return None

        total_trades = len(self.closed_trades)
        winning_trades = [t for t in self.closed_trades if t["is_win"]]
        losing_trades = [t for t in self.closed_trades if not t["is_win"]]

        wins = len(winning_trades)
        losses = len(losing_trades)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

        total_pnl = sum(t["pnl"] for t in self.closed_trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

        avg_win = sum(t["pnl"] for t in winning_trades) / wins if wins > 0 else 0
        avg_loss = sum(t["pnl"] for t in losing_trades) / losses if losses > 0 else 0

        # Profit factor
        gross_profit = sum(t["pnl"] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t["pnl"] for t in losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

        # Average hold time
        avg_hold_time = (
            sum(t["hold_days"] for t in self.closed_trades) / total_trades
            if total_trades > 0
            else 0
        )

        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "avg_hold_time_days": avg_hold_time,
        }

    def get_unrealized_pnl(self):
        """
        Calculate unrealized P&L from open positions

        Returns:
            Dict with unrealized P&L info
        """
        unrealized_pnl = 0
        positions_info = []

        for ticker, info in self.open_positions.items():
            # Get current price from data feed
            for data in self.strategy.datas:
                if data._name == ticker:
                    current_price = float(data.close[0])
                    buy_price = info["buy_price"]
                    size = info["size"]

                    position_pnl = (current_price - buy_price) * size
                    unrealized_pnl += position_pnl

                    positions_info.append(
                        {
                            "ticker": ticker,
                            "size": size,
                            "buy_price": buy_price,
                            "current_price": current_price,
                            "pnl": position_pnl,
                        }
                    )
                    break

        return {
            "total_unrealized_pnl": unrealized_pnl,
            "positions": positions_info,
            "count": len(self.open_positions),
        }
