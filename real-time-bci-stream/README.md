# Running the App

Comfort/discomfort visualizer built on simulated EEG data.

## 1. Install dependencies

From repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install streamlit pandas numpy scipy brainflow
```

Already have a venv? Just activate it and run the pip install line above.

## 2. Run the app

From repo root:

```bash
python -m streamlit run real-time-bci-stream/app.py
```

Browser opens automatically at `http://localhost:8501`.

## 3. Use it

1. Click **Start session**.
2. Click **Generate sample** — creates a simulated EEG window and scores it.
3. Adjust the comfort slider, click **Save result** to log it to `history.csv`.
4. Click **Stop session** when done.

## Files

- `simulated_data.py` — generates fake 8-channel EEG windows
- `data_processing.py` — extracts band-power features, computes discomfort score
- `app.py` — Streamlit UI

Real OpenBCI Cyton setup: see [`cyton_setup_instructions.md`](./cyton_setup_instructions.md).
