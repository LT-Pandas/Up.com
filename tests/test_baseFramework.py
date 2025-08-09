import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from baseFramework import StockScreenerApp, calculate_dividend_yield
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
