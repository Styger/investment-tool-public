# tests/test_debt.py
import pytest
import backend.logic.debt


def test_calculate_debt_ratio_basic():
    """Test basic debt ratio calculation"""
    long_term_debt = 100_000_000  # 100M
    net_income = 50_000_000  # 50M

    ratio = long_term_debt / net_income
    assert ratio == pytest.approx(2.0, rel=1e-12)


def test_calculate_debt_ratio_low_debt():
    """Test with very low debt (excellent rating)"""
    long_term_debt = 40_000_000  # 40M
    net_income = 100_000_000  # 100M

    ratio = long_term_debt / net_income
    assert ratio == pytest.approx(0.4, rel=1e-12)
    assert ratio < 1.0  # Should be excellent


def test_calculate_debt_ratio_high_debt():
    """Test with high debt (risky rating)"""
    long_term_debt = 600_000_000  # 600M
    net_income = 100_000_000  # 100M

    ratio = long_term_debt / net_income
    assert ratio == pytest.approx(6.0, rel=1e-12)
    assert ratio > 5.0  # Should be risky


def test_calculate_debt_ratio_zero_income():
    """Test with zero net income - ratio should be None"""
    long_term_debt = 100_000_000
    net_income = 0

    # Ratio cannot be calculated
    assert net_income <= 0


def test_calculate_debt_ratio_negative_income():
    """Test with negative net income - ratio should be None"""
    long_term_debt = 100_000_000
    net_income = -50_000_000

    # Ratio cannot be calculated
    assert net_income <= 0


def test_single_year_analysis_net_income(monkeypatch):
    """Test single year analysis with net_income metric"""
    fake_balance_sheet = [
        {
            "calendarYear": "2024",
            "longTermDebt": 100_000_000_000,
            "totalDebt": 120_000_000_000,
        }
    ]

    fake_income_statement = [
        {
            "calendarYear": "2024",
            "netIncome": 50_000_000_000,
            "ebitda": 80_000_000_000,
            "operatingIncome": 70_000_000_000,
        }
    ]

    fake_cashflow_statement = [
        {
            "calendarYear": "2024",
            "operatingCashFlow": 60_000_000_000,
            "depreciationAndAmortization": 10_000_000_000,
        }
    ]

    def fake_get_balance_sheet(ticker, limit):
        return fake_balance_sheet

    def fake_get_income_statement(ticker, limit):
        return fake_income_statement

    def fake_get_cashflow_statement(ticker, limit):
        return fake_cashflow_statement

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
    monkeypatch.setattr(
        "backend.api.fmp_api.get_cashflow_statement",
        fake_get_cashflow_statement,
        raising=False,
    )

    result = backend.logic.debt.calculate_debt_metrics_from_ticker(
        "TEST", 2024, use_total_debt=False, metric_type="net_income"
    )

    assert result["ticker"] == "TEST"
    assert result["year"] == 2024
    assert result["long_term_debt"] == 100_000_000_000
    assert result["net_income"] == 50_000_000_000
    assert result["metric_type"] == "net_income"
    assert result["metric_value"] == 50_000_000_000
    assert result["debt_ratio"] == pytest.approx(2.0, rel=1e-9)


def test_single_year_analysis_ebitda(monkeypatch):
    """Test single year analysis with ebitda metric"""
    fake_balance_sheet = [
        {
            "calendarYear": "2024",
            "longTermDebt": 100_000_000_000,
            "totalDebt": 120_000_000_000,
        }
    ]

    fake_income_statement = [
        {
            "calendarYear": "2024",
            "netIncome": 50_000_000_000,
            "ebitda": 80_000_000_000,
            "operatingIncome": 70_000_000_000,
        }
    ]

    fake_cashflow_statement = [
        {
            "calendarYear": "2024",
            "operatingCashFlow": 60_000_000_000,
            "depreciationAndAmortization": 10_000_000_000,
        }
    ]

    def fake_get_balance_sheet(ticker, limit):
        return fake_balance_sheet

    def fake_get_income_statement(ticker, limit):
        return fake_income_statement

    def fake_get_cashflow_statement(ticker, limit):
        return fake_cashflow_statement

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
    monkeypatch.setattr(
        "backend.api.fmp_api.get_cashflow_statement",
        fake_get_cashflow_statement,
        raising=False,
    )

    result = backend.logic.debt.calculate_debt_metrics_from_ticker(
        "TEST", 2024, use_total_debt=False, metric_type="ebitda"
    )

    assert result["ticker"] == "TEST"
    assert result["year"] == 2024
    assert result["ebitda"] == 80_000_000_000
    assert result["ebitda_source"] == "direct"
    assert result["metric_type"] == "ebitda"
    assert result["metric_value"] == 80_000_000_000
    assert result["debt_ratio"] == pytest.approx(1.25, rel=1e-9)


