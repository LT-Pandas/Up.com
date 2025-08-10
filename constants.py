"""Configuration constants for StockScreenerApp."""

# Mapping between UI labels and parameter keys used by the API
LABEL_TO_KEY = {
    # Numeric filters
    "Lower Price": "priceMoreThan",
    "Upper Price": "priceLowerThan",
    "Lower Market Cap (10M-4T)": "marketCapMoreThan",
    "Upper Market Cap (10M-4T)": "marketCapLowerThan",
    "Lower Volume": "volumeMoreThan",
    "Upper Volume": "volumeLowerThan",
    "Lower Dividend": "dividendMoreThan",
    # MVP metrics
    "Revenue (TTM) ≥": "rev_ttm_min",
    "YoY Revenue Growth ≥ (%)": "yoy_rev_growth_pct_min",
    "YoY Growth Count (≥ last 4q)": "yoy_growth_quarter_count_min",
    "Max QoQ Revenue Declines (last 4q)": "max_qoq_rev_declines_last4",
    "Gross Margin % ≥": "gross_margin_pct_min",
    "Δ Gross Margin YoY (pp) ≥": "delta_gm_pp_yoy_min",
    "Opex % Slope (last 4q) ≤": "opex_pct_slope_last4_max",
    "Operating CF (TTM) ≥": "ocf_ttm_min",
    "Δ Operating CF TTM YoY ≥": "delta_ocf_ttm_yoy_min",
    "R&D % of Revenue ≤": "rd_pct_max",
    "Δ R&D % YoY (pp) ≤": "delta_rd_pct_pp_yoy_max",
    "R&D Growth ≤ Revenue Growth (YoY)": "rd_growth_lte_rev_growth",
    "Deferred Revenue Rising (YoY)": "deferred_rev_yoy_increase",
    "Cash Conversion Cycle Slope (last 4q) ≤": "ccc_slope_last4_max",
    "Rule of 40 (Growth + Op Margin) ≥": "rule40_op_ttm_min",
    "Capex % of Revenue ≤": "capex_pct_max",
    # Dropdowns + Boolean filters
    "Sector": "sector",
    "Industry": "industry",
    "Exchange": "exchange",
    "Is ETF?": "isEtf",
    "Is Fund?": "isFund",
    "YoY Growth (%)": "yoyGrowth",
    "Profit Margin (%)": "profitMargin",
    "R&D Ratio (%)": "rdRatio",
    "Company Age (yrs)": "companyAge",
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
    # Options for the sector dropdown in alphabetical order for easier browsing
    "sector": [
        "Basic Materials",
        "Communication Services",
        "Consumer Cyclical",
        "Consumer Defensive",
        "Energy",
        "Financial Services",
        "Healthcare",
        "Industrials",
        "Real Estate",
        "Technology",
        "Utilities",
    ],
    # Expanded industry list in alphabetical order
    "industry": [
        "Advertising Agencies",
        "Agricultural Farm Products",
        "Agricultural Inputs",
        "Aluminum",
        "Apparel - Footwear & Accessories",
        "Apparel - Manufacturers",
        "Apparel - Retail",
        "Auto - Dealerships",
        "Auto - Manufacturers",
        "Auto - Parts",
        "Auto - Recreational Vehicles",
        "Beverages - Alcoholic",
        "Beverages - Non-Alcoholic",
        "Beverages - Wineries & Distilleries",
        "Broadcasting",
        "Chemicals",
        "Chemicals - Specialty",
        "Construction Materials",
        "Copper",
        "Department Stores",
        "Discount Stores",
        "Education & Training Services",
        "Entertainment",
        "Food Confectioners",
        "Food Distribution",
        "Furnishings, Fixtures & Appliances",
        "Gambling, Resorts & Casinos",
        "Gold",
        "Grocery Stores",
        "Home Improvement",
        "Household & Personal Products",
        "Industrial Materials",
        "Internet Content & Information",
        "Leisure",
        "Luxury Goods",
        "Other Precious Metals",
        "Packaged Foods",
        "Packaging & Containers",
        "Paper, Lumber & Forest Products",
        "Personal Products & Services",
        "Publishing",
        "Residential Construction",
        "Restaurants",
        "Silver",
        "Specialty Retail",
        "Steel",
        "Telecommunications Services",
        "Tobacco",
        "Travel Lodging",
        "Travel Services",
    ],
    "country": ["US", "Canada", "Germany", "UK", "France", "India", "Japan", "China"],
    "exchange": ["NASDAQ", "NYSE", "AMEX"],
    "isEtf": ["true", "false"],
    "isFund": ["true", "false"],
    "isActivelyTrading": ["true", "false"],
    "includeAllShareClasses": ["true", "false"],
    "yoyGrowth": ["Annual", "Quarterly"],
    "profitMargin": ["Annual", "Quarterly"],
    "rdRatio": ["Annual", "Quarterly"],
    "companyAge": None,
    "mvpStage": ["Pre-product", "Early Product", "Scaling"],
    # Post-R&D / MVP filters with default ranges
    "rev_ttm_min": {"from": 0, "to": 1_000_000_000_000, "resolution": 1_000_000, "default": 25_000_000},
    "yoy_rev_growth_pct_min": {"from": -100, "to": 300, "resolution": 1, "default": 20},
    "yoy_growth_quarter_count_min": {"from": 0, "to": 4, "resolution": 1, "default": 2},
    "max_qoq_rev_declines_last4": {"from": 0, "to": 3, "resolution": 1, "default": 1},
    "gross_margin_pct_min": {"from": -100, "to": 100, "resolution": 1, "default": 40},
    "delta_gm_pp_yoy_min": {"from": -100, "to": 100, "resolution": 1, "default": 5},
    "opex_pct_slope_last4_max": {"from": -5, "to": 5, "resolution": 0.1, "default": -0.1},
    "ocf_ttm_min": {"from": -1_000_000_000, "to": 1_000_000_000_000, "resolution": 1_000_000, "default": 0},
    "delta_ocf_ttm_yoy_min": {"from": -1_000_000_000, "to": 1_000_000_000_000, "resolution": 1_000_000, "default": 10_000_000},
    "rd_pct_max": {"from": 0, "to": 100, "resolution": 1, "default": 30},
    "delta_rd_pct_pp_yoy_max": {"from": -100, "to": 100, "resolution": 1, "default": -5},
    "rd_growth_lte_rev_growth": [True, False],
    "deferred_rev_yoy_increase": [True, False],
    "ccc_slope_last4_max": {"from": -100, "to": 100, "resolution": 1, "default": -5},
    "rule40_op_ttm_min": {"from": -100, "to": 200, "resolution": 1, "default": 20},
    "capex_pct_max": {"from": 0, "to": 100, "resolution": 1, "default": 15},
}
