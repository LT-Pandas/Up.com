import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend import StockDataService

class DummyRequests:
    def __init__(self, data=None, mapping=None):
        self.last_url = None
        self.data = data or []
        self.mapping = mapping or {}

    def get(self, url, *a, **k):
        self.last_url = url

        data = self.data
        for key, val in self.mapping.items():
            if key in url:
                data = val
                break

        class R:
            def __init__(self, d):
                self._data = d

            def json(self):
                return self._data

        return R(data)

def test_dividend_params_pass_through(monkeypatch):
    req = DummyRequests()
    monkeypatch.setattr('backend.requests', req)
    svc = StockDataService('KEY', 'http://example.com/?', 'http://quote/')
    svc.search({'dividendMoreThan': 1.5, 'dividendLowerThan': 2})
    assert 'dividendMoreThan=1.5' in req.last_url
    assert 'dividendLowerThan=2' in req.last_url
    assert 'isActivelyTrading=true' in req.last_url

def test_get_dividend_history_url(monkeypatch):
    req = DummyRequests()
    monkeypatch.setattr('backend.requests', req)
    svc = StockDataService('KEY', 'http://example.com/?', 'http://quote/')
    svc.get_dividend_history('AAPL')
    assert req.last_url == (
        'https://financialmodelingprep.com/stable/dividends?symbol=AAPL&apikey=KEY'
    )


def test_market_stage_rule_of_40(monkeypatch):
    mapping = {
        'example.com/': [{'symbol': 'AAA'}, {'symbol': 'BBB'}],
        'income-statement/AAA': [
            {'revenue': 170, 'netIncome': 51},
            {'revenue': 150, 'netIncome': 15},
            {'revenue': 101, 'netIncome': 0},
            {'revenue': 100, 'netIncome': 0},
            {'revenue': 100, 'netIncome': 0},
        ],
        'income-statement/BBB': [
            {'revenue': 110, 'netIncome': 5},
            {'revenue': 105, 'netIncome': 4},
            {'revenue': 100, 'netIncome': 3},
            {'revenue': 95, 'netIncome': 2},
            {'revenue': 90, 'netIncome': 1},
        ],
    }
    req = DummyRequests(mapping=mapping)
    monkeypatch.setattr('backend.requests', req)
    svc = StockDataService('KEY', 'http://example.com/?', 'http://quote/')
    results = svc.search({'marketStage': 'Product Market Fit (Rule of 40)'})
    assert results == [{'symbol': 'AAA'}]

