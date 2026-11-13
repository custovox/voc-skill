"""End-to-end test through a real MCP client (in memory), on the demo data."""

import asyncio
from pathlib import Path

from fastmcp import Client

from voc_mcp import transcribe as tr
from voc_mcp.server import mcp

DATA = Path(__file__).resolve().parent.parent / "examples" / "data"


def run(coro):
    return asyncio.run(coro)


async def _flow(tmp_path):
    async with Client(mcp) as c:
        tools = {t.name for t in await c.list_tools()}
        loaded = (await c.call_tool("load_feedback", {"path": str(DATA / "avis_ecommerce.csv"),
                                                       "dataset_id": "demo"})).data
        st = (await c.call_tool("stats", {"dataset_id": "demo"})).data
        smp = (await c.call_tool("sample", {"dataset_id": "demo", "n": 50})).data
        calls = (await c.call_tool("load_feedback", {"path": str(DATA / "appels"), "dataset_id": "calls"})).data
        rep = (await c.call_tool("export_report", {
            "analysis": {"themes": [{"name": "Livraison", "count": 10, "intensity": 3}]},
            "output_dir": str(tmp_path), "dataset_id": "demo"})).data
        return tools, loaded, st, smp, calls, rep


def test_full_flow(tmp_path):
    tools, loaded, st, smp, calls, rep = run(_flow(tmp_path))
    assert {"load_feedback", "anonymize", "stats", "sample", "export_report"} <= tools
    assert ("transcribe" in tools) == tr.is_available()

    assert loaded["records"] == 200 and loaded["anonymized"] is True
    assert loaded["masked_entities"]["EMAIL"] >= 1 and loaded["masked_entities"]["PHONE"] >= 2
    assert st["total"] == 200 and st["rating"]["mean"] is not None
    assert smp["sampled"] == 50 and len(smp["records"]) == 50

    assert calls["records"] == 5
    all_text = " ".join(r["text"] for r in calls["preview"])
    for secret in ("CMD-2026-51187", "06 58 41 27 93", "k.haddad@exemple.com", "Victor Hugo"):
        assert secret not in all_text

    assert Path(rep["markdown"]).exists() and Path(rep["json"]).exists()


async def _anonymize_text():
    async with Client(mcp) as c:
        return (await c.call_tool("anonymize", {"text": "Écrivez à jean@exemple.fr"})).data


def test_anonymize_tool():
    assert run(_anonymize_text())["text"] == "Écrivez à [EMAIL]"


async def _unknown_dataset():
    async with Client(mcp) as c:
        return await c.call_tool("stats", {"dataset_id": "nope"}, raise_on_error=False)


def test_unknown_dataset_is_a_clear_error():
    res = run(_unknown_dataset())
    assert res.is_error and "load_feedback" in res.content[0].text
