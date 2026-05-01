"""
Sensor tools - read environmental data from Arduino sensors.
"""

from langchain_core.tools import tool
from helpers import send_command


@tool
def read_temperature() -> str:
    """Read the current ambient temperature in Celsius from the DHT11 sensor."""
    response = send_command("READ_TEMP")
    return f"Current temperature: {response}°C"


@tool
def read_humidity() -> str:
    """Read the current ambient humidity percentage from the DHT11 sensor."""
    response = send_command("READ_HUMIDITY")
    return f"Current humidity: {response}%"


@tool
def read_distance() -> str:
    """Read the distance in centimeters from the ultrasonic sensor.
    Useful for detecting obstacles or measuring distance to objects."""
    response = send_command("READ_DIST")
    return f"Distance to nearest object: {response} cm"


@tool
def get_environmental_state() -> str:
    """Get all sensor readings at once: temperature, humidity, and distance.
    Useful for understanding the overall environmental state in one call."""
    temp = send_command("READ_TEMP")
    humidity = send_command("READ_HUMIDITY")
    distance = send_command("READ_DIST")
    return (
        f"Temperature {temp}°C, "
        f"Humidity {humidity}%, "
        f"Distance to nearest object {distance}cm"
    )


# Export the tools as a list for easy import
SENSOR_TOOLS = [
    read_temperature,
    read_humidity,
    read_distance,
    get_environmental_state,
]
