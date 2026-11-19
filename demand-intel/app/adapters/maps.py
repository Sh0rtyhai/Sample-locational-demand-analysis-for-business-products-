"""Google Places adapter (saturation + competitive pressure).

LIVE mode requires a Google Places API key in config.json
("google_maps_api_key"). It counts matching businesses per state capital
(text search) — density of sellers proxies saturation (inverse) and review
volume proxies competitive pressure (inverse).

Without a key it falls back to a deterministic sample generator, labelled
is_mock=1 everywhere so nothing on screen pretends to be real.

State capitals / major commercial centres used for the Places query.
"""

import math
import random

import requests

from .. import db
from ..catalog import STATES

CAPITAL_COORDS = {
    "pls": (6.4446, 100.2046),   # Kangar
    "kd": (6.1248, 100.3678),    # Alor Setar
    "png": (5.4141, 100.3288),   # George Town
    "ktn": (6.1254, 102.2389),   # Kota Bharu
    "tgn": (5.3306, 103.1408),   # Kuala Terengganu
    "prk": (4.5921, 101.0776),   # Ipoh
    "phg": (3.4951, 102.2400),   # Kuantan
    "sgr": (3.0738, 101.5183),   # Shah Alam
    "kl": (3.1390, 101.6869),    # KL
    "pgj": (2.9441, 101.6887),   # Putrajaya
    "nsn": (2.7287, 101.9383),   # Seremban
    "mlk": (2.1896, 102.2501),   # Melaka City
    "jhr": (1.4927, 103.7567),   # Johor Bahru
    "swk": (1.5533, 110.3592),   # Kuching
    "lbn": (5.2833, 115.2292),   # Labuan
    "sbh": (5.9804, 116.0735),   # Kota Kinabalu
}

_last_error = None


def last_error():
    return _last_error


class MapsAdapter:
    id = "maps"
    factor_ids = ["saturation", "competition"]

    def __init__(self, api_key: str):
        self.api_key = api_key.strip()

    def is_live(self):
        return bool(self.api_key)

    def status(self):
        return {
            "id": self.id, "factor": "saturation,competition", "live": self.is_live(),
            "source": "Google Places API (business density)" if self.is_live()
                      else "SAMPLE GENERATOR (no API key configured)",
            "note": "" if self.is_live() else "add google_maps_api_key to config.json to activate live collection",
        }

    def _places_count(self, lat, lng, query):
        """Returns (n_results, total_reviews) via Places Text Search (prototype scope:
        counts first page, which caps at 20 — a known, documented limitation)."""
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        r = requests.get(url, params={
            "query": f"{query} near {lat},{lng}",
            "location": f"{lat},{lng}", "radius": 25000, "key": self.api_key,
        }, timeout=15)
        data = r.json()
        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            raise RuntimeError(f"Places API status={data.get('status')}")
        results = data.get("results", [])
        reviews = sum(x.get("user_ratings_total", 0) or 0 for x in results)
        return len(results), reviews

    def _collect_mock(self, product, week):
        rng = random.Random(f"{product['id']}|maps|{week}")
        for s in STATES:
            sellers = rng.randint(2, 30)
            reviews = sellers * rng.randint(5, 60)
            # saturation: fewer sellers relative to demand proxy = more open space
            sat = max(5, min(95, 100 - sellers * 3))
            comp = max(5, min(95, 100 - math.log2(reviews + 1) * 10))
            db.insert_reading("maps", product["id"], s["id"], "saturation", float(sat), week,
                              is_mock=True, note=f"sample: {sellers} sellers")
            db.insert_reading("maps", product["id"], s["id"], "competition", float(comp), week,
                              is_mock=True, note=f"sample: {reviews} reviews")
        return len(STATES) * 2

    def collect(self, product, week):
        global _last_error
        if self.is_live():
            try:
                n = 0
                for s in STATES:
                    lat, lng = CAPITAL_COORDS[s["id"]]
                    sellers, reviews = self._places_count(lat, lng, product["maps_query"])
                    sat = max(5, min(95, 100 - sellers * 3))
                    comp = max(5, min(95, 100 - math.log2(reviews + 1) * 10))
                    db.insert_reading("maps", product["id"], s["id"], "saturation", float(sat), week,
                                      is_mock=False, note=f"Places: {sellers} results")
                    db.insert_reading("maps", product["id"], s["id"], "competition", float(comp), week,
                                      is_mock=False, note=f"Places: {reviews} total reviews")
                    n += 2
                _last_error = None
                return {"adapter": self.id, "readings": n, "live": True}
            except Exception as e:
                _last_error = f"Places API failed: {e}"
        n = self._collect_mock(product, week)
        return {"adapter": self.id, "readings": n, "live": False, "fallback": _last_error}
