"""
Embodied AI agent with vision and voice capability.
Pi 4 + USB Webcam + Microphone + Arduino + Claude with multimodal input.
"""

import serial
import time
import base64
import os
import cv2
import wave
import pyaudio
import whisper
from pathlib import Path
from datetime import datetime
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent



# Hardware setup


# Serial to Arduino
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
time.sleep(2)
ser.flushInput()
print(f"Serial connection established on {SERIAL_PORT}")

# USB Webcam
WEBCAM_INDEX = 0
webcam = cv2.VideoCapture(WEBCAM_INDEX)
webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
time.sleep(2)

if not webcam.isOpened():
    raise RuntimeError(f"Could not open webcam at index {WEBCAM_INDEX}")
print("USB webcam ready")

# Whisper for speech recognition
print("Loading Whisper model...")
WHISPER_MODEL = whisper.load_model("base")
print("Whisper ready")

# Audio recording config
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

# Image storage
IMAGE_DIR = Path("./captures")
IMAGE_DIR.mkdir(exist_ok=True)



# Helpers


def send_command(command: str) -> str:
    """Send a command to Arduino and return the response."""
    try:
        ser.flushInput()
        ser.write(f"{command}\n".encode())
        response = ser.readline().decode('utf-8', errors='ignore').strip()
        if not response:
            return "ERROR: No response from Arduino"
        return response
    except serial.SerialException as e:
        return f"ERROR: Serial communication failed - {str(e)}"


def write_to_lcd(message: str) -> str:
    """Direct LCD write."""
    if len(message) > 32:
        message = message[:29] + "..."
    safe_message = message.replace(":", "-")
    response = send_command(f"LCD:{safe_message}")
    return response


