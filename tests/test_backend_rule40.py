import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import backend
from backend import StockDataService

def test_market_stage_rule_of_40(monkeypatch):
    screener_data = [{"symbol": "AAA"}, {"symbol": "BBB"}]
    income_match = [
        {"revenue": 200, "netIncome": 30},
        {"revenue": 150, "netIncome": 30},
        {"revenue": 100, "netIncome": 0},
        {"revenue": 100, "netIncome": 0},
        {"revenue": 100, "netIncome": 0},
        {"revenue": 100, "netIncome": 0},
    ]
    income_no_match = [
        {"revenue": 100, "netIncome": 0},
        {"revenue": 100, "netIncome": 0},
        {"revenue": 100, "netIncome": 0},
        {"revenue": 100, "netIncome": 0},
        {"revenue": 100, "netIncome": 0},
        {"revenue": 100, "netIncome": 0},
    ]

    def fake_get(url, timeout=None):
        class Resp:
            def __init__(self, data):
                self._data = data
            def json(self):
                return self._data
        if "income-statement" in url:
            if "AAA" in url:
                return Resp(income_match)
            else:
                return Resp(income_no_match)
        return Resp(screener_data)

    monkeypatch.setattr(backend.requests, "get", fake_get)

    service = StockDataService("key", "base", "quote")
    results = service.search({"marketStage": "Product Market Fit (Rule of 40)"})
    assert [r["symbol"] for r in results] == ["AAA"]
