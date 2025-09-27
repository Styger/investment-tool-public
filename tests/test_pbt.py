# tests/test_pbt_calculator.py
import pytest
import math
from unittest.mock import patch
import logic.pbt

# Import der zu testenden Module
# from logic.pbt import calculate_pbt_from_ticker, _calculate_pbt_price, _get_investment_recommendation


class TestPBTCore:
    """Tests für die Kern-PBT-Berechnungslogik"""

    def test_calculate_pbt_price_basic_calculation(self):
        """Test der grundlegenden PBT-Preisberechnung"""
        # Arrange
        fcf = 10.0
        growth = 0.10  # 10%

        # Erwarteter PBT-Preis = Summe der Jahre 1..8 (Jahr 0 wird NICHT addiert)
        expected_price = sum(fcf * (1 + growth) ** y for y in range(1, 9))
        expected_price = round(expected_price, 2)

        # Act
        price, table = logic.pbt._calculate_pbt_price(
            fcf, growth, return_full_table=True
        )

        # Assert
        assert price == expected_price
        assert isinstance(table, list)
        assert len(table) == 17  # Jahre 0-16

    def test_calculate_pbt_price_table_structure(self):
        """Test der Tabellenstruktur bei PBT-Berechnung"""
        # Arrange
        fcf = 10.0
        growth = 0.10

        # Act
        price, table = logic.pbt._calculate_pbt_price(
            fcf, growth, return_full_table=True
        )

        # Assert - Jahr 0: Income = fcf, Summe = 0, kein Fair_Value
        row0 = table[0]
        assert row0["Jahr"] == 0
        assert math.isclose(row0["Einnahme"], 10.00, abs_tol=1e-9)
        assert math.isclose(row0["Summe_Cashflows"], 0.00, abs_tol=1e-9)
        assert row0["Fair_Value"] is None

        # Assert - Jahr 1: Income = 11.0, Summe = 11.0
        row1 = table[1]
        assert row1["Jahr"] == 1
        assert math.isclose(row1["Einnahme"], 11.00, abs_tol=1e-9)
        assert math.isclose(row1["Summe_Cashflows"], 11.00, abs_tol=1e-9)
        assert row1["Fair_Value"] is None

        # Assert - Jahr 8: Fair_Value gesetzt
        row8 = table[8]
        assert row8["Jahr"] == 8
        assert row8["Fair_Value"] == row8["Summe_Cashflows"]
        assert row8["Fair_Value"] == price

    def test_calculate_pbt_price_without_table(self):
        """Test der PBT-Berechnung ohne Tabellenerstellung"""
        # Arrange
        fcf = 5.0
        growth = 0.15

        # Act
        price, table = logic.pbt._calculate_pbt_price(
            fcf, growth, return_full_table=False
        )

        # Assert
        assert isinstance(price, float)
        assert price > 0
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
        price, _ = logic.pbt._calculate_pbt_price(fcf, growth, return_full_table=False)

        # Assert - Preis sollte mindestens expected_min sein
        assert price >= expected_min

        # Zusätzliche Plausibilitätsprüfung
        if growth == 0.0:
            expected_exact = fcf * 8  # Exakt bei 0% Wachstum
            assert abs(price - expected_exact) < 0.01


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

    @patch("api.fmp_api.get_key_metrics")
    @patch("api.fmp_api.get_current_price")
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
        mos = 0.25

        # Erwarteter Preis aus _calculate_pbt_price für fcf=5.0
        expected_fair_value, _ = logic.pbt._calculate_pbt_price(5.0, growth, False)
        expected_buy_price = expected_fair_value * (1 - mos)

        # Act
        fair_value, buy_price, table, price_info = logic.pbt.calculate_pbt_from_ticker(
            ticker="AAPL",
            year=2024,
            growth_estimate=growth,
            margin_of_safety=mos,
            return_full_table=True,
        )

        # Assert
        assert fair_value == expected_fair_value
        assert buy_price == expected_buy_price
        assert isinstance(table, list)
        assert len(table) == 17

        # Price Info Assertions
        assert price_info["Current Stock Price"] == sample_current_price
        assert price_info["Fair Value (8Y Payback)"] == round(expected_fair_value, 2)
        assert price_info["Buy Price (with MOS)"] == round(expected_buy_price, 2)
        assert price_info["Margin of Safety"] == "25.0%"
        assert price_info["FCF per Share"] == 5.0

    @patch("api.fmp_api.get_key_metrics")
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
        with pytest.raises(
            ValueError, match=r"Kein FCF pro Aktie für Jahr 2024 gefunden"
        ):
            logic.pbt.calculate_pbt_from_ticker(
                ticker="MISSING", year=2024, growth_estimate=0.15
            )

    @patch("api.fmp_api.get_key_metrics")
    @patch("api.fmp_api.get_current_price")
    def test_calculate_pbt_from_ticker_price_fetch_failure(
        self, mock_current_price, mock_key_metrics, sample_key_metrics
    ):
        """Test für Fehler beim Abrufen des aktuellen Preises"""
        # Arrange
        mock_key_metrics.return_value = sample_key_metrics
        mock_current_price.side_effect = Exception("API Error")

        # Act
        fair_value, buy_price, table, price_info = logic.pbt.calculate_pbt_from_ticker(
            ticker="AAPL", year=2024, growth_estimate=0.15
        )

        # Assert
        assert fair_value > 0
        assert buy_price > 0
        assert price_info["Current Stock Price"] == 0.0
        assert price_info["Price vs Fair Value"] == "N/A"
        assert price_info["Investment Recommendation"] == "No price data available"

    @patch("api.fmp_api.get_key_metrics")
    @patch("api.fmp_api.get_current_price")
    def test_calculate_pbt_from_ticker_without_table(
        self, mock_current_price, mock_key_metrics, sample_key_metrics
    ):
        """Test für PBT-Berechnung ohne Tabellenerstellung"""
        # Arrange
        mock_key_metrics.return_value = sample_key_metrics
        mock_current_price.return_value = 150.0

        # Act
        fair_value, buy_price, table, price_info = logic.pbt.calculate_pbt_from_ticker(
            ticker="AAPL", year=2024, growth_estimate=0.1, return_full_table=False
        )

        # Assert
        assert fair_value > 0
        assert buy_price > 0
        assert table is None
        assert isinstance(price_info, dict)

    @pytest.mark.parametrize(
        "mos,expected_mos_text",
        [
            (0.20, "20.0%"),
            (0.30, "30.0%"),
            (0.50, "50.0%"),
        ],
    )
    @patch("api.fmp_api.get_key_metrics")
    @patch("api.fmp_api.get_current_price")
    def test_different_margin_of_safety(
        self,
        mock_current_price,
        mock_key_metrics,
        sample_key_metrics,
        mos,
        expected_mos_text,
    ):
        """Test für verschiedene Margin of Safety Werte"""
        # Arrange
        mock_key_metrics.return_value = sample_key_metrics
        mock_current_price.return_value = 100.0

        # Act
        fair_value, buy_price, _, price_info = logic.pbt.calculate_pbt_from_ticker(
            ticker="AAPL", year=2024, growth_estimate=0.1, margin_of_safety=mos
        )

        # Assert
        expected_buy_price = fair_value * (1 - mos)
        assert abs(buy_price - expected_buy_price) < 0.01
        assert price_info["Margin of Safety"] == expected_mos_text


