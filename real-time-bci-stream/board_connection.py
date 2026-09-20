# This file is part of Sixth Sense, a real-time BCI dashboard for monitoring pain and discomfort for caretaker of non-verbal patients.

"""Lazy BrainFlow/Cyton connection helper. Nothing here runs at import time."""

DEFAULT_SERIAL_PORT = "/dev/cu.usbserial-DM01IK21"


def connect_cyton(serial_port=DEFAULT_SERIAL_PORT, existing_board=None):
    """Attempt to open a BrainFlow session against a Cyton board.

    existing_board, if given, is released first. BrainFlow keeps a
    process-wide session guard, so any board left over from a prior
    attempt (including ones from an earlier Streamlit rerun) must be
    released or a fresh prepare_session() raises ANOTHER_BOARD_IS_CREATED_ERROR.

    Returns (board, error_message). board is None on failure.
    """
    try:
        from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
    except ImportError as exc:
        return None, f"BrainFlow not installed: {exc}"

    disconnect_cyton(existing_board)

    # BrainFlow's session guard is process-wide, and a board object can be lost
    # across Streamlit reruns while its session stays open. Clear any orphan
    # session so prepare_session() below does not hit
    # ANOTHER_BOARD_IS_CREATED_ERROR.
    try:
        BoardShim.release_all_sessions()
    except Exception:
        pass

    params = BrainFlowInputParams()
    params.serial_port = serial_port

    board = BoardShim(BoardIds.CYTON_BOARD.value, params)

    try:
        board.prepare_session()
        board.start_stream()
        return board, None
    except Exception as exc:
        try:
            if board.is_prepared():
                board.release_session()
        except Exception:
            pass
        return None, f"Could not connect to Cyton on {serial_port}: {exc}"

# this method disconnects the Cyton board and releases the session.
def disconnect_cyton(board):
    if board is None:
        return
    try:
        board.stop_stream()
    except Exception:
        pass
    try:
        board.release_session()
    except Exception:
        pass

#this gets the latest n_samples of EEG from an active board session. get_current_board_data returns every row the board produces — EEG plus accelerometer, aux, and timestamp channels, 24 rows on a Cyton. Only the EEG rows are returned here, so callers see an (n_eeg_channels, n_samples) window that matches the simulated one.
def capture_window(board, n_samples=250):
    """Read the latest n_samples of EEG from an active board session.

    get_current_board_data returns every row the board produces — EEG plus
    accelerometer, aux, and timestamp channels, 24 rows on a Cyton. Only the
    EEG rows are returned here, so callers see an (n_eeg_channels, n_samples)
    window that matches the simulated one.
    """
    from brainflow.board_shim import BoardShim, BoardIds

    data = board.get_current_board_data(n_samples)
    # Extract only the EEG channels
    eeg_rows = BoardShim.get_eeg_channels(BoardIds.CYTON_BOARD.value)
    return data[eeg_rows, :]
