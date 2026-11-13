"""Optional audio transcription with speaker diarisation, based on FunASR.

This module is only active when the optional dependencies are installed:

    uv pip install "voc-mcp[audio]"      # or: pip install funasr torch torchaudio

Default model: Whisper large-v3 *turbo* (multilingual, French and English),
loaded through FunASR, with the FSMN voice-activity detector and the CAM++
speaker model for diarisation. Models are downloaded on first use (~1.6 GB).
Change them with the environment variables VOC_ASR_MODEL, VOC_VAD_MODEL,
VOC_SPK_MODEL (for example ``VOC_ASR_MODEL=paraformer-zh`` for Chinese).

Speaker roles: FunASR returns anonymous speaker ids (0, 1...). We label as
"Agent" the speaker whose first turns sound like a contact-centre greeting,
otherwise the first speaker. The agent should double-check this labelling.
"""

from __future__ import annotations

import importlib.util
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".opus", ".webm", ".mp4"}

# Phrases typical of an agent opening or handling a call (FR + EN).
AGENT_CUES = re.compile(
    r"service client|bienvenue|que puis-je|comment puis-je|je vais vérifier|votre numéro de|"
    r"je vous remercie de votre appel|merci d'avoir appelé|customer service|how can i help|"
    r"how may i help|thank you for calling|let me check|can i have your",
    re.IGNORECASE,
)


def is_available() -> bool:
    """True when FunASR (and therefore torch) can be imported."""
    return importlib.util.find_spec("funasr") is not None


@lru_cache(maxsize=1)
def _model():
    """Load the FunASR pipeline once and keep it in memory."""
    from funasr import AutoModel  # imported lazily: heavy dependency

    asr = os.getenv("VOC_ASR_MODEL", "Whisper-large-v3-turbo")
    kwargs: dict[str, Any] = dict(
        model=asr,
        vad_model=os.getenv("VOC_VAD_MODEL", "fsmn-vad"),
        spk_model=os.getenv("VOC_SPK_MODEL", "cam++"),
        disable_update=True,
    )
    if asr.lower().startswith("whisper"):
        kwargs["hub"] = "openai"  # Whisper weights are fetched from OpenAI's release
    return AutoModel(**kwargs)


def assign_roles(segments: list[dict[str, Any]]) -> dict[Any, str]:
    """Map raw speaker ids to "Agent" / "Client" (other speakers: "Speaker N")."""
    speakers = list(dict.fromkeys(s["speaker"] for s in segments))
    if not speakers:
        return {}
    first_words: dict[Any, str] = {}
    for s in segments:
        if len(first_words.get(s["speaker"], "")) < 300:
            first_words[s["speaker"]] = first_words.get(s["speaker"], "") + " " + s["text"]
    cue_scores = {spk: len(AGENT_CUES.findall(txt)) for spk, txt in first_words.items()}
    agent = max(speakers, key=lambda spk: (cue_scores.get(spk, 0), -speakers.index(spk)))
    roles = {agent: "Agent"}
    others = [s for s in speakers if s != agent]
    if others:
        roles[others[0]] = "Client"
    for i, spk in enumerate(others[1:], start=3):
        roles[spk] = f"Speaker {i}"
    return roles


def segments_from_funasr(result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise FunASR output into [{start, end, speaker, text}]."""
    out = []
    for item in result:
        sentences = item.get("sentence_info")
        if sentences:
            for s in sentences:
                out.append({"start": s.get("start", 0) / 1000, "end": s.get("end", 0) / 1000,
                            "speaker": s.get("spk", 0),
                            "text": (s.get("sentence") or s.get("text") or "").strip()})
        elif item.get("text"):
            # Model without sentence timestamps: no diarisation possible.
            out.append({"start": 0.0, "end": 0.0, "speaker": 0, "text": item["text"].strip()})
    return [s for s in out if s["text"]]


def format_transcript(segments: list[dict[str, Any]], roles: dict[Any, str]) -> str:
    """Merge consecutive turns of the same speaker into "Role : text" lines."""
    lines: list[str] = []
    last = None
    for s in segments:
        role = roles.get(s["speaker"], f"Speaker {s['speaker']}")
        if role == last:
            lines[-1] += " " + s["text"]
        else:
            lines.append(f"{role} : {s['text']}")
            last = role
    return "\n".join(lines)


def transcribe_file(path: str | Path, language: str = "auto") -> dict[str, Any]:
    """Transcribe one audio file. ``language``: "auto", "fr", "en"..."""
    if not is_available():
        raise RuntimeError(
            "Audio transcription is disabled: FunASR is not installed. "
            "Install the optional extra with: uv pip install \"voc-mcp[audio]\""
        )
    p = Path(path).expanduser()
    model = _model()
    kwargs: dict[str, Any] = {"input": str(p), "batch_size_s": 300}
    if os.getenv("VOC_ASR_MODEL", "Whisper").lower().startswith("whisper"):
        kwargs["DecodingOptions"] = {"task": "transcribe",
                                     "language": None if language == "auto" else language,
                                     "fp16": False}
    elif language != "auto":
        kwargs["language"] = language
    segments = segments_from_funasr(model.generate(**kwargs))
    roles = assign_roles(segments)
    diarised = len({s["speaker"] for s in segments}) > 1
    return {
        "file": p.name,
        "diarised": diarised,
        "roles": {str(k): v for k, v in roles.items()},
        "segments": [{**s, "role": roles.get(s["speaker"])} for s in segments],
        "transcript": format_transcript(segments, roles),
        "warning": None if diarised else "Only one speaker detected: roles could not be separated.",
    }
