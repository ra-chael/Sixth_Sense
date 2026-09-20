#this section is importing libraries and modules which are being used in the app.py script.
import os
import time
from collections import deque
from datetime import datetime

# this is importing additional libraries and modules which are being used in the app.py script.
import numpy as np
import pandas as pd
import streamlit as st

# this section is importing other libraries aswell as other functions from the different scripts.
import hero
from pain_visualizer import render_pain_visualizer
from doctor_summary import create_doctor_summary
from simulated_data import generate_eeg_window
from sixth_sense_backend import (
    get_current_reading,
    create_event,
    save_event,
    load_history,
    HISTORY_COLUMNS,
)
from emotion import CHANNEL_NAMES, EmotionTracker
from board_connection import (
    connect_cyton,
    disconnect_cyton,
    capture_window,
    DEFAULT_SERIAL_PORT,
)

#this section is creating a csv file to store the history of the data being collected and also creating a directory to store the recordings.
HISTORY_PATH = os.path.join(os.path.dirname(__file__), "history.csv")
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")

WINDOW_SAMPLES = 250
TREND_LENGTH = 90
BASELINE_WINDOWS = 20

st.set_page_config(page_title="Sixth Sense", layout="wide")

# --- session state -----------------------------------------------------------

# this section is creating a dictionary which contains all the default values for the state variables used in the app.
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
    "environment": None,
}

# this creates a session state if it doesnt exist in the dictionary.
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# this creates a session state in the history if it isnt already existing in the dictionary.
if "history" not in st.session_state:
    st.session_state.history = load_history().to_dict("records")
else:
    st.session_state.history = []

# this method is returning the latest n_samples of EEG data from an active board session. If simulation mode is enabled, it generates a simulated EEG window instead.
def read_window(simulation_mode, discomfort=False):
    if simulation_mode:
        return generate_eeg_window(
            elevated_state=discomfort
        )

    return capture_window(
        st.session_state.board,
        n_samples=WINDOW_SAMPLES
    )

# this function checks the signal quality of the EEG data being collected and returns a string indicating the quality of the signal.
def channel_labels(window):
    """10-20 names where we have them, plain indices beyond that."""
    n = np.asarray(window).shape[0]
    return [
        CHANNEL_NAMES[i] if i < len(CHANNEL_NAMES) else f"ch{i + 1}" for i in range(n)
    ]

# this function returns the elapsed time since the session started in minutes and seconds format. If the session has not started, it returns "--:--".
def elapsed_text():
    if not st.session_state.session_start:
        return "--:--"
    delta = int(time.time() - st.session_state.session_start)
    return f"{delta // 60:02d}:{delta % 60:02d}"


# --- header ------------------------------------------------------------------

# this is creating the headwr aswell as the caption which will be displayed in the streamlit app (the UI).
st.title("Sixth Sense")
st.caption(
    "This tool visializes the patients internal state. To assist the caregiver to better understand the patients needs."
    "This is an estimate and not a medical diagnosis and is therefore not a substitute for professional medical advice."
)

# this section is creating three tabs in the streamlit app, one for the dashboard, one for the saved events, and one for the care summary.
dashboard_tab, events_tab, doctor_tab = st.tabs([
    "Dashboard",
    "Saved events",
    "Care summary",
])

# this section is creating a side bar which shows the setup options for the app (including the data source, serial port, participant ID, calibration, mute and night mode options). It also allows the user to connect to the OpenBCI Cyton board and record a resting baseline.
with st.sidebar:
    st.subheader("Setup")

    mode = st.radio("Data source", ["Simulation mode", "OpenBCI Cyton"])
    simulation_mode = mode == "Simulation mode"

    if simulation_mode and st.session_state.board is not None:
        disconnect_cyton(st.session_state.board)
        st.session_state.board = None

    #this if statement checks if the simulation mode is not selected, then it shows the serial port input box and connect/disconnect buttons for the OpenBCI Cyton board. It also shows any error messages related to the board connection.
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

    #this section is creating a text input box in the sidebar
    participant_id = st.text_input("Participant ID", value="P01")

    #this section is creating a subheader and a caption in the sidebar for the environmental sensors.
    st.divider()
    st.subheader("Environment Sensors")

    sensor_mode = st.radio(
        "Environmental data source",
        [
            "Simulated sensors",
            "External sensors",
        ],
    )

    sensor_simulation = sensor_mode == "Simulated sensors"

    if sensor_simulation:
        st.caption(
            "Using simulated temperature, humidity, and noise readings "
            "for testing and demonstration."
        )
    else:
        st.caption(
            "External sensor support is not connected yet."
        )

    #this section is creating a subheader and a caption in the sidebar for the calibration of the app. It also allows the user to record a resting baseline for the participant.
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

    # this section is creating a subheader and a caption in the sidebar for the display settings of the app. It also allows the user to mute the sound and enable night mode in the app. It also allows the user to select the refresh rate of the app.
    st.divider()
    st.subheader("Display Settings")
    st.session_state.muted = st.toggle("Mute", value=st.session_state.muted)
    st.session_state.night = st.toggle("Night mode", value=st.session_state.night)

    refresh_rate = st.select_slider(
        "Refresh", options=[1.0, 2.0, 5.0], value=1.0, format_func=lambda s: f"{s:g}s"
    )

