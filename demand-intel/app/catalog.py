"""Product catalog, geography, and category weight presets.

The search-terms mapping is the core product IP: real consumers rarely search
the product's catalog name, so each product carries the terms it will actually
be scored against.
"""

CATEGORIES = {
    "food":        {"label": "Food & Beverage",       "weights": {"search": 35, "buying": 25, "saturation": 20, "competition": 20}},
    "apparel":     {"label": "Apparel & Textiles",    "weights": {"search": 30, "buying": 30, "saturation": 25, "competition": 15}},
    "electronics": {"label": "Electronics & Gadgets", "weights": {"search": 35, "buying": 30, "saturation": 15, "competition": 20}},
    "services":    {"label": "Services & Digital",    "weights": {"search": 40, "buying": 20, "saturation": 20, "competition": 20}},
}

PRODUCTS = [
    {
        "id": "sambal",
        "name": "Bottled Sambal & Condiments",
        "cat": "food",
        "search_terms": ["sambal", "sambal belacan", "sos sambal", "sambal sedap"],
        "maps_query": "sambal",
    },
    {
        "id": "batik",
        "name": "Handwoven Batik Textiles",
        "cat": "apparel",
        "search_terms": ["batik", "batik Malaysia", "kain batik", "batik terengganu"],
        "maps_query": "batik shop",
    },
    {
        "id": "keropok",
        "name": "Keropok Lekor (Fish Snacks)",
        "cat": "food",
        "search_terms": ["keropok lekor", "keropok", "keropok lekor terengganu"],
        "maps_query": "keropok lekor",
    },
    {
        "id": "smartplug",
        "name": "Smart Home Plugs",
        "cat": "electronics",
        "search_terms": ["smart plug", "smart home plug", "wifi plug"],
        "maps_query": "smart home store",
    },
    {
        "id": "webdev",
        "name": "SME Web Development Services",
        "cat": "services",
        "search_terms": ["web development Malaysia", "website design company", "ecommerce website"],
        "maps_query": "web development company",
    },
]

FACTORS = [
    {"id": "search",      "name": "Search Interest",      "desc": "people actively looking for the product (regional search trends)"},
    {"id": "buying",      "name": "Buying Power",         "desc": "local affordability & segment size (official income statistics)"},
    {"id": "saturation",  "name": "Market Saturation",    "desc": "supply vs demand balance; high score = open space to enter"},
    {"id": "competition", "name": "Competitive Pressure", "desc": "how contested the market is; high score = less contested"},
]

# 16 Malaysian states / federal territories
STATES = [
    {"id": "pls", "name": "Perlis"},
    {"id": "kd",  "name": "Kedah"},
    {"id": "png", "name": "Penang"},
    {"id": "ktn", "name": "Kelantan"},
    {"id": "tgn", "name": "Terengganu"},
    {"id": "prk", "name": "Perak"},
    {"id": "phg", "name": "Pahang"},
    {"id": "sgr", "name": "Selangor"},
    {"id": "kl",  "name": "Kuala Lumpur"},
    {"id": "pgj", "name": "Putrajaya"},
    {"id": "nsn", "name": "Negeri Sembilan"},
    {"id": "mlk", "name": "Melaka"},
    {"id": "jhr", "name": "Johor"},
    {"id": "swk", "name": "Sarawak"},
    {"id": "lbn", "name": "Labuan"},
    {"id": "sbh", "name": "Sabah"},
]

# Names used to query real external sources (Google Trends geo names / DOSM table order)
STATE_EXT_NAMES = {
    "pls": "Perlis", "kd": "Kedah", "png": "Pulau Pinang", "ktn": "Kelantan",
    "tgn": "Terengganu", "prk": "Perak", "phg": "Pahang", "sgr": "Selangor",
    "kl": "Kuala Lumpur", "pgj": "Putrajaya", "nsn": "Negeri Sembilan",
    "mlk": "Melaka", "jhr": "Johor", "swk": "Sarawak", "lbn": "Labuan", "sbh": "Sabah",
}
