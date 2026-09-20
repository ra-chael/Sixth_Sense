"""
Environmental sensor support for Sixth Sense.

For the hackathon prototype, this module can generate simulated
environmental readings.

Later, real temperature, humidity, noise, or other environmental
sensors can be connected here without changing the rest of the app.
"""

import random


def get_environment_data(simulation=True):
    """
    Return the current environmental sensor readings.

    Parameters:
        simulation (bool):
            True  -> generate fake sensor values for testing/demo.
            False -> eventually read values from real external sensors.

    Returns:
        dictionary containing the environmental readings.
    """

    if simulation:
        return generate_simulated_environment()

    return read_real_environment()


def generate_simulated_environment():
    """
    Generate realistic-looking environmental values for
    development and hackathon demonstrations.
    """

    temperature = round(random.uniform(20.0, 27.0), 1)

    humidity = round(random.uniform(35.0, 65.0), 1)

    noise_level = round(random.uniform(30.0, 75.0), 1)

    return {
        "temperature": temperature,
        "humidity": humidity,
        "noise_level": noise_level,
        "sensor_status": "Simulated",
    }


def read_real_environment():
    """
    Placeholder for real external sensors.

    Later, Arduino / Raspberry Pi / serial / Bluetooth sensor
    code can replace this section.
    """

    return {
        "temperature": None,
        "humidity": None,
        "noise_level": None,
        "sensor_status": "Not connected",
    }