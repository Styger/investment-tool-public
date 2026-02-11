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
        self.open_positions = {}  # {ticker: {'buy_price': float, 'buy_size': int, ...}}
        self.closed_trades = []  # List of completed trades

    def handle_buy_execution(self, order, ticker, price, size):
        """
        Handle buy order execution

        Args:
            order: Backtrader order
            ticker: Stock ticker
            price: Execution price
            size: Number of shares
        """
        self.strategy.log(f"BUY EXECUTED: {ticker} @ ${price:.2f} ({size} shares)")

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

            self.strategy.log(
                f"  Updated position: {total_size} shares @ ${avg_price:.2f} (avg)"
            )
        else:
            # New position
            date = self.strategy.datas[0].datetime.date(0).isoformat()
            self.open_positions[ticker] = {
                "buy_price": price,
                "buy_size": size,
                "buy_date": date,
                "total_sold": 0,
                "total_sell_value": 0.0,
            }

    def handle_sell_execution(self, order, ticker, price, size):
        """
        Handle sell order execution

        Args:
            order: Backtrader order
            ticker: Stock ticker
            price: Execution price
            size: Number of shares
        """
        if ticker in self.open_positions:
            buy_info = self.open_positions[ticker]
            buy_price = buy_info["buy_price"]

            # Track this sell
            buy_info["total_sold"] += size
            buy_info["total_sell_value"] += price * size

            # Check current position
            position = self.strategy.getposition(order.data)

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
                        "sell_date": self.strategy.datas[0]
                        .datetime.date(0)
                        .isoformat(),
                    }
                )

                result = "✅ WIN" if total_pnl > 0 else "❌ LOSS"
                self.strategy.log(
                    f"TRADE #{len(self.closed_trades)}: {ticker} CLOSED - "
                    f"{result} ${total_pnl:.2f} ({pnl_pct:+.1f}%) "
                    f"[{int(total_size)} shares: ${buy_price:.2f} → ${avg_sell_price:.2f}]"
                )

                del self.open_positions[ticker]
            else:
                # Partial sell
                pnl = (price - buy_price) * size
                result = "✅" if pnl > 0 else "❌"
                self.strategy.log(
                    f"SELL EXECUTED: {ticker} @ ${price:.2f} ({size} shares) "
                    f"{result} ${pnl:.2f} [Partial: {position.size} remaining]"
                )
        else:
            # No tracking info - just log
            self.strategy.log(
                f"SELL EXECUTED: {ticker} @ ${price:.2f} ({size} shares) [No tracking]"
            )

    def get_statistics(self):
        """
        Get trade statistics

        Returns:
            Dict with trade statistics
        """
        total_closed = len(self.closed_trades)

        if total_closed == 0:
            return None

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

        profit_factor = None
        if avg_loss != 0 and losses > 0:
            profit_factor = abs(avg_win * wins) / abs(avg_loss * losses)

        return {
            "total_trades": total_closed,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
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
                    size = info["buy_size"]

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
