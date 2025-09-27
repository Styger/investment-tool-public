# tests/test_ten_cap_calculator.py
import pytest
from unittest.mock import patch, MagicMock
import logic.tencap


class TestTenCapCore:
    """Tests für die Kern-TEN-CAP-Berechnungslogik"""

    def test_calculate_working_capital_change(self):
        """Test der Working Capital Berechnung"""
        # Arrange
        data = {
            # bereits mit korrektem Vorzeichen (Assets ↑ => negativ, Liabilities ↑ => positiv)
            "accountsReceivables": -3_000_000,
            "accountsPayables": 1_000_000,
        }

        # Act
        wc, comps = logic.tencap._calculate_working_capital_change(data)

        # Assert
        assert wc == pytest.approx(
            (-3_000_000 + 1_000_000) / 1_000_000
        )  # = -2.0 (in Mio)
        assert comps["accounts_receivable"] == pytest.approx(-3.0)
        assert comps["accounts_payable"] == pytest.approx(1.0)

    def test_calculate_owner_earnings(self):
        """Test der Owner Earnings Berechnung"""
        # Arrange
        profit_before_tax = 50.0
        depreciation = 5.0
        working_capital_change = -2.0
        maintenance_capex = 20.0

        # Act
        owner_earnings = logic.tencap._calculate_owner_earnings(
            profit_before_tax, depreciation, working_capital_change, maintenance_capex
        )

        # Assert
        # 50 + 5 + (-2) - (20 * 0.5) = 50 + 5 - 2 - 10 = 43
        expected = (
            profit_before_tax
            + depreciation
            + working_capital_change
            - (maintenance_capex * 0.5)
        )
        assert owner_earnings == pytest.approx(expected)
        assert owner_earnings == pytest.approx(43.0)

    @pytest.mark.parametrize(
        "depreciation,expected_warning",
        [
            (0, True),
            (5.0, False),
        ],
    )
    def test_calculate_owner_earnings_warnings(
        self, depreciation, expected_warning, capsys
    ):
        """Test für Warnungen bei ungewöhnlichen Werten"""
        # Act
        logic.tencap._calculate_owner_earnings(50.0, depreciation, -2.0, 20.0)

        # Assert
        captured = capsys.readouterr()
        if expected_warning:
            assert "Depreciation is 0" in captured.out
        else:
            assert "Depreciation is 0" not in captured.out


class TestTenCapFormatting:
    """Tests für die Report-Formatierung"""

    @pytest.fixture
    def sample_language(self):
        """Fixture mit Sprach-Dictionary"""
        return {
            "ten_cap_calc_title": "TEN CAP Analyse für",
            "ten_cap_profit_before_tax": "Gewinn vor Steuern:",
            "ten_cap_depreciation": "+ Abschreibungen:",
            "ten_cap_working_capital": "Δ Working Capital:",
            "ten_cap_capex": "- 50% Maintenance CapEx:",
            "ten_cap_owner_earnings": "= Owner Earnings:",
            "ten_cap_shares": "Aktien (Mio):",
            "ten_cap_eps": "Earnings per Share:",
            "ten_cap_price": "TEN CAP Buy Price:",
            "ten_cap_fair_value": "TEN CAP Fair Value:",
            "current_stock_price": "Current Stock Price:",
            "price_comparison": "Price vs. Fair Value:",
        }

    @pytest.fixture
    def sample_data(self):
        """Fixture mit Beispiel-Berechnungsdaten"""
        return {
            "ticker": "aapl",
            "year": 2024,
            "profit_before_tax": 50.0,
            "depreciation": 5.0,
            "working_capital_change": -2.0,
            "maintenance_capex": 20.0,
            "owner_earnings": 43.0,
            "shares_outstanding": 200.0,
            "earnings_per_share": 0.215,
            "ten_cap_buy_price": 2.15,
            "ten_cap_fair_value": 4.30,
        }

    def test_format_ten_cap_report_basic(self, sample_data, sample_language):
        """Test der grundlegenden Report-Formatierung"""
        # Act
        output = logic.tencap._format_ten_cap_report(sample_data, sample_language)

        # Assert - Stichproben auf Struktur & gerundete Formatierung
        assert "TEN CAP Analyse für AAPL (2024)" in output
        assert "Gewinn vor Steuern:" in output and "50.00M" in output
        assert "+ Abschreibungen:" in output and "5.00M" in output
        assert "Δ Working Capital:" in output and "-2.00M" in output
        assert "- 50% Maintenance CapEx:" in output and "10.00M" in output  # 20.0 * 0.5
        assert "= Owner Earnings:" in output and "43.00M" in output
        assert "Aktien (Mio):" in output and "200.00" in output
        assert "Earnings per Share:" in output and "0.21" in output
        assert "TEN CAP Buy Price:" in output and "2.15" in output

    def test_format_ten_cap_report_with_current_price(
        self, sample_data, sample_language
    ):
        """Test der Report-Formatierung mit aktuellem Preis"""
        # Arrange
        sample_data.update(
            {
                "current_stock_price": 180.50,
                "price_vs_fair_value_tencap": "Overvalued by 25.0%",
            }
        )

        # Act
        output = logic.tencap._format_ten_cap_report(sample_data, sample_language)

        # Assert
        assert "Current Stock Price:" in output and "180.50" in output
        assert "Price vs. Fair Value:" in output and "Overvalued by 25.0%" in output