def capture_image() -> str:
    """Capture an image from the webcam and return its path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = IMAGE_DIR / f"capture_{timestamp}.jpg"
    
    for _ in range(3):
        webcam.read()
    
    ret, frame = webcam.read()
    if not ret:
        raise RuntimeError("Failed to capture image from webcam")
    
    cv2.imwrite(str(image_path), frame)
    return str(image_path)


def encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to base64 for the API."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def analyse_image_with_claude(image_path: str, question: str) -> str:
    """Send an image to Claude with a question and return the analysis."""
    image_data = encode_image_to_base64(image_path)
    
    vision_llm = ChatAnthropic(
        model="claude-sonnet-4-5",
        temperature=0,
        max_tokens=500,
    )
    
    response = vision_llm.invoke([
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": question
                }
            ]
        }
    ])
    
    return response.content


def summarise_for_lcd(full_response: str, llm) -> str:
    """Compress a response to LCD-friendly length."""
    if len(full_response) <= 32:
        return full_response
    
    summary_response = llm.invoke([
        ("system", "Summarise in max 32 characters total. Output only the summary, nothing else."),
        ("user", full_response)
    ])
    
    return summary_response.content.strip()[:32]


def record_audio(filename: str = "input.wav", duration: int = 5) -> str:
    """Record audio from default microphone for specified duration."""
    audio = pyaudio.PyAudio()
    
    stream = audio.open(
        format=AUDIO_FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )
    
    print(f"HAL listening for {duration} seconds...")
    
    frames = []
    for _ in range(0, int(SAMPLE_RATE / CHUNK_SIZE * duration)):
        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        frames.append(data)
    
    print("Recording done")
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(AUDIO_FORMAT))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))
    
    return filename


def transcribe_audio(filename: str) -> str:
    """Use Whisper to transcribe audio to text."""
    write_to_lcd("Transcribing...")
    result = WHISPER_MODEL.transcribe(filename, fp16=False)
    return result["text"].strip()


def get_voice_input(duration: int = 5) -> str:
    """Record audio and return transcribed text."""
    record_audio("input.wav", duration)
    text = transcribe_audio("input.wav")
    return text



# Sensor and actuator tools


@tool
def read_temperature() -> str:
    """Read the current ambient temperature in Celsius."""
    response = send_command("READ_TEMP")
    return f"Current temperature: {response}°C"


@tool
def read_humidity() -> str:
    """Read the current ambient humidity percentage."""
    response = send_command("READ_HUMIDITY")
    return f"Current humidity: {response}%"


@tool
def read_distance() -> str:
    """Read the distance in centimeters from the ultrasonic sensor."""
    response = send_command("READ_DIST")
    return f"Distance to nearest object: {response} cm"


@tool
def set_servo_angle(angle: int) -> str:
    """Set the servo motor to a specific angle between 0 and 180 degrees.
    
    Args:
        angle: Target angle in degrees, must be between 0 and 180
    """
    if not 0 <= angle <= 180:
        return f"ERROR: Angle {angle} out of range. Must be between 0 and 180."
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
        return f"ERROR: Invalid state '{state}'."
    command = "LED:ON" if state == "on" else "LED:OFF"
    send_command(command)
    return f"LED is now {state}"


@tool
def play_buzzer(duration_ms: int) -> str:
    """Activate the buzzer for a specific duration in milliseconds.
    
    Args:
        duration_ms: Duration in milliseconds, between 100 and 5000
    """
    if not 100 <= duration_ms <= 5000:
        return f"ERROR: Duration out of safe range."
    send_command(f"BUZZER:{duration_ms}")
    return f"Buzzer played for {duration_ms}ms"


@tool
def display_message(message: str) -> str:
    """Display a status message on the LCD during a task. Max 32 characters.
    
    Args:
        message: Text to display
    """
    if len(message) > 32:
        return f"ERROR: Message too long."
    write_to_lcd(message)
    return f"Displayed: '{message}'"


@tool
def get_environmental_state() -> str:
    """Get all sensor readings at once: temperature, humidity, and distance."""
    temp = send_command("READ_TEMP")
    humidity = send_command("READ_HUMIDITY")
    distance = send_command("READ_DIST")
    return (
        f"Temperature {temp}°C, "
        f"Humidity {humidity}%, "
        f"Distance to nearest object {distance}cm"
    )



# Vision tools


@tool
def look_around() -> str:
    """Capture an image with the webcam and get a general description of what is visible.
    Use this when you need to understand the visual environment or when the user asks
    about what is in front of the robot.
    
    Returns:
        A description of what the camera sees
    """
    write_to_lcd("Looking...")
    image_path = capture_image()
    
    description = analyse_image_with_claude(
        image_path,
        "Describe what you see in this image in 2-3 concise sentences. "
        "Focus on objects, people, and notable features. Be specific about "
        "positions and colours."
    )
    
    return f"Camera view: {description}"


@tool
def look_for_object(object_description: str) -> str:
    """Capture an image and check if a specific object is visible.
    Useful for finding things, identifying targets, or confirming presence of items.
    
    Args:
        object_description: What to look for (e.g., "a red ball", "a person wearing a hat")
    
    Returns:
        Whether the object was found and where it is in the frame
    """
    write_to_lcd("Searching...")
    image_path = capture_image()
    
    description = analyse_image_with_claude(
        image_path,
        f"Look for the following in this image: {object_description}. "
        f"Respond in this format: 'FOUND: <description and location in frame>' "
        f"or 'NOT FOUND: <what is visible instead>'. Be concise."
    )
    
    return description


@tool
def read_visible_text() -> str:
    """Capture an image and read any text visible in the camera view.
    Useful for reading labels, signs, instructions, or any printed text.
    
    Returns:
        The text that was read, or a note that no text was found
    """
    write_to_lcd("Reading...")
    image_path = capture_image()
    
    text = analyse_image_with_claude(
        image_path,
        "Read any text visible in this image. If there is text, return it exactly. "
        "If there is no text, respond 'NO_TEXT_VISIBLE'. Be concise."
    )
    
    return f"Text reading: {text}"


@tool
def assess_scene_safety() -> str:
    """Capture an image and assess if the visible scene appears safe or has any hazards.
    Useful before performing actions that could cause damage.
    
    Returns:
        Safety assessment of the visible scene
    """
    write_to_lcd("Assessing...")
    image_path = capture_image()
    
    assessment = analyse_image_with_claude(
        image_path,
        "Assess this scene for safety. Look for obstacles, fragile objects, "
        "people, animals, or anything that could be damaged. Respond in this format: "
        "'SAFE: <brief reason>' or 'CAUTION: <specific concern>'. Be concise."
    )
    
    return f"Safety check: {assessment}"


@tool
def compare_to_previous_view(time_description: str) -> str:
    """Capture a new image and compare it to a previously captured image to detect changes.
    Useful for monitoring tasks or detecting movement.
    
    Args:
        time_description: When was the previous image taken (e.g., "30 seconds ago")
    
    Returns:
        Description of changes between the views
    """
    captures = sorted(IMAGE_DIR.glob("capture_*.jpg"))
    
    if len(captures) < 1:
        new_path = capture_image()
        return "No previous image available. Captured new baseline."
    
    previous_path = str(captures[-1])
    write_to_lcd("Comparing...")
    new_path = capture_image()
    
    vision_llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0, max_tokens=500)
    
    response = vision_llm.invoke([
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": encode_image_to_base64(previous_path),
                    },
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": encode_image_to_base64(new_path),
                    },
                },
                {
                    "type": "text",
                    "text": (
                        f"The first image was taken {time_description}. "
                        f"The second image was just captured. "
                        f"What has changed between them? Be concise."
                    )
                }
            ]
        }
    ])
    
    return f"Change detection: {response.content}"



# Agent setup


llm = ChatAnthropic(
    model="claude-sonnet-4-5",
    temperature=0,
)

tools_list = [
    # Sensor tools
    read_temperature,
    read_humidity,
    read_distance,
    get_environmental_state,
    # Actuator tools
    set_servo_angle,
    set_led,
    play_buzzer,
    display_message,
    # Vision tools
    look_around,
    look_for_object,
    read_visible_text,
    assess_scene_safety,
    compare_to_previous_view,
]

system_prompt = """You are an embodied AI agent called HAL:9000 with sensors, actuators, and vision.

