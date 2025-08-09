try:
    import requests
except Exception:  # pragma: no cover - optional dependency for tests
    class _RequestsStub:
        def get(self, *a, **k):
            raise ModuleNotFoundError("requests is required to fetch remote data")

    requests = _RequestsStub()
import concurrent.futures
from datetime import datetime


class StockDataService:
    """Backend service handling data retrieval from the API."""

    def __init__(self, api_key: str, base_url: str, quote_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.quote_url = quote_url
        self._income_cache: dict[str, list] = {}

    def _build_query(self, params: dict, exclude: set[str] | None = None,
                     default_limit: int | None = 20) -> str:
        """Convert params to a query string."""
        exclude = exclude or set()
        parts = []
        for key, val in params.items():
            if key in exclude or val in ["", None]:
                continue
            base_key = key.split("_")[0]
            part_val = str(val).lower() if isinstance(val, bool) else val
            parts.append(f"{base_key}={part_val}")
        query = "&".join(parts)
        if default_limit is not None and "limit" not in params:
            query += f"&limit={default_limit}"
        return query

    def search(self, params: dict) -> list:
        """Return a list of search results based on provided parameters."""
        params = dict(params)
        params.setdefault("isActivelyTrading", True)

        if "stockSearch" in params:
            symbol_fragment = params["stockSearch"]
            if not symbol_fragment:
                return []
            url = (
                "https://financialmodelingprep.com/api/v3/search?"
                f"query={symbol_fragment}&limit=10&exchange=NASDAQ&apikey={self.api_key}"
                f"&isActivelyTrading=true"
            )
        else:
            query = self._build_query(params)
            url = f"{self.base_url}{query}&apikey={self.api_key}"

        response = requests.get(url)
        data = response.json()
        if "dividendMoreThan" in params:
            try:
                threshold = float(params["dividendMoreThan"])
            except Exception:
                threshold = 0
            filtered = []
            for item in data:
                div = item.get("lastAnnualDividend") or item.get("lastDiv") or 0
                try:
                    div = float(div)
                except Exception:
                    div = 0
                if div >= threshold:
                    filtered.append(item)
            data = filtered
        return data

    def get_quotes(self, symbols: list[str]) -> list:
        if not symbols:
            return []
        url = f"{self.quote_url}{','.join(symbols)}?apikey={self.api_key}"
        response = requests.get(url)
        return response.json()

    def get_historical_prices(self, symbol: str) -> list:
        try:
            url = (
                "https://financialmodelingprep.com/api/v3/historical-chart/5min/"
                f"{symbol}?apikey={self.api_key}"
            )
            response = requests.get(url)
            data = response.json()
            return [
                (datetime.strptime(item["date"], "%Y-%m-%d %H:%M:%S"), item["close"])
                for item in reversed(data)
            ]
        except Exception:
            return []

    def get_profile(self, symbol: str) -> dict:
        """Return company profile data for the given symbol."""
        try:
            url = (
                f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={self.api_key}"
            )
            response = requests.get(url)
            data = response.json()
            if isinstance(data, list):
                return data[0] if data else {}
            return data
        except Exception:
            return {}
