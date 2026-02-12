"""
Run ValueKit Strategy Backtest
With Performance Metrics, Benchmark Comparison, and Consensus Valuation
"""

import backtrader as bt
from datetime import datetime
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.backtesting.strategies.valuekit import ValueKitStrategy
from backend.backtesting.data.feeds import FMPDataFeed
from backend.backtesting.data.loaders import load_historical_data
from backend.backtesting.universe.definitions import get_universe
from backend.backtesting.core.broker_config import configure_broker
from backend.backtesting.analytics.metrics import PerformanceMetrics
from backend.backtesting.analytics.benchmark import BenchmarkComparison


def run_valuekit_backtest(
    universe_name="value_3",
    from_year=2018,
    to_year=2022,
    starting_cash=100000.0,
    commission=0.001,
    mos_threshold=10.0,
    moat_threshold=30.0,
    use_dcf=True,
    use_pbt=True,
    use_tencap=True,
):
    """
    Run backtest with ValueKit Strategy + Metrics + Benchmark + Consensus Valuation

    Args:
        universe_name: Stock universe to test
        from_year: Start year
        to_year: End year
        starting_cash: Initial capital
        commission: Commission rate
        mos_threshold: Minimum MOS for buy (%)
        moat_threshold: Minimum Moat Score for buy (0-50)
        use_dcf: Use DCF valuation method
        use_pbt: Use PBT valuation method
        use_tencap: Use TEN CAP valuation method
        pbt_growth_rate: Growth rate for PBT calculation (e.g., 0.15 = 15%)

    Returns:
        Dict with all results
    """
    print("=" * 70)
    print("VALUEKIT STRATEGY BACKTEST - CONSENSUS VALUATION")
    print("=" * 70)

    # Get universe
    universe = get_universe(universe_name)
    print(f"Universe: {universe_name.upper()} ({len(universe)} stocks)")
    print(f"Period: {from_year}-{to_year}")
    print(f"Starting Cash: ${starting_cash:,.0f}")
    print()

    # Print valuation methods
    methods_enabled = []
    if use_dcf:
        methods_enabled.append("DCF")
    if use_pbt:
        methods_enabled.append("PBT")
    if use_tencap:
        methods_enabled.append("TEN CAP")

    print("Valuation Methods:")
    for method in methods_enabled:
        print(f"  ✅ {method}")
    if not methods_enabled:
        print("  ⚠️  WARNING: No valuation methods enabled!")
    print()

    print(f"Thresholds:")
    print(f"  MOS > {mos_threshold}%")
    print(f"  Moat > {moat_threshold}/50")
    print()

    # Create Cerebro
    cerebro = bt.Cerebro()

    # Add strategy with new parameters
    cerebro.addstrategy(
        ValueKitStrategy,
        mos_threshold=mos_threshold,
        moat_threshold=moat_threshold,
        use_dcf=use_dcf,
        use_pbt=use_pbt,
        use_tencap=use_tencap,
    )

    # Load data
    from_date = datetime(from_year, 1, 1)
    to_date = datetime(to_year, 12, 31)

    print("Loading historical data...")
    loaded = 0

    for ticker in universe:
        try:
            df = load_historical_data(ticker, from_date, to_date)

            if df is None or len(df) == 0:
                print(f"  ⚠️  {ticker}: No data available")
                continue

            data = FMPDataFeed(dataname=df)
            data._name = ticker
            cerebro.adddata(data, name=ticker)

            loaded += 1
            print(f"  ✅ {ticker}: {len(df)} days")

        except Exception as e:
            print(f"  ❌ {ticker}: Error - {e}")

    print(f"\n✅ Loaded {loaded}/{len(universe)} stocks")

    if loaded == 0:
        print("❌ No data loaded - cannot run backtest")
        return None

    # Configure broker
    configure_broker(cerebro, starting_cash, commission, force_fills=True)

    # Run backtest
    start_value = cerebro.broker.getvalue()
    print(f"\n💰 Starting Portfolio Value: ${start_value:,.2f}")

    print("\n" + "=" * 70)
    print("RUNNING BACKTEST...")
    print("=" * 70)

    # Run and get strategy instance
    results = cerebro.run()
    strategy = results[0]

    # Get final value
    final_value = cerebro.broker.getvalue()

    # Calculate basic metrics
    profit = final_value - start_value
    profit_pct = (profit / start_value) * 100
    years = (to_date - from_date).days / 365.25
    cagr = (((final_value / start_value) ** (1 / years)) - 1) * 100

    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print(f"Starting Value: ${start_value:,.2f}")
    print(f"Final Value:    ${final_value:,.2f}")
    print(f"Profit:         ${profit:,.2f}")
    print(f"Return:         {profit_pct:.2f}%")
    print(f"CAGR:           {cagr:.2f}%")
    print("=" * 70)

    # ========================================================================
    # CALCULATE ADVANCED METRICS
    # ========================================================================
    print("\n" + "=" * 70)
    print("PERFORMANCE METRICS")
    print("=" * 70)

    # Get data from strategy
    portfolio_values = strategy.portfolio_values
    closed_trades = strategy.trade_tracker.closed_trades

    # Calculate daily returns
    if len(portfolio_values) > 1:
        import numpy as np

        values = np.array(portfolio_values)
        # Safety: Replace zeros to avoid division by zero
        values_safe = np.where(values[:-1] == 0, 1, values[:-1])
        daily_returns = (np.diff(values) / values_safe).tolist()
    else:
        daily_returns = []

    # Calculate all metrics
    metrics = PerformanceMetrics.calculate_all_metrics(
        portfolio_values=portfolio_values,
        trades=closed_trades,
        starting_value=start_value,
        years=years,
    )

    # Print metrics
    print(f"Sharpe Ratio:        {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio:       {metrics['sortino_ratio']:.2f}")
    print(f"Max Drawdown:        {metrics['max_drawdown']:.2f}%")
    print(f"Calmar Ratio:        {metrics['calmar_ratio']:.2f}")
    print(f"Win Rate:            {metrics['win_rate']:.1f}%")
    print(f"Profit Factor:       {metrics['profit_factor']:.2f}")
    print(f"Avg Hold Time:       {metrics['avg_hold_time_days']:.0f} days")

    # ========================================================================
    # BENCHMARK COMPARISON
    # ========================================================================
    print("\n" + "=" * 70)
    print("BENCHMARK COMPARISON (S&P 500)")
    print("=" * 70)

    benchmark_results = BenchmarkComparison.compare_with_benchmark(
        strategy_metrics=metrics,
        strategy_returns=daily_returns,
        from_date=from_date,
        to_date=to_date,
        starting_value=start_value,
    )

    if benchmark_results["benchmark_available"]:
        print(f"S&P 500 Return:      {benchmark_results['benchmark_return']:.2f}%")
        print(f"S&P 500 CAGR:        {benchmark_results['benchmark_cagr']:.2f}%")
        print(f"Strategy Return:     {benchmark_results['strategy_return']:.2f}%")
        print(f"Strategy CAGR:       {benchmark_results['strategy_cagr']:.2f}%")
        print()
        print(f"Outperformance:      {benchmark_results['outperformance']:+.2f}%")
        print(f"Alpha:               {benchmark_results['alpha']:+.2f}%")
        print(f"Beta:                {benchmark_results['beta']:.2f}")
        print(f"Correlation:         {benchmark_results['correlation']:.2f}")
        print(f"Information Ratio:   {benchmark_results['information_ratio']:.2f}")
    else:
        print("⚠️  Benchmark data not available")

    print("=" * 70)

    # ========================================================================
    # GENERATE CHARTS
    # ========================================================================
    from backend.backtesting.analytics.visualizations import BacktestVisualizer

    visualizer = BacktestVisualizer()

    charts = visualizer.generate_all_charts(
        dates=strategy.dates,
        portfolio_values=portfolio_values,
        benchmark_values=benchmark_results.get("benchmark_portfolio_values")
        if benchmark_results["benchmark_available"]
        else None,
        trades=closed_trades,
        prefix="valuekit_",
    )

    # ========================================================================
    # EXPORT DATA
    # ========================================================================
    from backend.backtesting.analytics.export import BacktestExporter

    exporter = BacktestExporter()

    exports = exporter.export_all(
        dates=strategy.dates,
        portfolio_values=portfolio_values,
        benchmark_values=benchmark_results.get("benchmark_portfolio_values")
        if benchmark_results["benchmark_available"]
        else None,
        trades=closed_trades,
        metrics=metrics,
        benchmark=benchmark_results,
        prefix="valuekit_",
        format="csv",  # Change to "excel" for .xlsx
    )

    print("=" * 70)

    # Return all results
    return {
        "start_value": start_value,
        "final_value": final_value,
        "profit": profit,
        "return_pct": profit_pct,
        "cagr": cagr,
        "metrics": metrics,
        "benchmark": benchmark_results,
        "portfolio_values": portfolio_values,
        "dates": strategy.dates,
        "trades": closed_trades,
        "charts": charts,
        "exports": exports,
        "valuation_methods": methods_enabled,  # NEW: Track which methods were used
    }


if __name__ == "__main__":
    # Test with small universe
    results = run_valuekit_backtest(
        universe_name="value_3",
        from_year=2018,
        to_year=2022,
        starting_cash=100000.0,
        use_dcf=True,
        use_pbt=True,
        use_tencap=True,
    )
