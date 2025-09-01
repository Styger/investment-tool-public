# tests/test_ten_cap.py
import pytest

# >>> Pfad anpassen, falls dein Modul anders heißt
import logic.tencap


def test__calculate_working_capital_change():
    data = {
        # bereits mit korrektem Vorzeichen (Assets ↑ => negativ, Liabilities ↑ => positiv)
        "accountsReceivables": -3_000_000,
        "accountsPayables": 1_000_000,
    }
    wc, comps = logic.tencap._calculate_working_capital_change(data)
    assert wc == pytest.approx((-3_000_000 + 1_000_000) / 1_000_000)  # = -2.0 (in Mio)
    assert comps["accounts_receivable"] == pytest.approx(-3.0)
    assert comps["accounts_payable"] == pytest.approx(1.0)


def test__format_ten_cap_report_basic():
    data = {
        "ticker": "aapl",
        "year": 2024,
        "profit_before_tax": 50.0,
        "depreciation": 5.0,
        "working_capital_change": -2.0,
        "maintenance_capex": 20.0,  # wird halbiert in der Ausgabezeile
        "owner_earnings": 43.0,
        "shares_outstanding": 200.0,
        "earnings_per_share": 0.215,
        "ten_cap_buy_price": 2.15,
    }
    out = logic.tencap._format_ten_cap_report(data, logic.tencap.language)
    # Stichproben auf Struktur & gerundete Formatierung
    assert "TEN CAP Analyse für AAPL (2024)" in out
    assert "Gewinn vor Steuern:" in out and "$     50.00M" in out
    assert "+ Abschreibungen:" in out and "$      5.00M" in out
    assert "Δ Working Capital:" in out and "$     -2.00M" in out
    assert "- 50% Maintenance CapEx:" in out and "$     10.00M" in out
    assert "= Owner Earnings:" in out and "$     43.00M" in out
    assert "Aktien (Mio):" in out and "    200.00" in out
    assert "Earnings per Share:" in out and "$      0.21" in out
    assert "TEN CAP Buy Price:" in out and "$      2.15" in out


def test__get_ten_cap_result_happy_path(monkeypatch):
    # --- Arrange: Fake-FMP-Daten mit dem Zieljahr 2024
    income = [
        {"calendarYear": "2023", "incomeBeforeTax": 45_000_000},
        {
            "calendarYear": "2024",
            "incomeBeforeTax": 50_000_000,
            "weightedAverageShsOut": 0,
        },  # Shares aus metrics
    ]
    cashflow = [
        {
            "calendarYear": "2024",
            "depreciationAndAmortization": 5_000_000,
            "accountsReceivables": -3_000_000,
            "accountsPayables": 1_000_000,
            "capitalExpenditure": -20_000_000,  # abs() -> 20.0
        }
    ]
    metrics = [{"calendarYear": "2024", "weightedAverageShsOut": 200_000_000}]

    monkeypatch.setattr(
        logic.tencap.fmp_api, "get_income_statement", lambda t, limit=10: income
    )
    monkeypatch.setattr(
        logic.tencap.fmp_api, "get_cashflow_statement", lambda t, limit=10: cashflow
    )
    monkeypatch.setattr(
        logic.tencap.fmp_api, "get_key_metrics", lambda t, limit=10: metrics
    )

    # Erwartungswerte (in Mio):
    pbt = 50.0
    dep = 5.0
    wc = (-3_000_000 + 1_000_000) / 1_000_000  # -2.0
    maint = abs(-20_000_000) / 1_000_000  # 20.0
    owner = pbt + dep + wc - 0.5 * maint  # 50 + 5 - 2 - 10 = 43
    shs = 200_000_000 / 1_000_000  # 200.0
    eps = owner / shs  # 0.215
    price = eps / 0.10  # 2.15

    # --- Act
    res = logic.tencap._get_ten_cap_result("AAPL", 2024)

    # --- Assert
    assert res is not None
    assert res["profit_before_tax"] == pytest.approx(pbt)
    assert res["depreciation"] == pytest.approx(dep)
    assert res["working_capital_change"] == pytest.approx(wc)
    assert res["maintenance_capex"] == pytest.approx(maint)
    assert res["owner_earnings"] == pytest.approx(owner)
    assert res["shares_outstanding"] == pytest.approx(shs)
    assert res["earnings_per_share"] == pytest.approx(eps)
    assert res["ten_cap_buy_price"] == pytest.approx(price)
    # Komponenten vorhanden
    assert res["wc_components"]["accounts_receivable"] == pytest.approx(-3.0)
    assert res["wc_components"]["accounts_payable"] == pytest.approx(1.0)


