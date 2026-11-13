"""VoC MCP server: deterministic tools that support a Voice-of-the-Customer
analysis performed by the agent itself (no external AI API, no API key).

Typical flow (also described in skills/voix-du-client/SKILL.md):

    load_feedback -> stats -> sample -> (agent analyses) -> export_report

Datasets are kept in memory for the duration of the session and are identified
by a short ``dataset_id``. Anonymisation is applied at load time by default.

Run locally:   uv run voc-mcp        (or: python -m voc_mcp.server)
"""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from . import __version__
from .anonymize import anonymize_text
from .loaders import load_records
from .report import build_report
from .sampling import stratified_sample
from .stats import compute_stats
from . import transcribe as tr

mcp = FastMCP(
    name="voc",
    version=__version__,
    instructions=(
        "Tools to load, pseudonymise, describe and sample customer feedback, then export a "
        "Voice-of-the-Customer report. Always keep anonymisation on unless the user explicitly "
        "says the data contains no personal information. The semantic analysis (themes, "
        "emotions, weak signals, actions) is done by you, following the 'voix-du-client' skill."
    ),
)

# In-memory store: dataset_id -> {"records": [...], "info": {...}}
DATASETS: dict[str, dict[str, Any]] = {}

# Maximum characters of verbatim returned per record, to protect the context window.
MAX_TEXT = int(os.getenv("VOC_MAX_TEXT_CHARS", "2000"))


def _get(dataset_id: str) -> dict[str, Any]:
    if dataset_id not in DATASETS:
        known = ", ".join(DATASETS) or "none"
        raise ValueError(f"Unknown dataset_id '{dataset_id}'. Loaded datasets: {known}. Call load_feedback first.")
    return DATASETS[dataset_id]


def _public(r: dict[str, Any]) -> dict[str, Any]:
    """Compact view of a record for the agent (no 'extra', long texts truncated)."""
    text = r["text"] if len(r["text"]) <= MAX_TEXT else r["text"][:MAX_TEXT] + " […]"
    return {k: v for k, v in {"id": r["id"], "text": text, "date": r["date"], "rating": r["rating"],
                              "channel": r["channel"]}.items() if v is not None}


@mcp.tool
def load_feedback(
    path: Annotated[str, Field(description="Path to a CSV, XLSX, JSON or TXT file, or to a folder of such files.")],
    dataset_id: Annotated[str | None, Field(description="Name for this dataset; defaults to the file or folder name.")] = None,
    text_column: Annotated[str | None, Field(description="Column holding the verbatim; auto-detected if omitted.")] = None,
    date_column: Annotated[str | None, Field(description="Date column; auto-detected if omitted.")] = None,
    rating_column: Annotated[str | None, Field(description="Rating column (e.g. 1-5); auto-detected if omitted.")] = None,
    channel_column: Annotated[str | None, Field(description="Channel column; auto-detected if omitted.")] = None,
    sheet: Annotated[str | None, Field(description="Excel sheet name (first sheet by default).")] = None,
    default_channel: Annotated[str | None, Field(description="Channel to use when the file has none (e.g. 'email').")] = None,
    anonymize: Annotated[bool, Field(description="Pseudonymise personal data at load time. Keep True (GDPR) unless told otherwise.")] = True,
) -> dict[str, Any]:
    """Load customer feedback (reviews, verbatims, call transcripts) and normalise it.

    Columns for text, date, rating and channel are detected from common French and
    English names, or can be forced. Returns a summary and a 5-record preview;
    use `stats` and `sample` to explore the data.
    """
    records, info = load_records(path, text_column, date_column, rating_column, channel_column,
                                 sheet=sheet, default_channel=default_channel)
    masked: Counter = Counter()
    if anonymize:
        for r in records:
            r["text"], c = anonymize_text(r["text"])
            masked += c
    did = dataset_id or Path(path).stem or "dataset"
    DATASETS[did] = {"records": records, "info": info, "anonymized": anonymize}
    return {
        "dataset_id": did,
        "records": len(records),
        "files": info["files"],
        "anonymized": anonymize,
        "masked_entities": dict(masked),
        "preview": [_public(r) for r in records[:5]],
        "next_step": "Call stats(dataset_id), then sample(dataset_id) to read the verbatims.",
    }


@mcp.tool
def anonymize(
    text: Annotated[str | None, Field(description="A text to pseudonymise.")] = None,
    dataset_id: Annotated[str | None, Field(description="A loaded dataset to pseudonymise in place.")] = None,
) -> dict[str, Any]:
    """Mask personal data: names, e-mails, phones, postal addresses, IBAN, card,
    order and contract numbers. Works on a single text or on a whole dataset.

    Rule-based (French and English formats). Best effort: review the output.
    """
    if text is None and dataset_id is None:
        raise ValueError("Provide either 'text' or 'dataset_id'.")
    if text is not None:
        masked, counts = anonymize_text(text)
        return {"text": masked, "masked_entities": dict(counts)}
    ds = _get(dataset_id)  # type: ignore[arg-type]
    total: Counter = Counter()
    for r in ds["records"]:
        r["text"], c = anonymize_text(r["text"])
        total += c
    ds["anonymized"] = True
    return {"dataset_id": dataset_id, "records": len(ds["records"]), "masked_entities": dict(total)}


