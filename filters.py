class MinDividendBlock:
    """Filter stocks by minimum quarterly dividend."""

    def __init__(self, value: float):
        self.value = value

    def apply(self, stocks: list[dict]) -> list[dict]:
        """Return stocks with nextDividend >= self.value."""
        filtered = []
        for stock in stocks:
            next_div = stock.get("nextDividend")
            if next_div is None:
                continue
            try:
                div_val = float(next_div)
            except (TypeError, ValueError):
                continue
            if div_val >= self.value:
                filtered.append(stock)
        return filtered
