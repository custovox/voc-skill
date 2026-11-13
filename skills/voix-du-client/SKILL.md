---
name: voix-du-client
description: Turns customer reviews, verbatims, survey comments, support tickets or call transcripts into an actionable Voice-of-the-Customer (VoC) diagnosis - themes and pain points, sentiment and emotions, weak signals, representative quotes, prioritisation (frequency x intensity) and an action plan. Use when the user wants to analyse customer feedback, avis clients, verbatims, irritants, NPS/CSAT comments or "voix du client", in French or English.
license: MIT
compatibility: Works on its own; much better with the companion "voc" MCP server (load_feedback, anonymize, stats, sample, export_report, optional transcribe).
metadata:
  author: CustoVox.ai
  version: "0.1.0"
  language: fr, en
---

# Voice of the Customer analysis / Analyse de la voix du client

You turn raw customer feedback into a diagnosis a CX, marketing or customer-service
team can act on. **You do the semantic analysis yourself**: no external AI API is needed.
The `voc` MCP tools handle the deterministic parts (loading, anonymisation, statistics,
sampling, scoring and report files).

**Language**: write the report in the language of the user (French by default if the
data is in French). Quotes stay in their original language.

## Step 0 - Frame the request (ask only what is missing)

1. Which file(s) or folder? (CSV, XLSX, JSON, TXT, call transcripts, audio)
2. Business context: brand/sector, period, what decision the analysis should inform.
3. Any specific question (e.g. "why did ratings drop in March?", "delivery only")?
4. Output folder for the report (default: a `voc-report/` folder next to the data).

If the user just gives a file and says "analyse", proceed with sensible defaults and state them.

## Step 1 - Load and protect the data (GDPR)

- Call `load_feedback(path)`. Anonymisation is **on by default**: never turn it off unless
  the user explicitly confirms there is no personal data.
- Check the detected columns in the response; if wrong, call again with `text_column`,
  `date_column`, `rating_column`, `channel_column`.
- Audio files: if the `transcribe` tool exists, call it with `output_dir`, then load the
  produced `.txt` transcripts. If it does not exist, tell the user that audio needs the
  optional `[audio]` extra (see README) - do not try to transcribe otherwise.
- Never copy personal data into the report. If you notice unmasked personal data in a
  verbatim, mask it yourself in quotes (e.g. `[NAME]`) and mention it in the limitations.

**Without the MCP server**: read the file directly, mask personal data yourself before
quoting anything, and compute counts by hand or with a short script.

## Step 2 - Describe

Call `stats(dataset_id)`: volume, period, channels, ratings, evolution over time.
Note anything striking (a channel with much lower ratings, a month with a spike).

## Step 3 - Read the verbatims

- Up to ~300 short reviews: `sample(dataset_id, n=<total>)` returns everything
  (use `offset`/`limit` to page through).
- Larger files: `sample(dataset_id, n=200-300, strata=["channel","rating"])`, then a
  second sample with another `seed` to check that your themes are stable. Always say in
  the report that counts were extrapolated from a sample, and how.

## Step 4 - Analyse (the core of the work)

Follow `references/analysis-grid.md`. In short:

1. **Themes and pain points** - code each verbatim with 1-3 themes from an emerging
   codebook (start from the e-commerce taxonomy in the grid, rename to fit the data).
   Aim for 6-12 themes, mutually exclusive, each with a one-line definition. Separate
   `pain_point` themes from `delight` themes (strengths).
2. **Count** mentions per theme (number of verbatims, not number of words). Be honest:
   count as you go, keep the ids of the verbatims for each theme.
3. **Sentiment and emotions** - overall sentiment per verbatim (positive / mixed /
   neutral / negative) and dominant emotion (frustration, anger, disappointment,
   worry, confusion, relief, satisfaction, delight, trust). Sarcasm counts as negative.
4. **Intensity (1-5)** per pain point - see the scale in the grid: 1 = mild annoyance,
   3 = clear dissatisfaction, 5 = rupture (churn, refund demand, public escalation,
   health or safety issue).
5. **Weak signals** - see `references/weak-signals.md`: rare but new, severe or
   growing topics (e.g. 3 mentions of skin reaction in the last month). Give the ids.
6. **Quotes** - 2-3 per theme, short, typical (not the most extreme unless flagged),
   varied in channel and rating, kept verbatim (already anonymised).

## Step 5 - Prioritise and plan

- Priority score = share of mentions x intensity (computed by `export_report`), placed in
  four quadrants: urgent (frequent and intense), widespread irritant, acute targeted
  issue, monitor. See `references/prioritisation.md`.
- Action plan: for each top pain point, 1-2 concrete actions with horizon (quick win
  < 1 month / 3 months / 6 months+), expected impact, effort, owner (team), and a KPI to
  track. Actions address root causes, not only symptoms. Also capitalise on strengths.

## Step 6 - Export

Build the `analysis` object described in `references/report-template.md` and call
`export_report(analysis, output_dir, language="fr"|"en", dataset_id=...)`.
Then give the user, in the chat: the 3-5 key findings, the top 3 priorities, the weak
signals, and the paths of the `.md` and `.json` files.

## Quality checklist (before answering)

- [ ] Every number in the report comes from a count, `stats`, or is clearly marked as an estimate.
- [ ] Each theme has a definition, a count, quotes; each pain point has an intensity.
- [ ] Positive themes are reported too (what to protect).
- [ ] Weak signals are backed by verbatim ids.
- [ ] No personal data in quotes. Limitations stated (sample, period, channel bias, auto-roles in calls).
- [ ] Recommendations are specific to the data, not generic CX advice.