class TestInvestmentRecommendation:
    """Tests für Investitionsempfehlungen"""

    @pytest.mark.parametrize(
        "current_price,fair_value,buy_price,expected",
        [
            (50.0, 200.0, 100.0, "Strong Buy (Below MOS price)"),
            (150.0, 200.0, 100.0, "Buy (Below fair value)"),
            (205.0, 200.0, 100.0, "Hold (Near fair value)"),
            (250.0, 200.0, 100.0, "Avoid (Overvalued)"),
            (0.0, 200.0, 100.0, "No price data available"),
            (-10.0, 200.0, 100.0, "No price data available"),
        ],
    )
    def test_investment_recommendations(
        self, current_price, fair_value, buy_price, expected
    ):
        """Parametrisierter Test für alle Investitionsempfehlungen"""
        result = logic.pbt._get_investment_recommendation(
            current_price, fair_value, buy_price
        )
        assert result == expected

    def test_hold_boundary_condition(self):
        """Test für Grenzfall bei Hold-Empfehlung"""
        # Genau 10% über fair value sollte noch Hold sein
        fair_value = 100.0
        buy_price = 75.0
        current_price = 110.0  # Exakt 10% über fair value

        result = logic.pbt._get_investment_recommendation(
            current_price, fair_value, buy_price
        )
        assert result == "Hold (Near fair value)"


