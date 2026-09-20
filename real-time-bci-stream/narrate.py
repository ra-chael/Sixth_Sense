"""Plain-language narration of a state change, via a local LLM.

Scope, deliberately narrow: the model is given numbers this pipeline already
computed and asked to phrase them for a caregiver. It never sees raw EEG and
never decides the state — an LLM cannot read EEG, and letting one infer
emotion would replace a defensible signal chain with a confident guess.

Everything runs locally through Ollama, so no participant data leaves the
machine. If Ollama is not running or the model is missing, narration is
skipped and the app is unaffected.
"""

import json
import urllib.error
import urllib.request

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:8b"

# Short, because this runs while a caregiver is waiting to read it.
TIMEOUT_S = 20

SYSTEM_PROMPT = """You write one-line notes for a caregiver monitoring a \
non-verbal patient through an EEG comfort/discomfort visualizer.

You are given measurements the system already computed. Your job is only to \
phrase them in plain language. Follow these rules exactly:

- One sentence, at most 25 words.
- Describe what the signal did, not what the patient feels. Say "signals \
suggest", "reading shows", not "the patient is distressed".
- Never diagnose, never suggest medical action, never mention pain.
- If movement was detected, say so — it means the reading may reflect \
motion rather than a change of state.
- If signal quality is Poor, say the reading is uncertain.
- No preamble, no quotes, no explanation. Output the sentence only."""


def available(model=DEFAULT_MODEL):
    """True when Ollama is reachable and the model is present."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=2) as r:
            tags = json.load(r)
        names = [m.get("name", "") for m in tags.get("models", [])]
        return any(n == model or n.startswith(model.split(":")[0]) for n in names)
    except Exception:
        return False


def _describe(event):
    """The measurements, as a compact line for the model to rephrase."""
    parts = [
        f"state changed from {event.get('from_state')} to {event.get('state')}",
        f"valence {event.get('valence', 0):+.2f}",
        f"arousal {event.get('arousal', 0):+.2f}",
        f"signal quality {event.get('signal_quality', 'unknown')}",
    ]

    motion = event.get("motion")
    if motion is not None:
        parts.append(
            "head movement detected" if event.get("moving") else "head still"
        )

    return "; ".join(parts)


def narrate(event, model=DEFAULT_MODEL, timeout=TIMEOUT_S):
    """One caregiver-facing sentence for a state change, or None.

    Returns None on any failure — a missing narration is a cosmetic loss, and
    nothing here is allowed to interrupt a session.
    """
    payload = {
        "model": model,
        "prompt": _describe(event),
        "system": SYSTEM_PROMPT,
        "stream": False,
        "think": False,
        "options": {
            # Low temperature: this is rephrasing, not writing.
            "temperature": 0.3,
            "num_predict": 60,
        },
    }

    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = json.load(r).get("response", "").strip()
    except Exception:
        return None

    return _clean(text)


def _clean(text):
    """Strip the things small models add despite being told not to."""
    if not text:
        return None

    # Some models emit a reasoning block even with think disabled.
    if "</think>" in text:
        text = text.split("</think>", 1)[1].strip()

    text = text.strip().strip('"').strip()

    # One sentence only.
    for end in (". ", "\n"):
        if end in text:
            text = text.split(end, 1)[0].rstrip(".") + "."
            break

    return text or None
