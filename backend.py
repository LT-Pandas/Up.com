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
        self._dividend_cache: dict[str, float] = {}

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

        if any("marketStage" in k for k in params):
            query = self._build_query(params, exclude={"marketStage"}, default_limit=100)
            base_screen_url = f"{self.base_url}{query}&apikey={self.api_key}"
            response = requests.get(base_screen_url)
            screener_data = response.json()

            matching_stocks = []

            def fetch_income(symbol: str):
                if symbol in self._income_cache:
                    return symbol, self._income_cache[symbol]
                try:
                    url = (
                        "https://financialmodelingprep.com/api/v3/income-statement/"
                        f"{symbol}?period=quarter&limit=6&apikey={self.api_key}"
                    )
                    data = requests.get(url, timeout=3).json()
                    self._income_cache[symbol] = data
                    return symbol, data
                except Exception:
                    return symbol, []

            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(fetch_income, s["symbol"]) for s in screener_data]
                income_results = {}
                for future in concurrent.futures.as_completed(futures):
                    symbol, inc_data = future.result()
                    if inc_data:
                        income_results[symbol] = inc_data

                for stock in screener_data:
                    symbol = stock["symbol"]
                    income_data = income_results.get(symbol, [])
                    if len(income_data) < 5:
                        continue
                    try:
                        q0, q1, q2, q3, q4 = income_data[:5]
                        rev0 = float(q0.get("revenue") or 0)
                        rev1 = float(q1.get("revenue") or 0)
                        rev2 = float(q2.get("revenue") or 0)
                        rev3 = float(q3.get("revenue") or 0)
                        rev4 = float(q4.get("revenue") or 0)
                        net0 = float(q0.get("netIncome") or 0)
                        net1 = float(q1.get("netIncome") or 0)
                        if any(v == 0 for v in [rev0, rev1, rev2, rev3, rev4]):
                            continue
                        growth0 = (rev0 - rev1) / rev1 * 100
                        growth1 = (rev1 - rev2) / rev2 * 100
                        margin0 = (net0 / rev0) * 100
                        margin1 = (net1 / rev1) * 100
                        rule40_avg = ((growth0 + margin0) + (growth1 + margin1)) / 2
                        flat_prev1 = (rev2 - rev3) / rev3 * 100
                        flat_prev2 = (rev3 - rev4) / rev4 * 100
                        if rule40_avg >= 40 and abs(flat_prev1) <= 5 and abs(flat_prev2) <= 5:
                            matching_stocks.append(stock)
                            if len(matching_stocks) >= 20:
                                break
                    except Exception:
                        continue
            data = matching_stocks
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

    def get_quarterly_dividend(self, symbol: str) -> float | None:
        """Return the most recent quarterly dividend for the given symbol."""
        if symbol in self._dividend_cache:
            return self._dividend_cache[symbol]
        try:
            url = (
                "https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/"
                f"{symbol}?apikey={self.api_key}&limit=1"
            )
            response = requests.get(url)
            data = response.json()
            if isinstance(data, dict):
                data = data.get("historical", [])
            if isinstance(data, list) and data:
                item = data[0]
                val = item.get("dividend") or item.get("adjDividend")
                if val not in [None, "", "N/A"]:
                    val = float(val)
                    self._dividend_cache[symbol] = val
                    return val
        except Exception:
            pass
        return None

    def get_next_quarter_dividend(self, symbol: str) -> float | None:
        """Return the upcoming quarterly dividend for the given symbol."""
        try:
            url = (
                "https://financialmodelingprep.com/api/v3/dividend-calendar?"
                f"symbol={symbol}&apikey={self.api_key}&limit=1"
            )
            response = requests.get(url)
            data = response.json()
            if isinstance(data, list) and data:
                val = data[0].get("dividend")
                if val not in [None, "", "N/A"]:
                    return float(val)
        except Exception:
            pass
        return None