def test__get_ten_cap_result_missing_year_returns_none(monkeypatch, capsys):
    # nur 2023 vorhanden
    monkeypatch.setattr(
        logic.tencap.fmp_api,
        "get_income_statement",
        lambda t, limit=10: [{"calendarYear": "2023"}],
    )
    monkeypatch.setattr(
        logic.tencap.fmp_api,
        "get_cashflow_statement",
        lambda t, limit=10: [{"calendarYear": "2023"}],
    )
    monkeypatch.setattr(
        logic.tencap.fmp_api,
        "get_key_metrics",
        lambda t, limit=10: [{"calendarYear": "2023"}],
    )

    res = logic.tencap._get_ten_cap_result("MSFT", 2024)
    assert res is None
    out = capsys.readouterr().out
    assert "Could not find complete data for 2024" in out


def test__get_ten_cap_result_invalid_shares_returns_none(monkeypatch, capsys):
    # Shares = 0 -> sollte None liefern
    income = [
        {
            "calendarYear": "2024",
            "incomeBeforeTax": 10_000_000,
            "weightedAverageShsOut": 0,
        }
    ]
    cashflow = [
        {
            "calendarYear": "2024",
            "depreciationAndAmortization": 1_000_000,
            "accountsReceivables": 0,
            "accountsPayables": 0,
            "capitalExpenditure": -2_000_000,
        }
    ]
    metrics = [{"calendarYear": "2024", "weightedAverageShsOut": 0}]

    monkeypatch.setattr(
        logic.tencap.fmp_api, "get_income_statement", lambda t, limit=10: income
    )
    monkeypatch.setattr(
        logic.tencap.fmp_api, "get_cashflow_statement", lambda t, limit=10: cashflow
    )
    monkeypatch.setattr(
        logic.tencap.fmp_api, "get_key_metrics", lambda t, limit=10: metrics
    )

    res = logic.tencap._get_ten_cap_result("TSLA", 2024)
    assert res is None
    out = capsys.readouterr().out
    assert "No valid shares outstanding" in out


def test_print_ten_cap_analysis_success(monkeypatch, capsys):
    # Stub: gib deterministisches Resultat zurück
    fake_res = {
        "ticker": "AAPL",
        "year": 2024,
        "profit_before_tax": 50.0,
        "depreciation": 5.0,
        "working_capital_change": -2.0,
        "maintenance_capex": 20.0,
        "owner_earnings": 43.0,
        "shares_outstanding": 200.0,
        "earnings_per_share": 0.215,
        "ten_cap_buy_price": 2.15,
        "wc_components": {"accounts_receivable": -3.0, "accounts_payable": 1.0},
    }
    monkeypatch.setattr(logic.tencap, "_get_ten_cap_result", lambda t, y: fake_res)

    logic.tencap.print_ten_cap_analysis("AAPL", 2024, logic.tencap.language)
    out = capsys.readouterr().out
    assert "TEN CAP Analyse für AAPL (2024)" in out
    assert "TEN CAP Buy Price:" in out
    assert "$      2.15" in out


def test_print_ten_cap_analysis_error(monkeypatch, capsys):
    monkeypatch.setattr(logic.tencap, "_get_ten_cap_result", lambda t, y: None)
    logic.tencap.print_ten_cap_analysis("EVVTY", 2025, logic.tencap.language)
    out = capsys.readouterr().out
    assert "[ERROR] Could not find complete data for EVVTY in 2025" in out
    assert "2025: N/A" in out


def test_calculate_ten_cap_price(monkeypatch):
    monkeypatch.setattr(
        logic.tencap, "_get_ten_cap_result", lambda t, y: {"ten_cap_buy_price": 3.21}
    )
    assert logic.tencap.calculate_ten_cap_price("AAPL", 2024) == pytest.approx(3.21)

    monkeypatch.setattr(logic.tencap, "_get_ten_cap_result", lambda t, y: None)
    assert logic.tencap.calculate_ten_cap_price("AAPL", 2024) is None
