"""
Stock Universes for Backtesting
Defines which stocks to test
"""

# Russell 1000 Top 100 by Market Cap (as of 2024)
# Source: https://www.ishares.com/us/products/239707/ishares-russell-1000-etf
RUSSELL_1000_TOP_100 = [
    # Mega Cap Tech
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "AVGO",
    # Large Cap Tech
    "ORCL",
    "CRM",
    "ADBE",
    "CSCO",
    "ACN",
    "AMD",
    "INTC",
    "IBM",
    "QCOM",
    "TXN",
    "INTU",
    "NOW",
    "AMAT",
    "PANW",
    "MU",
    "ADI",
    "LRCX",
    "KLAC",
    "SNPS",
    "CDNS",
    # Financial Services
    "BRKB",
    "JPM",
    "V",
    "MA",
    "BAC",
    "WFC",
    "GS",
    "MS",
    "SPGI",
    "BLK",
    "C",
    "SCHW",
    "AXP",
    "PNC",
    "USB",
    "TFC",
    "COF",
    "BK",
    "AIG",
    "MET",
    # Healthcare
    "UNH",
    "JNJ",
    "LLY",
    "ABBV",
    "MRK",
    "PFE",
    "TMO",
    "ABT",
    "DHR",
    "AMGN",
    "BMY",
    "CVS",
    "ELV",
    "CI",
    "HUM",
    "GILD",
    "VRTX",
    "REGN",
    "ZTS",
    "MCK",
    # Consumer
    "WMT",
    "HD",
    "PG",
    "KO",
    "PEP",
    "COST",
    "MCD",
    "NKE",
    "SBUX",
    "TGT",
    "LOW",
    "TJX",
    "EL",
    "CL",
    "KMB",
    "GIS",
    "K",
    "HSY",
    "CLX",
    "CHD",
    # Energy
    "XOM",
    "CVX",
    "COP",
    "SLB",
    "EOG",
    "MPC",
    "PSX",
    "VLO",
    "OXY",
    "HAL",
    # Industrials
    "BA",
    "UPS",
    "RTX",
    "HON",
    "CAT",
    "GE",
    "MMM",
    "DE",
    "LMT",
    "UNP",
]

# S&P 100 (alternative, smaller universe for faster testing)
SP_100 = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "BRKB",
    "V",
    "UNH",
    "JNJ",
    "XOM",
    "JPM",
    "WMT",
    "LLY",
    "MA",
    "PG",
    "AVGO",
    "HD",
    "CVX",
    "MRK",
    "ABBV",
    "COST",
    "KO",
    "PEP",
    "ADBE",
    "CSCO",
    "MCD",
    "TMO",
    "ACN",
    "NFLX",
    "ABT",
    "CRM",
    "ORCL",
    "DHR",
    "NKE",
    "VZ",
    "BAC",
    "DIS",
    "WFC",
    "CMCSA",
    "TXN",
    "AMD",
    "QCOM",
    "PM",
    "INTC",
    "IBM",
    "INTU",
    "UNP",
    "RTX",
    "HON",
    "GS",
    "SPGI",
    "AMGN",
    "CAT",
    "LOW",
    "MS",
    "COP",
    "BLK",
    "NOW",
    "PFE",
    "AXP",
    "SYK",
    "BKNG",
    "BMY",
    "ISRG",
    "T",
    "LMT",
    "PLD",
    "ELV",
    "VRTX",
    "BA",
    "GE",
    "GILD",
    "ADI",
    "REGN",
    "MMC",
    "TJX",
    "CI",
    "SLB",
    "MDLZ",
    "DE",
    "AMT",
    "SCHW",
    "ADP",
    "CB",
    "CVS",
    "MO",
    "ZTS",
    "SO",
    "DUK",
    "BDX",
    "LRCX",
    "USB",
    "PNC",
    "FI",
    "MU",
    "EOG",
    "TFC",
    "BSX",
    "SHW",
]

# Test Universe (10 stocks for quick testing)
TEST_UNIVERSE_10 = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "JPM",
    "UNH",
    "JNJ",
    "V",
    "WMT",
]

# Test Universe (5 stocks for very quick testing)
TEST_UNIVERSE_5 = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]


# ============================================================================
# VALUE STOCKS TEST UNIVERSE
# Based on actual buy signals from 2018-2022 backtest
# These stocks DEFINITELY generated trades with MOS 10% / Moat 30 thresholds
# ============================================================================

VALUE_TEST_6 = [
    "VZ",  # Verizon - MOS 50.1% (strongest signal!)
    "CMCSA",  # Comcast - MOS 46.5%
    "PFE",  # Pfizer - MOS 27.4%
    "UNP",  # Union Pacific - MOS 22.7%
    "MU",  # Micron - MOS 16.4%
    "MO",  # Altria - MOS 11.1%
]

VALUE_TEST_10 = [
    # Original 6 with strong buy signals
    "VZ",  # Verizon - MOS 50.1%
    "CMCSA",  # Comcast - MOS 46.5%
    "PFE",  # Pfizer - MOS 27.4%
    "UNP",  # Union Pacific - MOS 22.7%
    "MU",  # Micron - MOS 16.4%
    "MO",  # Altria - MOS 11.1%
    # Additional stocks that had trades
    "INTC",  # Intel - appeared in logs
    "COP",  # ConocoPhillips - Energy (cyclical)
    "EOG",  # EOG Resources - Energy (cyclical)
    "META",  # Meta - Tech selloff 2022
]

VALUE_TEST_3 = [
    "VZ",  # Verizon - Strongest MOS signal (50.1%)
    "CMCSA",  # Comcast - Strong MOS signal (46.5%)
    "UNP",  # Union Pacific - Quality Industrial (22.7%)
]


def get_universe(name: str = "test_10"):
    """
    Get stock universe by name

    Args:
        name: Universe name
            - 'russell_100': Russell 1000 Top 100 (100 stocks)
            - 'sp_100': S&P 100 (100 stocks)
            - 'test_10': Generic test (10 stocks)
            - 'test_5': Generic test (5 stocks)
            - 'value_3': Value stocks with guaranteed trades (3 stocks) ⭐ RECOMMENDED FOR DEBUGGING
            - 'value_6': Value stocks with guaranteed trades (6 stocks)
            - 'value_10': Value stocks with guaranteed trades (10 stocks)

    Returns:
        List of ticker symbols
    """
    universes = {
        "russell_100": RUSSELL_1000_TOP_100,
        "sp_100": SP_100,
        "test_10": TEST_UNIVERSE_10,
        "test_5": TEST_UNIVERSE_5,
        "value_3": VALUE_TEST_3,
        "value_6": VALUE_TEST_6,
        "value_10": VALUE_TEST_10,
    }

    return universes.get(name, TEST_UNIVERSE_10)


if __name__ == "__main__":
    print("📊 Available Stock Universes\n")

    for name in [
        "value_3",
        "value_6",
        "value_10",
        "test_5",
        "test_10",
        "sp_100",
        "russell_100",
    ]:
        universe = get_universe(name)
        print(f"{name.upper()}: {len(universe)} stocks")
        if len(universe) <= 10:
            print(f"   Stocks: {', '.join(universe)}")
        else:
            print(f"   First 10: {', '.join(universe[:10])}")
        print()
