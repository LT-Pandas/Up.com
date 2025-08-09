import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from baseFramework import StockScreenerApp, compute_dividend_values


def test_get_param_key_from_label():
    app = StockScreenerApp.__new__(StockScreenerApp)
    assert app.get_param_key_from_label("Lower Market Cap (10M-4T)") == "marketCapMoreThan"
    assert app.get_param_key_from_label("Sector") == "sector"
    assert app.get_param_key_from_label("Stock Search") == "stockSearch"
    assert app.get_param_key_from_label("Unknown") == "Unknown"


def test_compute_dividend_values_from_yield():
    div_yield, div_price = compute_dividend_values(None, 2.5, 100)
    assert div_yield == "2.50%"
    assert div_price == "$2.50"
