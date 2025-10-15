# tests/test_profitability.py
import pytest
import backend.logic.profitability


def test_calculate_roe_basic():
    """Test basic ROE calculation"""
    net_income = 100_000_000  # 100M
    shareholders_equity = 500_000_000  # 500M

    roe = net_income / shareholders_equity
    assert roe == pytest.approx(0.2, rel=1e-12)  # 20%


def test_calculate_roa_basic():
    """Test basic ROA calculation"""
    net_income = 100_000_000  # 100M
    total_assets = 1_000_000_000  # 1B

    roa = net_income / total_assets
    assert roa == pytest.approx(0.1, rel=1e-12)  # 10%


def test_calculate_margins():
    """Test margin calculations"""
    revenue = 1_000_000_000  # 1B
    gross_profit = 400_000_000  # 400M
    operating_income = 200_000_000  # 200M
    net_income = 150_000_000  # 150M

    gross_margin = gross_profit / revenue
    operating_margin = operating_income / revenue
    net_margin = net_income / revenue

    assert gross_margin == pytest.approx(0.4, rel=1e-12)  # 40%
    assert operating_margin == pytest.approx(0.2, rel=1e-12)  # 20%
    assert net_margin == pytest.approx(0.15, rel=1e-12)  # 15%


def test_calculate_asset_turnover():
    """Test asset turnover calculation"""
    revenue = 1_000_000_000  # 1B
    total_assets = 800_000_000  # 800M

    asset_turnover = revenue / total_assets
    assert asset_turnover == pytest.approx(1.25, rel=1e-12)  # 1.25x


def test_roe_with_zero_equity():
    """Test ROE with zero equity - should be None"""
    net_income = 100_000_000
    shareholders_equity = 0

    # ROE cannot be calculated
    assert shareholders_equity <= 0


def test_single_year_analysis_with_stubbed_data(monkeypatch):
    """Test single year analysis with mocked API data"""
    fake_balance_sheet = [
        {
            "calendarYear": "2024",
            "totalAssets": 1_000_000_000_000,  # 1T
            "totalStockholdersEquity": 500_000_000_000,  # 500B
        }
    ]

    fake_income_statement = [
        {
            "calendarYear": "2024",
            "revenue": 400_000_000_000,  # 400B
            "grossProfit": 180_000_000_000,  # 180B
            "operatingIncome": 120_000_000_000,  # 120B
            "netIncome": 100_000_000_000,  # 100B
        }
    ]

    def fake_get_balance_sheet(ticker, limit):
        return fake_balance_sheet

    def fake_get_income_statement(ticker, limit):
        return fake_income_statement

    monkeypatch.setattr(
        "backend.api.fmp_api.get_balance_sheet",
        fake_get_balance_sheet,
        raising=False,
    )
    monkeypatch.setattr(
        "backend.api.fmp_api.get_income_statement",
        fake_get_income_statement,
        raising=False,
    )

    result = backend.logic.profitability.calculate_profitability_metrics_from_ticker(
        "TEST", 2024
    )

    assert result["ticker"] == "TEST"
    assert result["year"] == 2024
    assert result["revenue"] == 400_000_000_000
    assert result["net_income"] == 100_000_000_000
    assert result["total_assets"] == 1_000_000_000_000
    assert result["shareholders_equity"] == 500_000_000_000

    # ROE = 100B / 500B = 0.2 (20%)
    assert result["roe"] == pytest.approx(0.2, rel=1e-9)

    # ROA = 100B / 1T = 0.1 (10%)
    assert result["roa"] == pytest.approx(0.1, rel=1e-9)

    # Gross Margin = 180B / 400B = 0.45 (45%)
    assert result["gross_margin"] == pytest.approx(0.45, rel=1e-9)

    # Operating Margin = 120B / 400B = 0.3 (30%)
    assert result["operating_margin"] == pytest.approx(0.3, rel=1e-9)

    # Net Margin = 100B / 400B = 0.25 (25%)
    assert result["net_margin"] == pytest.approx(0.25, rel=1e-9)

    # Asset Turnover = 400B / 1T = 0.4
    assert result["asset_turnover"] == pytest.approx(0.4, rel=1e-9)


def test_single_year_with_negative_income(monkeypatch):
    """Test with negative net income"""
    fake_balance_sheet = [
        {
            "calendarYear": "2024",
            "totalAssets": 1_000_000_000_000,
            "totalStockholdersEquity": 500_000_000_000,
        }
    ]

    fake_income_statement = [
        {
            "calendarYear": "2024",
            "revenue": 400_000_000_000,
            "grossProfit": 180_000_000_000,
            "operatingIncome": 120_000_000_000,
            "netIncome": -50_000_000_000,  # Negative!
        }
    ]

    def fake_get_balance_sheet(ticker, limit):
        return fake_balance_sheet

    def fake_get_income_statement(ticker, limit):
        return fake_income_statement

    monkeypatch.setattr(
        "backend.api.fmp_api.get_balance_sheet",
        fake_get_balance_sheet,
        raising=False,
    )
    monkeypatch.setattr(
        "backend.api.fmp_api.get_income_statement",
        fake_get_income_statement,
        raising=False,
    )

    result = backend.logic.profitability.calculate_profitability_metrics_from_ticker(
        "TEST", 2024
    )

    assert result["net_income"] == -50_000_000_000
    # ROE and ROA will be negative
    assert result["roe"] < 0
    assert result["roa"] < 0
    # Net margin will be negative
    assert result["net_margin"] < 0


