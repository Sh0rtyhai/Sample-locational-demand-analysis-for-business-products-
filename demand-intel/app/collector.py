"""Collection orchestration: weekly backfill on first run, then scheduled updates.

Weeks are ISO Mondays. The backfill generates one reading per product x state x
factor per week for the configured window so trend charts have history from the
first launch. A lock prevents overlapping runs.
"""

import threading
from datetime import date, datetime, timedelta, timezone

from . import db
from .adapters.dosm import DOSMAdapter
from .adapters.maps import MapsAdapter
from .adapters.trends import TrendsAdapter
from .catalog import PRODUCTS

_lock = threading.Lock()
_last_run = None


def last_run():
    return _last_run


def week_monday(d: date) -> str:
    """ISO date string of the Monday of the week containing d."""
    monday = d - timedelta(days=d.weekday())
    return monday.isoformat()


def make_adapters(cfg):
    return {
        "trends": TrendsAdapter(),
        "dosm": DOSMAdapter(),
        "maps": MapsAdapter(cfg.get("google_maps_api_key", "")),
    }


def collect_all(cfg, weeks=None, force=False):
    """Collect readings for all products. weeks: list of ISO monday strings;
    None = current week only. Returns per-adapter summary."""
    global _last_run
    with _lock:
        started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        db.execute("INSERT INTO run_log (job, started_at) VALUES (?,?)", ("collect", started))
        adapters = make_adapters(cfg)
        if weeks is None:
            weeks = [week_monday(date.today())]
        summary = []
        for product in PRODUCTS:
            for wk in weeks:
                for a in adapters.values():
                    summary.append(a.collect(product, wk))
        # DOSM is an annual snapshot: only insert once per distinct week (idempotent-ish
        # is handled by queries taking latest; avoid stacking duplicate values)
        finished = datetime.now(timezone.utc).isoformat(timespec="seconds")
        db.execute("UPDATE run_log SET finished_at=?, status=? WHERE job='collect' AND started_at=?",
                   (finished, "ok", started))
        _last_run = {"started": started, "finished": finished, "adapters": summary}
        return _last_run


def backfill(cfg):
    """First-run history: weekly series for the backfill window.
    DOSM only needs the latest week; trends/maps get full history."""
    weeks = []
    today = date.today()
    for i in range(cfg.get("backfill_weeks", 12) - 1, -1, -1):
        weeks.append(week_monday(today - timedelta(weeks=i)))
    return collect_all(cfg, weeks=weeks)
