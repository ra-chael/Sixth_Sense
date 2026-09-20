import os
import time
from collections import deque
from datetime import datetime

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import hero
import narrate
import theme
import trend as trend_chart
from simulated_data import generate_eeg_window
from data_processing import check_signal_quality, detect_artifact
import emotion as emotion_module
from emotion import CHANNEL_NAMES, EmotionTracker
from board_connection import (
    connect_cyton,
    disconnect_cyton,
    capture_window,
    capture_motion,
    DEFAULT_SERIAL_PORT,
)

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "history.csv")
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")

WINDOW_SAMPLES = 250
TREND_LENGTH = 90
BASELINE_WINDOWS = 20

# Accelerometer magnitude, in g, above which the head counts as moving.
# Provisional — it has not been calibrated against a worn headset yet.
MOTION_THRESHOLD = 0.02

HISTORY_COLUMNS = [
    "timestamp",
    "participant_id",
    "state",
    "valence",
    "arousal",
    "signal_quality",
    "summary",
    "note",
]

st.set_page_config(
    page_title="Comfort/Discomfort Visualizer", page_icon="🧠", layout="wide"
)
theme.apply()

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
    "run_baseline": False,
    "sim_manual": False,
    "sim_arousal": 0.0,
    "sim_valence": 0.0,
    "sim_artifact": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

if "history" not in st.session_state:
    if os.path.exists(HISTORY_PATH):
        st.session_state.history = pd.read_csv(HISTORY_PATH).to_dict("records")
    else:
        st.session_state.history = []


