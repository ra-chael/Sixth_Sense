import numpy as np

# Mirrors whatever the real pipeline is using, so synthetic windows are
# generated at the same rate they will be analysed at. Imported as a module,
# not a value: `from emotion import SAMPLE_RATE` would copy the number at
# import time and miss any later update from the board.
import emotion as _emotion

ALPHA_FREQ = 10.0
BETA_FREQ = 22.0
GAMMA_FREQ = 38.0


# The three states the visualizer reports, as the affective coordinates that
# produce them. These are targets for the synthesiser, not display values: a
# window generated here goes through the same Welch/band-power/threshold chain
# as a real one, and the estimator has to measure its way back to the state.
# Drift is how far each reading wanders, so a preset looks like a live signal
# rather than a constant.
PRESETS = {
    "Calm": {"arousal": -0.55, "valence": 0.45, "drift": 0.10},
    "Sad": {"arousal": 0.05, "valence": -0.55, "drift": 0.12},
    "Stressed": {"arousal": 0.75, "valence": -0.70, "drift": 0.10},
}


def generate_preset_window(name, n_channels=8, n_samples=250, rng=None):
    """A window for one of the named states, with natural variation."""
    preset = PRESETS[name]
    rng = rng or np.random
    drift = preset["drift"]
    return generate_eeg_window(
        n_channels=n_channels,
        n_samples=n_samples,
        arousal=preset["arousal"] + rng.normal(0, drift),
        valence=preset["valence"] + rng.normal(0, drift),
    )


def generate_eeg_window(
    n_channels=8,
    n_samples=250,
    discomfort=False,
    arousal=None,
    valence=None,
    artifact=None,
):
    """Return a simulated EEG window shaped (n_channels, n_samples).

    arousal and valence, when given, drive the signal continuously in the
    range -1..1 and override the `discomfort` flag. They are inverses of what
    the estimator measures, so that asking for a given valence produces a
    window the estimator reads back as roughly that value:

      arousal -> fast-band (beta and gamma) amplitude against alpha/theta
      valence -> right-frontal alpha relative to left (negative suppresses Fp2)

    artifact is one of None, "blink" or "clench", and injects the transient
    that the artifact guard is meant to reject.
    """
    t = np.arange(n_samples) / _emotion.SAMPLE_RATE

    if arousal is None and valence is None:
        # Legacy two-state behaviour.
        arousal = 0.7 if discomfort else -0.4
        valence = -0.6 if discomfort else 0.3

    arousal = float(np.clip(arousal if arousal is not None else 0.0, -1.0, 1.0))
    valence = float(np.clip(valence if valence is not None else 0.0, -1.0, 1.0))

    # Map arousal onto the fast/slow amplitude balance the estimator reads.
    # Gains are deliberately gentle: a steeper mapping saturated the estimator
    # near the ends of the range, which made Moderate almost unreachable from
    # the sliders and hid the middle of the scale.
    a01 = (arousal + 1.0) / 2.0
    alpha_amp = 9.0 - 2.6 * a01
    beta_amp = 2.0 + 3.4 * a01
    gamma_amp = 0.8 + 1.8 * a01

    # Valence is an Fp2-vs-Fp1 alpha ratio: negative valence means relatively
    # less right-frontal alpha. Channels 0 and 1 stand in for Fp1 and Fp2.
    right_alpha_scale = float(np.exp(valence * 0.45))
    asymmetry = {1: right_alpha_scale}

    window = np.zeros((n_channels, n_samples))
    for ch in range(n_channels):
        phase = np.random.uniform(0, 2 * np.pi)
        scale = asymmetry.get(ch, 1.0)
        signal = (
            alpha_amp * scale * np.sin(2 * np.pi * ALPHA_FREQ * t + phase)
            + beta_amp * np.sin(2 * np.pi * BETA_FREQ * t + phase)
            + gamma_amp * np.sin(2 * np.pi * GAMMA_FREQ * t + phase)
            + 6.0 * np.sin(2 * np.pi * 6.0 * t + phase)
        )
        window[ch] = signal + np.random.normal(0, 3.0, n_samples)

    if artifact == "blink" and n_samples > 60:
        # Brief, large, mostly frontal — the shape of a real eyeblink.
        start = n_samples // 4
        span = min(18, n_samples - start)
        bump = 380.0 * np.hanning(span)
        for ch in (0, 1):
            if ch < n_channels:
                window[ch, start : start + span] += bump
    elif artifact == "clench" and n_samples > 80:
        # Sustained broadband muscle activity across every channel.
        start = n_samples // 3
        span = min(70, n_samples - start)
        window[:, start : start + span] += np.random.normal(
            0, 170.0, (n_channels, span)
        )

    return window
