import numpy as np

SAMPLE_RATE = 250

# this gets the latest n_samples of EEG from an active board session. get_current_board_data returns every row the board produces — EEG plus accelerometer, aux, and timestamp channels, 24 rows on a Cyton. Only the EEG rows are returned here, so callers see an (n_eeg_channels, n_samples) window that matches the simulated one.
def generate_eeg_window(n_channels=8, n_samples=250, elevated_state=False):
    """Return simulated EEG window shaped (n_channels, n_samples)."""
    t = np.arange(n_samples) / SAMPLE_RATE

    alpha_freq = 10.0
    beta_freq = 22.0

    alpha_amp = 8.0
    beta_amp = 6.0 if elevated_state else 2.0

    # Channels 0 and 1 stand in for Fp1/Fp2. Suppressing right-frontal alpha
    # during elevated_state gives the asymmetry the valence estimate reads, so the
    # simulated signal exercises both axes and not just arousal.
    asymmetry = {1: 0.45} if elevated_state else {}

    window = np.zeros((n_channels, n_samples))
    for ch in range(n_channels):
        phase = np.random.uniform(0, 2 * np.pi)
        alpha = alpha_amp * asymmetry.get(ch, 1.0) * np.sin(
            2 * np.pi * alpha_freq * t + phase
        )
        beta = beta_amp * np.sin(2 * np.pi * beta_freq * t + phase)
        noise = np.random.normal(0, 3.0, n_samples)
        window[ch] = alpha + beta + noise

    return window
