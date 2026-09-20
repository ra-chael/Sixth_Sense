#This script is looking at the EEG data and calculating the valence and arousal based on the frontal alpha asymmetry and frontal beta/(alpha+theta) ratio. It also keeps track of the baseline and smoothed state across captures, and provides a method to update the estimates based on new windows of EEG data.

"""Valence/arousal estimation from an 8-channel Cyton window.

Valence comes from frontal alpha asymmetry (right-minus-left alpha power at
Fp2/Fp1) and arousal from the frontal beta/(alpha+theta) ratio. Both are
expressed relative to a per-participant baseline, because the absolute values
differ enormously between people and between electrode placements.

This is a demonstration estimate of affective state, not a clinical measure.
"""

import numpy as np
from scipy.signal import welch

SAMPLE_RATE = 250

# OpenBCI Cyton default 10-20 placement, in channel order.
CHANNEL_NAMES = ["Fp1", "Fp2", "C3", "C4", "P7", "P8", "O1", "O2"]

LEFT_FRONTAL = "Fp1"
RIGHT_FRONTAL = "Fp2"

BANDS = {
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
}

# Smoothing and hysteresis. The EMA keeps a single noisy window from yanking
# the display around; the margin means a state has to be clearly exceeded
# before we switch, so the UI does not flicker on the boundary.
EMA_ALPHA = 0.25
HYSTERESIS = 0.08

# Lower bounds on the baseline spread, in the units of each raw measure.
# Without these a very consistent baseline makes every later window look like
# a large deviation.
MIN_VALENCE_STD = 0.25
MIN_AROUSAL_STD = 0.05

STATES = ["Stable", "Elevated", "High Distress Signal"]

# Arousal thresholds on the normalized (baseline-relative) scale.
MODERATE_AROUSAL = 0.35
EXTREME_AROUSAL = 0.70

# this method is creating an array aswell as a window for the sample rate
def band_powers(window):
    """Per-channel power in each band. window is (n_channels, n_samples)."""
    window = np.asarray(window, dtype=float)
    nperseg = min(window.shape[-1], 256)
    freqs, psd = welch(window, fs=SAMPLE_RATE, nperseg=nperseg, axis=-1)

    powers = {}
    for name, (low, high) in BANDS.items():
        mask = (freqs >= low) & (freqs <= high)
        powers[name] = psd[..., mask].mean(axis=-1)
    return powers

# this method is getting the index of a channel name in the channel_names list. 
def _channel_index(name, channel_names):
    try:
        return channel_names.index(name)
    except ValueError:
        return None

# this method is creating windows for the valence and arousal of the EEG data. It calculates the log-ratio of right to left frontal alpha for valence and the ratio of frontal beta to slower activity for arousal. It returns the valence, arousal, and per-channel powers.
def raw_valence_arousal(window, channel_names=None):
    """Unnormalized valence and arousal for a single window.

    Returns (valence, arousal, per_channel_powers). Valence is the log-ratio of
    right to left frontal alpha — positive means relatively more left-frontal
    activity, which the approach-withdrawal literature associates with more
    positive affect. Arousal is frontal beta over slower activity.
    """
    channel_names = channel_names or CHANNEL_NAMES
    powers = band_powers(window)

    left = _channel_index(LEFT_FRONTAL, channel_names)
    right = _channel_index(RIGHT_FRONTAL, channel_names)

    eps = 1e-12
    alpha = powers["alpha"]

    if left is not None and right is not None:
        valence = float(np.log(alpha[right] + eps) - np.log(alpha[left] + eps))
        frontal = [left, right]
    else:
        # No frontal pair available — valence is undefined, report neutral.
        valence = 0.0
        frontal = list(range(min(2, len(alpha))))

    beta = powers["beta"][frontal].mean()
    slow = powers["alpha"][frontal].mean() + powers["theta"][frontal].mean()
    arousal = float(beta / (slow + eps))

    return valence, arousal, powers

