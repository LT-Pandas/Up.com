try:
    import requests
except Exception:  # pragma: no cover - optional dependency for tests
    class _RequestsStub:
        def get(self, *a, **k):
            raise ModuleNotFoundError("requests is required to fetch remote data")

    requests = _RequestsStub()
import concurrent.futures
from datetime import datetime
import time


_income_cache: dict[str, list] = {}
_cash_cache: dict[str, list] = {}
_bs_cache: dict[str, list] = {}


def _fetch_json(url: str) -> list | dict:
    response = requests.get(url, timeout=10)
    try:
        return response.json()
    except Exception:
        return []


def _linear_slope(values: list[float | None]) -> float | None:
    pts = [(i, v) for i, v in enumerate(values) if v is not None]
    if len(pts) < 3:
        return None
    xs, ys = zip(*pts)
    n = len(xs)
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xx = sum(x * x for x in xs)
    sum_xy = sum(x * y for x, y in pts)
    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        return None
    return (n * sum_xy - sum_x * sum_y) / denom


def compute_mvp_metrics(symbol: str, api_key: str) -> dict | None:
    try:
        if symbol not in _income_cache:
            url = f"https://financialmodelingprep.com/api/v3/income-statement/{symbol}?period=quarter&apikey={api_key}"
            _income_cache[symbol] = _fetch_json(url)
            time.sleep(0.1)
        if symbol not in _cash_cache:
            url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{symbol}?period=quarter&apikey={api_key}"
            _cash_cache[symbol] = _fetch_json(url)
            time.sleep(0.1)
        if symbol not in _bs_cache:
            url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{symbol}?period=quarter&apikey={api_key}"
            _bs_cache[symbol] = _fetch_json(url)
            time.sleep(0.1)
        income = _income_cache.get(symbol, [])
        cash = _cash_cache.get(symbol, [])
        bs = _bs_cache.get(symbol, [])

        def to_map(data):
            return {item.get("date"): item for item in data if isinstance(item, dict) and item.get("date")}

        inc_map = to_map(income)
        cash_map = to_map(cash)
        bs_map = to_map(bs)
        dates = sorted(set(inc_map) | set(cash_map) | set(bs_map), reverse=True)

        def g(d, m, *keys):
            for k in keys:
                if m.get(d, {}).get(k) is not None:
                    try:
                        return float(m[d][k])
                    except Exception:
                        continue
            return None

        revenue = [g(d, inc_map, "revenue") for d in dates]
        cost = [g(d, inc_map, "costOfRevenue") for d in dates]
        op_income = [g(d, inc_map, "operatingIncome") for d in dates]
        rd = [g(d, inc_map, "researchAndDevelopmentExpenses") for d in dates]
        sga = [g(d, inc_map, "sellingGeneralAndAdministrativeExpenses") for d in dates]
        ocf = [g(d, cash_map, "netCashProvidedByOperatingActivities") for d in dates]
        capex = [g(d, cash_map, "capitalExpenditure") for d in dates]
        deferred_rev = [g(d, bs_map, "deferredRevenue") for d in dates]
        ar = [g(d, bs_map, "netReceivables", "accountsReceivable") for d in dates]
        inventory = [g(d, bs_map, "inventory") for d in dates]
        ap = [g(d, bs_map, "accountPayables", "accountsPayable", "accountsPayables") for d in dates]

        gross_margin_pct = []
        opex_pct = []
        qoq_rev_growth_pct = []
        yoy_rev_growth_pct = []
        rd_pct = []
        delta_gm_pp_yoy = []
        delta_rd_pct_pp_yoy = []

        for i, rev in enumerate(revenue):
            if rev and rev > 0:
                c = cost[i] if i < len(cost) else None
                gm = (rev - c) / rev * 100 if c is not None else None
                gross_margin_pct.append(gm)
                r = rd[i] if i < len(rd) else None
                s = sga[i] if i < len(sga) else None
                if r is not None and s is not None:
                    opex_pct.append((r + s) / rev * 100)
                else:
                    opex_pct.append(None)
                rd_pct.append(r / rev * 100 if r is not None else None)
            else:
                gross_margin_pct.append(None)
                opex_pct.append(None)
                rd_pct.append(None)

            # QoQ growth
            if i + 1 < len(revenue) and revenue[i + 1] and revenue[i + 1] > 0 and rev is not None:
                qoq = (rev - revenue[i + 1]) / revenue[i + 1] * 100
                qoq_rev_growth_pct.append(qoq)
            else:
                qoq_rev_growth_pct.append(None)

            if i + 4 < len(revenue) and revenue[i + 4] and revenue[i + 4] > 0 and rev is not None:
                yoy = (rev - revenue[i + 4]) / revenue[i + 4] * 100
                yoy_rev_growth_pct.append(yoy)
                gm_prev = gross_margin_pct[i + 4] if i + 4 < len(gross_margin_pct) else None
                rd_prev = rd_pct[i + 4] if i + 4 < len(rd_pct) else None
                if gm is not None and gm_prev is not None:
                    delta_gm_pp_yoy.append(gm - gm_prev)
                else:
                    delta_gm_pp_yoy.append(None)
                if rd_pct[i] is not None and rd_prev is not None:
                    delta_rd_pct_pp_yoy.append(rd_pct[i] - rd_prev)
                else:
                    delta_rd_pct_pp_yoy.append(None)
            else:
                yoy_rev_growth_pct.append(None)
                delta_gm_pp_yoy.append(None)
                delta_rd_pct_pp_yoy.append(None)

        rev_ttm = sum(x for x in revenue[:4] if x is not None)
        op_income_ttm = sum(x for x in op_income[:4] if x is not None)
        ocf_ttm = sum(x for x in ocf[:4] if x is not None)
        capex_ttm = sum(x for x in capex[:4] if x is not None)

        op_margin_ttm = (op_income_ttm / rev_ttm * 100) if rev_ttm else None
        prev_rev = sum(x for x in revenue[4:8] if x is not None)
        rev_growth_ttm_pct = ((rev_ttm - prev_rev) / prev_rev * 100) if prev_rev else None
        prev_ocf = sum(x for x in ocf[4:8] if x is not None)
        delta_ocf_ttm_yoy = ocf_ttm - prev_ocf if prev_ocf or prev_ocf == 0 else None
        rd_growth_yoy_pct = ((rd[0] - rd[4]) / rd[4] * 100) if len(rd) > 4 and rd[4] not in [None, 0] and rd[0] is not None else None

        opex_slope = _linear_slope(opex_pct[:4])

        declines = 0
        for i in range(3):
            if i + 1 < len(revenue) and revenue[i] is not None and revenue[i + 1] is not None:
                if revenue[i] < revenue[i + 1]:
                    declines += 1

        yoy_growth_quarter_count = sum(1 for v in yoy_rev_growth_pct[:4] if v is not None and v >= 0)

        rd_growth_lte_rev_growth_boolean = None
        if rd_growth_yoy_pct is not None and rev_growth_ttm_pct is not None:
            rd_growth_lte_rev_growth_boolean = rd_growth_yoy_pct <= rev_growth_ttm_pct

        deferred_rev_yoy_increase = None
        if len(deferred_rev) > 4 and deferred_rev[0] is not None and deferred_rev[4] is not None:
            deferred_rev_yoy_increase = deferred_rev[0] > deferred_rev[4]

        days = 90
        dso = []
        dio = []
        dpo = []
        ccc = []
        for i, rev in enumerate(revenue):
            ar_v = ar[i] if i < len(ar) else None
            inv_v = inventory[i] if i < len(inventory) else None
            ap_v = ap[i] if i < len(ap) else None
            cost_v = cost[i] if i < len(cost) else None
            dso.append((ar_v / rev) * days if rev not in [None, 0] and ar_v is not None else None)
            dio.append((inv_v / cost_v) * days if cost_v not in [None, 0] and inv_v is not None else None)
            dpo.append((ap_v / cost_v) * days if cost_v not in [None, 0] and ap_v is not None else None)
            if dso[-1] is not None and dio[-1] is not None and dpo[-1] is not None:
                ccc.append(dso[-1] + dio[-1] - dpo[-1])
            else:
                ccc.append(None)

        ccc_slope_last4 = _linear_slope(ccc[:4])

        rule40_op_ttm = None
        if rev_growth_ttm_pct is not None and op_margin_ttm is not None:
            rule40_op_ttm = rev_growth_ttm_pct + op_margin_ttm

        capex_pct = (abs(capex_ttm) / rev_ttm * 100) if rev_ttm else None

        metrics = {
            "rev_ttm": rev_ttm if rev_ttm else None,
            "yoy_rev_growth_pct_array": yoy_rev_growth_pct,
            "yoy_growth_quarter_count": yoy_growth_quarter_count,
            "max_qoq_rev_declines_last4": declines,
            "gross_margin_pct_latest": gross_margin_pct[0] if gross_margin_pct else None,
            "delta_gm_pp_yoy_latest": delta_gm_pp_yoy[0] if delta_gm_pp_yoy else None,
            "opex_pct_slope_last4": opex_slope,
            "ocf_ttm": ocf_ttm if ocf_ttm or ocf_ttm == 0 else None,
            "delta_ocf_ttm_yoy": delta_ocf_ttm_yoy,
            "rd_pct_latest": rd_pct[0] if rd_pct else None,
            "delta_rd_pct_pp_yoy_latest": delta_rd_pct_pp_yoy[0] if delta_rd_pct_pp_yoy else None,
            "rd_growth_lte_rev_growth_boolean": rd_growth_lte_rev_growth_boolean,
            "deferred_rev_yoy_increase": deferred_rev_yoy_increase,
            "ccc_slope_last4": ccc_slope_last4,
            "rule40_op_ttm": rule40_op_ttm,
            "capex_pct": capex_pct,
        }
        return metrics
    except Exception:
        return None


