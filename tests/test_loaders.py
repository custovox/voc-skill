import json

import pytest

from voc_mcp.loaders import load_records, parse_date, parse_rating


def test_parse_helpers():
    assert parse_date("12/03/2026") == "2026-03-12"
    assert parse_date("2026-03-12T10:00:00Z") == "2026-03-12"
    assert parse_date("n/a") is None
    assert parse_rating("4,5") == 4.5
    assert parse_rating("4/5") == 4.0
    assert parse_rating("") is None


def test_csv_semicolon_with_french_headers(tmp_path):
    f = tmp_path / "avis.csv"
    f.write_text("id;date;note;canal;avis\nA1;01/04/2026;5;site;\"Super crème; vraiment\"\nA2;02/04/2026;2;app;\n",
                 encoding="utf-8")
    records, info = load_records(f)
    assert len(records) == 1  # empty verbatim skipped
    r = records[0]
    assert (r["id"], r["date"], r["rating"], r["channel"]) == ("A1", "2026-04-01", 5.0, "site")
    assert info["files"][0]["empty_skipped"] == 1


def test_csv_cp1252_encoding(tmp_path):
    f = tmp_path / "excel.csv"
    f.write_bytes("comment,rating\nTrès déçue,1\n".encode("cp1252"))
    records, _ = load_records(f)
    assert records[0]["text"] == "Très déçue"


def test_forced_columns_and_unknown_column(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("col_a,col_b,stars\nshort,The parcel arrived broken and late,2\n", encoding="utf-8")
    records, _ = load_records(f, text_column="col_b", rating_column="stars")
    assert records[0]["text"].startswith("The parcel") and records[0]["rating"] == 2.0
    with pytest.raises(ValueError):
        load_records(f, text_column="nope")


def test_text_column_fallback_longest(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("x,y\n1,Une longue phrase de client mécontent\n", encoding="utf-8")
    records, info = load_records(f)
    assert info["files"][0]["detected"]["text"] == "y"


def test_xlsx(tmp_path):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Review", "Rating", "Channel", "Date"])
    ws.append(["Great serum", 5, "web", "2026-05-01"])
    f = tmp_path / "reviews.xlsx"
    wb.save(f)
    records, _ = load_records(f)
    assert records[0]["text"] == "Great serum" and records[0]["channel"] == "web"


def test_json_wrapped_list(tmp_path):
    f = tmp_path / "r.json"
    f.write_text(json.dumps({"reviews": [{"content": "Bon produit", "score": "4"}]}), encoding="utf-8")
    records, _ = load_records(f)
    assert records[0]["text"] == "Bon produit" and records[0]["rating"] == 4.0


def test_txt_lines_and_transcript_folder(tmp_path):
    (tmp_path / "lines.txt").write_text("Avis un\n\nAvis deux\n", encoding="utf-8")
    (tmp_path / "call.txt").write_text("Agent : Bonjour\nClient : J'ai un souci\n", encoding="utf-8")
    records, info = load_records(tmp_path)
    assert len(info["files"]) == 2
    call = [r for r in records if r["channel"] == "call"]
    assert len(call) == 1 and "Client : J'ai un souci" in call[0]["text"]
    assert len([r for r in records if r["source"] == "lines.txt"]) == 2


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_records("does/not/exist.csv")