class TestTenCapResult:
    """Tests für die _get_ten_cap_result Funktion"""

    @pytest.fixture
    def mock_financial_data(self):
        """Fixture mit Mock-Finanzdaten"""
        return {
            "income": [
                {"calendarYear": "2023", "incomeBeforeTax": 45_000_000},
                {
                    "calendarYear": "2024",
                    "incomeBeforeTax": 50_000_000,
                    "weightedAverageShsOut": 0,  # Shares aus metrics
                },
            ],
            "cashflow": [
                {
                    "calendarYear": "2024",
                    "depreciationAndAmortization": 5_000_000,
                    "accountsReceivables": -3_000_000,
                    "accountsPayables": 1_000_000,
                    "capitalExpenditure": -20_000_000,  # abs() -> 20.0
                }
            ],
            "metrics": [{"calendarYear": "2024", "weightedAverageShsOut": 200_000_000}],
        }

    @patch("logic.tencap.fmp_api.get_income_statement")
    @patch("logic.tencap.fmp_api.get_cashflow_statement")
    @patch("logic.tencap.fmp_api.get_key_metrics")
    @patch("logic.tencap.fmp_api.get_current_price")
    def test_get_ten_cap_result_happy_path(
        self, mock_price, mock_metrics, mock_cashflow, mock_income, mock_financial_data
    ):
        """Test für erfolgreiche TEN CAP Berechnung"""
        # Arrange
        mock_income.return_value = mock_financial_data["income"]
        mock_cashflow.return_value = mock_financial_data["cashflow"]
        mock_metrics.return_value = mock_financial_data["metrics"]
        mock_price.return_value = 175.50

        # Erwartungswerte (in Mio):
        pbt = 50.0
        dep = 5.0
        wc = (-3_000_000 + 1_000_000) / 1_000_000  # -2.0
        maint = abs(-20_000_000) / 1_000_000  # 20.0
        owner = pbt + dep + wc - 0.5 * maint  # 50 + 5 - 2 - 10 = 43
        shs = 200_000_000 / 1_000_000  # 200.0
        eps = owner / shs  # 0.215
        buy_price = eps / 0.10  # 2.15
        fair_value = buy_price * 2  # 4.30

        # Act
        result = logic.tencap._get_ten_cap_result("AAPL", 2024)

        # Assert
        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["year"] == 2024
        assert result["profit_before_tax"] == pytest.approx(pbt)
        assert result["depreciation"] == pytest.approx(dep)
        assert result["working_capital_change"] == pytest.approx(wc)
        assert result["maintenance_capex"] == pytest.approx(maint)
        assert result["owner_earnings"] == pytest.approx(owner)
        assert result["shares_outstanding"] == pytest.approx(shs)
        assert result["earnings_per_share"] == pytest.approx(eps)
        assert result["ten_cap_buy_price"] == pytest.approx(buy_price)
        assert result["ten_cap_fair_value"] == pytest.approx(fair_value)
        assert result["current_stock_price"] == 175.50

        # Working Capital Komponenten
        assert result["wc_components"]["accounts_receivable"] == pytest.approx(-3.0)
        assert result["wc_components"]["accounts_payable"] == pytest.approx(1.0)

        # Investment Recommendation sollte vorhanden sein
        assert "investment_recommendation" in result

    @patch("logic.tencap.fmp_api.get_income_statement")
    @patch("logic.tencap.fmp_api.get_cashflow_statement")
    @patch("logic.tencap.fmp_api.get_key_metrics")
    def test_get_ten_cap_result_missing_year_returns_none(
        self, mock_metrics, mock_cashflow, mock_income, capsys
    ):
        """Test für fehlende Daten für spezifisches Jahr"""
        # Arrange - nur 2023 vorhanden
        mock_income.return_value = [{"calendarYear": "2023"}]
        mock_cashflow.return_value = [{"calendarYear": "2023"}]
        mock_metrics.return_value = [{"calendarYear": "2023"}]

        # Act
        result = logic.tencap._get_ten_cap_result("MSFT", 2024)

        # Assert
        assert result is None
        captured = capsys.readouterr()
        assert "Could not find complete data for 2024" in captured.out

    @patch("logic.tencap.fmp_api.get_income_statement")
    @patch("logic.tencap.fmp_api.get_cashflow_statement")
    @patch("logic.tencap.fmp_api.get_key_metrics")
    def test_get_ten_cap_result_invalid_shares_returns_none(
        self, mock_metrics, mock_cashflow, mock_income, capsys
    ):
        """Test für ungültige Aktienanzahl"""
        # Arrange - Shares = 0 sollte None liefern
        mock_income.return_value = [
            {
                "calendarYear": "2024",
                "incomeBeforeTax": 10_000_000,
                "weightedAverageShsOut": 0,
            }
        ]
        mock_cashflow.return_value = [
            {
                "calendarYear": "2024",
                "depreciationAndAmortization": 1_000_000,
                "accountsReceivables": 0,
                "accountsPayables": 0,
                "capitalExpenditure": -2_000_000,
            }
        ]
        mock_metrics.return_value = [
            {"calendarYear": "2024", "weightedAverageShsOut": 0}
        ]

        # Act
        result = logic.tencap._get_ten_cap_result("TSLA", 2024)

        # Assert
        assert result is None
        captured = capsys.readouterr()
        assert "No valid shares outstanding" in captured.out

    @patch("logic.tencap.fmp_api.get_income_statement")
    @patch("logic.tencap.fmp_api.get_cashflow_statement")
    @patch("logic.tencap.fmp_api.get_key_metrics")
    @patch("logic.tencap.fmp_api.get_current_price")
    def test_get_ten_cap_result_price_fetch_error(
        self, mock_price, mock_metrics, mock_cashflow, mock_income, mock_financial_data
    ):
        """Test für Fehler beim Abrufen des aktuellen Preises"""
        # Arrange
        mock_income.return_value = mock_financial_data["income"]
        mock_cashflow.return_value = mock_financial_data["cashflow"]
        mock_metrics.return_value = mock_financial_data["metrics"]
        mock_price.side_effect = Exception("API Error")

        # Act
        result = logic.tencap._get_ten_cap_result("AAPL", 2024)

        # Assert
        assert result is not None
        assert result["current_stock_price"] is None
        assert result["price_vs_fair_value_tencap"] == "N/A"


