"""Valence/arousal estimation from an 8-channel Cyton window.

Valence comes from frontal alpha asymmetry (right-minus-left alpha power at
Fp2/Fp1) and arousal from the ratio of fast activity (beta, plus gamma at a
reduced weight) to slow activity (alpha + theta) at the same two sites. Both
are expressed relative to a per-participant baseline, because the absolute
values differ enormously between people and between electrode placements.

Scope, stated plainly: of the eight recorded channels only the frontal pair
feeds the estimate. Not because the others are unusable — all eight record
cleanly — but because both measurements are defined on that pair. Valence is
frontal alpha asymmetry, an Fp1-vs-Fp2 quantity by construction, and frontal
beta is the standard arousal index. Bringing in the other six would require a
weighting we have no labelled data to justify, which adds parameters rather
than information. All eight are recorded and displayed so the narrowness is
visible rather than hidden.

This is a demonstration estimate of affective state, not a clinical measure.
"""

import numpy as np
from scipy.signal import welch

# The Cyton's own rate. Never hardcode a different value here: the band edges
# below are in Hz, so a mismatch between this and the board silently shifts
# every band — an "alpha" reading taken at the wrong rate is really measuring
# some other frequency entirely. set_sample_rate() updates it from the board
# at connect time.
SAMPLE_RATE = 250

# Which 10-20 site each Cyton pin is wired to, pin 1 first.
#
# VERIFY THIS AGAINST THE CAP BEFORE TRUSTING A SESSION. It is the one
# setting whose failure is invisible: wire the frontal pair somewhere else and
# the app still produces confident-looking numbers, they just describe a
# different part of the head. The montage card that ships with some caps
# numbers posterior-first (1=O2, 2=P4, 3=C4), which is the reverse of the
# BrainFlow default below.
CHANNEL_NAMES = ["Fp1", "Fp2", "C3", "C4", "P7", "P8", "O1", "O2"]

# Posterior-first wiring, as printed on the OpenBCI montage card. Swap this in
# if that is how the cap is actually connected.
CHANNEL_NAMES_POSTERIOR_FIRST = ["O2", "P4", "C4", "F4", "F3", "C3", "P3", "O1"]

LEFT_FRONTAL = "Fp1"
RIGHT_FRONTAL = "Fp2"

BANDS = {
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    # Gamma is the band most consistently associated with pain and high
    # arousal, so a discomfort estimate that ignored it would have an obvious
    # hole. It is capped below 50 Hz to stay clear of mains hum (60 Hz here,
    # 50 Hz elsewhere) and is weighted rather than counted equally with beta,
    # because scalp gamma is also where EMG from jaw and neck muscle lands.
    "gamma": (30.0, 45.0),
}

# How much gamma contributes to arousal relative to beta. Deliberately below
# 1.0: gamma is informative but the least artifact-free band we use.
GAMMA_WEIGHT = 0.5

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

# Welch needs a reasonable stretch of signal before its estimate means
# anything; below this the window is treated as not yet usable.
MIN_SAMPLES = 64

STATES = ["Stable", "Moderate", "Extreme"]

# Arousal thresholds on the normalized (baseline-relative) scale.
MODERATE_AROUSAL = 0.35
EXTREME_AROUSAL = 0.70


def set_sample_rate(rate):
    """Adopt the rate the board actually reports.

    Called once on connect. Welch and every band edge depend on it, so this
    has to match the hardware rather than an assumption — the failure mode is
    silent and total: at the wrong rate the alpha band measures a different
    frequency and nothing looks broken.
    """
    global SAMPLE_RATE
    rate = int(rate)
    if rate <= 0:
        return SAMPLE_RATE
    SAMPLE_RATE = rate
    return SAMPLE_RATE


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


def _channel_index(name, channel_names):
    try:
        return channel_names.index(name)
    except ValueError:
        return None


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

    fast = (
        powers["beta"][frontal].mean()
        + GAMMA_WEIGHT * powers["gamma"][frontal].mean()
    )
    slow = powers["alpha"][frontal].mean() + powers["theta"][frontal].mean()
    arousal = float(fast / (slow + eps))

    return valence, arousal, powers


