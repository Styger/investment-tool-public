# tests/test_cagr_run_analysis.py
import re
import pytest
import backend.logic.cagr


def test_compute_cagr_basic():
    c = backend.logic.cagr.compute_cagr(100, 200, 10)
    expected = (200 / 100) ** (1 / 10) - 1
    assert c == pytest.approx(expected, rel=1e-12)


def test_compute_cagr_identity_zero_growth():
    assert backend.logic.cagr.compute_cagr(100, 100, 5) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize(
    "start,end,years",
    [(0, 100, 5), (-10, 100, 5), (100, 0, 5), (100, 100, 0)],
)
def test_compute_cagr_invalid_inputs(start, end, years):
    with pytest.raises(ValueError):
        backend.logic.cagr.compute_cagr(start, end, years)


def test_run_analysis_with_all_metrics_including_fcf(monkeypatch, capsys):
    """Test für CAGR-Analyse mit allen Metriken inklusive FCF"""
    all_fake_rows = [
        {
            "Year": 2020,
            "EPS": 1.00,
            "Book": 10.00,
            "Revenue": 20.00,
            "CF": 5.00,
            "FCF": 3.00,
        },
        {
            "Year": 2021,
            "EPS": 1.10,
            "Book": 11.00,
            "Revenue": 22.00,
            "CF": 5.50,
            "FCF": 3.30,
        },
        {
            "Year": 2022,
            "EPS": 1.21,
            "Book": 12.10,
            "Revenue": 24.20,
            "CF": 6.05,
            "FCF": 3.63,
        },
        {
            "Year": 2023,
            "EPS": 1.33,
            "Book": 13.31,
            "Revenue": 26.62,
            "CF": 6.66,
            "FCF": 3.99,
        },
        {
            "Year": 2024,
            "EPS": 1.46,
            "Book": 14.64,
            "Revenue": 29.28,
            "CF": 7.32,
            "FCF": 4.39,
        },
    ]

    def fake_get_year_data_by_range(ticker, start_year, years):
        end_year = start_year + years
        filtered_rows = [
            r for r in all_fake_rows if start_year <= r["Year"] <= end_year
        ]
        filtered_mos = {
            "book": [r["Book"] for r in filtered_rows],
            "eps": [r["EPS"] for r in filtered_rows],
            "revenue": [r["Revenue"] for r in filtered_rows],
            "cashflow": [r["CF"] for r in filtered_rows],
            "fcf": [r["FCF"] for r in filtered_rows],
        }
        return filtered_rows, filtered_mos

    monkeypatch.setattr(
        "backend.api.fmp_api.get_year_data_by_range",
        fake_get_year_data_by_range,
        raising=False,
    )
    monkeypatch.setattr(
        backend.logic.cagr,
        "get_year_data_by_range",
        fake_get_year_data_by_range,
        raising=False,
    )

    period = 3
    backend.logic.cagr.run_analysis(
        "ALL_METRICS",
        2020,
        2024,
        period,
        include_book=True,
        include_eps=True,
        include_revenue=True,
        include_cashflow=True,
        include_fcf=True,
    )
    out, _ = capsys.readouterr()

    assert "==== ALL_METRICS Yearly CAGR (3y periods) ====" in out
    assert "Active metrics: book, eps, revenue, cashflow, fcf" in out

    # Alle Spalten sollten vorhanden sein
    assert re.search(r"\bbook\b", out)
    assert re.search(r"\beps\b", out)
    assert re.search(r"\brevenue\b", out)
    assert re.search(r"\bcashflow\b", out)
    assert re.search(r"\bfcf\b", out)
    assert re.search(r"\bavg\b", out)

    # Mindestens zwei Perioden
    assert re.search(r"\b2020\s+2023\b", out)
    assert re.search(r"\b2021\s+2024\b", out)
