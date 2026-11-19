"""Google Trends adapter (search interest).

Tries the official-ish unofficial route (pytrends) first. If pytrends is not
installed, blocked, or rate-limited, falls back to a deterministic sample
generator and labels the readings is_mock=1. The dashboard displays LIVE vs
MOCK status honestly either way.

pytrends interest_by_region returns 0-100 relative interest per state, which
is exactly the raw unit the percentile-rank scorer expects.
"""

import random

from .. import db
from ..catalog import STATES, STATE_EXT_NAMES

_last_error = None


def last_error():
    return _last_error


class TrendsAdapter:
    id = "trends"
    factor_ids = ["search"]

    def __init__(self):
        self._pytrends = None
        try:
            from pytrends.request import TrendReq
            self._TrendReq = TrendReq
        except Exception:
            self._TrendReq = None

    def is_live(self):
        return self._TrendReq is not None

    def status(self):
        return {
            "id": self.id, "factor": "search", "live": self.is_live(),
            "source": "Google Trends interest_by_region (pytrends)" if self.is_live()
                      else "SAMPLE GENERATOR (pytrends unavailable)",
            "note": "" if self.is_live() else "pip install pytrends to activate live collection",
        }

    def _collect_live(self, product, week):
        pt = self._TrendReq(hl="en-US", tz=0)
        # Google Trends batches keywords; one payload per product's primary term
        pt.build_payload(product["search_terms"][:1], timeframe="today 3-m", geo="MY")
        df = pt.interest_by_region(resolution="REGION", inc_low_vol=True)
        counts = 0
        col = df.columns[0]
        for _, row in df.iterrows():
            geo_name = row["geoName"]
            sid = next((s["id"] for s in STATES if STATE_EXT_NAMES[s["id"]] == geo_name), None)
            if sid is None:
                continue
            val = row[col]
            if val is None or (isinstance(val, float) and val != val):  # NaN check
                continue
            db.insert_reading("trends", product["id"], sid, "search", float(val), week,
                              is_mock=False, note=f"GT interest_by_region term='{product['search_terms'][0]}'")
            counts += 1
        return counts

    def _collect_mock(self, product, week):
        rng = random.Random(f"{product['id']}|{week}")
        for s in STATES:
            base = rng.uniform(20, 90)
            if s["id"] in ("sgr", "kl", "png", "pgj", "jhr"):
                base += rng.uniform(0, 15)
            db.insert_reading("trends", product["id"], s["id"], "search", round(base, 1), week,
                              is_mock=True, note="sample: pytrends unavailable")
        return len(STATES)

    def collect(self, product, week):
        global _last_error
        if self.is_live():
            try:
                n = self._collect_live(product, week)
                if n:
                    _last_error = None
                    return {"adapter": self.id, "readings": n, "live": True}
                _last_error = "pytrends returned 0 states (rate limit or geo mismatch)"
            except Exception as e:
                _last_error = f"pytrends failed: {e}"
        n = self._collect_mock(product, week)
        return {"adapter": self.id, "readings": n, "live": False, "fallback": _last_error}
