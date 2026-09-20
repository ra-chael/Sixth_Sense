# this script is doing the backend logic for the Sixth Sense application. It contains functions that are independent of Streamlit so they can be reused by the current Streamlit prototype and by a future web API. The functions include getting the current reading from the EEG window, creating an event when the detected state changes, saving an event to history.csv, and loading previously saved events.

"""
Shared backend logic for Sixth Sense.

This module contains functions that are independent of Streamlit so they
can be reused by the current Streamlit prototype and by a future web API.
"""

import os
from datetime import datetime

import pandas as pd

from data_processing import check_signal_quality
from sensors import get_environment_data

import time
import numpy as np

from emotion import EmotionTracker
from simulated_data import generate_eeg_window
from board_connection import (
    connect_cyton,
    disconnect_cyton,
    capture_window,
)
from doctor_summary import create_doctor_summary

tracker = EmotionTracker()

board = None
simulation_mode = True
simulate_discomfort = False
sensor_simulation = True

participant_id = "P01"

previous_state = None
latest_reading = None

WINDOW_SAMPLES = 250


# this section is creating a path to the histroiry.csv file and is defining the wanted columns for it.
HISTORY_PATH = os.path.join(os.path.dirname(__file__), "history.csv")

HISTORY_COLUMNS = [
    "timestamp",
    "participant_id",
    "from_state",
    "state",
    "valence",
    "arousal",
    "signal_quality",
    "pain_present",
    "pain_location",
    "pain_level",
    "pain_type",
    "pain_note",
    "temperature",
    "humidity",
    "noise_level",
    "note",
]

# this method is checking the 
def get_current_reading(
    window,
    tracker,
    participant_id="P01",
    sensor_simulation=True,
):
    """
    Process one EEG window and return the complete current reading.

    The function does not depend on Streamlit, which allows it to be used
    later by a Flask/FastAPI backend for the HTML/JavaScript website.
    """

    result = tracker.update(window)

    environment = get_environment_data(
        simulation=sensor_simulation
    )

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "participant_id": participant_id,

        "state": result["state"],
        "valence": result["valence"],
        "arousal": result["arousal"],
        "signal_quality": check_signal_quality(window),
        "calibrated": result["calibrated"],

        "band_powers": result["band_powers"],

        "temperature": environment.get("temperature"),
        "humidity": environment.get("humidity"),
        "noise_level": environment.get("noise_level"),
        "sensor_status": environment.get("sensor_status"),
    }


def create_event(current_reading, previous_state):
    """
    Create a caregiver event when the detected state changes.
    """

    return {
        "timestamp": current_reading["timestamp"],
        "participant_id": current_reading["participant_id"],

        "from_state": previous_state,
        "state": current_reading["state"],

        "valence": current_reading["valence"],
        "arousal": current_reading["arousal"],
        "signal_quality": current_reading["signal_quality"],

        "pain_present": "",
        "pain_location": "",
        "pain_level": 0,
        "pain_type": "",
        "pain_note": "",

        "temperature": current_reading["temperature"],
        "humidity": current_reading["humidity"],
        "noise_level": current_reading["noise_level"],

        "note": "",
    }


def save_event(event):
    """
    Save a caregiver-reviewed event to history.csv.
    """

    record = {
        column: event.get(column, "")
        for column in HISTORY_COLUMNS
    }

    if os.path.exists(HISTORY_PATH):
        history = pd.read_csv(HISTORY_PATH)
    else:
        history = pd.DataFrame(columns=HISTORY_COLUMNS)

    history = pd.concat(
        [history, pd.DataFrame([record])],
        ignore_index=True,
    )

    history.to_csv(HISTORY_PATH, index=False)

    return record


def load_history():
    """
    Load previously saved caregiver-reviewed events.
    """

    if not os.path.exists(HISTORY_PATH):
        return pd.DataFrame(columns=HISTORY_COLUMNS)

    return pd.read_csv(HISTORY_PATH)

def get_history():
    history = load_history()

    if history.empty:
        return []

    history = history.fillna("")

    return history.to_dict("records")

def get_doctor_summary():
    history = load_history()
    return create_doctor_summary(history)