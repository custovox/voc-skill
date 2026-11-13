"""Descriptive statistics on normalised feedback records."""

from __future__ import annotations

from collections import Counter
from statistics import mean, median
from typing import Any


def _distribution(values: list[Any]) -> list[dict[str, Any]]:
    """Count + share for each value, most frequent first."""
    total = len(values) or 1
    return [{"value": v, "count": c, "share": round(c / total, 3)}
            for v, c in Counter(values).most_common()]


def compute_stats(records: list[dict[str, Any]], period: str = "month") -> dict[str, Any]:
    """Volumes and breakdowns by channel, period and rating.

    ``period`` is "month" (YYYY-MM), "week" (YYYY-Www) or "day".
    """
    from datetime import date

    n = len(records)
    ratings = [r["rating"] for r in records if r.get("rating") is not None]
    dates = sorted(r["date"] for r in records if r.get("date"))

    def bucket(d: str) -> str:
        if period == "day":
            return d
        if period == "week":
            y, w, _ = date.fromisoformat(d).isocalendar()
            return f"{y}-W{w:02d}"
        return d[:7]

    by_period = Counter(bucket(d) for d in dates)
    # Average rating per period helps spot a degradation over time.
    rating_by_period: dict[str, list[float]] = {}
    for r in records:
        if r.get("date") and r.get("rating") is not None:
            rating_by_period.setdefault(bucket(r["date"]), []).append(r["rating"])

    lengths = [len(r["text"].split()) for r in records]
    rating_bins = [str(int(x)) if float(x).is_integer() else str(x) for x in ratings]

    return {
        "total": n,
        "date_range": {"start": dates[0], "end": dates[-1]} if dates else None,
        "by_channel": _distribution([r.get("channel") or "unknown" for r in records]),
        "by_period": [
            {"period": p, "count": by_period[p],
             "avg_rating": round(mean(rating_by_period[p]), 2) if p in rating_by_period else None}
            for p in sorted(by_period)
        ],
        "rating": {
            "count": len(ratings),
            "mean": round(mean(ratings), 2) if ratings else None,
            "median": median(ratings) if ratings else None,
            "distribution": sorted(_distribution(rating_bins), key=lambda d: float(d["value"])),
            # Share of low ratings (<= 2 on a 5-point scale): a quick "detractor" proxy
            "low_share": round(sum(1 for x in ratings if x <= 2) / len(ratings), 3) if ratings else None,
        },
        "text_length_words": {
            "mean": round(mean(lengths), 1) if lengths else 0,
            "median": median(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
        },
        "missing": {
            "date": sum(1 for r in records if not r.get("date")),
            "rating": sum(1 for r in records if r.get("rating") is None),
            "channel": sum(1 for r in records if not r.get("channel")),
        },
    }
