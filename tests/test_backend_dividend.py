import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import backend
from backend import StockDataService


def test_dividend_filter(monkeypatch):
    data = [
        {"symbol": "AAA", "lastAnnualDividend": 1.5},
        {"symbol": "BBB", "lastAnnualDividend": 0.5},
        {"symbol": "CCC"},
    ]

    def fake_get(url):
        class Resp:
            def json(self):
                return data

        return Resp()

    monkeypatch.setattr(backend.requests, "get", fake_get)

    service = StockDataService("key", "base", "quote")
    results = service.search({"dividendMoreThan": 1})
    assert [r["symbol"] for r in results] == ["AAA"]

