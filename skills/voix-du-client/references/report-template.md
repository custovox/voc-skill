# Report template (`analysis` object for `export_report`)

The report is rendered from this JSON structure (also saved as `.json` for dashboards
or for comparing several periods). Full schema: `../assets/report-schema.json`.

```json
{
  "title": "Voix du client - Maison Verveine - T1 2026",
  "scope": {
    "source": "avis_ecommerce.csv + 5 transcriptions d'appels",
    "records_analysed": 205,
    "records_total": 205,
    "sampling": "exhaustif"
  },
  "executive_summary": [
    "One sentence per key finding, with a number."
  ],
  "themes": [
    {
      "name": "Colis abîmés (pots en verre cassés)",
      "type": "pain_point",
      "description": "One-line definition of what is coded under this theme.",
      "count": 23,
      "intensity": 4,
      "emotions": ["colère", "déception"],
      "channels": ["site", "appel"],
      "quotes": [
        {"id": "AV-0042", "text": "Le pot était en miettes...", "rating": 1, "channel": "site"}
      ]
    },
    {
      "name": "Efficacité des soins",
      "type": "delight",
      "description": "...",
      "count": 61,
      "emotions": ["satisfaction"],
      "quotes": []
    }
  ],
  "sentiment": {"positive": 98, "mixed": 30, "neutral": 7, "negative": 70, "comment": "..."},
  "emotions": [{"emotion": "frustration", "count": 41, "comment": "mostly delivery"}],
  "weak_signals": [
    {"signal": "...", "count": 3, "evidence_ids": ["AV-0187"], "why_it_matters": "...", "recommended_check": "..."}
  ],
  "action_plan": [
    {"action": "...", "themes": ["..."], "horizon": "quick win", "impact": "high", "effort": "low",
     "owner": "Logistique", "kpi": "..."}
  ],
  "limitations": ["..."]
}
```

Rules:
- `count` is an integer number of verbatims; `intensity` is required (1-5) for pain points.
- Use the user's language for names and texts; quotes stay verbatim.
- `export_report` adds `priorities` (scores and quadrants), `stats` (if `dataset_id` is given)
  and `generated_at` to the JSON.
