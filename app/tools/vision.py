"""
Vision tools - capture images and analyse them with Claude's multimodal API.
"""

from langchain_core.tools import tool

import hardware
from helpers import (
    capture_image,
    write_to_lcd,
    analyse_image_with_claude,
    compare_images_with_claude,
)


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
    captures = sorted(hardware.image_dir.glob("capture_*.jpg"))
    
    if len(captures) < 1:
        capture_image()
        return "No previous image available. Captured new baseline."
    
    previous_path = str(captures[-1])
    write_to_lcd("Comparing...")
    new_path = capture_image()
    
    response = compare_images_with_claude(
        previous_path,
        new_path,
        f"The first image was taken {time_description}. "
        f"The second image was just captured. "
        f"What has changed between them? Be concise."
    )
    
    return f"Change detection: {response}"


# Export the tools as a list for easy import
VISION_TOOLS = [
    look_around,
    look_for_object,
    read_visible_text,
    assess_scene_safety,
    compare_to_previous_view,
]
