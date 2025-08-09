import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from baseFramework import extract_dividend


def test_extract_dividend_prefers_annual():
    quote = {"lastDiv": 8, "lastAnnualDividend": 6}
    profile = {}
    assert extract_dividend(quote, profile) == 6


def test_extract_dividend_fallback_last_div():
    quote = {}
    profile = {"lastDiv": "1.25"}
    assert extract_dividend(quote, profile) == 1.25