class TestInvestmentRecommendation:
    """Tests für Investitionsempfehlungen"""

    @pytest.mark.parametrize(
        "current_price,fair_value,buy_price,expected",
        [
            (2.0, 4.0, 2.15, "Strong Buy (Below TEN CAP price)"),
            (3.0, 4.0, 2.15, "Buy (Below fair value)"),
            (4.2, 4.0, 2.15, "Hold (Near fair value)"),
            (5.0, 4.0, 2.15, "Avoid (Overvalued)"),
            (None, 4.0, 2.15, "No price data available"),
            (0.0, 4.0, 2.15, "No price data available"),
        ],
    )
    def test_investment_recommendations(
        self, current_price, fair_value, buy_price, expected
    ):
        """Parametrisierter Test für alle Investitionsempfehlungen"""
        result = logic.tencap._get_investment_recommendation(
            current_price, fair_value, buy_price
        )
        assert result == expected


class TestPublicInterface:
    """Tests für die öffentlichen Funktionen"""

    @pytest.fixture
    def sample_result(self):
        """Fixture mit Beispiel-Ergebnis"""
        return {
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
            "ten_cap_fair_value": 4.30,
            "current_stock_price": 175.50,
            "price_vs_fair_value_tencap": "Overvalued by 25.0%",
            "investment_recommendation": "Avoid (Overvalued)",
            "wc_components": {"accounts_receivable": -3.0, "accounts_payable": 1.0},
        }

    @patch("logic.tencap._get_ten_cap_result")
    def test_print_ten_cap_analysis_success(
        self, mock_get_result, sample_result, capsys
    ):
        """Test für erfolgreiche Analyse-Ausgabe"""
        # Arrange
        mock_get_result.return_value = sample_result

        # Act
        logic.tencap.print_ten_cap_analysis("AAPL", 2024, logic.tencap.default_language)

        # Assert
        captured = capsys.readouterr()
        assert "TEN CAP Analyse für AAPL (2024)" in captured.out
        assert "TEN CAP Buy Price:" in captured.out
        assert "2.15" in captured.out

    @patch("logic.tencap._get_ten_cap_result")
    def test_print_ten_cap_analysis_error(self, mock_get_result, capsys):
        """Test für Fehlerfall bei Analyse"""
        # Arrange
        mock_get_result.return_value = None

        # Act
        logic.tencap.print_ten_cap_analysis(
            "EVVTY", 2025, logic.tencap.default_language
        )

        # Assert
        captured = capsys.readouterr()
        assert "[ERROR] Could not find complete data for EVVTY in 2025" in captured.out
        assert "2025: N/A" in captured.out

    @patch("logic.tencap._get_ten_cap_result")
    def test_calculate_ten_cap_price_success(self, mock_get_result):
        """Test für erfolgreiche Preisberechnung"""
        # Arrange
        mock_get_result.return_value = {"ten_cap_buy_price": 3.21}

        # Act
        result = logic.tencap.calculate_ten_cap_price("AAPL", 2024)

        # Assert
        assert result == pytest.approx(3.21)

    @patch("logic.tencap._get_ten_cap_result")
    def test_calculate_ten_cap_price_failure(self, mock_get_result):
        """Test für fehlgeschlagene Preisberechnung"""
        # Arrange
        mock_get_result.return_value = None

        # Act
        result = logic.tencap.calculate_ten_cap_price("AAPL", 2024)

        # Assert
        assert result is None

    @patch("logic.tencap._get_ten_cap_result")
    def test_calculate_ten_cap_with_comparison(self, mock_get_result, sample_result):
        """Test für TEN CAP mit Preisvergleich"""
        # Arrange
        mock_get_result.return_value = sample_result

        # Act
        result = logic.tencap.calculate_ten_cap_with_comparison("AAPL", 2024)

        # Assert
        assert result == sample_result
        assert "current_stock_price" in result
        assert "price_vs_fair_value_tencap" in result


