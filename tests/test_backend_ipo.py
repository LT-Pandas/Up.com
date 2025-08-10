import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import backend
from backend import StockDataService


def test_ipo_search(monkeypatch):
    captured = {}

    def fake_get(url):
        captured['url'] = url

        class Resp:
            def json(self):
                return [{"symbol": "ABC", "company": "ABC Corp", "ipoDate": "2024-01-15"}]

        return Resp()

    monkeypatch.setattr(backend.requests, "get", fake_get)

    class FakeDate(backend.datetime):
        @classmethod
        def utcnow(cls):
            return cls(2024, 1, 1)

    monkeypatch.setattr(backend, "datetime", FakeDate)

    service = StockDataService("key", "base", "quote")
    results = service.search({"ipoDays": 14})

    assert "from=2024-01-01" in captured['url']
    assert "to=2024-01-15" in captured['url']
    assert results[0]["name"] == "ABC Corp"

