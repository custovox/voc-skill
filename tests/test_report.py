import json

import pytest

from voc_mcp.report import build_report, prioritise

ANALYSIS = {
    "title": "Test",
    "scope": {"records_analysed": 100, "records_total": 100},
    "executive_summary": ["Delivery is the main issue."],
    "themes": [
        {"name": "Late delivery", "type": "pain_point", "count": 30, "intensity": 3,
         "quotes": [{"id": "1", "text": "Late again, call me at 06 12 34 56 78", "rating": 2, "channel": "site"}]},
        {"name": "Broken jars", "type": "pain_point", "count": 20, "intensity": 4},
        {"name": "Skin redness", "type": "pain_point", "count": 3, "intensity": 5},
        {"name": "Promo code", "type": "pain_point", "count": 5, "intensity": 2},
        {"name": "Efficacy", "type": "delight", "count": 50},
    ],
    "action_plan": [{"action": "Better packaging", "themes": ["Broken jars"], "horizon": "quick win"}],
}


def test_prioritise_scores_and_quadrants():
    p = {x["name"]: x for x in prioritise(ANALYSIS["themes"], 100)}
    assert "Efficacy" not in p  # delights are not prioritised
    assert p["Broken jars"]["score"] == 0.8 and p["Broken jars"]["quadrant"] == "critical"
    assert p["Late delivery"]["quadrant"] == "mass"
    assert p["Skin redness"]["quadrant"] == "acute"
    assert p["Promo code"]["quadrant"] == "watch"
    ranked = prioritise(ANALYSIS["themes"], 100)
    assert ranked[0]["name"] == "Late delivery"  # 0.30 x 3 = 0.90 > 0.80


def test_build_report_writes_files_and_remasks(tmp_path):
    res = build_report(ANALYSIS, tmp_path, "r", language="en")
    md = (tmp_path / "r.md").read_text(encoding="utf-8")
    data = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert "Pain-point prioritisation" in md and "Strengths" in md
    assert "06 12 34 56 78" not in md and "[PHONE]" in md
    assert res["quotes_remasked"] == 1
    assert data["priorities"][0]["name"] == "Late delivery"


def test_french_headings(tmp_path):
    build_report(ANALYSIS, tmp_path, "r", language="fr")
    assert "Plan d'action" in (tmp_path / "r.md").read_text(encoding="utf-8")


def test_invalid_analysis(tmp_path):
    with pytest.raises(ValueError, match="intensity"):
        build_report({"themes": [{"name": "x", "count": 2}]}, tmp_path)
    with pytest.raises(ValueError, match="themes"):
        build_report({}, tmp_path)