Available capabilities:
- Sensors: temperature, humidity, ultrasonic distance
- Actuators: servo motor (0-180°), LED, buzzer, LCD display (32 chars max)
- Vision: USB webcam with image analysis

Decision-making guidelines:
- Use vision when you need to understand the visual scene
- Use sensors for environmental measurements
- Combine both when helpful (e.g., visual confirmation after a sensor reading)
- The LCD is your primary way of speaking to the user
- Keep final responses under 32 characters for clean LCD display
- Use display_message during tasks for status updates
- For safety-critical actions, use assess_scene_safety first
- If a tool fails, acknowledge and try alternatives
- Be direct and concise

When the user asks something visual, prefer vision tools over guessing.
When asked to find or identify something, use look_for_object.
"""

agent = create_agent(llm, tools_list, system_prompt=system_prompt)



# Main loop


def run_command(user_input: str):
    """Run a user command through the agent."""
    print(f"\n{'='*60}")
    print(f"USER: {user_input}")
    print('='*60)
    
    write_to_lcd("Thinking...")
    
    result = agent.invoke({
        "messages": [("user", user_input)]
    })
    
    # for message in result["messages"]:
    #     if hasattr(message, 'content') and message.content:
    #         role = message.__class__.__name__
    #         print(f"\n[{role}]: {message.content}")
    #     if hasattr(message, 'tool_calls') and message.tool_calls:
    #         for tc in message.tool_calls:
    #             print(f"\n[TOOL]: {tc['name']}({tc['args']})")
    
    final_message = result["messages"][-1]
    final_response = final_message.content if hasattr(final_message, 'content') else str(final_message)
    
    lcd_text = summarise_for_lcd(final_response, llm)
    write_to_lcd(lcd_text)
    print(f"\n[LCD]: {lcd_text}")


if __name__ == "__main__":
    print("\nVision-enabled HAL:9000 ready.\n")
    print("Commands: type a prompt, or 'hal' to speak, 'quit' to exit\n")
    write_to_lcd("HAL:9000 ready")
    
    try:
        while True:
            user_input = input("\n> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if user_input.lower() in ['hal', 'h']:
                write_to_lcd("Yes, Harsha?")
                time.sleep(1)
                user_input = get_voice_input(duration=5)
                if not user_input:
                    print("I'm sorry, Harsha. I'm afraid I can't do that.")
                    write_to_lcd("I'm sorry, Harsha. I'm afraid I can't do that.")
                    continue
                print(f"HAL heard: {user_input}")
            
            if not user_input:
                continue
            
            try:
                run_command(user_input)
            except Exception as e:
                error_msg = f"Error: {str(e)[:25]}"
                write_to_lcd(error_msg)
                print(f"\nERROR: {e}")
    
    finally:
        write_to_lcd("HAL:9000 offline")
        time.sleep(1)
        webcam.release()
        ser.close()
        print("\nShutdown complete.")