# --- session controls --------------------------------------------------------

# this whole section is creating the session controls in the dashboard.
with dashboard_tab:
    col_a, col_b, col_c = st.columns([1, 1, 3])

    #this section is creating the start and stop session buttons in the dashboard. It also shows the current status of the session (live or stopped) and allows the user to simulate discomfort in simulation mode.
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

    # this function is creating the live panel in the dashboard which shows the current state of the participant (valence, arousal, state, signal quality) and also shows the trend of the valence and arousal over time. It also shows the band power of the EEG signal and allows the user to view the raw window and features of the EEG signal.
    def live_panel():
        if st.session_state.session_active:
            window = read_window(
                simulation_mode, st.session_state.get("sim_discomfort", False)
            )

            # this part is getting the current reading of the participant by calling the get_current_reading function from the sixth_sense_backend.py script. It passes the current window of EEG data, the emotion tracker, participant ID, and sensor simulation flag as parameters. The result is then stored in the session state for later use.
            result = get_current_reading(
                window=window,
                tracker=st.session_state.tracker,
                participant_id=participant_id,
                sensor_simulation=sensor_simulation,
            )

            st.session_state.latest = result
            st.session_state.window = window

            st.session_state.environment = {
                "temperature": result["temperature"],
                "humidity": result["humidity"],
                "noise_level": result["noise_level"],
                "sensor_status": result["sensor_status"],
            }

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

            # this part is checking if the current state of the participant is different from the previous state and if it is, it adds an event to the events list in the session state. It also stores the current state as the previous state for the next iteration.
            if (
                st.session_state.prev_state is not None
                and result["state"] != st.session_state.prev_state
            ):
                event = create_event(
                    current_reading=result,
                    previous_state=st.session_state.prev_state,
                )

                st.session_state.events.insert(0, event)
            st.session_state.prev_state = result["state"]

        latest = st.session_state.latest
        if not latest:
            st.info("Start a session to begin reading.")
            return

        # this part is rendering the hero section of the dashboard visualizing the current state of the user as well as showing the elapsed time since the start.
        hero.render(
            state=latest["state"],
            valence=latest["valence"],
            arousal=latest["arousal"],
            quality=latest["signal_quality"],
            muted=st.session_state.muted,
            night=st.session_state.night,
            elapsed=elapsed_text(),
        )


        # this part is displaying the environmental data in the dashboard if it is available. It shows the temperature, humidity and noise level in the dashboard.
        environment = st.session_state.environment

        if environment:

            st.subheader("Environment")

            env1, env2, env3 = st.columns(3)

            with env1:
                temperature = environment.get("temperature")

                if temperature is not None:
                    st.metric(
                        "🌡️ Temperature",
                        f"{temperature:.1f} °C"
                    )
                else:
                    st.metric(
                        "🌡️ Temperature",
                        "Unavailable"
                    )

            with env2:
                humidity = environment.get("humidity")

                if humidity is not None:
                    st.metric(
                        "💧 Humidity",
                        f"{humidity:.1f} %"
                    )
                else:
                    st.metric(
                        "💧 Humidity",
                        "Unavailable"
                    )

            with env3:
                noise = environment.get("noise_level")

                if noise is not None:
                    st.metric(
                        "🔊 Noise",
                        f"{noise:.1f} dB"
                    )
                else:
                    st.metric(
                        "🔊 Noise",
                        "Unavailable"
                    )


        # this part is checking if the tracker is calibrated and if it is not, it shows a warning message to the user to record a resting baseline in the sidebar.

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

        # this loop is going through the latest data and displaying it in a json format in the dashboard. It excludes the band powers and timestamp from the display.
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

# --- care / doctor summary ---------------------------------------------------