@mcp.tool
def stats(
    dataset_id: Annotated[str, Field(description="Dataset returned by load_feedback.")],
    period: Annotated[str, Field(description="Time bucket: 'month', 'week' or 'day'.")] = "month",
) -> dict[str, Any]:
    """Descriptive statistics: volume, date range, breakdown by channel, by period
    (with average rating) and by rating, text length and missing values."""
    return compute_stats(_get(dataset_id)["records"], period=period)


@mcp.tool
def sample(
    dataset_id: Annotated[str, Field(description="Dataset returned by load_feedback.")],
    n: Annotated[int, Field(description="Number of records to return. If n >= dataset size, all records are returned.", ge=1, le=2000)] = 150,
    strata: Annotated[list[str] | None, Field(description="Stratification keys among 'channel', 'rating', 'month'. Default: channel + rating.")] = None,
    seed: Annotated[int, Field(description="Random seed, for a reproducible sample.")] = 42,
    offset: Annotated[int, Field(description="When returning all records, skip this many (pagination).", ge=0)] = 0,
    limit: Annotated[int | None, Field(description="When returning all records, return at most this many (pagination).")] = None,
) -> dict[str, Any]:
    """Return verbatims to analyse. For large files, draws a stratified sample
    proportional to each segment, with at least one record per segment so that
    rare segments (e.g. 1-star phone complaints) are not lost."""
    records = _get(dataset_id)["records"]
    picked, allocation = stratified_sample(records, n, strata, seed)
    page = picked[offset: offset + limit if limit else None]
    return {
        "dataset_id": dataset_id,
        "population": len(records),
        "sampled": len(picked),
        "returned": len(page),
        "offset": offset,
        "allocation": allocation,
        "records": [_public(r) for r in page],
    }


@mcp.tool
def export_report(
    analysis: Annotated[dict[str, Any], Field(description=(
        "Structured analysis. Required: 'themes' = list of {name, type ('pain_point'|'delight'), description, "
        "count (int), intensity (1-5, pain points), emotions [str], channels [str], quotes [{id, text, rating, channel}]}. "
        "Optional: title, scope {source, records_analysed, records_total, sampling}, executive_summary [str], "
        "sentiment {positive, mixed, neutral, negative, comment}, emotions [{emotion, count, comment}], "
        "weak_signals [{signal, count, evidence_ids, why_it_matters, recommended_check}], "
        "action_plan [{action, themes, horizon, impact, effort, owner, kpi}], limitations [str]."))],
    output_dir: Annotated[str, Field(description="Folder where the report files are written.")],
    filename: Annotated[str, Field(description="Base file name, without extension.")] = "voc_report",
    language: Annotated[str, Field(description="Report headings language: 'fr' or 'en'.")] = "fr",
    dataset_id: Annotated[str | None, Field(description="If given, the dataset statistics are embedded in the report.")] = None,
) -> dict[str, Any]:
    """Write a Markdown report and a structured JSON file. Pain points are ranked
    by score = share of mentions x intensity, and placed in a priority quadrant.
    Quotes are re-anonymised as a safety net."""
    st = compute_stats(_get(dataset_id)["records"]) if dataset_id else None
    return build_report(analysis, output_dir, filename, language, st)


if tr.is_available():
    # Registered only when the optional FunASR dependency is installed.
    @mcp.tool
    def transcribe(
        path: Annotated[str, Field(description="Audio file (wav, mp3, m4a, flac...) or folder of audio files.")],
        language: Annotated[str, Field(description="'auto', 'fr', 'en'...")] = "auto",
        output_dir: Annotated[str | None, Field(description="If given, writes one 'Agent : / Client :' .txt transcript per file, ready for load_feedback.")] = None,
    ) -> dict[str, Any]:
        """Transcribe customer calls with speaker diarisation (agent / client), using FunASR.
        Roles are inferred heuristically; check them. Transcripts are pseudonymised."""
        p = Path(path).expanduser()
        files = sorted(f for f in p.iterdir() if f.suffix.lower() in tr.AUDIO_EXTENSIONS) if p.is_dir() else [p]
        results = []
        for f in files:
            res = tr.transcribe_file(f, language)
            res["transcript"], _ = anonymize_text(res["transcript"])
            res.pop("segments")  # keep the response compact
            if output_dir:
                out = Path(output_dir).expanduser()
                out.mkdir(parents=True, exist_ok=True)
                (out / f"{f.stem}.txt").write_text(res["transcript"], encoding="utf-8")
                res["saved_to"] = str(out / f"{f.stem}.txt")
            results.append(res)
        return {"files": len(results), "results": results}


def main() -> None:
    """Console entry point (stdio transport, used by Claude Code, Codex, Cursor)."""
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