class TestEdgeCases:
    """Tests für Grenzfälle und Randwerte"""

    def test_working_capital_change_missing_data(self):
        """Test für fehlende Working Capital Daten"""
        # Arrange
        data = {}  # Keine Working Capital Daten

        # Act
        wc, comps = logic.tencap._calculate_working_capital_change(data)

        # Assert
        assert wc == 0.0
        assert comps["accounts_receivable"] == 0.0
        assert comps["accounts_payable"] == 0.0

    def test_owner_earnings_negative_result(self):
        """Test für negative Owner Earnings"""
        # Arrange - Sehr hohe CapEx
        profit_before_tax = 10.0
        depreciation = 2.0
        working_capital_change = 0.0
        maintenance_capex = 50.0  # Sehr hoch

        # Act
        owner_earnings = logic.tencap._calculate_owner_earnings(
            profit_before_tax, depreciation, working_capital_change, maintenance_capex
        )

        # Assert
        # 10 + 2 + 0 - (50 * 0.5) = 12 - 25 = -13
        assert owner_earnings == pytest.approx(-13.0)

    @pytest.mark.parametrize(
        "year_input,year_str",
        [
            (2024, "2024"),
            ("2024", "2024"),
            (2023, "2023"),
        ],
    )
    @patch("logic.tencap.fmp_api.get_income_statement")
    @patch("logic.tencap.fmp_api.get_cashflow_statement")
    @patch("logic.tencap.fmp_api.get_key_metrics")
    def test_year_conversion_handling(
        self, mock_metrics, mock_cashflow, mock_income, year_input, year_str
    ):
        """Test für String/Int-Konvertierung bei Jahreszahlen"""
        # Arrange
        mock_income.return_value = [
            {"calendarYear": year_str, "incomeBeforeTax": 50_000_000}
        ]
        mock_cashflow.return_value = [
            {
                "calendarYear": year_str,
                "depreciationAndAmortization": 5_000_000,
                "accountsReceivables": 0,
                "accountsPayables": 0,
                "capitalExpenditure": -10_000_000,
            }
        ]
        mock_metrics.return_value = [
            {"calendarYear": year_str, "weightedAverageShsOut": 100_000_000}
        ]

        # Act
        result = logic.tencap._get_ten_cap_result("TEST", year_input)

        # Assert
        assert result is not None
        assert result["year"] == year_input


# Pytest Konfiguration und Ausführung
if __name__ == "__main__":
    # Pytest programmatisch ausführen
    pytest.main([__file__, "-v", "--tb=short"])