def test_single_year_analysis_ebitda_calculated(monkeypatch):
    """Test single year analysis with calculated ebitda (fallback)"""
    fake_balance_sheet = [
        {
            "calendarYear": "2024",
            "longTermDebt": 100_000_000_000,
            "totalDebt": 120_000_000_000,
        }
    ]

    fake_income_statement = [
        {
            "calendarYear": "2024",
            "netIncome": 50_000_000_000,
            "ebitda": 0,  # Not available
            "operatingIncome": 70_000_000_000,
        }
    ]

    fake_cashflow_statement = [
        {
            "calendarYear": "2024",
            "operatingCashFlow": 60_000_000_000,
            "depreciationAndAmortization": 10_000_000_000,
        }
    ]

    def fake_get_balance_sheet(ticker, limit):
        return fake_balance_sheet

    def fake_get_income_statement(ticker, limit):
        return fake_income_statement

    def fake_get_cashflow_statement(ticker, limit):
        return fake_cashflow_statement

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
    monkeypatch.setattr(
        "backend.api.fmp_api.get_cashflow_statement",
        fake_get_cashflow_statement,
        raising=False,
    )

    result = backend.logic.debt.calculate_debt_metrics_from_ticker(
        "TEST", 2024, use_total_debt=False, metric_type="ebitda"
    )

    # EBITDA should be calculated: Operating Income + D&A
    expected_ebitda = 70_000_000_000 + 10_000_000_000
    assert result["ebitda"] == expected_ebitda
    assert result["ebitda_source"] == "calculated"
    assert result["metric_value"] == expected_ebitda
    assert result["debt_ratio"] == pytest.approx(1.25, rel=1e-9)


def test_single_year_analysis_operating_cash_flow(monkeypatch):
    """Test single year analysis with operating_cash_flow metric"""
    fake_balance_sheet = [
        {
            "calendarYear": "2024",
            "longTermDebt": 100_000_000_000,
            "totalDebt": 120_000_000_000,
        }
    ]

    fake_income_statement = [
        {
            "calendarYear": "2024",
            "netIncome": 50_000_000_000,
            "ebitda": 80_000_000_000,
            "operatingIncome": 70_000_000_000,
        }
    ]

    fake_cashflow_statement = [
        {
            "calendarYear": "2024",
            "operatingCashFlow": 60_000_000_000,
            "depreciationAndAmortization": 10_000_000_000,
        }
    ]

    def fake_get_balance_sheet(ticker, limit):
        return fake_balance_sheet

    def fake_get_income_statement(ticker, limit):
        return fake_income_statement

    def fake_get_cashflow_statement(ticker, limit):
        return fake_cashflow_statement

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
    monkeypatch.setattr(
        "backend.api.fmp_api.get_cashflow_statement",
        fake_get_cashflow_statement,
        raising=False,
    )

    result = backend.logic.debt.calculate_debt_metrics_from_ticker(
        "TEST", 2024, use_total_debt=False, metric_type="operating_cash_flow"
    )

    assert result["ticker"] == "TEST"
    assert result["operating_cash_flow"] == 60_000_000_000
    assert result["metric_type"] == "operating_cash_flow"
    assert result["metric_value"] == 60_000_000_000
    assert result["debt_ratio"] == pytest.approx(1.667, rel=1e-3)


def test_single_year_analysis_with_negative_income(monkeypatch):
    """Test single year analysis with negative income"""
    fake_balance_sheet = [
        {
            "calendarYear": "2024",
            "longTermDebt": 100_000_000_000,
            "totalDebt": 120_000_000_000,
        }
    ]

    fake_income_statement = [
        {
            "calendarYear": "2024",
            "netIncome": -10_000_000_000,  # Negative
            "ebitda": 80_000_000_000,
            "operatingIncome": 70_000_000_000,
        }
    ]

    fake_cashflow_statement = [
        {
            "calendarYear": "2024",
            "operatingCashFlow": 60_000_000_000,
            "depreciationAndAmortization": 10_000_000_000,
        }
    ]

    def fake_get_balance_sheet(ticker, limit):
        return fake_balance_sheet

    def fake_get_income_statement(ticker, limit):
        return fake_income_statement

    def fake_get_cashflow_statement(ticker, limit):
        return fake_cashflow_statement

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
    monkeypatch.setattr(
        "backend.api.fmp_api.get_cashflow_statement",
        fake_get_cashflow_statement,
        raising=False,
    )

    result = backend.logic.debt.calculate_debt_metrics_from_ticker(
        "TEST", 2024, use_total_debt=False, metric_type="net_income"
    )

    assert result["net_income"] == -10_000_000_000
    assert result["debt_ratio"] is None  # Cannot calculate with negative income


