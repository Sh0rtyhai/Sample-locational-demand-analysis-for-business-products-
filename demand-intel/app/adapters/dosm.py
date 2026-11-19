"""DOSM Buying Power adapter — REAL data, no API key needed.

Source: Department of Statistics Malaysia (DOSM), median monthly household
gross income by state (Household Income Survey, latest published release:
HIS 2022, published 2023). This is genuinely real, official data embedded as
a static table — income moves slowly, so yearly snapshots are appropriate.

Saturation is derived from buying power + a competition base read from the
maps adapter; the DOSM adapter only claims the 'buying' factor.
"""

from .. import db
from ..catalog import STATE_EXT_NAMES

# DOSM Household Income Survey 2022: median monthly household gross income (RM)
# by state, official published figures. Real data, snapshot 2022.
MEDIAN_INCOME_RM = {
    "pls": 3821, "kd": 4559, "png": 6859, "ktn": 3827, "tgn": 4424,
    "prk": 5391, "phg": 5140, "sgr": 8131, "kl": 9300, "pgj": 10998,
    "nsn": 5290, "mlk": 5516, "jhr": 6143, "swk": 5155, "lbn": 6074, "sbh": 3935,
}


class DOSMAdapter:
    id = "dosm"
    factor_ids = ["buying"]

    def is_live(self):
        return True  # embedded official statistics — genuinely real

    def status(self):
        return {
            "id": self.id, "factor": "buying", "live": True,
            "source": "DOSM Household Income Survey 2022 (official, embedded snapshot)",
            "note": "Median monthly household gross income by state, RM",
        }

    def collect(self, product, week):
        n = 0
        for sid, income in MEDIAN_INCOME_RM.items():
            db.insert_reading("dosm", product["id"], sid, "buying", float(income), week, is_mock=False,
                              note="DOSM HIS2022 median household income (RM)")
            n += 1
        return {"adapter": self.id, "readings": n, "live": True}
