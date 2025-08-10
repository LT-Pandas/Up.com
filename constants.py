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


# Friendly one-liners describing what each preview block does.  These
# are displayed as tooltips when a user hovers over a block in the UI.
PREVIEW_DESCRIPTIONS = {
    "Stock Search": "Look up a stock by name or ticker to jump straight in.",
    "Sector": "Filter companies by the slice of the economy they play in.",
    "Industry": "Drill down to the specific line of work that interests you.",
    "Exchange": "Choose the trading floor where the stock struts its stuff.",
    "Is ETF?": "Decide if you want a basket of stocks instead of a single hero.",
    "Is Fund?": "Limit results to pooled investments for the crowd-minded.",
    "Lower Price": "Start your treasure hunt at this price or higher.",
    "Upper Price": "Skip anything that costs more than this price tag.",
    "Lower Market Cap (10M-4T)": "Consider only businesses at least this beefy.",
    "Upper Market Cap (10M-4T)": "Ignore companies that have outgrown this market cap ceiling.",
    "Lower Volume": "Look only at stocks that trade at least this much in a day.",
    "Upper Volume": "Avoid tickers that are busier than your local coffee shop.",
    "Lower Dividend": "Show only companies handing out dividends at or above this mark.",
    "Limit Results": "Keep your list short enough to read before lunch.",
    "Revenue (TTM) ≥": "Focus on firms pulling in at least this much over the last year.",
    "YoY Revenue Growth ≥ (%)": "Keep only companies whose sales grew at least this much compared to last year.",
    "YoY Growth Count (≥ last 4q)": "See how many consecutive quarters of growth are needed to impress you.",
    "Max QoQ Revenue Declines (last 4q)": "Set the maximum number of quarterly sales slip-ups you're willing to forgive.",
    "Gross Margin % ≥": "Find businesses keeping at least this slice of each dollar they earn.",
    "Δ Gross Margin YoY (pp) ≥": "Demand at least this positive swing in profit margin compared to last year.",
    "Opex % Slope (last 4q) ≤": "Pick companies whose spending isn't ballooning faster than a party balloon.",
    "Operating CF (TTM) ≥": "Stick with firms bringing in at least this much real cash over the year.",
    "Δ Operating CF TTM YoY ≥": "Ask for at least this boost in cash flow compared to last year.",
    "R&D % of Revenue ≤": "Limit to companies that don't treat research like a bottomless piggy bank.",
    "Δ R&D % YoY (pp) ≤": "Favor businesses keeping their research budget from creeping up too much.",
    "R&D Growth ≤ Revenue Growth (YoY)": "Choose companies where experimentation isn't outrunning sales.",
    "Deferred Revenue Rising (YoY)": "Highlight firms whose prepaid orders aren't taking a nap.",
    "Cash Conversion Cycle Slope (last 4q) ≤": "Select businesses turning stock into cash without dawdling.",
    "Rule of 40 (Growth + Op Margin) ≥": "Insist on companies that score at least this on the growth-plus-profit scoreboard.",
    "Capex % of Revenue ≤": "Avoid firms dumping too much of their earnings into shiny new toys.",
    "YoY Growth (%)": "Compare today's revenue to last year's, like a progress report.",
    "Profit Margin (%)": "See what part of each dollar in sales a company actually keeps.",
    "R&D Ratio (%)": "Check how much revenue is reinvested in fresh ideas.",
    "Company Age (yrs)": "Set a minimum age—no startups in diapers unless you say so.",
    "MVP Stage": "Filter by how far along a company's big idea has matured.",
}


def get_preview_description(label: str) -> str:
    """Return a short human-friendly description for a preview block."""
    return PREVIEW_DESCRIPTIONS.get(label, "")


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
