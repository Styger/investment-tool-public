# tests/test_mos.py
import math
import pytest

import logic.mos


def test_calculate_mos_value_success(monkeypatch):
    """
    Happy path: EPS is present and > 0. We mock FMP so no network is hit.
    """

    # --- arrange: mock API response ---
    def fake_get_year_data_by_range(ticker, start_year, years=0):
        # matches the shape mos.calculate_mos_value_from_ticker expects
        # first element has "EPS"
        return ([{"EPS": 5.0}], {})  # EPS now = 5.0

    monkeypatch.setattr(
        logic.mos.fmp_api, "get_year_data_by_range", fake_get_year_data_by_range
    )

    # --- act ---
    res = logic.mos.calculate_mos_value_from_ticker(
        ticker="AAPL",
        year=2024,
        growth_rate=0.20,  # 20%
    )

    # --- assert: recompute expected values (same formula as in the function) ---
    eps_now = 5.0
    growth = 0.20
    discount = 0.15
    eps_10y = eps_now * ((1 + growth) ** 10)
    future_pe = growth * 200  # 40
    future_value = eps_10y * future_pe
    fair_value_today = future_value / ((1 + discount) ** 10)
    mos_price = fair_value_today * (1 - 0.50)

    # compare rounded (function rounds to 2 decimals)
    assert res["Ticker"] == "AAPL"
    assert res["Year"] == 2024
    assert res["Growth Rate"] == 20.00
    assert res["EPS_now"] == 5.00
    assert res["EPS_10y"] == round(eps_10y, 2)
    assert res["Future Value"] == round(future_value, 2)
    assert res["Fair Value Today"] == round(fair_value_today, 2)
    assert res["MOS Price (50%)"] == round(mos_price, 2)


def test_calculate_mos_value_no_eps(monkeypatch, capsys):
    """
    When EPS is missing/<=0 we expect the simple zeros dict.
    """

    def fake_get_year_data_by_range(ticker, start_year, years=0):
        return ([{"EPS": 0}], {})  # triggers fallback branch

    monkeypatch.setattr(
        logic.mos.fmp_api, "get_year_data_by_range", fake_get_year_data_by_range
    )

    res = logic.mos.calculate_mos_value_from_ticker(
        ticker="AAPL", year=2024, growth_rate=0.10
    )

    # Should be the minimal dict with zeros
    assert res == {
        "EPS_10y": 0,
        "Future Value": 0,
        "Fair Value Today": 0,
        "MOS Price (50%)": 0,
    }

    # Optional: verify it logged something
    out, _ = capsys.readouterr()
    assert "No valid EPS data found for AAPL in year 2024" in out
