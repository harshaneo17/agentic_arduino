"""
Helper functions used by tools across the application.
Includes serial communication, image capture, audio capture, and LLM calls.
"""

import base64
import time
import wave
import cv2
import pyaudio
import serial
from datetime import datetime
from langchain_anthropic import ChatAnthropic

import config
import hardware



# Serial communication


def send_command(command: str) -> str:
    """Send a command to Arduino and return the response."""
    try:
        hardware.ser.flushInput()
        hardware.ser.write(f"{command}\n".encode())
        response = hardware.ser.readline().decode('utf-8', errors='ignore').strip()
        if not response:
            return "ERROR: No response from Arduino"
        return response
    except serial.SerialException as e:
        return f"ERROR: Serial communication failed - {str(e)}"


def write_to_lcd(message: str) -> str:
    """Write a message to the LCD with safe truncation."""
    if len(message) > config.LCD_MAX_CHARS:
        message = message[:config.LCD_MAX_CHARS - 3] + "..."
    safe_message = message.replace(":", "-")  # Avoid breaking the protocol
    return send_command(f"LCD:{safe_message}")



# Image capture and encoding


def capture_image() -> str:
    """Capture an image from the webcam. Returns the file path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = hardware.image_dir / f"capture_{timestamp}.jpg"
    
    # Flush stale frames from buffer
    for _ in range(3):
        hardware.webcam.read()
    
    ret, frame = hardware.webcam.read()
    if not ret:
        raise RuntimeError("Failed to capture image from webcam")
    
    cv2.imwrite(str(image_path), frame)
    return str(image_path)


def encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to base64 for the API."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")



# Vision LLM calls


def analyse_image_with_claude(image_path: str, question: str) -> str:
    """Send a single image to Claude with a question and return the analysis."""
    image_data = encode_image_to_base64(image_path)
    
    vision_llm = ChatAnthropic(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.VISION_MAX_TOKENS,
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
                {"type": "text", "text": question}
            ]
        }
    ])
    
    return response.content


def compare_images_with_claude(
    previous_path: str,
    new_path: str,
    question: str
) -> str:
    """Send two images to Claude and ask a comparison question."""
    vision_llm = ChatAnthropic(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.VISION_MAX_TOKENS,
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
                {"type": "text", "text": question}
            ]
        }
    ])
    
    return response.content



# Output summarisation


def summarise_for_lcd(full_response: str, llm) -> str:
    """Compress a response to LCD-friendly length using the LLM itself."""
    if len(full_response) <= config.LCD_MAX_CHARS:
        return full_response
    
    summary_response = llm.invoke([
        ("system", f"Summarise in max {config.LCD_MAX_CHARS} characters total. "
                   "Output only the summary, nothing else."),
        ("user", full_response)
    ])
    
    return summary_response.content.strip()[:config.LCD_MAX_CHARS]



# Audio recording and transcription


def record_audio(filename: str = "input.wav", duration: int = None) -> str:
    """Record audio from default microphone for specified duration."""
    if duration is None:
        duration = config.RECORD_DURATION
    
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=config.AUDIO_FORMAT,
        channels=config.AUDIO_CHANNELS,
        rate=config.AUDIO_SAMPLE_RATE,
        input=True,
        frames_per_buffer=config.AUDIO_CHUNK_SIZE
    )
    
    print(f"HAL listening for {duration} seconds...")
    
    frames = []
    chunks_to_record = int(
        config.AUDIO_SAMPLE_RATE / config.AUDIO_CHUNK_SIZE * duration
    )
    for _ in range(chunks_to_record):
        data = stream.read(config.AUDIO_CHUNK_SIZE, exception_on_overflow=False)
        frames.append(data)
    
    print("Recording done")
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(config.AUDIO_CHANNELS)
        wf.setsampwidth(audio.get_sample_size(config.AUDIO_FORMAT))
        wf.setframerate(config.AUDIO_SAMPLE_RATE)
        wf.writeframes(b''.join(frames))
    
    return filename


def transcribe_audio(filename: str) -> str:
    """Use Whisper to transcribe audio to text."""
    write_to_lcd("Transcribing...")
    result = hardware.whisper_model.transcribe(filename, fp16=False)
    return result["text"].strip()


def get_voice_input(duration: int = None) -> str:
    """Record audio and return transcribed text."""
    record_audio("input.wav", duration)
    return transcribe_audio("input.wav")
