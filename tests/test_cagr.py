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


def test_run_analysis_with_stubbed_data(monkeypatch, capsys):
    fake_rows = [
        {"Year": 2019, "EPS": 1.00},
        {"Year": 2020, "EPS": 1.10},
        {"Year": 2021, "EPS": 1.21},
        {"Year": 2022, "EPS": 1.33},
        {"Year": 2023, "EPS": 1.46},
        {"Year": 2024, "EPS": 1.61},
    ]
    fake_mos = {
        "eps": [r["EPS"] for r in fake_rows],
        "book": [],
        "revenue": [],
        "cashflow": [],
    }

    def fake_get_year_data_by_range(ticker, start_year, years):
        return fake_rows, fake_mos

    # robust gegen Importstil patchen
    monkeypatch.setattr(
        "api.fmp_api.get_year_data_by_range", fake_get_year_data_by_range, raising=False
    )
    monkeypatch.setattr(
        backend.logic.cagr,
        "get_year_data_by_range",
        fake_get_year_data_by_range,
        raising=False,
    )

    period = 4
    backend.logic.cagr.run_analysis("TEST", 2019, 2024, period)
    out, _ = capsys.readouterr()

    assert "==== TEST Yearly CAGR (4y periods) ====" in out
    assert re.search(r"\bfrom\s+to\b", out)
    assert re.search(r"\b2019\s+2023\b", out)
    assert re.search(r"\b2020\s+2024\b", out)

    # Deine run_analysis formatiert ohne %
    assert " 9.92" in out and " 9.99" in out
    # alternativ generischer Check:
    # assert re.search(r"\b\d+(?:\.\d{1,2})\b", out)