def test_multi_year_analysis_with_stubbed_data(monkeypatch):
    """Test multi-year analysis with mocked API data"""
    fake_balance_sheet = [
        {
            "calendarYear": "2022",
            "totalAssets": 900_000_000_000,
            "totalStockholdersEquity": 450_000_000_000,
        },
        {
            "calendarYear": "2023",
            "totalAssets": 950_000_000_000,
            "totalStockholdersEquity": 475_000_000_000,
        },
        {
            "calendarYear": "2024",
            "totalAssets": 1_000_000_000_000,
            "totalStockholdersEquity": 500_000_000_000,
        },
    ]

    fake_income_statement = [
        {
            "calendarYear": "2022",
            "revenue": 360_000_000_000,
            "grossProfit": 162_000_000_000,
            "operatingIncome": 108_000_000_000,
            "netIncome": 90_000_000_000,
        },
        {
            "calendarYear": "2023",
            "revenue": 380_000_000_000,
            "grossProfit": 171_000_000_000,
            "operatingIncome": 114_000_000_000,
            "netIncome": 95_000_000_000,
        },
        {
            "calendarYear": "2024",
            "revenue": 400_000_000_000,
            "grossProfit": 180_000_000_000,
            "operatingIncome": 120_000_000_000,
            "netIncome": 100_000_000_000,
        },
    ]

    def fake_get_balance_sheet(ticker, limit):
        return fake_balance_sheet

    def fake_get_income_statement(ticker, limit):
        return fake_income_statement

    monkeypatch.setattr(
        "backend.api.fmp_api.get_balance_sheet",
        fake_get_balance_sheet,
        raising=False,
    )
    monkeypatch.setattr(
        "backend.api.fmp_api.get_income_statement",
        fake_get_income_statement,
        raising=False,
    )

    results = backend.logic.profitability.calculate_profitability_metrics_multi_year(
        "TEST", 2022, 2024
    )

    assert len(results) == 3

    # Check 2022
    assert results[0]["year"] == 2022
    assert results[0]["revenue"] == 360_000_000_000
    assert results[0]["net_income"] == 90_000_000_000
    assert results[0]["roe"] == pytest.approx(0.2, rel=1e-9)  # 90B / 450B

    # Check 2023
    assert results[1]["year"] == 2023
    assert results[1]["revenue"] == 380_000_000_000
    assert results[1]["net_income"] == 95_000_000_000
    assert results[1]["roe"] == pytest.approx(0.2, rel=1e-9)  # 95B / 475B

    # Check 2024
    assert results[2]["year"] == 2024
    assert results[2]["revenue"] == 400_000_000_000
    assert results[2]["net_income"] == 100_000_000_000
    assert results[2]["roe"] == pytest.approx(0.2, rel=1e-9)  # 100B / 500B


def test_multi_year_with_missing_year(monkeypatch):
    """Test multi-year analysis when data for some years is missing"""
    fake_balance_sheet = [
        {
            "calendarYear": "2022",
            "totalAssets": 900_000_000_000,
            "totalStockholdersEquity": 450_000_000_000,
        },
        # 2023 missing
        {
            "calendarYear": "2024",
            "totalAssets": 1_000_000_000_000,
            "totalStockholdersEquity": 500_000_000_000,
        },
    ]

    fake_income_statement = [
        {
            "calendarYear": "2022",
            "revenue": 360_000_000_000,
            "grossProfit": 162_000_000_000,
            "operatingIncome": 108_000_000_000,
            "netIncome": 90_000_000_000,
        },
        # 2023 missing
        {
            "calendarYear": "2024",
            "revenue": 400_000_000_000,
            "grossProfit": 180_000_000_000,
            "operatingIncome": 120_000_000_000,
            "netIncome": 100_000_000_000,
        },
    ]

    def fake_get_balance_sheet(ticker, limit):
        return fake_balance_sheet

    def fake_get_income_statement(ticker, limit):
        return fake_income_statement

    monkeypatch.setattr(
        "backend.api.fmp_api.get_balance_sheet",
        fake_get_balance_sheet,
        raising=False,
    )
    monkeypatch.setattr(
        "backend.api.fmp_api.get_income_statement",
        fake_get_income_statement,
        raising=False,
    )

    results = backend.logic.profitability.calculate_profitability_metrics_multi_year(
        "TEST", 2022, 2024
    )

    assert len(results) == 3

    # 2023 should have 0 values and None ratios
    assert results[1]["year"] == 2023
    assert results[1]["revenue"] == 0
    assert results[1]["net_income"] == 0
    assert results[1]["roe"] is None
    assert results[1]["roa"] is None


@pytest.mark.parametrize(
    "net_income,equity,expected_roe",
    [
        (100_000_000, 500_000_000, 0.2),  # 20% - Very Good
        (150_000_000, 500_000_000, 0.3),  # 30% - Excellent
        (50_000_000, 500_000_000, 0.1),  # 10% - Acceptable
        (200_000_000, 1_000_000_000, 0.2),  # 20% - Very Good
    ],
)
def test_various_roe_scenarios(net_income, equity, expected_roe):
    """Test various ROE scenarios"""
    roe = net_income / equity
    assert roe == pytest.approx(expected_roe, rel=1e-9)


@pytest.mark.parametrize(
    "gross_profit,revenue,expected_margin",
    [
        (400_000_000, 1_000_000_000, 0.4),  # 40%
        (200_000_000, 1_000_000_000, 0.2),  # 20%
        (600_000_000, 1_000_000_000, 0.6),  # 60%
    ],
)
def test_various_margin_scenarios(gross_profit, revenue, expected_margin):
    """Test various margin scenarios"""
    margin = gross_profit / revenue
    assert margin == pytest.approx(expected_margin, rel=1e-9)