class TestEdgeCases:
    """Tests für Grenzfälle und Randwerte"""

    def test_zero_growth_rate(self):
        """Test für Wachstumsrate von 0%"""
        # Arrange
        fcf = 5.0
        growth = 0.0

        # Act
        price, table = logic.pbt._calculate_pbt_price(
            fcf, growth, return_full_table=True
        )

        # Assert
        # Bei 0% Wachstum: 8 Jahre à 5.0 = 40.0
        expected_price = 8 * fcf
        assert price == expected_price

        # Alle Jahre 1-8 sollten gleiche Einnahme haben
        for year in range(1, 9):
            assert table[year]["Einnahme"] == fcf

    def test_very_high_growth_rate(self):
        """Test für sehr hohe Wachstumsraten"""
        # Arrange
        fcf = 1.0
        growth = 0.50  # 50% Wachstum

        # Act
        price, _ = logic.pbt._calculate_pbt_price(fcf, growth, return_full_table=False)

        # Assert - Bei 50% Wachstum sollte der Wert deutlich höher sein als bei 0%
        zero_growth_price = 8.0  # 8 Jahre à 1.0
        assert price > zero_growth_price * 5  # Mindestens 5x höher

        # Berechnung prüfen: 1*(1.5^1 + 1.5^2 + ... + 1.5^8)
        expected_min = sum(1.0 * (1.5**year) for year in range(1, 9))
        assert price >= expected_min * 0.95  # Mit kleiner Toleranz

    def test_negative_fcf_handling(self):
        """Test für negative FCF-Werte"""
        # Arrange
        fcf = -5.0
        growth = 0.10

        # Act
        price, table = logic.pbt._calculate_pbt_price(
            fcf, growth, return_full_table=True
        )

        # Assert
        # Negative FCF sollte zu negativem Preis führen
        assert price < 0
        assert table[0]["Einnahme"] == -5.0

    @pytest.mark.parametrize(
        "year_str,year_int",
        [
            ("2024", 2024),
            (2024, 2024),
            ("2023", 2023),
        ],
    )
    @patch("api.fmp_api.get_key_metrics")
    def test_year_string_int_conversion(self, mock_key_metrics, year_str, year_int):
        """Test für String/Int-Konvertierung bei Jahreszahlen"""
        # Arrange
        mock_key_metrics.return_value = [
            {"calendarYear": year_str, "freeCashFlowPerShare": 5.0}
        ]

        # Act & Assert - sollte nicht fehlschlagen
        try:
            fair_value, _, _, _ = logic.pbt.calculate_pbt_from_ticker(
                ticker="TEST", year=year_int, growth_estimate=0.1
            )
            assert fair_value > 0
        except ValueError:
            pytest.fail("Year conversion should work for both string and int")


class TestIntegration:
    """Integrationstests für komplette Workflows"""

    @patch("api.fmp_api.get_key_metrics")
    @patch("api.fmp_api.get_current_price")
    def test_complete_workflow_undervalued_stock(
        self, mock_current_price, mock_key_metrics
    ):
        """Test für kompletten Workflow mit unterbewerteter Aktie"""
        # Arrange - Szenario: Aktie ist stark unterbewertet
        mock_key_metrics.return_value = [
            {"calendarYear": "2024", "freeCashFlowPerShare": 10.0}
        ]
        mock_current_price.return_value = 50.0  # Niedrig im Vergleich zu fair value

        # Act
        fair_value, buy_price, table, price_info = logic.pbt.calculate_pbt_from_ticker(
            ticker="CHEAP",
            year=2024,
            growth_estimate=0.15,
            margin_of_safety=0.30,
            return_full_table=True,
        )

        # Assert
        assert price_info["Current Stock Price"] < price_info["Fair Value (8Y Payback)"]
        assert (
            "Strong Buy" in price_info["Investment Recommendation"]
            or "Buy" in price_info["Investment Recommendation"]
        )
        assert price_info["Percentage Diff (Fair)"] < 0  # Negativ = unterbewertet
        assert len(table) == 17

    @patch("api.fmp_api.get_key_metrics")
    @patch("api.fmp_api.get_current_price")
    def test_complete_workflow_overvalued_stock(
        self, mock_current_price, mock_key_metrics
    ):
        """Test für kompletten Workflow mit überbewerteter Aktie"""
        # Arrange - Szenario: Aktie ist überbewertet
        mock_key_metrics.return_value = [
            {"calendarYear": "2024", "freeCashFlowPerShare": 2.0}
        ]
        mock_current_price.return_value = 300.0  # Hoch im Vergleich zu fair value

        # Act
        fair_value, buy_price, _, price_info = logic.pbt.calculate_pbt_from_ticker(
            ticker="EXPENSIVE", year=2024, growth_estimate=0.05
        )

        # Assert
        assert price_info["Current Stock Price"] > price_info["Fair Value (8Y Payback)"]
        assert "Avoid" in price_info["Investment Recommendation"]
        assert price_info["Percentage Diff (Fair)"] > 0  # Positiv = überbewertet


# Fixtures für erweiterte Tests
@pytest.fixture
def mock_api_responses():
    """Fixture für verschiedene API-Antworten"""
    return {
        "success_metrics": [{"calendarYear": "2024", "freeCashFlowPerShare": 6.05}],
        "no_data": [],
        "multiple_years": [
            {"calendarYear": "2022", "freeCashFlowPerShare": 4.0},
            {"calendarYear": "2023", "freeCashFlowPerShare": 5.0},
            {"calendarYear": "2024", "freeCashFlowPerShare": 6.0},
        ],
    }


@pytest.fixture
def calculation_scenarios():
    """Fixture für verschiedene Berechnungsszenarien"""
    return [
        {
            "ticker": "AAPL",
            "growth": 0.08,
            "mos": 0.30,
            "description": "Conservative Apple",
        },
        {
            "ticker": "NVDA",
            "growth": 0.25,
            "mos": 0.50,
            "description": "Aggressive Nvidia",
        },
        {
            "ticker": "KO",
            "growth": 0.03,
            "mos": 0.20,
            "description": "Defensive Coca-Cola",
        },
    ]


# Pytest Konfiguration und Ausführung
if __name__ == "__main__":
    # Pytest programmatisch ausführen
    pytest.main([__file__, "-v", "--tb=short"])
