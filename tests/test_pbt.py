# tests/test_pbt_calculator.py
import pytest
import math
from unittest.mock import patch
import backend.logic.pbt


class TestPBTCore:
    """Tests für die Kern-PBT-Berechnungslogik"""

    def test_calculate_pbt_price_basic_calculation(self):
        """Test der grundlegenden PBT-Preisberechnung"""
        # Arrange
        fcf = 10.0
        growth = 0.10  # 10%

        # Erwarteter Buy Price = Summe der Jahre 1..8 (Jahr 0 wird NICHT addiert)
        expected_buy_price = sum(fcf * (1 + growth) ** y for y in range(1, 9))
        expected_buy_price = round(expected_buy_price, 2)
        expected_fair_value = round(expected_buy_price * 2, 2)

        # Act
        buy_price, fair_value, table = backend.logic.pbt._calculate_pbt_price(
            fcf, growth, return_full_table=True
        )

        # Assert
        assert buy_price == expected_buy_price
        assert fair_value == expected_fair_value
        assert isinstance(table, list)
        assert len(table) == 9  # Jahre 0-8

    def test_calculate_pbt_price_table_structure(self):
        """Test der Tabellenstruktur bei PBT-Berechnung"""
        # Arrange
        fcf = 10.0
        growth = 0.10

        # Act
        buy_price, fair_value, table = backend.logic.pbt._calculate_pbt_price(
            fcf, growth, return_full_table=True
        )

        # Assert - Jahr 0: Income = fcf, Summe = 0
        row0 = table[0]
        assert row0["Jahr"] == 0
        assert math.isclose(row0["Einnahme"], 10.00, abs_tol=1e-9)
        assert math.isclose(row0["Summe_Cashflows"], 0.00, abs_tol=1e-9)

        # Assert - Jahr 1: Income = 11.0, Summe = 11.0
        row1 = table[1]
        assert row1["Jahr"] == 1
        assert math.isclose(row1["Einnahme"], 11.00, abs_tol=1e-9)
        assert math.isclose(row1["Summe_Cashflows"], 11.00, abs_tol=1e-9)

        # Assert - Jahr 8: Buy Price
        row8 = table[8]
        assert row8["Jahr"] == 8
        assert row8["Summe_Cashflows"] == buy_price

    def test_calculate_pbt_price_without_table(self):
        """Test der PBT-Berechnung ohne Tabellenerstellung"""
        # Arrange
        fcf = 5.0
        growth = 0.15

        # Act
        buy_price, fair_value, table = backend.logic.pbt._calculate_pbt_price(
            fcf, growth, return_full_table=False
        )

        # Assert
        assert isinstance(buy_price, float)
        assert buy_price > 0
        assert fair_value == buy_price * 2
        assert table is None

    @pytest.mark.parametrize(
        "fcf,growth,expected_min",
        [
            (1.0, 0.0, 8.0),  # 0% Wachstum: 8 Jahre à 1.0 = 8.0
            (2.0, 0.0, 16.0),  # 0% Wachstum: 8 Jahre à 2.0 = 16.0
            (1.0, 0.1, 11.0),  # 10% Wachstum: mindestens 11.0
        ],
    )
    def test_calculate_pbt_price_different_scenarios(self, fcf, growth, expected_min):
        """Parametrisierter Test für verschiedene FCF/Wachstum-Szenarien"""
        # Act
        buy_price, fair_value, _ = backend.logic.pbt._calculate_pbt_price(
            fcf, growth, return_full_table=False
        )

        # Assert
        assert buy_price >= expected_min
        assert fair_value == buy_price * 2

        # Zusätzliche Plausibilitätsprüfung
        if growth == 0.0:
            expected_exact = fcf * 8
            assert abs(buy_price - expected_exact) < 0.01


class TestPBTFromTicker:
    """Tests für die Ticker-basierte PBT-Berechnung"""

    @pytest.fixture
    def sample_key_metrics(self):
        """Fixture mit Beispiel-Key-Metrics-Daten"""
        return [
            {"calendarYear": "2022", "freeCashFlowPerShare": 3.5},
            {"calendarYear": "2023", "freeCashFlowPerShare": 4.0},
            {"calendarYear": "2024", "freeCashFlowPerShare": 5.0},
        ]

    @pytest.fixture
    def sample_current_price(self):
        """Fixture mit Beispiel-Aktienkurs"""
        return 175.50

    @patch("backend.api.fmp_api.get_key_metrics")
    @patch("backend.api.fmp_api.get_current_price")
    def test_calculate_pbt_from_ticker_success(
        self,
        mock_current_price,
        mock_key_metrics,
        sample_key_metrics,
        sample_current_price,
    ):
        """Test für erfolgreiche PBT-Berechnung von Ticker"""
        # Arrange
        mock_key_metrics.return_value = sample_key_metrics
        mock_current_price.return_value = sample_current_price

        growth = 0.2

        # Erwarteter Preis aus _calculate_pbt_price für fcf=5.0
        expected_buy_price, expected_fair_value, _ = (
            backend.logic.pbt._calculate_pbt_price(5.0, growth, False)
        )

        # Act
        buy_price, fair_value, table, price_info = (
            backend.logic.pbt.calculate_pbt_from_ticker(
                ticker="AAPL",
                year=2024,
                growth_estimate=growth,
                return_full_table=True,
            )
        )

        # Assert
        assert buy_price == expected_buy_price
        assert fair_value == expected_fair_value
        assert isinstance(table, list)
        assert len(table) == 9

        # Price Info Assertions
        assert price_info["Current Stock Price"] == sample_current_price
        assert price_info["Buy Price (8Y Payback)"] == round(expected_buy_price, 2)
        assert price_info["Fair Value (2x Payback)"] == round(expected_fair_value, 2)
        assert price_info["FCF per Share"] == 5.0

    @patch("backend.api.fmp_api.get_key_metrics")
    def test_calculate_pbt_from_ticker_missing_year(
        self, mock_key_metrics, sample_key_metrics
    ):
        """Test für fehlende FCF-Daten für spezifisches Jahr"""
        # Arrange - Entferne 2024 Daten
        limited_metrics = [
            km for km in sample_key_metrics if km["calendarYear"] != "2024"
        ]
        mock_key_metrics.return_value = limited_metrics

        # Act & Assert
        with pytest.raises(ValueError):
            backend.logic.pbt.calculate_pbt_from_ticker(
                ticker="MISSING", year=2024, growth_estimate=0.15
            )

    @patch("backend.api.fmp_api.get_key_metrics")
    @patch("backend.api.fmp_api.get_current_price")
    def test_calculate_pbt_from_ticker_price_fetch_failure(
        self, mock_current_price, mock_key_metrics, sample_key_metrics
    ):
        """Test für Fehler beim Abrufen des aktuellen Preises"""
        # Arrange
        mock_key_metrics.return_value = sample_key_metrics
        mock_current_price.side_effect = Exception("API Error")

        # Act
        buy_price, fair_value, table, price_info = (
            backend.logic.pbt.calculate_pbt_from_ticker(
                ticker="AAPL", year=2024, growth_estimate=0.15
            )
        )

        # Assert
        assert buy_price > 0
        assert fair_value > 0
        assert price_info["Current Stock Price"] == 0.0
        assert price_info["Price Comparison"] == "N/A"
        assert price_info["Investment Recommendation"] == "No price data available"