# this class is tracking the baseline and smoothed state across captures. It holds the baseline values for valence and arousal, as well as the exponentially smoothed values for valence and arousal. It also keeps track of the current state (Stable, Elevated, or High Distress Signal) based on the smoothed values.
class EmotionTracker:
    """Holds the baseline and the smoothed state across captures."""

    def __init__(self, channel_names=None):
        self.channel_names = channel_names or CHANNEL_NAMES
        self.baseline = None
        self.valence_ema = None
        self.arousal_ema = None
        self.state = "Stable"

    # -- baseline ---------------------------------------------------------

    def set_baseline(self, windows):
        """Calibrate from a list of resting windows."""
        valences, arousals = [], []
        for window in windows:
            valence, arousal, _ = raw_valence_arousal(window, self.channel_names)
            valences.append(valence)
            arousals.append(arousal)

        # A short baseline can produce an implausibly small spread, which would
        # make the z-scores explode and peg the display at its limits on
        # ordinary resting variation. Floor the std so normal drift stays in
        # the middle of the scale.
        self.baseline = {
            "valence_mean": float(np.mean(valences)),
            "valence_std": max(float(np.std(valences)), MIN_VALENCE_STD),
            "arousal_mean": float(np.mean(arousals)),
            "arousal_std": max(float(np.std(arousals)), MIN_AROUSAL_STD),
        }
        return self.baseline

    @property
    def calibrated(self):
        return self.baseline is not None

    # -- per-window update ------------------------------------------------

    # this method updates the valence and arousal estimates based on a new window of EEG data
    def update(self, window):
        valence, arousal, powers = raw_valence_arousal(window, self.channel_names)

        if self.baseline:
            b = self.baseline
            valence_n = (valence - b["valence_mean"]) / b["valence_std"]
            arousal_n = (arousal - b["arousal_mean"]) / b["arousal_std"]
        else:
            # Uncalibrated: fall back to a fixed scaling so the UI still moves.
            valence_n = valence
            arousal_n = arousal - 1.0

        # z-scores are unbounded; squash to a stable display range.
        valence_s = float(np.tanh(valence_n / 2.0))
        arousal_s = float(np.tanh(arousal_n / 2.0))

        self.valence_ema = _ema(self.valence_ema, valence_s, EMA_ALPHA)
        self.arousal_ema = _ema(self.arousal_ema, arousal_s, EMA_ALPHA)

        self.state = self._next_state(self.arousal_ema, self.valence_ema)

        return {
            "valence": round(self.valence_ema, 3),
            "arousal": round(self.arousal_ema, 3),
            "valence_raw": round(valence_s, 3),
            "arousal_raw": round(arousal_s, 3),
            "state": self.state,
            "level": STATES.index(self.state),
            "calibrated": self.calibrated,
            "band_powers": {
                band: {
                    name: float(value)
                    for name, value in zip(self.channel_names, channel_powers)
                }
                for band, channel_powers in powers.items()
            },
        }

    # this method maps the arousal onto a level based on the current state and hysteresis. It returns "High Distress Signal" if the arousal exceeds the extreme threshold, "Elevated" if it exceeds the moderate threshold, and "Stable" otherwise.
    def _next_state(self, arousal, valence):
        """Map arousal (with negative valence aggravating it) onto a level.

        Hysteresis: leaving the current state needs the threshold to be
        exceeded by HYSTERESIS, so a value sitting on a boundary holds.
        """
        # Negative valence pushes the same arousal into a higher level —
        # Positive valence may indicate that elevated arousal is not distress.
        # The resulting state is an experimental signal estimate, not a diagnosis.
        distress = arousal + max(0.0, -valence) * 0.5

        current = STATES.index(self.state)
        moderate = MODERATE_AROUSAL
        extreme = EXTREME_AROUSAL

        if current >= 1:
            moderate -= HYSTERESIS
        if current >= 2:
            extreme -= HYSTERESIS

        if distress >= extreme:
            return "High Distress Signal"
        if distress >= moderate:
            return "Elevated"
        return "Stable"

# this method returning the value of the moving average of the previous value and the current value based on the alpha parameter.
def _ema(previous, value, alpha):
    if previous is None:
        return value
    return previous * (1 - alpha) + value * alpha
