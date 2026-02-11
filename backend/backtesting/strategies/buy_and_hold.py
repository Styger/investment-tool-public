"""
Simple Buy & Hold Strategy
Test strategy to verify Backtrader works
"""

import backtrader as bt


class BuyAndHoldStrategy(bt.Strategy):
    """
    Simple Buy & Hold Strategy
    - Buys on first day
    - Holds until end
    - Tests if Backtrader works
    """

    def __init__(self):
        # Track if we already bought
        self.order = None
        self.bought = False

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        """Called when order is executed"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: ${order.executed.price:.2f}")
            elif order.issell():
                self.log(f"SELL EXECUTED, Price: ${order.executed.price:.2f}")

        self.order = None

    def next(self):
        """Called for each bar (day)"""
        # Check if we have an order pending
        if self.order:
            return

        # If not bought yet, buy everything
        if not self.bought:
            # Calculate how many shares we can buy
            cash = self.broker.getcash()
            price = self.datas[0].close[0]
            size = int(cash / price * 0.95)  # Use 95% of cash

            self.log(f"BUY CREATE, Price: ${price:.2f}, Size: {size} shares")
            self.order = self.buy(size=size)
            self.bought = True

        # Only log last day
        if len(self) == len(self.data) - 1:
            self.log(f"FINAL DAY - Close: ${self.datas[0].close[0]:.2f}")