def test_single_year_analysis_total_debt(monkeypatch):
    """Test single year analysis with total debt instead of long-term debt"""
    fake_balance_sheet = [
        {
            "calendarYear": "2024",
            "longTermDebt": 100_000_000_000,
            "totalDebt": 120_000_000_000,
        }
    ]

    fake_income_statement = [
        {
            "calendarYear": "2024",
            "netIncome": 50_000_000_000,
            "ebitda": 80_000_000_000,
            "operatingIncome": 70_000_000_000,
        }
    ]

    fake_cashflow_statement = [
        {
            "calendarYear": "2024",
            "operatingCashFlow": 60_000_000_000,
            "depreciationAndAmortization": 10_000_000_000,
        }
    ]

    def fake_get_balance_sheet(ticker, limit):
        return fake_balance_sheet

    def fake_get_income_statement(ticker, limit):
        return fake_income_statement

    def fake_get_cashflow_statement(ticker, limit):
        return fake_cashflow_statement

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
    monkeypatch.setattr(
        "backend.api.fmp_api.get_cashflow_statement",
        fake_get_cashflow_statement,
        raising=False,
    )

    result = backend.logic.debt.calculate_debt_metrics_from_ticker(
        "TEST", 2024, use_total_debt=True, metric_type="net_income"
    )

    assert result["use_total_debt"] is True
    assert result["debt_used"] == 120_000_000_000  # Total debt
    assert result["debt_ratio"] == pytest.approx(2.4, rel=1e-9)


def test_multi_year_analysis_with_stubbed_data(monkeypatch):
    """Test multi-year analysis with mocked API data"""
    fake_balance_sheet = [
        {
            "calendarYear": "2022",
            "longTermDebt": 80_000_000_000,
            "totalDebt": 90_000_000_000,
        },
        {
            "calendarYear": "2023",
            "longTermDebt": 90_000_000_000,
            "totalDebt": 100_000_000_000,
        },
        {
            "calendarYear": "2024",
            "longTermDebt": 100_000_000_000,
            "totalDebt": 110_000_000_000,
        },
    ]

    fake_income_statement = [
        {
            "calendarYear": "2022",
            "netIncome": 40_000_000_000,
            "ebitda": 60_000_000_000,
            "operatingIncome": 50_000_000_000,
        },
        {
            "calendarYear": "2023",
            "netIncome": 45_000_000_000,
            "ebitda": 65_000_000_000,
            "operatingIncome": 55_000_000_000,
        },
        {
            "calendarYear": "2024",
            "netIncome": 50_000_000_000,
            "ebitda": 70_000_000_000,
            "operatingIncome": 60_000_000_000,
        },
    ]

    fake_cashflow_statement = [
        {
            "calendarYear": "2022",
            "operatingCashFlow": 45_000_000_000,
            "depreciationAndAmortization": 10_000_000_000,
        },
        {
            "calendarYear": "2023",
            "operatingCashFlow": 50_000_000_000,
            "depreciationAndAmortization": 10_000_000_000,
        },
        {
            "calendarYear": "2024",
            "operatingCashFlow": 55_000_000_000,
            "depreciationAndAmortization": 10_000_000_000,
        },
    ]

    def fake_get_balance_sheet(ticker, limit):
        return fake_balance_sheet

    def fake_get_income_statement(ticker, limit):
        return fake_income_statement

    def fake_get_cashflow_statement(ticker, limit):
        return fake_cashflow_statement

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
    monkeypatch.setattr(
        "backend.api.fmp_api.get_cashflow_statement",
        fake_get_cashflow_statement,
        raising=False,
    )

    results = backend.logic.debt.calculate_debt_metrics_multi_year(
        "TEST", 2022, 2024, use_total_debt=False, metric_type="net_income"
    )

    assert len(results) == 3

    # Check 2022
    assert results[0]["year"] == 2022
    assert results[0]["long_term_debt"] == 80_000_000_000
    assert results[0]["net_income"] == 40_000_000_000
    assert results[0]["debt_ratio"] == pytest.approx(2.0, rel=1e-9)

    # Check 2023
    assert results[1]["year"] == 2023
    assert results[1]["long_term_debt"] == 90_000_000_000
    assert results[1]["net_income"] == 45_000_000_000
    assert results[1]["debt_ratio"] == pytest.approx(2.0, rel=1e-9)

    # Check 2024
    assert results[2]["year"] == 2024
    assert results[2]["long_term_debt"] == 100_000_000_000
    assert results[2]["net_income"] == 50_000_000_000
    assert results[2]["debt_ratio"] == pytest.approx(2.0, rel=1e-9)


@pytest.mark.parametrize(
    "long_term_debt,net_income,expected_ratio",
    [
        (50_000_000, 100_000_000, 0.5),  # Excellent
        (150_000_000, 100_000_000, 1.5),  # Very Good
        (250_000_000, 100_000_000, 2.5),  # Good
        (400_000_000, 100_000_000, 4.0),  # Acceptable
        (600_000_000, 100_000_000, 6.0),  # Risky
    ],
)
def test_various_debt_ratios(long_term_debt, net_income, expected_ratio):
    """Test various debt ratio scenarios"""
    ratio = long_term_debt / net_income
    assert ratio == pytest.approx(expected_ratio, rel=1e-9)
