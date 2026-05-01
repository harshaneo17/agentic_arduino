"""
Configuration constants for the agent.
Adjust these to match your hardware setup.
"""

import pyaudio


# Serial / Arduino

SERIAL_PORT = '/dev/ttyACM0'  # Or /dev/ttyACM0 depending on Arduino
BAUD_RATE = 9600
SERIAL_TIMEOUT = 2


# Webcam

WEBCAM_INDEX = 0
WEBCAM_WIDTH = 1024
WEBCAM_HEIGHT = 768


# Audio / Whisper

AUDIO_FORMAT = pyaudio.paInt16
AUDIO_CHANNELS = 1
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_SIZE = 1024
RECORD_DURATION = 5  # seconds
WHISPER_MODEL_SIZE = "base"  # tiny, base, small, medium, large


# LLM

LLM_MODEL = "claude-sonnet-4-5"
LLM_TEMPERATURE = 0
VISION_MAX_TOKENS = 500


# Storage

IMAGE_DIR = "./captures"


# LCD constraints

LCD_MAX_CHARS = 32


# Safety bounds

SERVO_MIN_ANGLE = 0
SERVO_MAX_ANGLE = 180
BUZZER_MIN_MS = 100
BUZZER_MAX_MS = 5000
