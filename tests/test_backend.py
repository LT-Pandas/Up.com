import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend import StockDataService

class DummyRequests:
    def __init__(self):
        self.last_url = None
    def get(self, url, *a, **k):
        self.last_url = url
        class R:
            def __init__(self, u):
                self.url = u
            def json(self):
                return []
        return R(url)

def test_dividend_params_scaled(monkeypatch):
    req = DummyRequests()
    monkeypatch.setattr('backend.requests', req)
    svc = StockDataService('KEY', 'http://example.com/?', 'http://quote/')
    svc.search({'dividendMoreThan': 1.5, 'dividendLowerThan': 2})
    assert 'dividendMoreThan=6.0' in req.last_url
    assert 'dividendLowerThan=8.0' in req.last_url
