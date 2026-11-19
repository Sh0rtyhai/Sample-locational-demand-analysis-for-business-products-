"""FastAPI application: serves the catalog, computed scores, and system status.

GET /api/meta       -> products, states, factors, weight presets (frontend config)
GET /api/scores     -> per-state composite + breakdown for a product (with weights)
GET /api/trend      -> weekly composite history for a product+state
POST /api/collect   -> trigger a collection run now
GET /api/status     -> adapter LIVE/MOCK status, last run, freshness
"""

import json
from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import collector, db, scoring
from .catalog import CATEGORIES, FACTORS, PRODUCTS, STATES

app = FastAPI(title="Demand Intelligence API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CFG = {}


def init(cfg):
    global CFG
    CFG = cfg
    db.init(cfg["db_path"])


@app.get("/api/meta")
def meta():
    return {
        "products": PRODUCTS,
        "states": STATES,
        "factors": FACTORS,
        "categories": CATEGORIES,
    }


@app.get("/api/scores")
def scores(product: str):
    prod = next((p for p in PRODUCTS if p["id"] == product), None)
    if prod is None:
        return {"error": "unknown product"}
    weights = CATEGORIES[prod["cat"]]["weights"]

    # gather latest readings per factor, percentile-rank across states
    factor_ranks = {}
    factor_meta = {}
    for f in scoring.FACTORS:
        readings = {}
        is_mock = False
        for st in STATES:
            r = db.latest_reading(adapter_for_factor(f), product, st["id"], f)
            if r is not None:
                readings[st["id"]] = r["value"]
                is_mock = is_mock or bool(r["is_mock"])
                factor_meta[f] = {"week": r["week"], "collected_at": r["collected_at"],
                                  "mock": bool(r["is_mock"]), "note": r["note"]}
        factor_ranks[f] = scoring.percentile_ranks(readings)

    out = []
    for st in STATES:
        score, conf, cov, breakdown = scoring.composite_state(factor_ranks, weights, st["id"])
        out.append({
            "state_id": st["id"], "state": st["name"], "score": score,
            "confidence": conf, "coverage": cov, "breakdown": breakdown,
        })
    return {
        "product": prod, "weights": weights,
        "scores": out, "factor_meta": factor_meta,
    }


@app.get("/api/trend")
def trend(product: str, state: str):
    rows = db.query(
        "SELECT week, value FROM raw_readings WHERE adapter='trends' AND product_id=? AND state_id=? "
        "AND factor_id='search' AND value IS NOT NULL ORDER BY week ASC", (product, state))
    return {"product": product, "state": state,
            "series": [{"week": r["week"], "value": r["value"]} for r in rows]}


def adapter_for_factor(factor):
    return {"search": "trends", "buying": "dosm", "saturation": "maps", "competition": "maps"}[factor]


class CollectBody(BaseModel):
    weeks: int = 1


@app.post("/api/collect")
def trigger_collect(body: CollectBody):
    from datetime import timedelta
    weeks = [collector.week_monday(date.today() - timedelta(weeks=i))
             for i in range(max(1, min(body.weeks, 26)) - 1, -1, -1)]
    result = collector.collect_all(CFG, weeks=weeks)
    return result


@app.get("/api/status")
def status():
    adapters = collector.make_adapters(CFG)
    runs = db.query("SELECT * FROM run_log ORDER BY id DESC LIMIT 1")
    last = dict(runs[0]) if runs else None
    counts = {r["is_mock"]: r["n"] for r in db.query(
        "SELECT is_mock, COUNT(*) AS n FROM raw_readings GROUP BY is_mock")}
    return {
        "adapters": [a.status() for a in adapters.values()],
        "last_run": last,
        "readings": {"real": counts.get(0, 0), "mock": counts.get(1, 0)},
    }


@app.get("/")
def frontend():
    return FileResponse("frontend/index.html")
