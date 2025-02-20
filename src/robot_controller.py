import os
import sys
import time
import threading
import numpy as np
from typing import Optional, Dict, Any

# Add parent directory to Python path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.controllers.motor import MotorController
from src.controllers.vision import VisionController
from src.controllers.audio import AudioController
from src.controllers.voice import VoiceController
from src.controllers.ai import AIController
from src.controllers.lights import LightController

class RobotController:
    """Main robot controller that coordinates all subsystems"""
    
    def __init__(self):
        """Initialize robot controller"""
        self._lock = threading.Lock()
        
        # Load config
        self.config = Config()
        
        # Initialize subsystems
        try:
            self.motor = MotorController()
        except Exception as e:
            print(f"Failed to initialize motor controller: {e}")
            self.motor = None
            
        try:
            self.vision = VisionController()
        except Exception as e:
            print(f"Failed to initialize vision controller: {e}")
            self.vision = None
            
        try:
            self.audio = AudioController()
        except Exception as e:
            print(f"Failed to initialize audio controller: {e}")
            self.audio = None
            
        try:
            self.voice = VoiceController()
        except Exception as e:
            print(f"Failed to initialize voice controller: {e}")
            self.voice = None
            
        try:
            self.ai = AIController()
        except Exception as e:
            print(f"Failed to initialize AI controller: {e}")
            self.ai = None
            
        try:
            self.lights = LightController()
        except Exception as e:
            print(f"Failed to initialize LED matrix: {e}")
            self.lights = None
            
        # Set up audio visualization
        if self.audio and self.lights:
            self.audio.add_volume_callback(self._audio_callback)
            
        # Register cleanup
        import atexit
        atexit.register(self.cleanup)
        
    def set_motor_speeds(self, left: float, right: float):
        """
        Set motor speeds
        
        Args:
            left: Left motor speed (-1 to 1)
            right: Right motor speed (-1 to 1)
        """
        if self.motor:
            self.motor.set_motor_speeds(left, right)
            
    def move_head(self, pan: Optional[float] = None, tilt: Optional[float] = None):
        """
        Move head servos
        
        Args:
            pan: Pan angle in degrees (-90 to 90)
            tilt: Tilt angle in degrees (-45 to 45)
        """
        if self.motor:
            self.motor.move_head(pan, tilt)
            
    def move_arm(self, side: str, position: float):
        """
        Move arm servo
        
        Args:
            side: 'left' or 'right'
            position: Position (0 to 1)
        """
        if self.motor:
            self.motor.move_arm(side, position)
            
    def start_vision(self):
        """Start vision processing"""
        if self.vision:
            self.vision.start()
            
    def stop_vision(self):
        """Stop vision processing"""
        if self.vision:
            self.vision.stop()
            
    def get_frame(self):
        """Get current camera frame"""
        if self.vision:
            return self.vision.get_frame()
        return None
        
    def get_objects(self):
        """Get detected objects"""
        if self.vision:
            return self.vision.get_objects()
        return []
        
    def say(self, text: str, blocking: bool = False):
        """
        Speak text using text-to-speech
        
        Args:
            text: Text to speak
            blocking: Wait for speech to complete
        """
        if self.voice:
            self.voice.speak(text, blocking)
            
    def listen(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Listen for speech and convert to text
        
        Args:
            timeout: How long to wait before giving up
            
        Returns:
            Recognized text or None if no speech detected
        """
        if self.voice:
            return self.voice.listen(timeout=timeout)
        return None
        
    def process_text(self, text: str) -> str:
        """
        Process text with AI and get response
        
        Args:
            text: Input text
            
        Returns:
            AI response
        """
        if self.ai:
            return self.ai.process_text(text)
        return "AI processing not available"
        
    def set_lights(self, r: int, g: int, b: int):
        """
        Set LED matrix color
        
        Args:
            r: Red (0-255)
            g: Green (0-255)
            b: Blue (0-255)
        """
        if self.lights:
            self.lights.set_all(r, g, b)
            
    def clear_lights(self):
        """Turn off all LEDs"""
        if self.lights:
            self.lights.clear()
            
    def _audio_callback(self, volume: float):
        """Handle audio volume updates"""
        if self.lights:
            # Map volume to brightness (0-255)
            brightness = int(volume * 255)
            self.lights.set_all(brightness, brightness, 0)  # Yellow visualization
            
    def stop(self):
        """Stop all subsystems"""
        if self.motor:
            self.motor.cleanup()
            
        if self.vision:
            self.vision.cleanup()
            
        if self.audio:
            self.audio.cleanup()
            
        if self.voice:
            self.voice.cleanup()
            
        if self.lights:
            self.lights.cleanup()
            
    def cleanup(self):
        """Clean up resources"""
        self.stop()

if __name__ == "__main__":
    robot = RobotController()
    robot.start_vision()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        robot.cleanup()
