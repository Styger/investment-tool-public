# tests/test_fmp_api.py
import pytest

# >>> Pfad anpassen, falls nötig
import api.fmp_api


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_fetch_historical_price_json_calls_requests_get(monkeypatch):
    captured = {"url": None, "params": None}

    def fake_get(url, params=None):
        captured["url"] = url
        captured["params"] = params
        return _Resp({"ok": True})

    monkeypatch.setattr(api.fmp_api, "get_api_key", lambda: "APIKEY")
    import requests

    monkeypatch.setattr(requests, "get", fake_get)

    out = api.fmp_api.fetch_historical_price_json("AAPL", "2024-01-02")
    assert out == {"ok": True}
    assert captured["url"].endswith("/historical-price-full/AAPL")
    assert captured["params"]["from"] == "2024-01-02"
    assert captured["params"]["to"] == "2024-01-02"
    assert captured["params"]["apikey"] == "APIKEY"


def test_get_price_on_date_parses_close(monkeypatch, capsys):
    monkeypatch.setattr(
        api.fmp_api,
        "fetch_historical_price_json",
        lambda t, d: {"historical": [{"close": 42.25}]},
    )
    price = api.fmp_api.get_price_on_date("AAPL", "2024-01-02")
    # prints are okay; we just check the value
    assert price == 42.25


def test_get_price_on_date_no_data(monkeypatch):
    monkeypatch.setattr(api.fmp_api, "fetch_historical_price_json", lambda t, d: None)
    assert api.fmp_api.get_price_on_date("AAPL", "2024-01-02") is None

    monkeypatch.setattr(api.fmp_api, "fetch_historical_price_json", lambda t, d: {})
    assert api.fmp_api.get_price_on_date("AAPL", "2024-01-02") is None


def test_get_valid_price_falls_back_days(monkeypatch):
    # First day -> None, second day -> 100.0
    calls = {"n": 0, "dates": []}

    def fake_get_price(ticker, date_str):
        calls["n"] += 1
        calls["dates"].append(date_str)
        if calls["n"] == 1:
            return None
        return 100.0

    monkeypatch.setattr(api.fmp_api, "get_price_on_date", fake_get_price)

    base = "2024-01-10"
    price, used_date = api.fmp_api.get_valid_price("AAPL", base)
    assert price == 100.0
    # should be base-1 day
    assert used_date == "2024-01-09"
    # ensure it tried base first, then base-1
    assert calls["dates"][0] == "2024-01-10"
    assert calls["dates"][1] == "2024-01-09"


def test_get_year_data_by_range_basic(monkeypatch):
    # One target year only (years=0)
    year = 2024
    income = [{"calendarYear": str(year), "revenue": 1_500_000, "eps": 2.345}]
    cash = [
        {"calendarYear": str(year), "freeCashFlow": 500_000, "operatingCashFlow": 0}
    ]
    # leave roic None to exercise "–" path
    metrics = [
        {
            "calendarYear": str(year),
            "bookValuePerShare": 10.0,
            "revenuePerShare": 7.0,
            "roic": None,
        }
    ]

    monkeypatch.setattr(api.fmp_api, "get_income_statement", lambda t, limit=20: income)
    monkeypatch.setattr(api.fmp_api, "get_cashflow_statement", lambda t, limit=20: cash)
    monkeypatch.setattr(api.fmp_api, "get_key_metrics", lambda t, limit=20: metrics)

    rows, mos = api.fmp_api.get_year_data_by_range("AAPL", start_year=year, years=0)

    assert isinstance(rows, list) and len(rows) == 1
    r0 = rows[0]
    assert r0["Year"] == year
    assert r0["Revenue (Mio)"] == 1.5  # 1.5M
    assert r0["Free Cash Flow (Mio)"] == 0.5
    assert r0["EPS"] == pytest.approx(2.35)  # rounded
    assert r0["ROIC"] == "–"  # roic None -> dash

    # MOS metrics lists should have length 1 and carry values
    assert mos["book"] == [10.0]
    assert mos["eps"] == [pytest.approx(2.345)]
    assert mos["revenue"] == [7.0]
    assert mos["cashflow"] == [0]
