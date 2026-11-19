"""One-command start: init DB, backfill history if empty, start scheduler + API.

Usage:  python run.py     (then open http://127.0.0.1:8000)
"""
import json
import os
import sys

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import collector, db  # noqa: E402
from app.main import app, init  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    with open(os.path.join(BASE, "config.json")) as f:
        return json.load(f)


def scheduled_job(cfg):
    collector.collect_all(cfg)


def main():
    cfg = load_config()
    cfg["db_path"] = os.path.join(BASE, cfg.get("db_path", "data/demand.db"))
    init(cfg)

    # first-run: if the DB has no readings, backfill the weekly history window
    if not db.query("SELECT 1 FROM raw_readings LIMIT 1"):
        print("[init] empty database — running first collection + 12-week backfill ...")
        collector.backfill(cfg)
        print("[init] backfill complete")

    sched = BackgroundScheduler()
    sched.add_job(scheduled_job, "interval", hours=cfg.get("collection_interval_hours", 24),
                  args=[cfg], id="collect")
    sched.start()
    print(f"[run] scheduler active: every {cfg.get('collection_interval_hours', 24)}h")
    print("[run] API + dashboard: http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    main()
