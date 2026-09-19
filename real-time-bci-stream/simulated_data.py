import numpy as np

SAMPLE_RATE = 250


def generate_eeg_window(n_channels=8, n_samples=250, discomfort=False):
    """Return simulated EEG window shaped (n_channels, n_samples)."""
    t = np.arange(n_samples) / SAMPLE_RATE

    alpha_freq = 10.0
    beta_freq = 22.0

    alpha_amp = 8.0
    beta_amp = 6.0 if discomfort else 2.0

    window = np.zeros((n_channels, n_samples))
    for ch in range(n_channels):
        phase = np.random.uniform(0, 2 * np.pi)
        alpha = alpha_amp * np.sin(2 * np.pi * alpha_freq * t + phase)
        beta = beta_amp * np.sin(2 * np.pi * beta_freq * t + phase)
        noise = np.random.normal(0, 3.0, n_samples)
        window[ch] = alpha + beta + noise

    return window
