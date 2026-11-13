"""Stratified sampling, so that large files can be analysed by an agent whose
context window is limited, without losing small but important segments."""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

ALLOWED_STRATA = {"channel", "rating", "month"}


def _key(record: dict[str, Any], strata: list[str]) -> tuple:
    parts = []
    for s in strata:
        if s == "month":
            parts.append((record.get("date") or "unknown")[:7])
        elif s == "rating":
            r = record.get("rating")
            parts.append("unknown" if r is None else int(r))
        else:
            parts.append(record.get(s) or "unknown")
    return tuple(parts)


def stratified_sample(
    records: list[dict[str, Any]],
    n: int,
    strata: list[str] | None = None,
    seed: int = 42,
    min_per_stratum: int = 1,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Draw ``n`` records, proportionally to each stratum's size.

    * Each non-empty stratum gets at least ``min_per_stratum`` records, so rare
      segments (e.g. 1-star reviews by phone) stay visible.
    * Rounding uses the largest-remainder method so the total is exactly ``n``
      (or slightly more if the minimums force it).
    * A fixed ``seed`` makes the sample reproducible.

    Returns (sample, allocation) where allocation lists each stratum's quota.
    """
    strata = strata or ["channel", "rating"]
    unknown = set(strata) - ALLOWED_STRATA
    if unknown:
        raise ValueError(f"Unknown strata {sorted(unknown)}; allowed: {sorted(ALLOWED_STRATA)}")
    if n >= len(records):
        return list(records), [{"stratum": "all", "population": len(records), "sampled": len(records)}]

    groups: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        groups[_key(r, strata)].append(r)

    total = len(records)
    exact = {k: n * len(v) / total for k, v in groups.items()}
    quota = {k: max(min(min_per_stratum, len(groups[k])), int(x)) for k, x in exact.items()}
    # Distribute what is left to the strata with the largest fractional parts
    remaining = n - sum(quota.values())
    for k in sorted(exact, key=lambda k: exact[k] - int(exact[k]), reverse=True):
        if remaining <= 0:
            break
        if quota[k] < len(groups[k]):
            quota[k] += 1
            remaining -= 1

    rng = random.Random(seed)
    sample: list[dict[str, Any]] = []
    allocation = []
    for k in sorted(groups, key=str):
        picked = rng.sample(groups[k], min(quota[k], len(groups[k])))
        sample.extend(picked)
        allocation.append({"stratum": dict(zip(strata, k)), "population": len(groups[k]),
                           "sampled": len(picked)})
    return sample, allocation
