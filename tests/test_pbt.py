# tests/test_pbt_core.py
import math
import pytest
import logic.pbt


def test__calculate_pbt_price_table_and_value():
    # Arrange
    fcf = 10.0
    growth = 0.10  # 10%
    # Erwarteter PBT-Preis = Summe der Jahre 1..8 (Jahr 0 wird NICHT addiert)
    expected_price = sum(fcf * (1 + growth) ** y for y in range(1, 9))
    expected_price = round(expected_price, 2)

    # Act
    price, table = logic.pbt._calculate_pbt_price(fcf, growth, return_full_table=True)

    # Assert
    assert price == expected_price
    assert isinstance(table, list) and len(table) == 17  # 0..16

    # Zeile Jahr 0: Income = fcf, Summe = 0, kein PBT_Preis
    row0 = table[0]
    assert row0["Jahr"] == 0
    assert math.isclose(row0["Einnahme"], 10.00, rel_tol=0, abs_tol=1e-9)
    assert math.isclose(row0["Summe_Cashflows"], 0.00, rel_tol=0, abs_tol=1e-9)
    assert row0["PBT_Preis"] is None

    # Zeile Jahr 1: Income = 11.0, Summe = 11.0
    row1 = table[1]
    assert row1["Jahr"] == 1
    assert math.isclose(row1["Einnahme"], 11.00, rel_tol=0, abs_tol=1e-9)
    assert math.isclose(row1["Summe_Cashflows"], 11.00, rel_tol=0, abs_tol=1e-9)

    # Zeile Jahr 8: PBT_Preis gesetzt und == Summe_Cashflows == returned price
    row8 = table[8]
    assert row8["Jahr"] == 8
    assert row8["PBT_Preis"] == row8["Summe_Cashflows"] == expected_price


def test_calculate_pbt_from_ticker_happy_path(monkeypatch):
    # Arrange
    # Fake Key Metrics: enthält Eintrag für calendarYear 2024
    fake_km = [
        {"calendarYear": "2023", "freeCashFlowPerShare": 4.0},
        {"calendarYear": "2024", "freeCashFlowPerShare": 5.0},
        {"calendarYear": "2022", "freeCashFlowPerShare": 3.5},
    ]

    def fake_get_key_metrics(ticker, limit=20):
        assert ticker == "AAPL"
        assert limit == 20
        return fake_km

    # Patch in beiden Namensräumen (robust gegen Importstil)
    monkeypatch.setattr(
        "api.fmp_api.get_key_metrics", fake_get_key_metrics, raising=False
    )
    monkeypatch.setattr(
        logic.pbt.fmp_api, "get_key_metrics", fake_get_key_metrics, raising=False
    )

    growth = 0.2
    # Erwarteter Preis aus _calculate_pbt_price für fcf=5.0
    expected_price, expected_table = logic.pbt._calculate_pbt_price(5.0, growth, True)

    # Act
    price, table = logic.pbt.calculate_pbt_from_ticker(
        ticker="AAPL", year=2024, growth_estimate=growth, return_full_table=True
    )

    # Assert
    assert price == expected_price
    assert isinstance(table, list) and len(table) == 17
    # Stichprobe: Jahr 0 Income = 5.00, Summe 0.00; Jahr 8 PBT = expected_price
    assert table[0]["Einnahme"] == 5.00
    assert table[0]["Summe_Cashflows"] == 0.00
    assert table[8]["PBT_Preis"] == expected_price


def test_calculate_pbt_from_ticker_missing_year_raises(monkeypatch, capsys):
    # Arrange: kein Eintrag für 2024
    fake_km = [
        {"calendarYear": "2022", "freeCashFlowPerShare": 3.5},
        {"calendarYear": "2023", "freeCashFlowPerShare": 4.0},
    ]

    def fake_get_key_metrics(ticker, limit=20):
        return fake_km

    monkeypatch.setattr(
        "api.fmp_api.get_key_metrics", fake_get_key_metrics, raising=False
    )
    monkeypatch.setattr(
        logic.pbt.fmp_api, "get_key_metrics", fake_get_key_metrics, raising=False
    )

    # Act + Assert
    with pytest.raises(
        ValueError, match=r"Kein FCF pro Aktie für Jahr 2024 gefunden\."
    ):
        logic.pbt.calculate_pbt_from_ticker(
            ticker="EVVTY", year=2024, growth_estimate=0.15, return_full_table=False
        )

    # Optional: prüfen, dass eine Fehlermeldung auf stdout geloggt wurde
    out = capsys.readouterr().out
    assert "fehlgeschlagen" in out.lower()
