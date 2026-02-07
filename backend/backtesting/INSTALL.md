# Backtesting Installation

## Install Dependencies

```bash
pip install backtrader
pip install matplotlib
pip install quantstats
```

## Verify Installation

```bash
python -c "import backtrader; print('Backtrader version:', backtrader.__version__)"
```

## Run Proof of Concept

```bash
python -m backend.backtesting.backtest_poc
```

You should see:

- Buy & Hold backtest results
- Equity curve chart (popup window)