class EmotionTracker:
    """Holds the baseline and the smoothed state across captures."""

    def __init__(self, channel_names=None):
        self.channel_names = channel_names or CHANNEL_NAMES
        self.baseline = None
        self.valence_ema = None
        self.arousal_ema = None
        self.state = "Stable"
        # Kept so a held window can repeat the last real spectrum instead of
        # blanking it — on real EEG a third of windows carry an artifact, and
        # a chart that disappears that often reads as broken.
        self.last_band_powers = {band: {} for band in BANDS}

    # -- baseline ---------------------------------------------------------

    def set_baseline(self, windows):
        """Calibrate from a list of resting windows."""
        valences, arousals = [], []
        for window in windows:
            w = np.asarray(window, dtype=float)
            if w.ndim != 2 or w.shape[-1] < MIN_SAMPLES:
                continue
            valence, arousal, _ = raw_valence_arousal(w, self.channel_names)
            if np.isfinite(valence) and np.isfinite(arousal):
                valences.append(valence)
                arousals.append(arousal)

        # Refuse to calibrate on nothing — a baseline built from unusable
        # windows would silently mis-reference every later reading.
        if not valences:
            self.baseline = None
            return None

        # A short baseline can produce an implausibly small spread, which would
        # make the z-scores explode and peg the display at its limits on
        # ordinary resting variation. Floor the std so normal drift stays in
        # the middle of the scale.
        # Median/MAD keeps one remaining bad-but-not-rejected window from
        # moving the reference point or inflating the spread for the whole
        # session. 1.4826 makes MAD comparable to standard deviation for a
        # normal distribution; the floors still protect very short baselines.
        valence_center = float(np.median(valences))
        arousal_center = float(np.median(arousals))
        valence_mad = float(np.median(np.abs(np.asarray(valences) - valence_center)))
        arousal_mad = float(np.median(np.abs(np.asarray(arousals) - arousal_center)))
        self.baseline = {
            "valence_mean": valence_center,
            "valence_std": max(1.4826 * valence_mad, MIN_VALENCE_STD),
            "arousal_mean": arousal_center,
            "arousal_std": max(1.4826 * arousal_mad, MIN_AROUSAL_STD),
        }
        return self.baseline

    @property
    def calibrated(self):
        return self.baseline is not None

    # -- per-window update ------------------------------------------------

    def update(self, window):
        # A real board returns an empty or barely-filled buffer in the moments
        # after start_stream(), and a flat channel (detached electrode) yields
        # zero power. Both would otherwise produce NaN, and because the EMA
        # feeds back on itself a single NaN would latch for the rest of the
        # session. Hold the previous reading instead.
        window = np.asarray(window, dtype=float)
        if window.ndim != 2 or window.shape[-1] < MIN_SAMPLES:
            return self.hold("Waiting for samples")

        valence, arousal, powers = raw_valence_arousal(window, self.channel_names)

        if not (np.isfinite(valence) and np.isfinite(arousal)):
            return self.hold("Signal not usable")

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

        self.last_band_powers = {
            band: {
                name: float(value)
                for name, value in zip(self.channel_names, channel_powers)
            }
            for band, channel_powers in powers.items()
        }

        return {
            "valence": round(self.valence_ema, 3),
            "arousal": round(self.arousal_ema, 3),
            "valence_raw": round(valence_s, 3),
            "arousal_raw": round(arousal_s, 3),
            "state": self.state,
            "level": STATES.index(self.state),
            "calibrated": self.calibrated,
            "stale": False,
            "stale_reason": None,
            "band_powers": {
                band: {
                    name: float(value)
                    for name, value in zip(self.channel_names, channel_powers)
                }
                for band, channel_powers in powers.items()
            },
        }

    def hold(self, reason):
        """Repeat the last good reading, flagged so the UI can say why.

        Public because callers also need it: the app holds a window it has
        rejected as an artifact before the estimate ever runs.
        """
        return {
            "valence": round(self.valence_ema, 3) if self.valence_ema is not None else 0.0,
            "arousal": round(self.arousal_ema, 3) if self.arousal_ema is not None else 0.0,
            "valence_raw": 0.0,
            "arousal_raw": 0.0,
            "state": self.state,
            "level": STATES.index(self.state),
            "calibrated": self.calibrated,
            "stale": True,
            "stale_reason": reason,
            "band_powers": self.last_band_powers,
        }

    def _next_state(self, arousal, valence):
        """Map arousal (with negative valence aggravating it) onto a level.

        Hysteresis: leaving the current state needs the threshold to be
        exceeded by HYSTERESIS, so a value sitting on a boundary holds.
        """
        # Negative valence pushes the same arousal into a higher level —
        # high arousal with positive valence is excitement, not distress.
        distress = arousal + max(0.0, -valence) * 0.5

        current = STATES.index(self.state)
        moderate = MODERATE_AROUSAL
        extreme = EXTREME_AROUSAL

        if current >= 1:
            moderate -= HYSTERESIS
        if current >= 2:
            extreme -= HYSTERESIS

        if distress >= extreme:
            return "Extreme"
        if distress >= moderate:
            return "Moderate"
        return "Stable"


def _ema(previous, value, alpha):
    if previous is None:
        return value
    return previous * (1 - alpha) + value * alpha
