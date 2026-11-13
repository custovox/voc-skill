import pytest

from voc_mcp.sampling import stratified_sample
from voc_mcp.stats import compute_stats


def make_records():
    recs = []
    for i in range(90):
        recs.append({"id": str(i), "text": "ok bien", "date": f"2026-0{1 + i % 3}-10",
                     "rating": 5.0, "channel": "site"})
    for i in range(10):
        recs.append({"id": f"p{i}", "text": "très déçu du service", "date": "2026-03-20",
                     "rating": 1.0, "channel": "phone"})
    return recs


def test_stats_breakdowns():
    s = compute_stats(make_records())
    assert s["total"] == 100
    assert s["by_channel"][0] == {"value": "site", "count": 90, "share": 0.9}
    assert s["rating"]["low_share"] == 0.1
    assert [p["period"] for p in s["by_period"]] == ["2026-01", "2026-02", "2026-03"]
    assert s["date_range"] == {"start": "2026-01-10", "end": "2026-03-20"}


def test_stats_week_period():
    s = compute_stats(make_records(), period="week")
    assert s["by_period"][0]["period"].startswith("2026-W")


def test_sample_keeps_rare_strata_and_is_reproducible():
    recs = make_records()
    a, alloc = stratified_sample(recs, 20, ["channel"], seed=1)
    b, _ = stratified_sample(recs, 20, ["channel"], seed=1)
    assert [r["id"] for r in a] == [r["id"] for r in b]
    assert len(a) == 20
    assert sum(1 for r in a if r["channel"] == "phone") == 2  # proportional: 10 % of 20
    assert {x["stratum"]["channel"] for x in alloc} == {"site", "phone"}


def test_sample_minimum_one_per_stratum():
    recs = make_records()[:90] + make_records()[90:91]  # a single phone record
    sample, _ = stratified_sample(recs, 10, ["channel"])
    assert any(r["channel"] == "phone" for r in sample)


def test_sample_returns_all_when_n_large():
    recs = make_records()
    sample, _ = stratified_sample(recs, 500)
    assert len(sample) == 100


def test_sample_rejects_unknown_strata():
    with pytest.raises(ValueError):
        stratified_sample(make_records(), 10, ["colour"])
