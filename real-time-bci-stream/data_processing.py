import numpy as np
from scipy.signal import welch

# Single source of truth: emotion.SAMPLE_RATE is set from the board on
# connect, and a second hardcoded copy here would silently disagree with it.
import emotion as _emotion

BANDS = {
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
}


def _band_power(window, band):
    low, high = band
    freqs, psd = welch(window, fs=_emotion.SAMPLE_RATE, nperseg=min(window.shape[-1], 128), axis=-1)
    mask = (freqs >= low) & (freqs <= high)
    return psd[..., mask].mean(axis=-1).mean()


ARTIFACT_UV = 120.0
ARTIFACT_FRACTION = 0.02


def detect_artifact(window):
    """Flag windows dominated by a blink or muscle transient.

    A blink or jaw clench is a large, brief excursion that lands in the same
    fast bands as genuine arousal, so a window carrying one cannot be scored
    as if it were clean EEG. This looks for samples past a plausible cortical
    amplitude rather than judging the window as a whole, so a short spike is
    caught even when the average still looks reasonable.

    Returns (is_artifact, fraction_of_samples_affected).
    """
    window = np.asarray(window, dtype=float)
    if window.size == 0:
        return False, 0.0

    over = np.abs(window) > ARTIFACT_UV

    # Judge per channel, not across the whole array: a blink is brief and
    # lands mostly on the frontal pair, so averaging it over eight channels
    # dilutes it below any sensible threshold. The worst channel decides.
    per_channel = over.mean(axis=-1)
    fraction = float(per_channel.max())
    return fraction > ARTIFACT_FRACTION, fraction


def should_hold_window(window):
    """Return whether a window must be excluded before state estimation."""
    artifact, _ = detect_artifact(window)
    if artifact:
        return True, "Movement or blink detected"
    if check_signal_quality(window) == "Poor":
        return True, "Signal quality poor"
    return False, None


def check_signal_quality(window):
    """Very rough signal-quality heuristic based on amplitude range and flatline check."""
    window = np.asarray(window, dtype=float)
    if window.size == 0:
        return "Poor"

    peak = np.max(np.abs(window))
    variance = np.var(window)

    if peak > 200 or variance < 0.5:
        return "Poor"
    if peak > 100:
        return "Fair"
    return "Good"


def extract_features(window):
    theta_power = _band_power(window, BANDS["theta"])
    alpha_power = _band_power(window, BANDS["alpha"])
    beta_power = _band_power(window, BANDS["beta"])

    mean_amplitude = float(np.mean(np.abs(window)))
    signal_variance = float(np.var(window))
    beta_alpha_ratio = beta_power / alpha_power if alpha_power > 1e-9 else 0.0

    return {
        "mean_amplitude": mean_amplitude,
        "signal_variance": signal_variance,
        "theta_power": float(theta_power),
        "alpha_power": float(alpha_power),
        "beta_power": float(beta_power),
        "beta_alpha_ratio": float(beta_alpha_ratio),
    }


def compute_discomfort_score(features):
    """Rule-based demonstration score, 0-100. Not a medical measure."""
    ratio = features["beta_alpha_ratio"]
    variance = features["signal_variance"]

    score = 20.0 + ratio * 15.0 + min(variance, 50.0) * 0.3
    return float(np.clip(score, 0, 100))


def score_to_state(score, signal_quality):
    if signal_quality == "Poor":
        return "Uncertain"
    if score < 40:
        return "Comfortable"
    if score < 70:
        return "Uncertain"
    return "Possible discomfort"


def process_window(window):
    signal_quality = check_signal_quality(window)
    features = extract_features(window)
    discomfort_score = compute_discomfort_score(features)
    state = score_to_state(discomfort_score, signal_quality)

    return {
        **features,
        "signal_quality": signal_quality,
        "discomfort_score": round(discomfort_score, 1),
        "state": state,
    }
