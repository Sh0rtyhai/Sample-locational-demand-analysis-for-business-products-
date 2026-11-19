"""Normalization + composite scoring with full provenance.

Method (documented so it can be defended):
- Each factor reading is converted to a 0-100 percentile rank across all 16
  states for the same product+factor+week. Percentile ranking makes sources
  with different native units comparable and is population-robust.
- The composite is the weighted mean of available factor scores.
- Confidence reflects data coverage: HIGH = all 4 factors present,
  MED = >=75% weighted coverage, LOW = below that. Missing factors are
  excluded and the remaining weights re-normalized (never silently zeroed).
"""

FACTORS = ["search", "buying", "saturation", "competition"]


def percentile_ranks(readings):
    """readings: {state_id: value} -> {state_id: 0-100 percentile rank}.
    Missing states are absent from the output."""
    items = sorted(((s, v) for s, v in readings.items() if v is not None), key=lambda x: x[1])
    n = len(items)
    if n == 0:
        return {}
    out = {}
    for i, (s, _v) in enumerate(items):
        # rank position / (n-1) scaled to 0-100; n=1 -> neutral 50
        out[s] = round(100.0 * i / (n - 1), 1) if n > 1 else 50.0
    return out


def confidence_for(weight_covered, weight_total):
    ratio = weight_covered / weight_total if weight_total else 0
    if ratio >= 0.99:
        return "HIGH"
    if ratio >= 0.75:
        return "MED"
    return "LOW"


def composite_state(factor_ranks, weights, state_id):
    """factor_ranks: {factor_id: {state_id: rank}}. Returns (score, confidence, coverage, breakdown)."""
    total_w = sum(weights.get(f, 0) for f in FACTORS) or 1
    covered_w = 0.0
    acc = 0.0
    breakdown = {}
    for f in FACTORS:
        ranks = factor_ranks.get(f, {})
        w = weights.get(f, 0)
        rank = ranks.get(state_id)
        if rank is None:
            breakdown[f] = {"score": None, "weight_pct": round(100 * w / total_w), "status": "missing"}
            continue
        eff = round(100 * w / total_w)
        acc += rank * w
        covered_w += w
        breakdown[f] = {"score": rank, "weight_pct": eff, "status": "ok"}
    score = round(acc / covered_w, 1) if covered_w else None
    coverage = covered_w / total_w
    return score, confidence_for(covered_w, total_w), round(coverage, 2), breakdown
