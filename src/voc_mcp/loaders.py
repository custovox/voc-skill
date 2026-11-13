"""Read customer feedback files and normalise them into a common record format.

Every record is a plain ``dict`` with these keys (missing values are ``None``):

    id       - row identifier (from the file, or generated)
    text     - the verbatim (review, comment, call transcript...)
    date     - ISO date string "YYYY-MM-DD"
    rating   - numeric rating as float (e.g. 4.0)
    channel  - source channel (e.g. "site", "appel", "email")
    source   - file the record comes from
    extra    - other columns, kept as-is

Supported inputs: CSV, XLSX, JSON (list of objects or {"records": [...]}),
TXT (one feedback per line, or a whole call transcript per file), and folders
containing any of these.
"""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

SUPPORTED = {".csv", ".tsv", ".xlsx", ".json", ".txt"}

# Column-name candidates (lower-case, accents removed) for automatic detection.
CANDIDATES = {
    "text": ["text", "texte", "verbatim", "commentaire", "comment", "comments", "avis",
             "review", "review_text", "message", "feedback", "contenu", "content", "body",
             "transcription", "transcript", "description"],
    "date": ["date", "date_avis", "review_date", "created_at", "created", "timestamp",
             "datetime", "date_creation", "submitted_at"],
    "rating": ["note", "rating", "score", "stars", "etoiles", "nps", "csat", "note_globale"],
    "channel": ["canal", "channel", "source", "origine", "plateforme", "platform", "media"],
    "id": ["id", "identifiant", "review_id", "id_avis", "ticket_id", "uid"],
}

# Lines like "Agent : bonjour" or "CLIENT: hello" identify a call transcript.
SPEAKER_LINE = re.compile(r"^\s*(agent|conseill[eè]re?|client|customer|caller|advisor|speaker\s*\d+)\s*[:\-–]",
                          re.IGNORECASE | re.MULTILINE)


def _norm(name: str) -> str:
    """Normalise a column name: lower-case, no accents, underscores."""
    table = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")
    return re.sub(r"[\s\-]+", "_", str(name).strip().lower().translate(table))


def detect_columns(headers: list[str], rows: list[dict[str, Any]]) -> dict[str, str | None]:
    """Guess which column holds the text, date, rating, channel and id."""
    normed = {_norm(h): h for h in headers}
    found: dict[str, str | None] = {}
    for role, names in CANDIDATES.items():
        found[role] = next((normed[n] for n in names if n in normed), None)
    if found["text"] is None and headers:
        # Fallback: the column with the longest average content is the verbatim.
        def avg_len(h: str) -> float:
            vals = [str(r.get(h) or "") for r in rows[:200]]
            return sum(map(len, vals)) / max(len(vals), 1)
        found["text"] = max(headers, key=avg_len)
    return found


def parse_date(value: Any) -> str | None:
    """Turn common date representations into "YYYY-MM-DD" (or None)."""
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
                "%d/%m/%Y", "%d/%m/%Y %H:%M", "%d/%m/%y", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:19] if "T" in s else s, fmt).date().isoformat()
        except ValueError:
            continue
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)  # ISO with timezone, etc.
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def parse_rating(value: Any) -> float | None:
    """Accept 4, "4", "4,5", "4/5", "4.5 étoiles" -> float."""
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(value))
    return float(m.group(0).replace(",", ".")) if m else None


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):  # Excel on Windows often saves cp1252
        try:
            content = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    # Delimiter: the most frequent candidate in the header line. This is more
    # robust than csv.Sniffer, which fails on some Windows (CRLF) files.
    header = content.splitlines()[0] if content else ""
    delimiter = max(",;\t|", key=header.count) if header else ","
    if path.suffix.lower() == ".tsv":
        delimiter = "\t"
    reader = csv.DictReader(io.StringIO(content, newline=""), delimiter=delimiter)
    rows = [dict(r) for r in reader]
    return list(reader.fieldnames or []), rows