class StockDataService:
    """Backend service handling data retrieval from the API."""

    def __init__(self, api_key: str, base_url: str, quote_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.quote_url = quote_url
        self._income_cache: dict[str, list] = {}
        self._metrics_cache: dict[str, dict] = {}

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

        if "ipoDays" in params:
            try:
                days = int(params["ipoDays"])
            except Exception:
                return []
            from datetime import timedelta

            start = datetime.utcnow().date()
            end = start + timedelta(days=days)

            query = (
                f"from={start:%Y-%m-%d}&to={end:%Y-%m-%d}&"
                f"isActivelyTrading={str(params.get('isActivelyTrading')).lower()}&"
                f"limit={params.get('limit', 20)}"
            )
            url = f"{self.base_url}{query}&apikey={self.api_key}"
            response = requests.get(url)
            data = response.json()
            for item in data:
                if "company" in item and "name" not in item:
                    item["name"] = item["company"]
            return data

        mvp_keys = {
            "rev_ttm_min",
            "yoy_rev_growth_pct_min",
            "yoy_growth_quarter_count_min",
            "max_qoq_rev_declines_last4",
            "gross_margin_pct_min",
            "delta_gm_pp_yoy_min",
            "opex_pct_slope_last4_max",
            "ocf_ttm_min",
            "delta_ocf_ttm_yoy_min",
            "rd_pct_max",
            "delta_rd_pct_pp_yoy_max",
            "rd_growth_lte_rev_growth",
            "deferred_rev_yoy_increase",
            "ccc_slope_last4_max",
            "rule40_op_ttm_min",
            "capex_pct_max",
        }

        mvp_params = {k: params.pop(k) for k in list(params.keys()) if k in mvp_keys}

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
        if mvp_params:
            filtered = []
            for item in data:
                symbol = item.get("symbol")
                if not symbol:
                    continue
                metrics = self._metrics_cache.get(symbol)
                if metrics is None:
                    metrics = compute_mvp_metrics(symbol, self.api_key)
                    self._metrics_cache[symbol] = metrics
                if not metrics:
                    continue
                if self._passes_mvp_filters(metrics, mvp_params):
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

    def _passes_mvp_filters(self, m: dict, p: dict) -> bool:
        if "rev_ttm_min" in p:
            if m.get("rev_ttm") is None or m["rev_ttm"] < p["rev_ttm_min"]:
                return False
        if "yoy_rev_growth_pct_min" in p:
            arr = m.get("yoy_rev_growth_pct_array") or []
            count = sum(1 for x in arr[:4] if x is not None and x >= p["yoy_rev_growth_pct_min"])
            min_count = p.get("yoy_growth_quarter_count_min", 1)
            if count < min_count:
                return False
        elif "yoy_growth_quarter_count_min" in p:
            arr = m.get("yoy_rev_growth_pct_array") or []
            count = sum(1 for x in arr[:4] if x is not None and x >= 0)
            if count < p["yoy_growth_quarter_count_min"]:
                return False
        if "max_qoq_rev_declines_last4" in p:
            val = m.get("max_qoq_rev_declines_last4")
            if val is None or val > p["max_qoq_rev_declines_last4"]:
                return False
        if "gross_margin_pct_min" in p:
            val = m.get("gross_margin_pct_latest")
            if val is None or val < p["gross_margin_pct_min"]:
                return False
        if "delta_gm_pp_yoy_min" in p:
            val = m.get("delta_gm_pp_yoy_latest")
            if val is None or val < p["delta_gm_pp_yoy_min"]:
                return False
        if "opex_pct_slope_last4_max" in p:
            val = m.get("opex_pct_slope_last4")
            if val is None or val > p["opex_pct_slope_last4_max"]:
                return False
        if "ocf_ttm_min" in p:
            val = m.get("ocf_ttm")
            if val is None or val < p["ocf_ttm_min"]:
                return False
        if "delta_ocf_ttm_yoy_min" in p:
            val = m.get("delta_ocf_ttm_yoy")
            if val is None or val < p["delta_ocf_ttm_yoy_min"]:
                return False
        if "rd_pct_max" in p:
            val = m.get("rd_pct_latest")
            if val is None or val > p["rd_pct_max"]:
                return False
        if "delta_rd_pct_pp_yoy_max" in p:
            val = m.get("delta_rd_pct_pp_yoy_latest")
            if val is None or val > p["delta_rd_pct_pp_yoy_max"]:
                return False
        if p.get("rd_growth_lte_rev_growth"):
            if not m.get("rd_growth_lte_rev_growth_boolean"):
                return False
        if p.get("deferred_rev_yoy_increase"):
            if not m.get("deferred_rev_yoy_increase"):
                return False
        if "ccc_slope_last4_max" in p:
            val = m.get("ccc_slope_last4")
            if val is None or val > p["ccc_slope_last4_max"]:
                return False
        if "rule40_op_ttm_min" in p:
            val = m.get("rule40_op_ttm")
            if val is None or val < p["rule40_op_ttm_min"]:
                return False
        if "capex_pct_max" in p:
            val = m.get("capex_pct")
            if val is None or val > p["capex_pct_max"]:
                return False
        return True
