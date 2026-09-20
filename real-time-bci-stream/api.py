"""
API bridge between the Sixth Sense Python backend and the HTML/JavaScript
website.

Run with:

    python -m uvicorn api:app --reload

Then open:

    http://127.0.0.1:8000
"""

from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import sixth_sense_backend as backend

from emotion import EmotionTracker
from simulated_data import generate_eeg_window
from board_connection import (
    connect_cyton,
    disconnect_cyton,
    capture_window,
)
from doctor_summary import create_doctor_summary


# ---------------------------------------------------------------------------
# Runtime state
# ---------------------------------------------------------------------------

tracker = EmotionTracker()

board = None

# Start in simulation mode so the website works without the Cyton connected.
simulation_mode = True
simulate_discomfort = False
sensor_simulation = True

participant_id = "P01"

previous_state = None
latest_reading = None

WINDOW_SAMPLES = 250


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = BASE_DIR / "website"


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Sixth Sense API",
    description="Backend API for the Sixth Sense caregiver interface.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class EventInput(BaseModel):
    participant_id: str = "P01"
    pain_present: str = "No"

    pain_location: list[str] = Field(default_factory=list)

    pain_level: int = Field(
        default=0,
        ge=0,
        le=10,
    )

    pain_type: list[str] = Field(default_factory=list)

    pain_note: str = ""
    note: str = ""


class ConnectInput(BaseModel):
    serial_port: str


class SimulationInput(BaseModel):
    enabled: bool


# ---------------------------------------------------------------------------
# API status
# ---------------------------------------------------------------------------

@app.get("/api/status")
def api_status():
    """
    Check whether the Python API is running.
    """

    return {
        "status": "ok",
        "message": "Sixth Sense API is running",
        "simulation_mode": simulation_mode,
        "cyton_connected": board is not None,
        "participant_id": participant_id,
    }


# ---------------------------------------------------------------------------
# Current EEG / physiological reading
# ---------------------------------------------------------------------------

@app.get("/api/current")
def current_reading():
    global latest_reading
    global previous_state

    try:

        # ---------------------------------------------------------------
        # 1. Obtain EEG data
        # ---------------------------------------------------------------

        if simulation_mode:

            window = generate_eeg_window(
                n_samples=WINDOW_SAMPLES,
                elevated_state=simulate_discomfort,
            )

        else:

            if board is None:
                raise HTTPException(
                    status_code=503,
                    detail="Cyton is not connected.",
                )

            window = capture_window(
                board,
                n_samples=WINDOW_SAMPLES,
            )

        # ---------------------------------------------------------------
        # 2. Validate EEG
        # ---------------------------------------------------------------

        if window is None:
            raise HTTPException(
                status_code=503,
                detail="No EEG samples available yet.",
            )

        eeg = np.asarray(window, dtype=float)

        if eeg.size == 0:
            raise HTTPException(
                status_code=503,
                detail="No EEG samples available yet.",
            )

        if eeg.ndim == 1:
            eeg = eeg.reshape(1, -1)

        # ---------------------------------------------------------------
        # 3. Process EEG using the Sixth Sense backend
        # ---------------------------------------------------------------

        reading = backend.get_current_reading(
            window=eeg,
            tracker=tracker,
            participant_id=participant_id,
            sensor_simulation=sensor_simulation,
        )

        # Make sure we have a normal dictionary.
        reading = dict(reading)

        # ---------------------------------------------------------------
        # 4. Add EEG data for the website
        # ---------------------------------------------------------------

        # All EEG channels.
        reading["eeg"] = eeg.tolist()

        # First EEG channel (Fp1) for the live EEG graph.
        reading["eeg_trace"] = eeg[0].tolist()

        reading["simulation_mode"] = simulation_mode

        # ---------------------------------------------------------------
        # 5. Automatically save STATE CHANGES
        # ---------------------------------------------------------------

        current_state = reading.get("state")

        if (
            previous_state is not None
            and current_state is not None
            and current_state != previous_state
        ):

            event = backend.create_event(
                reading,
                previous_state,
            )

            backend.save_event(event)

        if current_state is not None:
            previous_state = current_state

        latest_reading = reading

        return reading

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not obtain current reading: {exc}",
        )


# ---------------------------------------------------------------------------
# Save caregiver observation
# ---------------------------------------------------------------------------

