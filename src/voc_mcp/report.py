"""Turn the agent's structured analysis into a Markdown report + a JSON file.

The agent does the semantic work (themes, emotions, quotes, actions). This
module does the deterministic part: it validates the structure, computes the
priority scores (frequency x intensity) so that they are reproducible, re-masks
quotes as a safety net, and renders a readable report in French or English.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .anonymize import anonymize_text

LABELS = {
    "fr": {
        "summary": "Synthèse", "scope": "Périmètre", "figures": "Chiffres clés",
        "priorities": "Priorisation des irritants (fréquence × intensité)",
        "themes": "Thèmes détaillés", "delights": "Points forts",
        "sentiment": "Sentiment et émotions", "weak": "Signaux faibles",
        "actions": "Plan d'action", "limits": "Limites de l'analyse",
        "theme": "Thème", "mentions": "Mentions", "share": "Part", "intensity": "Intensité (1-5)",
        "score": "Score", "quadrant": "Quadrant", "quotes": "Citations", "emotions": "Émotions",
        "action": "Action", "horizon": "Horizon", "owner": "Responsable", "kpi": "Indicateur",
        "effort": "Effort", "impact": "Impact", "addresses": "Irritants traités",
        "evidence": "Indices", "why": "Pourquoi c'est important", "check": "Vérification proposée",
        "records": "verbatims analysés", "of": "sur", "period": "Période", "channels": "Canaux",
        "rating": "Note moyenne", "low": "Part de notes ≤ 2", "generated": "Rapport généré le",
        "positive": "Positif", "neutral": "Neutre", "negative": "Négatif", "mixed": "Mitigé",
        "sampling": "Échantillonnage",
        "q": {"critical": "1 · Urgent : fréquent et intense", "mass": "2 · Irritant de masse",
              "acute": "3 · Point dur ciblé", "watch": "4 · À surveiller"},
        "anon": "Données pseudonymisées avant analyse (noms, e-mails, téléphones, adresses, références).",
    },
    "en": {
        "summary": "Executive summary", "scope": "Scope", "figures": "Key figures",
        "priorities": "Pain-point prioritisation (frequency × intensity)",
        "themes": "Themes in detail", "delights": "Strengths",
        "sentiment": "Sentiment and emotions", "weak": "Weak signals",
        "actions": "Action plan", "limits": "Limitations",
        "theme": "Theme", "mentions": "Mentions", "share": "Share", "intensity": "Intensity (1-5)",
        "score": "Score", "quadrant": "Quadrant", "quotes": "Quotes", "emotions": "Emotions",
        "action": "Action", "horizon": "Horizon", "owner": "Owner", "kpi": "KPI",
        "effort": "Effort", "impact": "Impact", "addresses": "Pain points addressed",
        "evidence": "Evidence", "why": "Why it matters", "check": "Suggested check",
        "records": "verbatims analysed", "of": "out of", "period": "Period", "channels": "Channels",
        "rating": "Average rating", "low": "Share of ratings ≤ 2", "generated": "Report generated on",
        "positive": "Positive", "neutral": "Neutral", "negative": "Negative", "mixed": "Mixed",
        "sampling": "Sampling",
        "q": {"critical": "1 · Urgent: frequent and intense", "mass": "2 · Widespread irritant",
              "acute": "3 · Acute, targeted issue", "watch": "4 · Monitor"},
        "anon": "Data pseudonymised before analysis (names, e-mails, phones, addresses, references).",
    },
}


def prioritise(themes: list[dict[str, Any]], analysed: int,
               freq_threshold: float = 0.10, intensity_threshold: float = 3.5) -> list[dict[str, Any]]:
    """Score pain points: score = share of mentions x intensity (1-5).

    Quadrants (thresholds are parameters so teams can adapt them):
      * critical: share >= freq_threshold and intensity >= intensity_threshold
      * mass:     frequent but less intense
      * acute:    rare but intense (often weak signals or severe incidents)
      * watch:    rare and mild
    """
    out = []
    for t in themes:
        if t.get("type", "pain_point") != "pain_point":
            continue
        share = (t.get("count") or 0) / max(analysed, 1)
        intensity = float(t.get("intensity") or 0)
        frequent, intense = share >= freq_threshold, intensity >= intensity_threshold
        quadrant = ("critical" if frequent and intense else "mass" if frequent
                    else "acute" if intense else "watch")
        out.append({"name": t["name"], "count": t.get("count", 0), "share": round(share, 3),
                    "intensity": intensity, "score": round(share * intensity, 3), "quadrant": quadrant})
    return sorted(out, key=lambda x: x["score"], reverse=True)


def validate(analysis: dict[str, Any]) -> list[str]:
    """Return a list of problems; an empty list means the analysis is usable."""
    problems = []
    if not isinstance(analysis.get("themes"), list) or not analysis["themes"]:
        problems.append("'themes' must be a non-empty list.")
    for i, t in enumerate(analysis.get("themes") or []):
        if not t.get("name"):
            problems.append(f"themes[{i}] has no 'name'.")
        if t.get("type", "pain_point") == "pain_point":
            if not isinstance(t.get("count"), int):
                problems.append(f"themes[{i}] ('{t.get('name')}') needs an integer 'count'.")
            if not isinstance(t.get("intensity"), (int, float)) or not 1 <= t["intensity"] <= 5:
                problems.append(f"themes[{i}] ('{t.get('name')}') needs 'intensity' between 1 and 5.")
    return problems


def _mask_quotes(analysis: dict[str, Any]) -> int:
    """Re-apply anonymisation to every quote (defence in depth). Returns #masks."""
    n = 0
    for t in analysis.get("themes") or []:
        for q in t.get("quotes") or []:
            q["text"], c = anonymize_text(q.get("text", ""))
            n += sum(c.values())
    return n