class TestInvestmentRecommendation:
    """Tests für Investitionsempfehlungen"""

    @pytest.mark.parametrize(
        "current_price,fair_value,buy_price,expected",
        [
            (50.0, 200.0, 100.0, "Strong Buy (At or below payback price)"),
            (150.0, 200.0, 100.0, "Buy (Below fair value)"),
            (205.0, 200.0, 100.0, "Hold (Near fair value)"),
            (250.0, 200.0, 100.0, "Avoid (Overvalued)"),
            (0.0, 200.0, 100.0, "No price data available"),
        ],
    )
    def test_investment_recommendations(
        self, current_price, fair_value, buy_price, expected
    ):
        """Parametrisierter Test für alle Investitionsempfehlungen"""
        result = backend.logic.pbt._get_investment_recommendation(
            current_price, fair_value, buy_price
        )
        assert result == expected


class TestEdgeCases:
    """Tests für Grenzfälle und Randwerte"""

    def test_zero_growth_rate(self):
        """Test für Wachstumsrate von 0%"""
        # Arrange
        fcf = 5.0
        growth = 0.0

        # Act
        buy_price, fair_value, table = backend.logic.pbt._calculate_pbt_price(
            fcf, growth, return_full_table=True
        )

        # Assert - Bei 0% Wachstum: 8 Jahre à 5.0 = 40.0
        expected_buy_price = 8 * fcf
        assert buy_price == expected_buy_price
        assert fair_value == expected_buy_price * 2

        # Alle Jahre 1-8 sollten gleiche Einnahme haben
        for year in range(1, 9):
            assert table[year]["Einnahme"] == fcf

    def test_very_high_growth_rate(self):
        """Test für sehr hohe Wachstumsraten"""
        # Arrange
        fcf = 1.0
        growth = 0.50  # 50% Wachstum

        # Act
        buy_price, fair_value, _ = backend.logic.pbt._calculate_pbt_price(
            fcf, growth, return_full_table=False
        )

        # Assert
        zero_growth_price = 8.0
        assert buy_price > zero_growth_price * 5
        assert fair_value == buy_price * 2


class TestIntegration:
    """Integrationstests für komplette Workflows"""

    @patch("backend.api.fmp_api.get_key_metrics")
    @patch("backend.api.fmp_api.get_current_price")
    def test_complete_workflow_undervalued_stock(
        self, mock_current_price, mock_key_metrics
    ):
        """Test für kompletten Workflow mit unterbewerteter Aktie"""
        # Arrange
        mock_key_metrics.return_value = [
            {"calendarYear": "2024", "freeCashFlowPerShare": 10.0}
        ]
        mock_current_price.return_value = 50.0

        # Act
        buy_price, fair_value, table, price_info = (
            backend.logic.pbt.calculate_pbt_from_ticker(
                ticker="CHEAP",
                year=2024,
                growth_estimate=0.15,
                return_full_table=True,
            )
        )

        # Assert
        assert price_info["Current Stock Price"] < buy_price
        assert "Strong Buy" in price_info["Investment Recommendation"]
        assert len(table) == 9

    @patch("backend.api.fmp_api.get_key_metrics")
    @patch("backend.api.fmp_api.get_current_price")
    def test_complete_workflow_overvalued_stock(
        self, mock_current_price, mock_key_metrics
    ):
        """Test für kompletten Workflow mit überbewerteter Aktie"""
        # Arrange
        mock_key_metrics.return_value = [
            {"calendarYear": "2024", "freeCashFlowPerShare": 2.0}
        ]
        mock_current_price.return_value = 300.0

        # Act
        buy_price, fair_value, _, price_info = (
            backend.logic.pbt.calculate_pbt_from_ticker(
                ticker="EXPENSIVE", year=2024, growth_estimate=0.05
            )
        )

        # Assert
        assert price_info["Current Stock Price"] > fair_value
        assert "Avoid" in price_info["Investment Recommendation"]


# Pytest Konfiguration und Ausführung
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