def _read_xlsx(path: Path, sheet: str | None) -> tuple[list[str], list[dict[str, Any]]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - openpyxl is a core dependency
        raise RuntimeError("Reading .xlsx files requires openpyxl (pip install openpyxl).") from exc
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    headers = [str(h) if h is not None else f"col_{i}" for i, h in enumerate(next(it, []))]
    rows = [dict(zip(headers, r)) for r in it if any(c not in (None, "") for c in r)]
    wb.close()
    return headers, rows


def _read_json(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):  # {"records": [...]} / {"reviews": [...]} / {"data": [...]}
        data = next((v for v in data.values() if isinstance(v, list)), [data])
    rows = [r if isinstance(r, dict) else {"text": r} for r in data]
    headers: list[str] = []
    for r in rows:
        headers += [k for k in r if k not in headers]
    return headers, rows


def _read_txt(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    content = path.read_text(encoding="utf-8-sig", errors="replace")
    if len(SPEAKER_LINE.findall(content)) >= 2:
        # A call transcript: the whole file is one record.
        return ["text"], [{"id": path.stem, "text": content.strip(), "channel": "call"}]
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    return ["text"], [{"text": ln} for ln in lines]


def read_file(path: Path, sheet: str | None = None) -> tuple[list[str], list[dict[str, Any]]]:
    """Dispatch on file extension; returns (headers, raw rows)."""
    ext = path.suffix.lower()
    if ext in (".csv", ".tsv"):
        return _read_csv(path)
    if ext == ".xlsx":
        return _read_xlsx(path, sheet)
    if ext == ".json":
        return _read_json(path)
    if ext == ".txt":
        return _read_txt(path)
    raise ValueError(f"Unsupported file type: {ext} (supported: {', '.join(sorted(SUPPORTED))})")


def load_records(
    path: str | Path,
    text_column: str | None = None,
    date_column: str | None = None,
    rating_column: str | None = None,
    channel_column: str | None = None,
    id_column: str | None = None,
    sheet: str | None = None,
    default_channel: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load one file, or every supported file in a folder and its sub-folders.

    Explicit ``*_column`` arguments override automatic detection.
    Returns (records, info) where info describes detected columns per file.
    """
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"File or folder not found: {p}")
    files = sorted(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED) if p.is_dir() else [p]
    if not files:
        raise ValueError(f"No supported files in {p}")

    records: list[dict[str, Any]] = []
    info: dict[str, Any] = {"files": []}
    overrides = {"text": text_column, "date": date_column, "rating": rating_column,
                 "channel": channel_column, "id": id_column}
    for f in files:
        headers, rows = read_file(f, sheet)
        cols = detect_columns(headers, rows)
        for role, forced in overrides.items():
            if forced:
                if forced not in headers:
                    raise ValueError(f"Column '{forced}' not found in {f.name}. Columns: {headers}")
                cols[role] = forced
        used = {c for c in cols.values() if c}
        skipped = 0
        for i, row in enumerate(rows, start=1):
            text = str(row.get(cols["text"]) or "").strip() if cols["text"] else ""
            if not text:
                skipped += 1
                continue
            records.append({
                "id": str(row.get(cols["id"])) if cols["id"] and row.get(cols["id"]) not in (None, "")
                else (row.get("id") or f"{f.stem}-{i}"),
                "text": text,
                "date": parse_date(row.get(cols["date"])) if cols["date"] else None,
                "rating": parse_rating(row.get(cols["rating"])) if cols["rating"] else None,
                # Priority: channel column > default_channel argument > channel implied by the
                # file type ("call" for transcripts)
                "channel": (str(row.get(cols["channel"])).strip() if cols["channel"] and row.get(cols["channel"])
                            else default_channel or row.get("channel")),
                "source": f.name,
                "extra": {k: v for k, v in row.items() if k not in used and k not in ("id", "channel")
                          and v not in (None, "")},
            })
        info["files"].append({"file": f.name, "rows": len(rows), "empty_skipped": skipped,
                              "columns": headers, "detected": cols})
    # Make ids unique across files
    seen: dict[str, int] = {}
    for r in records:
        rid = str(r["id"])
        if rid in seen:
            seen[rid] += 1
            r["id"] = f"{rid}#{seen[rid]}"
        else:
            seen[rid] = 0
    return records, info
