import numpy as np

from data_processing import should_hold_window
import emotion
from emotion import EmotionTracker


def test_flat_window_is_held_before_state_estimation():
    window = np.zeros((8, 250))

    hold, reason = should_hold_window(window)

    assert hold is True
    assert reason == "Signal quality poor"


def test_clean_window_is_scored():
    rng = np.random.default_rng(7)
    window = rng.normal(0, 8, (8, 250))

    hold, reason = should_hold_window(window)

    assert hold is False
    assert reason is None


def test_blink_window_is_held_before_state_estimation():
    window = np.zeros((8, 250))
    window[0, 80:100] = 300

    hold, reason = should_hold_window(window)

    assert hold is True
    assert reason == "Movement or blink detected"


def test_held_window_does_not_change_the_current_state():
    tracker = EmotionTracker()
    tracker.state = "Extreme"
    tracker.arousal_ema = 0.9
    tracker.valence_ema = -0.4
    window = np.zeros((8, 250))

    hold, reason = should_hold_window(window)
    result = tracker.hold(reason) if hold else tracker.update(window)

    assert result["state"] == "Extreme"
    assert result["stale"] is True


def test_baseline_uses_robust_center_against_one_outlier(monkeypatch):
    values = iter([(0.0, 1.0, {}), (0.0, 1.0, {}), (0.0, 1.0, {}), (0.0, 1.0, {}), (10.0, 10.0, {})])
    monkeypatch.setattr(emotion, "raw_valence_arousal", lambda *args: next(values))
    tracker = EmotionTracker()

    baseline = tracker.set_baseline([np.ones((8, 64)) for _ in range(5)])

    assert baseline["valence_mean"] == 0.0
    assert baseline["arousal_mean"] == 1.0
