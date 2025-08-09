import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend import StockDataService

class DummyRequests:
    def __init__(self, data=None):
        self.last_url = None
        self.data = data or []

    def get(self, url, *a, **k):
        self.last_url = url

        data = self.data

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