def _pct(x: float | None) -> str:
    return "–" if x is None else f"{x * 100:.0f} %"


def _num(x: float, lang: str, digits: int = 2) -> str:
    """Format a decimal number with the right separator (3,29 in French)."""
    s = f"{x:.{digits}f}"
    return s.replace(".", ",") if lang == "fr" else s


def render_markdown(analysis: dict[str, Any], priorities: list[dict[str, Any]], lang: str) -> str:
    L = LABELS.get(lang, LABELS["fr"])
    scope, stats = analysis.get("scope") or {}, analysis.get("stats") or {}
    md: list[str] = [f"# {analysis.get('title') or 'Voice of the Customer'}", ""]
    md.append(f"_{L['generated']} {datetime.now():%Y-%m-%d}. {L['anon']}_")
    md.append("")

    md += [f"## {L['summary']}", ""]
    md += [f"- {s}" for s in analysis.get("executive_summary") or []]
    md.append("")

    md += [f"## {L['scope']} · {L['figures']}", ""]
    analysed = scope.get("records_analysed") or stats.get("total")
    total = scope.get("records_total") or stats.get("total")
    md.append(f"- **{analysed}** {L['records']} {L['of']} {total}")
    if scope.get("source"):
        md.append(f"- Source : {scope['source']}" if lang == "fr" else f"- Source: {scope['source']}")
    if stats.get("date_range"):
        md.append(f"- {L['period']} : {stats['date_range']['start']} → {stats['date_range']['end']}")
    if stats.get("by_channel"):
        md.append(f"- {L['channels']} : " + ", ".join(
            f"{c['value']} ({c['count']})" for c in stats["by_channel"]))
    if stats.get("rating", {}).get("mean") is not None:
        md.append(f"- {L['rating']} : {_num(stats['rating']['mean'], lang)} / 5 · {L['low']} : {_pct(stats['rating']['low_share'])}")
    if scope.get("sampling"):
        md.append(f"- {L['sampling']} : {scope['sampling']}")
    md.append("")

    if priorities:
        md += [f"## {L['priorities']}", "",
               f"| # | {L['theme']} | {L['mentions']} | {L['share']} | {L['intensity']} | {L['score']} | {L['quadrant']} |",
               "|---|---|---|---|---|---|---|"]
        for i, p in enumerate(priorities, 1):
            md.append(f"| {i} | {p['name']} | {p['count']} | {_pct(p['share'])} | {_num(p['intensity'], lang, 0) if float(p['intensity']).is_integer() else _num(p['intensity'], lang, 1)} | "
                      f"{_num(p['score'], lang)} | {L['q'][p['quadrant']]} |")
        md.append("")

    def theme_block(t: dict[str, Any]) -> None:
        md.append(f"### {t['name']}")
        if t.get("description"):
            md.extend(["", t["description"]])
        meta = []
        if t.get("count") is not None:
            meta.append(f"{L['mentions']} : {t['count']}")
        if t.get("intensity") is not None:
            meta.append(f"{L['intensity']} : {t['intensity']}")
        if t.get("emotions"):
            meta.append(f"{L['emotions']} : {', '.join(t['emotions'])}")
        if t.get("channels"):
            meta.append(f"{L['channels']} : {', '.join(t['channels'])}")
        if meta:
            md.extend(["", "_" + " · ".join(meta) + "_"])
        if t.get("quotes"):
            md.append("")
            for q in t["quotes"]:
                tag = " · ".join(str(x) for x in (q.get("id"), q.get("channel"),
                                                   f"{q['rating']:g}/5" if q.get("rating") is not None else None) if x)
                md.append(f"> « {q['text']} »" + (f" — _{tag}_" if tag else ""))
                md.append(">")
            md.pop()
        md.append("")

    pains = [t for t in analysis["themes"] if t.get("type", "pain_point") == "pain_point"]
    order = {p["name"]: i for i, p in enumerate(priorities)}
    md += [f"## {L['themes']}", ""]
    for t in sorted(pains, key=lambda t: order.get(t["name"], 999)):
        theme_block(t)

    delights = [t for t in analysis["themes"] if t.get("type") == "delight"]
    if delights:
        md += [f"## {L['delights']}", ""]
        for t in delights:
            theme_block(t)

    sent, emos = analysis.get("sentiment"), analysis.get("emotions")
    if sent or emos:
        md += [f"## {L['sentiment']}", ""]
        if sent:
            parts = [f"{L[k]} : {sent[k]}" for k in ("positive", "mixed", "neutral", "negative") if k in sent]
            md.append("- " + " · ".join(parts))
            if sent.get("comment"):
                md.append(f"- {sent['comment']}")
        for e in emos or []:
            md.append(f"- **{e['emotion']}**" + (f" ({e['count']})" if e.get("count") is not None else "")
                      + (f" : {e['comment']}" if e.get("comment") else ""))
        md.append("")

    if analysis.get("weak_signals"):
        md += [f"## {L['weak']}", ""]
        for w in analysis["weak_signals"]:
            md.append(f"### {w['signal']}")
            if w.get("count") is not None or w.get("evidence_ids"):
                md.append(f"- {L['evidence']} : {w.get('count', len(w.get('evidence_ids', [])))} "
                          f"({', '.join(map(str, w.get('evidence_ids', [])))})")
            if w.get("why_it_matters"):
                md.append(f"- {L['why']} : {w['why_it_matters']}")
            if w.get("recommended_check"):
                md.append(f"- {L['check']} : {w['recommended_check']}")
            md.append("")

    if analysis.get("action_plan"):
        md += [f"## {L['actions']}", "",
               f"| {L['action']} | {L['addresses']} | {L['horizon']} | {L['impact']} | {L['effort']} | {L['owner']} | {L['kpi']} |",
               "|---|---|---|---|---|---|---|"]
        for a in analysis["action_plan"]:
            md.append(" | ".join([
                f"| {a.get('action', '')}", ", ".join(a.get("themes", [])), a.get("horizon", ""),
                a.get("impact", ""), a.get("effort", ""), a.get("owner", ""), f"{a.get('kpi', '')} |"]))
        md.append("")

    if analysis.get("limitations"):
        md += [f"## {L['limits']}", ""] + [f"- {x}" for x in analysis["limitations"]] + [""]
    return "\n".join(md).rstrip() + "\n"


def build_report(analysis: dict[str, Any], output_dir: str | Path, filename: str = "voc_report",
                 language: str = "fr", stats: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate, score, render and write ``<filename>.md`` and ``<filename>.json``."""
    problems = validate(analysis)
    if problems:
        raise ValueError("Analysis is incomplete: " + " ".join(problems))
    analysis = json.loads(json.dumps(analysis))  # deep copy; we add fields below
    if stats:
        analysis["stats"] = stats
    masked = _mask_quotes(analysis)
    scope = analysis.setdefault("scope", {})
    analysed = scope.get("records_analysed") or (stats or {}).get("total") or \
        sum(t.get("count", 0) for t in analysis["themes"])
    priorities = prioritise(analysis["themes"], analysed)
    analysis["priorities"] = priorities
    analysis["generated_at"] = datetime.now().isoformat(timespec="seconds")
    analysis["language"] = language

    out = Path(output_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    md_path, json_path = out / f"{filename}.md", out / f"{filename}.json"
    md_path.write_text(render_markdown(analysis, priorities, language), encoding="utf-8")
    json_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"markdown": str(md_path), "json": str(json_path), "priorities": priorities,
            "quotes_remasked": masked}
