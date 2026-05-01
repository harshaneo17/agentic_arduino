"""
Actuator tools - control physical outputs (servo, LED, buzzer, LCD).
"""

from langchain_core.tools import tool

import config
from helpers import send_command, write_to_lcd


@tool
def set_servo_angle(angle: int) -> str:
    """Set the servo motor to a specific angle between 0 and 180 degrees.
    
    Args:
        angle: Target angle in degrees, must be between 0 and 180
    """
    if not config.SERVO_MIN_ANGLE <= angle <= config.SERVO_MAX_ANGLE:
        return (
            f"ERROR: Angle {angle} out of range. "
            f"Must be between {config.SERVO_MIN_ANGLE} and {config.SERVO_MAX_ANGLE}."
        )
    response = send_command(f"SERVO:{angle}")
    return f"Servo set to {angle} degrees"


@tool
def set_led(state: str) -> str:
    """Turn the LED on or off.
    
    Args:
        state: Either "on" or "off"
    """
    state = state.lower().strip()
    if state not in ["on", "off"]:
        return f"ERROR: Invalid state '{state}'. Must be 'on' or 'off'."
    
    command = "LED:ON" if state == "on" else "LED:OFF"
    send_command(command)
    return f"LED is now {state}"


@tool
def play_buzzer(duration_ms: int) -> str:
    """Activate the buzzer for a specific duration in milliseconds.
    Use sparingly to alert about important events.
    
    Args:
        duration_ms: Duration in milliseconds, between 100 and 5000
    """
    if not config.BUZZER_MIN_MS <= duration_ms <= config.BUZZER_MAX_MS:
        return (
            f"ERROR: Duration out of safe range "
            f"({config.BUZZER_MIN_MS}-{config.BUZZER_MAX_MS}ms)."
        )
    send_command(f"BUZZER:{duration_ms}")
    return f"Buzzer played for {duration_ms}ms"


@tool
def display_message(message: str) -> str:
    """Display a status message on the LCD during a task. Max 32 characters.
    Use this for status updates DURING a task. Final responses are
    automatically displayed by the system.
    
    Args:
        message: Text to display
    """
    if len(message) > config.LCD_MAX_CHARS:
        return f"ERROR: Message too long ({len(message)} chars)."
    write_to_lcd(message)
    return f"Displayed: '{message}'"


# Export the tools as a list for easy import
ACTUATOR_TOOLS = [
    set_servo_angle,
    set_led,
    play_buzzer,
    display_message,
]
