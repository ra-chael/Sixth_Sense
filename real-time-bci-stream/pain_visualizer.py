# this script is visualizing where the patient is experiencing pain or discomfort. It allows a caregiver or patient to record observed or communicated discomfort alongside the EEG event. The script does not diagnose pain from EEG, but rather provides a way to document pain information for later analysis.

import streamlit as st

# this list is used in the pain visualizer to allow the user to select body areas where discomfort is observed or communicated. It is not used for any automated analysis of EEG data.
BODY_AREAS = [
    "Head",
    "Neck",
    "Left shoulder",
    "Right shoulder",
    "Chest",
    "Abdomen",
    "Upper back",
    "Lower back",
    "Left arm",
    "Right arm",
    "Left hand",
    "Right hand",
    "Left leg",
    "Right leg",
    "Left foot",
    "Right foot",
    "Other",
]

# this function renders the pain visualizer section of the Streamlit app. It allows a caregiver or patient to record observed or communicated discomfort alongside the EEG event. The function returns a dictionary containing the entered information, including whether pain is present, its location, level, type, and any additional notes.
def render_pain_visualizer(key_prefix="pain"):
    """
    Display the caregiver pain/discomfort input controls.

    This does NOT diagnose pain from EEG.
    It allows a caregiver or patient to record observed or
    communicated discomfort alongside the EEG event.

    Returns a dictionary containing the entered information.
    """

    st.subheader("Pain & Discomfort Check")

    st.caption(
        "Use this section to record observed or communicated discomfort. "
        "This information is entered by the caregiver or patient and is "
        "not determined by the EEG."
    )

    # this button allows the user to show what kind of pain the patient has.
    pain_present = st.radio(
        "Is pain or physical discomfort suspected?",
        ["No", "Unsure", "Yes"],
        horizontal=True,
        key=f"{key_prefix}_present",
    )

    # Default values when no pain information is entered
    pain_location = []
    pain_level = 0
    pain_type = []
    pain_note = ""

    # this if statement checks wether the user indicated the location of the pain or discomfort. If the user indicated that there is pain or discomfort, it displays additional input controls for the user to specify the location, level, type, and any additional notes about the pain or discomfort.
    if pain_present != "No":

        pain_location = st.multiselect(
            "Where is the possible discomfort?",
            BODY_AREAS,
            key=f"{key_prefix}_location",
        )

        # this part is creating a slider for the user to be able to indicate the level of pain for m the patient.
        pain_level = st.slider(
            "Observed or communicated discomfort level",
            min_value=0,
            max_value=10,
            value=0,
            help=(
                "0 = no observed discomfort, "
                "10 = strongest observed or communicated discomfort."
            ),
            key=f"{key_prefix}_level",
        )

        # this part is creating a multiselct for the caregiver to select the type of pain or discomfort the patient may be feeling.
        pain_type = st.multiselect(
            "How does the discomfort appear or feel?",
            [
                "Unknown",
                "Aching",
                "Sharp",
                "Burning",
                "Pressure",
                "Cramping",
                "Throbbing",
                "Tingling",
                "Other",
            ],
            key=f"{key_prefix}_type",
        )

        # this part is vcreating a text area where the caregiver can add any other notes about the pain or discomfort.
        pain_note = st.text_area(
            "Additional pain/discomfort notes",
            placeholder=(
                "Example: Patient repeatedly touched their right shoulder "
                "and appeared uncomfortable when moving the arm."
            ),
            key=f"{key_prefix}_note",
        )

    return {
        "pain_present": pain_present,
        "pain_location": ", ".join(pain_location),
        "pain_level": pain_level,
        "pain_type": ", ".join(pain_type),
        "pain_note": pain_note,
    }