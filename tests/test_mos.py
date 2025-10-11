import pytest
from unittest.mock import patch, MagicMock
import backend.logic.mos

# Annahme: Der Hauptcode ist in einem Modul namens 'mos_calculator'
# from mos_calculator import calculate_mos_value_from_ticker, _get_investment_recommendation


class TestMOSValueCalculator:
    """Test-Klasse für MOS Value Calculator"""

    @pytest.fixture
    def sample_data(self):
        """Fixture mit Beispieldaten"""
        return {
            "eps_data": [{"EPS": 6.05}],  # Beispiel für AAPL 2024
            "ticker": "AAPL",
            "year": 2024,
            "growth_rate": 0.10,
            "discount_rate": 0.15,
            "margin_of_safety": 0.50,
            "current_price": 150.00,
        }

    @patch("backend.api.fmp_api.get_year_data_by_range")
    @patch("backend.api.fmp_api.get_current_price")
    def test_normal_calculation_success(
        self, mock_current_price, mock_year_data, sample_data
    ):
        """Test für normale erfolgreiche Berechnung"""
        # Arrange
        mock_year_data.return_value = (sample_data["eps_data"], None)
        mock_current_price.return_value = sample_data["current_price"]

        # Act
        result = backend.logic.mos.calculate_mos_value_from_ticker(
            ticker=sample_data["ticker"],
            year=sample_data["year"],
            growth_rate=sample_data["growth_rate"],
            margin_of_safety=sample_data["margin_of_safety"],
        )

        # Assert
        assert result["Ticker"] == "AAPL"
        assert result["Year"] == 2024
        assert result["Growth Rate"] == 10.0
        assert result["EPS_now"] == 6.05
        assert result["EPS_10y"] > 0
        assert result["Fair Value Today"] > 0
        assert result["MOS Price"] > 0
        assert result["Current Stock Price"] == 150.00
        assert "Margin of Safety" in result
        assert result["Margin of Safety"] == "50.0%"

    @patch("backend.api.fmp_api.get_year_data_by_range")
    @patch("backend.api.fmp_api.get_current_price")
    def test_no_eps_data_available(self, mock_current_price, mock_year_data):
        """Test für fehlende EPS-Daten"""
        # Arrange
        mock_year_data.return_value = ([], None)
        mock_current_price.return_value = 150.00

        # Act
        result = backend.logic.mos.calculate_mos_value_from_ticker(
            ticker="INVALID", year=2024, growth_rate=0.10
        )

        # Assert
        assert result["EPS_10y"] == 0
        assert result["Future Value"] == 0
        assert result["Fair Value Today"] == 0
        assert result["MOS Price"] == 0
        assert result["Price vs Fair Value"] == "N/A"

    @patch("backend.api.fmp_api.get_year_data_by_range")
    @patch("backend.api.fmp_api.get_current_price")
    def test_negative_eps_handling(self, mock_current_price, mock_year_data):
        """Test für negative EPS-Werte"""
        # Arrange
        mock_year_data.return_value = ([{"EPS": -2.50}], None)
        mock_current_price.return_value = 50.00

        # Act
        result = backend.logic.mos.calculate_mos_value_from_ticker(
            ticker="LOSS", year=2024, growth_rate=0.10
        )

        # Assert - Bei negativen EPS sollten alle Werte 0 sein
        assert result["EPS_10y"] == 0
        assert result["Fair Value Today"] == 0
        assert result["MOS Price"] == 0

    @patch("backend.api.fmp_api.get_year_data_by_range")
    @patch("backend.api.fmp_api.get_current_price")
    def test_api_price_fetch_failure(
        self, mock_current_price, mock_year_data, sample_data
    ):
        """Test für Fehler beim Abrufen des aktuellen Preises"""
        # Arrange
        mock_year_data.return_value = (sample_data["eps_data"], None)
        mock_current_price.side_effect = Exception("API Error")

        # Act
        result = backend.logic.mos.calculate_mos_value_from_ticker(
            ticker="AAPL", year=2024, growth_rate=0.10
        )

        # Assert
        assert result["Current Stock Price"] == 0.0
        assert result["Price vs Fair Value"] == "N/A"
        assert (
            result["Fair Value Today"] > 0
        )  # Andere Berechnungen sollten funktionieren

    @patch("backend.api.fmp_api.get_year_data_by_range")
    @patch("backend.api.fmp_api.get_current_price")
    def test_different_margin_of_safety_values(
        self, mock_current_price, mock_year_data, sample_data
    ):
        """Test für verschiedene Margin of Safety Werte"""
        # Arrange
        mock_year_data.return_value = (sample_data["eps_data"], None)
        mock_current_price.return_value = 150.00

        # Act
        result_25 = backend.logic.mos.calculate_mos_value_from_ticker(
            ticker="AAPL", year=2024, growth_rate=0.10, margin_of_safety=0.25
        )
        result_75 = backend.logic.mos.calculate_mos_value_from_ticker(
            ticker="AAPL", year=2024, growth_rate=0.10, margin_of_safety=0.75
        )

        # Assert
        assert result_25["MOS Price"] > result_75["MOS Price"]
        assert result_25["Margin of Safety"] == "25.0%"
        assert result_75["Margin of Safety"] == "75.0%"

    @pytest.mark.parametrize(
        "eps,expected_zero_values",
        [
            (0, True),  # EPS = 0
            (-1.5, True),  # Negative EPS
            (0.01, False),  # Positive EPS
        ],
    )
    @patch("backend.api.fmp_api.get_year_data_by_range")
    @patch("backend.api.fmp_api.get_current_price")
    def test_eps_edge_cases(
        self, mock_current_price, mock_year_data, eps, expected_zero_values
    ):
        """Parametrisierter Test für verschiedene EPS-Werte"""
        # Arrange
        mock_year_data.return_value = ([{"EPS": eps}], None)
        mock_current_price.return_value = 100.0

        # Act
        result = backend.logic.mos.calculate_mos_value_from_ticker("TEST", 2024, 0.10)

        # Assert
        if expected_zero_values:
            assert result["Fair Value Today"] == 0
            assert result["MOS Price"] == 0
        else:
            assert result["Fair Value Today"] > 0
            assert result["MOS Price"] > 0


