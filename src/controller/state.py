from enum import Enum

class RobotState(Enum):
    """Robot conversation states"""
    STANDBY = "standby"  # Listening for wake word
    LISTENING = "listening"  # Converting speech to text
    PROCESSING = "processing"  # Processing conversation
    SPEAKING = "speaking"  # Speaking response