with doctor_tab:

    st.subheader("Care Team Summary")

    st.caption(
        "Summary of caregiver-recorded observations and experimental "
        "EEG-derived state estimates. This information is intended to "
        "support communication with the care team and is not a diagnosis."
    )

    summary = create_doctor_summary(
        st.session_state.history
    )

    #this if else statement checks if there are any caregiver-reviewed events already saved in the history file
    if summary["total_events"] == 0:
        st.info(
            "No caregiver-reviewed events have been saved yet."
        )

    else:

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Recorded events",
            summary["total_events"],
        )

        col2.metric(
            "Pain/discomfort events",
            summary["pain_events"],
        )

        average_pain = summary["average_pain_level"]

        col3.metric(
            "Average discomfort level",
            (
                f"{average_pain}/10"
                if average_pain is not None
                else "No data"
            ),
        )

        # ----- detected states -----
        
        # this section is displaying the recorded state changes in the dashboard if it is available. It shows a bar chart of the number of events for each detected state. If no state changes are available, it shows a caption indicating that no state changes have been recorded.
        st.subheader("Recorded state changes")

        if summary["state_counts"]:
            state_df = pd.DataFrame(
                {
                    "State": summary["state_counts"].keys(),
                    "Events": summary["state_counts"].values(),
                }
            )

            st.bar_chart(
                state_df.set_index("State")
            )

        # ----- discomfort -----

        #this section is displaying the pain and discomfort observations in the dashboard if it is available. It shows the body areas where discomfort was reported and the number of reports for each area. If no pain locations are available, it shows a caption indicating that no pain locations have been recorded.
        st.subheader("Pain & discomfort observations")

        if summary["pain_locations"]:

            pain_df = pd.DataFrame(
                {
                    "Body area": summary["pain_locations"].keys(),
                    "Reports": summary["pain_locations"].values(),
                }
            )

            st.dataframe(
                pain_df,
                use_container_width=True,
                hide_index=True,
            )

        else:
            st.caption(
                "No pain locations have been recorded."
            )

        # ----- environment -----

        # this section is displaying the average environmental data (temperature, humidity, noise) in the dashboard if it is available. It shows the average temperature, average humidity and average noise level in the dashboard.
        st.subheader("Environmental context")

        env1, env2, env3 = st.columns(3)

        env1.metric(
            "Average temperature",
            (
                f"{summary['average_temperature']} °C"
                if summary["average_temperature"] is not None
                else "No data"
            ),
        )

        env2.metric(
            "Average humidity",
            (
                f"{summary['average_humidity']} %"
                if summary["average_humidity"] is not None
                else "No data"
            ),
        )

        env3.metric(
            "Average noise",
            (
                f"{summary['average_noise']} dB"
                if summary["average_noise"] is not None
                else "No data"
            ),
        )

        # ----- caregiver observations -----

        # this section is displaying the caregiver observations in the dashboard if it is available. It shows the notes entered by the caregiver in a bullet point format. If no notes are available, it shows a caption indicating that no caregiver observations have been recorded.
        st.subheader("Caregiver observations")

        if summary["notes"]:
            for note in summary["notes"]:
                st.write(f"• {note}")
        else:
            st.caption(
                "No caregiver observations have been recorded."
            )

        st.divider()

        st.warning(
            "EEG-derived states are experimental estimates. "
            "They should be interpreted together with caregiver "
            "observations and other clinical information and must "
            "not be used as a diagnosis."
        )

# --- saved events ------------------------------------------------------------

# this whole section is creating the saved events tab in the dashboard
with events_tab:
    st.subheader("Saved events")
    st.caption(
        "Any State changes are during the monotoring are appearing here. You can add notes and pain information to each event, wether its pain, discomfort or any other observations."
        "After entering it will save it to the history.csv file and will be visualized in the app."
    )

    if not st.session_state.events:
        st.write("No state shifts recorded yet.")

    # this loop is going through the events list and displays each event in a container with the timestamp, participant ID, state change, valence, arousal, signal quality, and a text area for the caregiver to enter notes.
    for i, event in enumerate(st.session_state.events):
        with st.container(border=True):
            head, badge = st.columns([3, 1])
            head.write(f"**{event['timestamp']}** · {event['participant_id']}")
            badge.write(f"{event['from_state']} → **{event['state']}**")

            st.caption(
                f"valence {event['valence']:+.2f} · arousal {event['arousal']:+.2f} "
                f"· signal {event['signal_quality']}"
            )

            #this part is displaying each environmental data in the dashboar when available.
            st.write("**Environment at time of event**")

            env1, env2, env3 = st.columns(3)

            env1.metric(
                "🌡️ Temperature",
                (
                    f"{event['temperature']:.1f} °C"
                    if event.get("temperature") is not None
                    else "Unavailable"
                ),
            )

            env2.metric(
                "💧 Humidity",
                (
                    f"{event['humidity']:.1f} %"
                    if event.get("humidity") is not None
                    else "Unavailable"
                ),
            )

            env3.metric(
                "🔊 Noise",
                (
                    f"{event['noise_level']:.1f} dB"
                    if event.get("noise_level") is not None
                    else "Unavailable"
                ),
            )

            note = st.text_area(
                "Caregiver note", value=event["note"], key=f"note_{i}", height=80,
                placeholder="Example: Patient became restless and touched their right shoulder repeatedly.",
            )

            pain_data = render_pain_visualizer(key_prefix=f"pain_event_{i}")

            #this button saves the note and pain information entered by the user into the history csv file and also being visualized in the app.
            if st.button("Save note", key=f"save_{i}"):
                event["note"] = note
                event["pain_present"] = pain_data["pain_present"]
                event["pain_location"] = pain_data["pain_location"]
                event["pain_level"] = pain_data["pain_level"]
                event["pain_type"] = pain_data["pain_type"]
                event["pain_note"] = pain_data["pain_note"]

                record = save_event(event)

                st.session_state.history.append(record)

                st.success("Saved to history.csv")

    # this section is displaying the history of the saved notes and pain information entered by the user in a table format in the app.
    st.divider()
    st.subheader("History")
    if st.session_state.history:
        hist_df = pd.DataFrame(st.session_state.history)
        display_cols = [c for c in HISTORY_COLUMNS if c in hist_df.columns]
        st.dataframe(hist_df[display_cols], use_container_width=True)
    else:
        st.write("No saved readings yet.")
