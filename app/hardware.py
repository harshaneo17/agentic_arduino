"""
Hardware initialization and global resource management.
Other modules import the initialised resources from here.
"""

import serial
import cv2
import time
import whisper
from pathlib import Path

import config


# These globals are initialised by init_hardware()
# Other modules access them via this module

ser = None
webcam = None
whisper_model = None
image_dir = None


def init_hardware():
    """Initialise all hardware connections and shared resources.
    Call once at application startup before using any tools.
    """
    global ser, webcam, whisper_model, image_dir
    
    # Serial connection to Arduino
    ser = serial.Serial(
        config.SERIAL_PORT,
        config.BAUD_RATE,
        timeout=config.SERIAL_TIMEOUT
    )
    time.sleep(2)  # Arduino resets when serial opens
    ser.flushInput()
    print(f"Serial connection established on {config.SERIAL_PORT}")
    
    # USB Webcam
    webcam = cv2.VideoCapture(config.WEBCAM_INDEX)
    webcam.set(cv2.CAP_PROP_FRAME_WIDTH, config.WEBCAM_WIDTH)
    webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, config.WEBCAM_HEIGHT)
    time.sleep(2)  
    
    if not webcam.isOpened():
        raise RuntimeError(
            f"Could not open webcam at index {config.WEBCAM_INDEX}"
        )
    print("USB webcam ready")
    
    # Whisper for speech recognition
    print(f"Loading Whisper model ({config.WHISPER_MODEL_SIZE})...")
    whisper_model = whisper.load_model(config.WHISPER_MODEL_SIZE)
    print("Whisper ready")
    
    # Image storage directory
    image_dir = Path(config.IMAGE_DIR)
    image_dir.mkdir(exist_ok=True)


def shutdown_hardware():
    """Cleanly close all hardware connections."""
    global ser, webcam
    
    if webcam is not None:
        webcam.release()
        print("Webcam released")
    
    if ser is not None and ser.is_open:
        ser.close()
        print("Serial connection closed")