def read_window(simulation_mode, discomfort=False, manual=False):
    """One window from whichever source is selected.

    manual=False during calibration, so a baseline is always recorded against
    a neutral signal rather than whatever the sliders happen to be set to.
    """
    if not simulation_mode:
        return capture_window(st.session_state.board, n_samples=WINDOW_SAMPLES)

    if manual and st.session_state.get("sim_manual"):
        return generate_eeg_window(
            arousal=st.session_state.get("sim_arousal", 0.0),
            valence=st.session_state.get("sim_valence", 0.0),
            artifact=st.session_state.get("sim_artifact"),
        )

    return generate_eeg_window(discomfort=discomfort)


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
            # Shown rather than assumed: if this is not what the headset is
            # actually doing, every band reading is wrong.
            st.caption(
                f"Sample rate: {emotion_module.SAMPLE_RATE} Hz · "
                f"window: {WINDOW_SAMPLES} samples "
                f"({WINDOW_SAMPLES / emotion_module.SAMPLE_RATE:.1f}s)"
            )
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

    # Either the sidebar button or the inline "Fix" button on the dashboard
    # starts the same routine.
    start_baseline = st.button(
        "Record resting baseline", disabled=not hardware_ready
    ) or st.session_state.pop("run_baseline", False)

    if start_baseline:
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

    st.divider()
    st.subheader("Event summaries")

    # Checked once per rerun rather than per event, and the app works
    # unchanged when it is unavailable.
    llm_ready = narrate.available()

    if llm_ready:
        st.success(f"Local model ready ({narrate.DEFAULT_MODEL})")
        st.caption(
            "Each state change is phrased for the log. The model only "
            "rewords measurements this pipeline computed — it never sees EEG "
            "and never decides the state. Runs locally; nothing leaves this "
            "machine."
        )
    else:
        st.caption(
            f"No local model — summaries are skipped. To enable: "
            f"`ollama pull {narrate.DEFAULT_MODEL}`"
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
            st.session_state.sim_manual = st.toggle(
                "Drive the signal manually",
                value=st.session_state.get("sim_manual", False),
                help="Set valence and arousal directly instead of using the "
                "two-state discomfort preset.",
            )
            if not st.session_state.sim_manual:
                st.session_state.sim_discomfort = st.toggle(
                    "Simulate discomfort",
                    value=st.session_state.get("sim_discomfort", False),
                    help="Feeds the discomfort variant of the simulated signal.",
                )

    # Manual drive lives outside the columns so the sliders get full width.
    if (
        simulation_mode
        and st.session_state.session_active
        and st.session_state.get("sim_manual")
    ):
        with st.container(border=True):
            st.caption(
                "Synthesising a window with these targets. The reading below is "
                "the estimator's own measurement of that signal, so it lags "
                "while the moving average catches up."
            )
            sim_a, sim_v, sim_art = st.columns([2, 2, 1])
            st.session_state.sim_arousal = sim_a.slider(
                "Arousal", -1.0, 1.0, st.session_state.get("sim_arousal", 0.0), 0.05
            )
            st.session_state.sim_valence = sim_v.slider(
                "Valence", -1.0, 1.0, st.session_state.get("sim_valence", 0.0), 0.05
            )
            st.session_state.sim_artifact = sim_art.selectbox(
                "Inject artifact",
                [None, "blink", "clench"],
                format_func=lambda x: "none" if x is None else x,
                help="Exercises the artifact guard — these windows should be "
                "held rather than scored.",
            )

    # -- the live panel -------------------------------------------------------
    # Wrapped in a fragment so only this part reruns on each tick; the sidebar
    # and the events tab are left alone.

    @st.fragment(run_every=refresh_rate if st.session_state.session_active else None)
    def live_panel():
        if st.session_state.session_active:
            window = read_window(
                simulation_mode,
                st.session_state.get("sim_discomfort", False),
                manual=True,
            )
            # A blink or jaw clench puts a large transient in the same fast
            # bands as real arousal, so such a window is held rather than
            # scored — otherwise a facial twitch reads as distress.
            artifact, artifact_fraction = detect_artifact(window)
            if artifact:
                result = st.session_state.tracker.hold("Movement or blink detected")
            else:
                result = st.session_state.tracker.update(window)

            result["signal_quality"] = check_signal_quality(window)
            result["artifact_fraction"] = artifact_fraction
            result["timestamp"] = datetime.now().isoformat(timespec="seconds")

            # Head movement, for context only. It is never allowed to change
            # the estimate — it exists so a caregiver can tell a reading that
            # rose while the patient was still from one that rose while they
            # were moving.
            result["motion"] = (
                capture_motion(st.session_state.board)
                if not simulation_mode and st.session_state.board is not None
                else None
            )
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
                motion_value = result.get("motion")
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
                        "motion": motion_value,
                        "moving": (
                            motion_value is not None
                            and motion_value > MOTION_THRESHOLD
                        ),
                        # Filled in on the Saved events tab, not here: the
                        # model takes a second or two and this loop runs once
                        # per second.
                        "summary": None,
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
            calibrated=latest["calibrated"],
            stale=latest.get("stale", False),
        )

        if latest.get("stale"):
            st.info(
                f"{latest.get('stale_reason', 'Holding last reading')} — showing "
                "the previous reading until the signal recovers."
            )

        # Head movement sits beside the reading rather than inside it: an
        # arousal rise while the patient was still means something different
        # from one while they were moving, and only a person can judge which.
        motion = latest.get("motion")
        if motion is not None:
            moving = motion > MOTION_THRESHOLD
            st.caption(
                f"{'🔸' if moving else '🔹'} Head movement: "
                f"{'detected' if moving else 'still'} ({motion:.3f} g) — context "
                "only, this does not affect the estimate."
            )

        if not latest["calibrated"]:
            # Without a baseline the state barely moves, which reads as a broken
            # app rather than a missing step — so the fix is offered right here
            # instead of pointing at the sidebar.
            warn, act = st.columns([4, 1])
            warn.warning(
                "No baseline recorded — readings are not referenced to this "
                "participant, so the state will barely move."
            )
            if act.button("Fix: record baseline", use_container_width=True):
                st.session_state.run_baseline = True
                st.rerun()

        left, right = st.columns([3, 2])

        with left:
            st.subheader("Signal trend")
            chart = trend_chart.render(
                st.session_state.trend, latest["state"], st.session_state.night
            )
            if chart is not None:
                st.altair_chart(chart, use_container_width=True)
                st.caption(
                    "Solid line: arousal, coloured by current state. Dashed: "
                    "valence. Dotted rule: the Moderate threshold."
                )
            else:
                st.caption("Collecting…")

        with right:
            st.subheader("Band power")
            alpha = latest["band_powers"]["alpha"]
            beta = latest["band_powers"]["beta"]
            # A held reading carries no band powers; skip the chart rather than
            # leaving the fragment, which would drop the panels below.
            if not alpha:
                st.caption("Waiting for a usable window…")
            else:
                # Explicit sort: the default would order the electrodes A-Z
                # rather than by montage position.
                band_df = pd.DataFrame(
                    [
                        {"channel": ch, "band": band, "power": powers[ch]}
                        for band, powers in (("alpha", alpha), ("beta", beta))
                        for ch in alpha
                    ]
                )
                st.altair_chart(
                    alt.Chart(band_df)
                    .mark_bar()
                    .encode(
                        x=alt.X("channel:N", sort=list(alpha.keys()), title=None),
                        y=alt.Y("power:Q", title=None),
                        color=alt.Color(
                            "band:N",
                            title=None,
                            scale=alt.Scale(
                                domain=["alpha", "beta"],
                                range=["#7FAFCF", "#BF9BD6"],
                            ),
                            legend=alt.Legend(orient="top"),
                        ),
                        xOffset="band:N",
                    )
                    .properties(height=240)
                    .configure_view(strokeWidth=0)
                    .configure(background="transparent"),
                    use_container_width=True,
                )
                st.caption(
                    "Alpha (8–13 Hz) and beta (13–30 Hz) per electrode. The "
                    "estimate reads the Fp1/Fp2 pair; the rest are context."
                )

        with st.expander("Raw EEG and how this reading was derived"):
            st.caption(
                "The last one-second window, one row per electrode in 10-20 "
                "order. Fp1 and Fp2 are highlighted because the estimate is "
                "derived from them; the other channels are recorded but do not "
                "feed the current model."
            )
            window_arr = np.asarray(st.session_state.window)
            st.altair_chart(
                trend_chart.render_raw(
                    window_arr, channel_labels(window_arr), st.session_state.night
                ),
                use_container_width=True,
            )

            st.markdown("**How the numbers were derived**")
            derive = st.columns(4)
            derive[0].metric(
                "Valence",
                f"{latest['valence']:+.2f}",
                help="ln(alpha at Fp2) − ln(alpha at Fp1), then baseline-referenced "
                "and smoothed. Negative means relatively more right-frontal alpha, "
                "associated with withdrawal.",
            )
            derive[1].metric(
                "Arousal",
                f"{latest['arousal']:+.2f}",
                help="Frontal beta / (alpha + theta), baseline-referenced and "
                "smoothed. Higher means more activated.",
            )
            derive[2].metric(
                "Before smoothing",
                f"{latest['arousal_raw']:+.2f}",
                delta=f"{latest['arousal'] - latest['arousal_raw']:+.2f} from EMA",
                help="This window's arousal before the moving average. The gap "
                "shows how much smoothing is absorbing.",
            )
            derive[3].metric(
                "Signal quality",
                latest["signal_quality"],
                help="Amplitude and variance heuristic. 'Poor' forces the state "
                "to Uncertain rather than reporting a confident reading.",
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
                + (" · head moved" if event.get("moving") else "")
            )

            # Narration is generated here rather than in the capture loop, and
            # only once per event: the model takes a second or two, and the
            # loop runs once per second.
            if llm_ready and event.get("summary") is None:
                with st.spinner("Writing summary…"):
                    event["summary"] = narrate.narrate(event) or ""

            if event.get("summary"):
                st.info(event["summary"])

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
