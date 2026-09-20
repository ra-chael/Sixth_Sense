"""Plain-language summary of a state change, written without a model.

Scope, deliberately narrow: this phrases numbers the pipeline already
computed. It never sees raw EEG and never decides the state.

There is no LLM here, on purpose. The sentence a caregiver needs is simple
enough to assemble directly, and a template cannot hallucinate, cannot leak
the figures back, cannot invent a claim about the hardware, and cannot stall
the interface waiting on a provider. Every summary is produced locally, in
microseconds, with no key and no network.
"""


def _band(value, high, mid, labels):
    magnitude = abs(value)
    if magnitude >= high:
        return labels[0]
    if magnitude >= mid:
        return labels[1]
    return labels[2]


def summarize(event):
    """One caregiver-facing sentence describing a state change.

    Describes the signal, not the person: the pipeline measures EEG activity,
    and phrasing it as what someone feels would claim more than the
    measurement supports.
    """
    arousal = event.get("arousal", 0.0)
    valence = event.get("valence", 0.0)
    rising = event.get("state") in ("Moderate", "Extreme")

    size = _band(arousal, 0.6, 0.3, ["sharply", "noticeably", "slightly"])
    sentence = f"Activation rose {size}" if rising else f"Activation settled {size}"

    if valence < -0.25:
        sentence += " with a negative tone"
    elif valence > 0.25:
        sentence += " with a positive tone"

    # Movement first: a reading taken while the head moved may be movement
    # artefact rather than a real change, which is the most useful caveat a
    # caregiver can be given.
    if event.get("moving"):
        sentence += "; the head moved, so this may be movement rather than a real change"
    elif event.get("signal_quality") == "Poor":
        sentence += "; signal quality was poor, so the reading is unreliable"
    elif event.get("motion") is not None:
        sentence += "; the head was still"

    return sentence + "."


# The previous name, kept so existing callers and tests keep working.
fallback = summarize
narrate = summarize
