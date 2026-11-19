"""Adapter contract. Every collector implements:
  - id: adapter name stored with readings
  - factor_ids: which factors it feeds
  - is_live(): True when real external data is available (no mock)
  - collect(product, week) -> writes raw_readings via db, returns summary
Adapters must degrade gracefully: a failed live collect writes nothing and
the scoring layer treats that factor as missing (confidence drops, not lies).
"""


class AdapterError(Exception):
    pass
