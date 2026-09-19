import os
import time
from collections import deque
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

import hero
from simulated_data import generate_eeg_window
from data_processing import check_signal_quality
from emotion import CHANNEL_NAMES, EmotionTracker
from board_connection import (
    connect_cyton,
    disconnect_cyton,
    capture_window,
    DEFAULT_SERIAL_PORT,
)

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "history.csv")
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")

WINDOW_SAMPLES = 250
TREND_LENGTH = 90
BASELINE_WINDOWS = 20

HISTORY_COLUMNS = [
    "timestamp",
    "participant_id",
    "state",
    "valence",
    "arousal",
    "signal_quality",
    "note",
]

st.set_page_config(page_title="Comfort/Discomfort Visualizer", layout="wide")

# --- session state -----------------------------------------------------------

defaults = {
    "latest": None,
    "session_active": False,
    "board": None,
    "board_error": None,
    "tracker": EmotionTracker(),
    "trend": deque(maxlen=TREND_LENGTH),
    "events": [],
    "prev_state": None,
    "session_start": None,
    "muted": False,
    "night": False,
    "window": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

if "history" not in st.session_state:
    if os.path.exists(HISTORY_PATH):
        st.session_state.history = pd.read_csv(HISTORY_PATH).to_dict("records")
    else:
        st.session_state.history = []


def read_window(simulation_mode, discomfort=False):
    if simulation_mode:
        return generate_eeg_window(discomfort=discomfort)
    return capture_window(st.session_state.board, n_samples=WINDOW_SAMPLES)


def channel_labels(window):
    """10-20 names where we have them, plain indices beyond that."""
    n = np.asarray(window).shape[0]
    return [
        CHANNEL_NAMES[i] if i < len(CHANNEL_NAMES) else f"ch{i + 1}" for i in range(n)
    ]


def elapsed_text():
    if not st.session_state.session_start:
        return "--:--"
    delta = int(time.time() - st.session_state.session_start)
    return f"{delta // 60:02d}:{delta % 60:02d}"


# --- header ------------------------------------------------------------------

st.title("EEG Comfort/Discomfort Visualizer")
st.caption(
    "Demonstration prototype. Displays a possible comfort/discomfort "
    "state estimate — this is not a medical pain detector."
)

dashboard_tab, events_tab = st.tabs(["Dashboard", "Saved events"])

with st.sidebar:
    st.subheader("Setup")

    mode = st.radio("Data source", ["Simulation mode", "OpenBCI Cyton"])
    simulation_mode = mode == "Simulation mode"

    if simulation_mode and st.session_state.board is not None:
        disconnect_cyton(st.session_state.board)
        st.session_state.board = None

    if not simulation_mode:
        serial_port = st.text_input("Serial port", value=DEFAULT_SERIAL_PORT)

        if st.session_state.board is None:
            st.warning(
                "Not connected. Close the OpenBCI GUI first — the serial port "
                "can only be held by one process at a time."
            )
            if st.button("Connect to OpenBCI"):
                board, error = connect_cyton(
                    serial_port, existing_board=st.session_state.board
                )
                st.session_state.board = board
                st.session_state.board_error = error
                st.rerun()
        else:
            st.success("Connected to Cyton")
            if st.button("Disconnect"):
                disconnect_cyton(st.session_state.board)
                st.session_state.board = None
                st.rerun()

        if st.session_state.board_error:
            st.error(st.session_state.board_error)
            if "ANOTHER_BOARD_IS_CREATED" in st.session_state.board_error:
                st.caption(
                    "A BrainFlow session is still held somewhere. Make sure the "
                    "OpenBCI GUI is fully closed, then Connect again."
                )
            elif "BOARD_NOT_READY" in st.session_state.board_error:
                st.caption(
                    "The dongle opened but the board did not answer. Check the "
                    "Cyton power switch is on and the dongle switch is on GPIO 6."
                )

    participant_id = st.text_input("Participant ID", value="P01")

    st.divider()
    st.subheader("Calibration")
    tracker = st.session_state.tracker

    if tracker.calibrated:
        st.success("Baseline set")
    else:
        st.info("Not calibrated — values are unreferenced until you set a baseline.")

    hardware_ready = simulation_mode or st.session_state.board is not None

    st.caption(
        f"Participant sits still, eyes open, for ~{BASELINE_WINDOWS} seconds."
    )

    if st.button("Record resting baseline", disabled=not hardware_ready):
        progress = st.progress(0.0, text="Recording resting baseline…")
        windows = []
        for i in range(BASELINE_WINDOWS):
            windows.append(read_window(simulation_mode))
            progress.progress(
                (i + 1) / BASELINE_WINDOWS,
                text=f"Resting baseline… {i + 1}/{BASELINE_WINDOWS}",
            )
            time.sleep(1.0)
        tracker.set_baseline(windows)
        progress.empty()
        st.rerun()

    st.divider()
    st.session_state.muted = st.toggle("Mute", value=st.session_state.muted)
    st.session_state.night = st.toggle("Night mode", value=st.session_state.night)

    refresh_rate = st.select_slider(
        "Refresh", options=[1.0, 2.0, 5.0], value=1.0, format_func=lambda s: f"{s:g}s"
    )

# --- session controls --------------------------------------------------------

with dashboard_tab:
    col_a, col_b, col_c = st.columns([1, 1, 3])

    with col_a:
        if st.session_state.session_active:
            if st.button("Stop session", use_container_width=True):
                st.session_state.session_active = False
                st.rerun()
        else:
            if st.button(
                "Start session",
                type="primary",
                use_container_width=True,
                disabled=not hardware_ready,
            ):
                st.session_state.session_active = True
                st.session_state.session_start = time.time()
                st.session_state.trend.clear()
                st.session_state.prev_state = None
                st.rerun()

    with col_b:
        if st.session_state.session_active:
            st.success("Live")
        else:
            st.info("Stopped")

    with col_c:
        if simulation_mode and st.session_state.session_active:
            st.session_state.sim_discomfort = st.toggle(
                "Simulate discomfort",
                value=st.session_state.get("sim_discomfort", False),
                help="Feeds the discomfort variant of the simulated signal.",
            )

    # -- the live panel -------------------------------------------------------
    # Wrapped in a fragment so only this part reruns on each tick; the sidebar
    # and the events tab are left alone.

    @st.fragment(run_every=refresh_rate if st.session_state.session_active else None)
    def live_panel():
        if st.session_state.session_active:
            window = read_window(
                simulation_mode, st.session_state.get("sim_discomfort", False)
            )
            result = st.session_state.tracker.update(window)
            result["signal_quality"] = check_signal_quality(window)
            result["timestamp"] = datetime.now().isoformat(timespec="seconds")
            st.session_state.latest = result
            st.session_state.window = window

            st.session_state.trend.append(
                {
                    "t": datetime.now(),
                    "valence": result["valence"],
                    "arousal": result["arousal"],
                    "state": result["state"],
                }
            )

            # A shift is logged once, on the transition itself.
            if (
                st.session_state.prev_state is not None
                and result["state"] != st.session_state.prev_state
            ):
                st.session_state.events.insert(
                    0,
                    {
                        "timestamp": result["timestamp"],
                        "participant_id": participant_id,
                        "state": result["state"],
                        "from_state": st.session_state.prev_state,
                        "valence": result["valence"],
                        "arousal": result["arousal"],
                        "signal_quality": result["signal_quality"],
                        "note": "",
                    },
                )
            st.session_state.prev_state = result["state"]

        latest = st.session_state.latest
        if not latest:
            st.info("Start a session to begin reading.")
            return

        hero.render(
            state=latest["state"],
            valence=latest["valence"],
            arousal=latest["arousal"],
            quality=latest["signal_quality"],
            muted=st.session_state.muted,
            night=st.session_state.night,
            elapsed=elapsed_text(),
        )

        if not latest["calibrated"]:
            st.warning(
                "No baseline recorded — valence and arousal are not referenced to "
                "this participant. Record a resting baseline in the sidebar."
            )

        left, right = st.columns([3, 2])

        with left:
            st.subheader("Signal trend")
            if len(st.session_state.trend) > 1:
                trend_df = pd.DataFrame(list(st.session_state.trend)).set_index("t")
                st.line_chart(trend_df[["valence", "arousal"]], height=240)
            else:
                st.caption("Collecting…")

        with right:
            st.subheader("Band power")
            alpha = latest["band_powers"]["alpha"]
            beta = latest["band_powers"]["beta"]
            band_df = pd.DataFrame(
                {"alpha": alpha, "beta": beta},
                index=list(alpha.keys()),
            )
            st.bar_chart(band_df, height=240)

        with st.expander("Raw window and features"):
            window_arr = np.asarray(st.session_state.window)
            chart_df = pd.DataFrame(window_arr.T, columns=channel_labels(window_arr))
            st.line_chart(chart_df, height=200)
            st.json(
                {
                    k: v
                    for k, v in latest.items()
                    if k not in ("band_powers", "timestamp")
                }
            )

    live_panel()

# --- saved events ------------------------------------------------------------

with events_tab:
    st.subheader("Saved events")
    st.caption(
        "Every state shift during a session is logged here. Add a caregiver note "
        "and save it to history.csv."
    )

    if not st.session_state.events:
        st.write("No state shifts recorded yet.")

    for i, event in enumerate(st.session_state.events):
        with st.container(border=True):
            head, badge = st.columns([3, 1])
            head.write(f"**{event['timestamp']}** · {event['participant_id']}")
            badge.write(f"{event['from_state']} → **{event['state']}**")

            st.caption(
                f"valence {event['valence']:+.2f} · arousal {event['arousal']:+.2f} "
                f"· signal {event['signal_quality']}"
            )

            note = st.text_area(
                "Caregiver note", value=event["note"], key=f"note_{i}", height=80
            )

            if st.button("Save note", key=f"save_{i}"):
                event["note"] = note
                record = {c: event.get(c, "") for c in HISTORY_COLUMNS}
                st.session_state.history.append(record)
                pd.DataFrame(st.session_state.history).to_csv(
                    HISTORY_PATH, index=False
                )
                st.success("Saved to history.csv")

    st.divider()
    st.subheader("History")
    if st.session_state.history:
        hist_df = pd.DataFrame(st.session_state.history)
        display_cols = [c for c in HISTORY_COLUMNS if c in hist_df.columns]
        st.dataframe(hist_df[display_cols], use_container_width=True)
    else:
        st.write("No saved readings yet.")
