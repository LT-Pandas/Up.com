import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from baseFramework import (
    StockScreenerApp,
    calculate_dividend_yield,
    calculate_intraday_change,
)
import pytest


def test_get_param_key_from_label():
    app = StockScreenerApp.__new__(StockScreenerApp)
    assert app.get_param_key_from_label("Lower Market Cap (10M-4T)") == "marketCapMoreThan"
    assert app.get_param_key_from_label("Sector") == "sector"
    assert app.get_param_key_from_label("Stock Search") == "stockSearch"
    assert app.get_param_key_from_label("Unknown") == "Unknown"
    assert app.get_param_key_from_label("Lower Dividend") == "dividendMoreThan"


def test_calculate_dividend_yield():
    # Yield supplied as a ratio should be converted to percentage
    assert calculate_dividend_yield(1.0, 0.02, 50) == pytest.approx(2.0)

    # When no yield supplied, derive from dividend and price
    assert calculate_dividend_yield(2.0, 0, 50) == pytest.approx(4.0)

    # Yield already given as percentage should remain unchanged
    assert calculate_dividend_yield(1.0, 5, 50) == pytest.approx(5.0)


def test_calculate_intraday_change():
    change, pct = calculate_intraday_change(105, 100)
    assert change == pytest.approx(5.0)
    assert pct == pytest.approx(5.0)

    change, pct = calculate_intraday_change(95, 100)
    assert change == pytest.approx(-5.0)
    assert pct == pytest.approx(-5.0)


def test_save_update_delete_algorithm():
    app = StockScreenerApp.__new__(StockScreenerApp)
    app.saved_algorithms = {}
    app.algorithm_previews = {}
    app.params = {"a": 1}
    app.current_algorithm = None

    added = []
    destroyed = []

    class DummyFrame:
        def __init__(self, n):
            self.n = n

        def destroy(self):
            destroyed.append(self.n)

    def stub_add(name):
        added.append(name)
        app.algorithm_previews[name] = DummyFrame(name)

    app._add_algorithm_preview = stub_add

    app.save_algorithm("Test")
    assert app.saved_algorithms["Test"] == {"a": 1}
    assert added == ["Test"]
    assert app.current_algorithm == "Test"

    app.params = {"a": 2}
    app.update_current_algorithm()
    assert app.saved_algorithms["Test"] == {"a": 2}
    assert added == ["Test"]  # no duplicate preview added

    app.delete_algorithm("Test")
    assert "Test" not in app.saved_algorithms
    assert "Test" not in app.algorithm_previews
    assert destroyed == ["Test"]
    assert app.current_algorithm is None
