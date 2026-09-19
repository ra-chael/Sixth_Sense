import os
from datetime import datetime

import pandas as pd
import streamlit as st

from simulated_data import generate_eeg_window
from data_processing import process_window

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "history.csv")

STATE_COLOR = {
    "Comfortable": "green",
    "Uncertain": "orange",
    "Possible discomfort": "red",
}
STATE_EMOJI = {
    "Comfortable": "🟢",
    "Uncertain": "🟡",
    "Possible discomfort": "🔴",
}

HISTORY_COLUMNS = [
    "timestamp",
    "discomfort_score",
    "comfort_rating",
    "signal_quality",
    "state",
]

st.set_page_config(page_title="Comfort/Discomfort Visualizer", layout="centered")
st.title("EEG Comfort/Discomfort Visualizer")
st.caption(
    "Demonstration prototype. Displays a possible comfort/discomfort "
    "state estimate — this is not a medical pain detector."
)

if "history" not in st.session_state:
    if os.path.exists(HISTORY_PATH):
        st.session_state.history = pd.read_csv(HISTORY_PATH).to_dict("records")
    else:
        st.session_state.history = []

if "latest" not in st.session_state:
    st.session_state.latest = None

if "session_active" not in st.session_state:
    st.session_state.session_active = False

col1, col2 = st.columns(2)
with col1:
    simulation_mode = st.checkbox("Simulation mode", value=True)
with col2:
    if st.session_state.session_active:
        if st.button("Stop session"):
            st.session_state.session_active = False
    else:
        if st.button("Start session", type="primary"):
            st.session_state.session_active = True

data_source = "Simulated EEG" if simulation_mode else "OpenBCI Cyton"
st.caption(f"**Data source:** {data_source}")

if st.session_state.session_active:
    st.success("Session active")
else:
    st.info("Session stopped — click 'Start session' to begin.")

generate_clicked = st.button(
    "Generate sample", type="secondary", disabled=not st.session_state.session_active
)

if generate_clicked:
    window = generate_eeg_window(discomfort=False)
    result = process_window(window)
    result["timestamp"] = datetime.now().isoformat(timespec="seconds")
    st.session_state.latest = result
    st.session_state.window = window

if st.session_state.latest:
    result = st.session_state.latest
    state = result["state"]
    color = STATE_COLOR[state]
    emoji = STATE_EMOJI[state]

    st.markdown(f"### {emoji} Current state: :{color}[{state}]")
    st.metric("Discomfort score", f"{result['discomfort_score']} / 100")
    st.write(f"**Signal quality:** {result['signal_quality']}")
    st.caption("This visualization represents a possible state change and is not a medical pain detector.")

    if "window" in st.session_state:
        chart_df = pd.DataFrame(st.session_state.window.T, columns=[f"ch{i+1}" for i in range(8)])
        st.line_chart(chart_df)

    with st.expander("Features"):
        st.json(
            {
                k: v
                for k, v in result.items()
                if k not in ("timestamp", "state", "signal_quality", "discomfort_score")
            }
        )

    comfort_rating = st.slider("Self-reported comfort (0 = worst, 10 = best)", 0, 10, 5)

    if st.button("Save result"):
        record = {**result, "comfort_rating": comfort_rating}
        st.session_state.history.append(record)
        pd.DataFrame(st.session_state.history).to_csv(HISTORY_PATH, index=False)
        st.success("Saved to history.csv")
else:
    st.info("Click 'Generate sample' to produce an EEG window.")

st.divider()
st.subheader("History")
if st.session_state.history:
    hist_df = pd.DataFrame(st.session_state.history)
    st.line_chart(hist_df.set_index("timestamp")["discomfort_score"])
    display_cols = [c for c in HISTORY_COLUMNS if c in hist_df.columns]
    st.dataframe(hist_df[display_cols], use_container_width=True)
else:
    st.write("No saved readings yet.")