@app.post("/api/event")
def save_caregiver_event(event: EventInput):
    """
    Save a caregiver observation together with the most recent EEG-derived
    physiological state.
    """

    if latest_reading is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "No EEG reading is available yet. "
                "Wait for the dashboard to receive a reading first."
            ),
        )

    try:

        event_data = {
            "timestamp": latest_reading.get("timestamp", ""),
            "participant_id": event.participant_id,

            "state": latest_reading.get("state", ""),

            "valence": latest_reading.get("valence", 0),
            "arousal": latest_reading.get("arousal", 0),

            "signal_quality": latest_reading.get(
                "signal_quality",
                "",
            ),

            # Pain is caregiver/patient entered.
            # It is NOT inferred from EEG.
            "pain_present": event.pain_present,
            "pain_location": ", ".join(event.pain_location),
            "pain_level": event.pain_level,
            "pain_type": ", ".join(event.pain_type),
            "pain_note": event.pain_note,

            # Environmental context
            "temperature": latest_reading.get(
                "temperature",
                None,
            ),

            "humidity": latest_reading.get(
                "humidity",
                None,
            ),

            "noise_level": latest_reading.get(
                "noise_level",
                None,
            ),

            "note": event.note,
        }

        saved_event = backend.save_event(event_data)

        return {
            "status": "saved",
            "event": saved_event,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save caregiver event: {exc}",
        )


# ---------------------------------------------------------------------------
# Event history
# ---------------------------------------------------------------------------

@app.get("/api/history")
def history():
    """
    Return saved events as JSON.
    """

    try:

        history_data = backend.load_history()

        # backend.load_history() currently returns a pandas DataFrame.
        # JavaScript cannot directly understand a DataFrame, so convert
        # it into a list of dictionaries.

        if hasattr(history_data, "empty"):

            if history_data.empty:
                return []

            history_data = history_data.fillna("")

            return history_data.to_dict(
                orient="records"
            )

        # In case the backend is later changed to return a list directly.
        return history_data

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load history: {exc}",
        )


# ---------------------------------------------------------------------------
# Doctor / care-team summary
# ---------------------------------------------------------------------------

@app.get("/api/summary")
def doctor_summary():
    """
    Generate the care-team summary from saved events.
    """

    try:

        history_data = backend.load_history()

        summary = create_doctor_summary(
            history_data
        )

        return summary

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not create doctor summary: {exc}",
        )


# ---------------------------------------------------------------------------
# Connect to OpenBCI Cyton
# ---------------------------------------------------------------------------

@app.post("/api/connect")
def connect_board(data: ConnectInput):
    global board
    global simulation_mode

    try:

        new_board, error = connect_cyton(
            serial_port=data.serial_port,
            existing_board=board,
        )

        if error:
            raise HTTPException(
                status_code=500,
                detail=error,
            )

        board = new_board
        simulation_mode = False

        return {
            "status": "connected",
            "serial_port": data.serial_port,
            "simulation_mode": False,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not connect to Cyton: {exc}",
        )


# ---------------------------------------------------------------------------
# Disconnect Cyton
# ---------------------------------------------------------------------------

@app.post("/api/disconnect")
def disconnect_board():
    global board
    global simulation_mode

    try:

        if board is not None:
            disconnect_cyton(board)

        board = None

        # Fall back to simulation so the website continues working.
        simulation_mode = True

        return {
            "status": "disconnected",
            "simulation_mode": True,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not disconnect Cyton: {exc}",
        )


# ---------------------------------------------------------------------------
# Turn simulated elevated EEG on/off
# ---------------------------------------------------------------------------

@app.post("/api/simulation/discomfort")
def set_simulated_discomfort(data: SimulationInput):
    global simulate_discomfort

    simulate_discomfort = data.enabled

    return {
        "status": "ok",
        "simulate_discomfort": simulate_discomfort,
    }


# ---------------------------------------------------------------------------
# Switch back to simulation mode
# ---------------------------------------------------------------------------

@app.post("/api/simulation")
def use_simulation():
    global board
    global simulation_mode

    try:

        if board is not None:
            disconnect_cyton(board)
            board = None

        simulation_mode = True

        return {
            "status": "ok",
            "simulation_mode": True,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not switch to simulation mode: {exc}",
        )


# ---------------------------------------------------------------------------
# Serve website static files
# ---------------------------------------------------------------------------

if WEBSITE_DIR.exists():

    app.mount(
        "/website",
        StaticFiles(directory=WEBSITE_DIR),
        name="website",
    )


# ---------------------------------------------------------------------------
# Website pages
# ---------------------------------------------------------------------------

@app.get("/")
def website_home():

    index_file = WEBSITE_DIR / "index.html"

    if not index_file.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "website/index.html was not found. "
                "Create the website folder and place "
                "the frontend files inside it."
            ),
        )

    return FileResponse(index_file)


@app.get("/events")
def events_page():

    file = WEBSITE_DIR / "events.html"

    if not file.exists():
        raise HTTPException(
            status_code=404,
            detail="website/events.html was not found.",
        )

    return FileResponse(file)


@app.get("/doctor-summary")
def doctor_summary_page():

    file = WEBSITE_DIR / "doctor-summary.html"

    if not file.exists():
        raise HTTPException(
            status_code=404,
            detail="website/doctor-summary.html was not found.",
        )

    return FileResponse(file)