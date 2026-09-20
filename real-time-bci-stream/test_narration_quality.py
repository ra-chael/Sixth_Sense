"""The summary is a template, so its guarantees are testable outright.

These assert the properties that mattered when a model wrote this sentence
and kept being violated: no figures read back, no claim about what the person
feels, and the movement caveat present whenever the head moved.
"""

import narrate


def test_summary_describes_rise_and_negative_tone():
    summary = narrate.summarize(
        {"state": "Extreme", "valence": -0.66, "arousal": 0.70, "moving": False,
         "motion": 0.001, "signal_quality": "Good"}
    )

    assert summary == (
        "Activation rose sharply with a negative tone; the head was still."
    )


def test_movement_caveat_outranks_everything_else():
    # A reading taken while the head moved may be artefact, which is the most
    # useful thing a caregiver can be told about it.
    summary = narrate.summarize(
        {"state": "Extreme", "valence": -0.66, "arousal": 0.70, "moving": True,
         "motion": 0.4, "signal_quality": "Poor"}
    )

    assert "the head moved" in summary
    assert "may be movement rather than a real change" in summary


def test_poor_signal_is_called_unreliable():
    summary = narrate.summarize(
        {"state": "Moderate", "valence": -0.3, "arousal": 0.4, "moving": False,
         "motion": 0.001, "signal_quality": "Poor"}
    )

    assert "unreliable" in summary


def test_settling_reads_differently_from_rising():
    settled = narrate.summarize(
        {"state": "Stable", "valence": 0.05, "arousal": 0.1, "moving": False,
         "motion": 0.001, "signal_quality": "Good"}
    )

    assert settled.startswith("Activation settled")
    # A near-zero tone is not worth naming either way.
    assert "tone" not in settled


def test_summary_never_prints_the_figures():
    # The caregiver can already see the numbers on screen; repeating them was
    # the single most common failure when a model wrote this line.
    for valence, arousal in ((-0.66, 0.70), (0.31, 0.45), (0.0, 0.0)):
        summary = narrate.summarize(
            {"state": "Extreme", "valence": valence, "arousal": arousal,
             "moving": False, "motion": 0.001, "signal_quality": "Good"}
        )

        assert not any(c.isdigit() for c in summary), summary
        for banned in ("valence", "arousal", "Extreme", "Moderate", "Stable"):
            assert banned not in summary, summary


def test_summary_describes_the_signal_not_the_person():
    summary = narrate.summarize(
        {"state": "Extreme", "valence": -0.9, "arousal": 0.9, "moving": False,
         "motion": 0.001, "signal_quality": "Good"}
    )

    for banned in ("patient", "pain", "distress", "feels", "experiencing"):
        assert banned not in summary.lower(), summary


def test_summary_is_one_short_sentence():
    summary = narrate.summarize(
        {"state": "Extreme", "valence": -0.66, "arousal": 0.70, "moving": True,
         "motion": 0.4, "signal_quality": "Good"}
    )

    assert summary.endswith(".")
    assert summary.count(".") == 1
    assert len(summary.split()) <= 25, summary
