# This script is creating a summary for the doctor or the caregiver where it summarizes the recorded observations and the recorded states. 
# It does not provide a diagnosis. 
# The summary includes statistics such as the total number of events, counts of detected states, number of pain events, average pain level, distribution of pain locations, average environmental conditions, and any notes entered by the caregiver.

"""
Creates a care-team summary from Sixth Sense caregiver-reviewed events.

The summary describes recorded observations and experimental EEG-derived
state estimates. It does not provide a diagnosis.
"""

import pandas as pd


def create_doctor_summary(history):
    """
    Create summary statistics from saved Sixth Sense events.

    history may be either:
        - a pandas DataFrame
        - a list of dictionaries
    """

    if isinstance(history, list):
        df = pd.DataFrame(history)
    else:
        df = history.copy()

    # this if statement makes sure that if the dataframe is empty, it will return an empty summary with default values for all the wanted statistics.
    if df.empty:
        return {
            "total_events": 0,
            "state_counts": {},
            "pain_events": 0,
            "average_pain_level": None,
            "pain_locations": {},
            "average_temperature": None,
            "average_humidity": None,
            "average_noise": None,
            "notes": [],
        }

    # ---------- states ----------

    state_counts = (
        df["state"]
        .value_counts()
        .to_dict()
        if "state" in df.columns
        else {}
    )

    # ---------- pain ----------

    if "pain_present" in df.columns:
        pain_df = df[
            df["pain_present"]
            .astype(str)
            .str.lower()
            .isin(["yes", "unsure"])
        ].copy()
    else:
        pain_df = pd.DataFrame()

    pain_events = len(pain_df)

    average_pain_level = None

    # this if statement wether the pain data frame is empty and if the pain level column is present in the main data frrame. If both conditions are met, it will calculate the average pain level.
    if not pain_df.empty and "pain_level" in pain_df.columns:
        pain_levels = pd.to_numeric(
            pain_df["pain_level"],
            errors="coerce",
        ).dropna()

        if not pain_levels.empty:
            average_pain_level = round(
                float(pain_levels.mean()),
                1,
            )

    # ---------- pain locations ----------

    pain_locations = {}

    #
    if not pain_df.empty and "pain_location" in pain_df.columns:

        locations = []

        for value in pain_df["pain_location"].dropna():
            for location in str(value).split(","):
                location = location.strip()

                if location:
                    locations.append(location)

        if locations:
            pain_locations = (
                pd.Series(locations)
                .value_counts()
                .to_dict()
            )

    # ---------- environment ----------

    def average_column(column):
        if column not in df.columns:
            return None

        values = pd.to_numeric(
            df[column],
            errors="coerce",
        ).dropna()

        if values.empty:
            return None

        return round(float(values.mean()), 1)

    # ---------- caregiver notes ----------

    notes = []

    if "note" in df.columns:
        notes.extend(
            str(note)
            for note in df["note"].dropna()
            if str(note).strip()
        )

    if "pain_note" in df.columns:
        notes.extend(
            str(note)
            for note in df["pain_note"].dropna()
            if str(note).strip()
        )

    return {
        "total_events": len(df),
        "state_counts": state_counts,

        "pain_events": pain_events,
        "average_pain_level": average_pain_level,
        "pain_locations": pain_locations,

        "average_temperature": average_column("temperature"),
        "average_humidity": average_column("humidity"),
        "average_noise": average_column("noise_level"),

        "notes": notes,
    }