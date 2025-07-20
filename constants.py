"""Configuration constants for StockScreenerApp."""

# Mapping between UI labels and parameter keys used by the API
LABEL_TO_KEY = {
    # Numeric filters
    "Lower Price": "priceMoreThan",
    "Upper Price": "priceLowerThan",
    "Lower Market Cap ($M)": "marketCapMoreThan",
    "Upper Market Cap ($M)": "marketCapLowerThan",
    "Lower Volume": "volumeMoreThan",
    "Upper Volume": "volumeLowerThan",
    "Lower Beta": "betaMoreThan",
    "Upper Beta": "betaLowerThan",
    "Lower Dividend": "dividendMoreThan",
    "Upper Dividend": "dividendLowerThan",
    # Dropdowns + Boolean filters
    "Sector": "sector",
    "Industry": "industry",
    "Exchange": "exchange",
    "Is ETF?": "isEtf",
    "Is Fund?": "isFund",
    "Market Stage": "marketStage",
    "YoY Growth (%)": "yoyGrowth",
    "Profit Margin (%)": "profitMargin",
    "R&D Ratio (%)": "rdRatio",
    "Company Age (yrs)": "companyAge",
    "Rule of 40": "ruleOf40",
    "MVP Stage": "mvpStage",
    # Misc Filters
    "Stock Search": "stockSearch",
    "Limit Results": "limit",
}

# Reverse lookup for labels from parameter keys
KEY_TO_LABEL = {v: k for k, v in LABEL_TO_KEY.items()}


def get_param_key_from_label(label: str) -> str:
    """Return the API parameter key for a given UI label."""
    return LABEL_TO_KEY.get(label, label)


def get_label_from_param_key(key: str) -> str:
    """Return the UI label for a given API parameter key."""
    base = key.split('_')[0]
    return KEY_TO_LABEL.get(base, base)

# Options for dropdown-based filters. ``None`` indicates a free text entry.
FILTER_OPTIONS = {
    "sector": ["Technology", "Energy", "Healthcare", "Financial Services", "Consumer Cyclical",
                "Communication Services", "Industrials", "Basic Materials", "Real Estate", "Utilities"],
    "industry": ["Software", "Oil & Gas", "Biotechnology", "Banks", "Retail", "Semiconductors"],
    "country": ["US", "Canada", "Germany", "UK", "France", "India", "Japan", "China"],
    "exchange": ["NASDAQ", "NYSE", "AMEX"],
    "isEtf": ["true", "false"],
    "isFund": ["true", "false"],
    "isActivelyTrading": ["true", "false"],
    "includeAllShareClasses": ["true", "false"],
    "marketStage": ["Rule of 40: Growth + Margin >= 40%"],
    "yoyGrowth": ["Annual", "Quarterly"],
    "profitMargin": ["Annual", "Quarterly"],
    "rdRatio": ["Annual", "Quarterly"],
    "companyAge": None,
    "ruleOf40": ["≥ 40"],
    "mvpStage": ["Pre-product", "Early Product", "Scaling"],
}
