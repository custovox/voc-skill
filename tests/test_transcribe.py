"""The heavy FunASR model is never loaded in tests: we test the pure helpers."""

import pytest

from voc_mcp import transcribe as tr


def test_segments_from_funasr_with_diarisation():
    raw = [{"sentence_info": [
        {"start": 0, "end": 1500, "spk": 1, "sentence": "Bonjour, j'appelle pour ma commande."},
        {"start": 1600, "end": 3000, "spk": 0, "sentence": "Service client bonjour, que puis-je faire ?"},
    ]}]
    segs = tr.segments_from_funasr(raw)
    assert segs[0] == {"start": 0.0, "end": 1.5, "speaker": 1, "text": "Bonjour, j'appelle pour ma commande."}


def test_roles_use_agent_cues_not_only_order():
    segs = [{"speaker": 1, "text": "Bonjour, j'ai un problème"},
            {"speaker": 0, "text": "Service client, comment puis-je vous aider ?"},
            {"speaker": 1, "text": "Mon colis est cassé"}]
    roles = tr.assign_roles(segs)
    assert roles == {0: "Agent", 1: "Client"}
    text = tr.format_transcript(segs, roles)
    assert text.splitlines()[0].startswith("Client : ")


def test_roles_fallback_first_speaker_and_english():
    segs = [{"speaker": "a", "text": "Hello"}, {"speaker": "b", "text": "Hi"}]
    assert tr.assign_roles(segs) == {"a": "Agent", "b": "Client"}
    segs = [{"speaker": 0, "text": "My order is late"}, {"speaker": 1, "text": "Thank you for calling, how can I help?"}]
    assert tr.assign_roles(segs)[1] == "Agent"


def test_consecutive_turns_are_merged():
    segs = [{"speaker": 0, "text": "Bonjour."}, {"speaker": 0, "text": "Je vous écoute."}]
    assert tr.format_transcript(segs, {0: "Agent"}) == "Agent : Bonjour. Je vous écoute."


@pytest.mark.skipif(tr.is_available(), reason="FunASR installed")
def test_clear_error_without_funasr(tmp_path):
    with pytest.raises(RuntimeError, match="voc-mcp\\[audio\\]"):
        tr.transcribe_file(tmp_path / "x.wav")
