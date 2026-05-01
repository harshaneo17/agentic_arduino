"""
Tools package - aggregates all tools from sensor, actuator, and vision modules.
"""

from tools.sensors import SENSOR_TOOLS
from tools.actuators import ACTUATOR_TOOLS
from tools.vision import VISION_TOOLS

# Combined list of all tools available to the agent
ALL_TOOLS = SENSOR_TOOLS + ACTUATOR_TOOLS + VISION_TOOLS

__all__ = ['ALL_TOOLS', 'SENSOR_TOOLS', 'ACTUATOR_TOOLS', 'VISION_TOOLS']