class TestInvestmentRecommendation:
    """Tests für die Investitionsempfehlungen"""

    @pytest.mark.parametrize(
        "current_price,fair_value,mos_price,expected",
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
        self, current_price, fair_value, mos_price, expected
    ):
        """Parametrisierter Test für alle Investitionsempfehlungen"""
        result = backend.logic.mos._get_investment_recommendation(
            current_price, fair_value, mos_price
        )
        assert result == expected


class TestEdgeCases:
    """Tests für Grenzfälle und Randwerte"""

    @patch("backend.api.fmp_api.get_year_data_by_range")
    @patch("backend.api.fmp_api.get_current_price")
    def test_zero_growth_rate(self, mock_current_price, mock_year_data):
        """Test für Wachstumsrate von 0%"""
        # Arrange
        mock_year_data.return_value = ([{"EPS": 5.0}], None)
        mock_current_price.return_value = 100.0

        # Act
        result = backend.logic.mos.calculate_mos_value_from_ticker(
            "AAPL", 2024, growth_rate=0.0
        )

        # Assert
        assert result["EPS_10y"] == 5.0  # Bei 0% Wachstum sollte EPS_10y = EPS_now sein
        assert result["Future Value"] == 0.0  # Future PE sollte 0 sein (0 * 200)

    @patch("backend.api.fmp_api.get_year_data_by_range")
    @patch("backend.api.fmp_api.get_current_price")
    def test_very_high_growth_rate(self, mock_current_price, mock_year_data):
        """Test für sehr hohe Wachstumsraten"""
        # Arrange
        mock_year_data.return_value = ([{"EPS": 1.0}], None)
        mock_current_price.return_value = 100.0

        # Act
        result = backend.logic.mos.calculate_mos_value_from_ticker(
            "GROWTH", 2024, growth_rate=0.50
        )

        # Assert
        assert result["EPS_10y"] > 50.0
        assert result["Future Value"] > 5000.0

    @pytest.mark.parametrize(
        "growth_rate,expected_multiplier",
        [
            (0.05, 1.629),  # 5% über 10 Jahre ≈ 1.629x
            (0.10, 2.594),  # 10% über 10 Jahre ≈ 2.594x
            (0.15, 4.046),  # 15% über 10 Jahre ≈ 4.046x
        ],
    )
    @patch("backend.api.fmp_api.get_year_data_by_range")
    @patch("backend.api.fmp_api.get_current_price")
    def test_growth_rate_calculations(
        self, mock_current_price, mock_year_data, growth_rate, expected_multiplier
    ):
        """Test für verschiedene Wachstumsraten"""
        # Arrange
        eps_base = 1.0
        mock_year_data.return_value = ([{"EPS": eps_base}], None)
        mock_current_price.return_value = 100.0

        # Act
        result = backend.logic.mos.calculate_mos_value_from_ticker(
            "TEST", 2024, growth_rate=growth_rate
        )

        # Assert (mit Toleranz für Rundungsfehler)
        expected_eps_10y = eps_base * expected_multiplier
        assert abs(result["EPS_10y"] - expected_eps_10y) < 0.01


# Fixtures für komplexere Testszenarien
@pytest.fixture
def mock_api_responses():
    """Fixture für verschiedene API-Antworten"""
    return {
        "success": ([{"EPS": 6.05}], None),
        "no_data": ([], None),
        "negative_eps": ([{"EPS": -2.50}], None),
        "zero_eps": ([{"EPS": 0.0}], None),
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


# Integration Tests
class TestIntegration:
    """Integrationstests für komplette Workflows"""

    @patch("backend.api.fmp_api.get_year_data_by_range")
    @patch("backend.api.fmp_api.get_current_price")
    def test_complete_workflow_undervalued_stock(
        self, mock_current_price, mock_year_data
    ):
        """Test für kompletten Workflow mit unterbewerteter Aktie"""
        # Arrange - Szenario: Aktie ist unterbewertet
        mock_year_data.return_value = ([{"EPS": 5.0}], None)
        mock_current_price.return_value = 50.0  # Niedrig im Vergleich zu fair value

        # Act
        result = backend.logic.mos.calculate_mos_value_from_ticker(
            "CHEAP", 2024, 0.10, 0.15, 0.30
        )

        # Assert
        assert result["Current Stock Price"] < result["Fair Value Today"]
        assert (
            "Buy" in result["Investment Recommendation"]
            or "Strong Buy" in result["Investment Recommendation"]
        )
        assert result["Percentage Difference"] < 0  # Negativ = unterbewertet


# Conftest.py Inhalt (separate Datei)
"""
# conftest.py
import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_print(monkeypatch):
    '''Automatisches Mocking von print für saubere Test-Ausgabe'''
    def mock_print_func(*args, **kwargs):
        pass  # Keine Ausgabe während Tests
    monkeypatch.setattr("builtins.print", mock_print_func)

@pytest.fixture
def clean_environment():
    '''Fixture für saubere Testumgebung'''
    # Setup
    yield
    # Teardown falls notwendig
"""

# Pytest Kommandos und Konfiguration
"""
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
"""

if __name__ == "__main__":
    # Pytest programmatisch ausführen
    pytest.main([__file__, "-v"])
