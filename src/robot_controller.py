#!/usr/bin/env python3

import os
import sys
import time
import threading
import numpy as np
from typing import Optional, Dict, Any
from enum import Enum

# Add parent directory to Python path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.modules.motor import MotorModule
from src.modules.vision import VisionModule
from src.modules.audio import AudioModule
from src.modules.voice import VoiceModule
from src.modules.conversation import ConversationModule
from src.modules.leds import LedsModule
from src.modules.wake_word import WakeWordModule
from src.modules.speech_to_text import SpeechToTextModule

class RobotState(Enum):
    """Robot conversation states"""
    STANDBY = "standby"  # Listening for wake word
    LISTENING = "listening"  # Converting speech to text
    PROCESSING = "processing"  # Processing conversation
    SPEAKING = "speaking"  # Speaking response

class RobotController:
    """Main robot controller that coordinates all subsystems"""
    
    def __init__(self, debug: bool = False):
        """Initialize robot controller"""
        self._lock = threading.Lock()
        self.debug = debug
        self._state = RobotState.STANDBY
        
        # Load config
        self.config = Config()
        
        # Initialize modules
        self.leds = LedsModule(debug=debug)
        self.motor = MotorModule(debug=debug)
        self.audio = AudioModule(debug=debug)
        self.wake_word = WakeWordModule(
            audio_module=self.audio,
            wake_word="porcupine",
            access_key=os.getenv("PICOVOICE_ACCESS_KEY"),  # Get from environment variable
            debug=debug
        )
        self.speech = SpeechToTextModule(
            audio_module=self.audio,
            debug=debug
        )
        self.voice = VoiceModule(debug=debug)
        self.conversation = ConversationModule(debug=debug)
        
        # Register callbacks
        if self.wake_word:
            self.wake_word.add_detection_callback(self._on_wake_word)
        if self.speech:
            self.speech.add_transcription_callback(self._on_transcription)
        if self.voice:
            self.voice.add_completion_callback(self._on_speech_complete)
            
    def start(self):
        """Start robot operation"""
        if self.debug:
            print("Starting robot...")
            
        # Start in standby mode
        self._set_state(RobotState.STANDBY)
        
        # Start wake word detection
        if self.wake_word:
            self.wake_word.start_listening()
            
        # Register timeout callback
        if self.speech:
            self.speech.add_timeout_callback(self._return_to_standby)
            
    def stop(self):
        """Stop robot operation"""
        if self.debug:
            print("Stopping robot...")
            
        # Stop all listening
        if self.wake_word:
            self.wake_word.stop_listening()
        if self.speech:
            self.speech.stop_listening()
            
        # Clean up
        self._cleanup()
            
    def _set_state(self, new_state: RobotState):
        """
        Set robot state and update LEDs
        
        Args:
            new_state: New state to set
        """
        if self.debug:
            print(f"State transition: {self._state} -> {new_state}")
            
        self._state = new_state
        
        # Update LED colors based on state
        if self.leds:
            if new_state == RobotState.STANDBY:
                self.leds.set_all(0, 127, 0)  # Green
            elif new_state == RobotState.LISTENING:
                self.leds.set_all(0, 0, 127)  # Blue
            elif new_state == RobotState.PROCESSING:
                self.leds.set_all(127, 0, 127)  # Purple
            elif new_state == RobotState.SPEAKING:
                self.leds.set_all(127, 127, 0)  # Yellow
                
    def _on_wake_word(self):
        """Handle wake word detection"""
        if self.debug:
            print(f"Wake word detected in state: {self._state}")
            
        if self._state != RobotState.STANDBY:
            if self.debug:
                print(f"Ignoring wake word in {self._state} state")
            return
            
        if self.debug:
            print("Wake word detected!")
            
        # Stop wake word detection first
        if self.wake_word:
            self.wake_word.stop_listening()
            
        # Start speech recognition before changing state
        if self.speech:
            if self.debug:
                print("Starting speech recognition")
            self.speech.start_listening()
            
        # Set state last (updates LEDs)
        self._set_state(RobotState.LISTENING)
            
    def _on_transcription(self, text: str):
        """
        Handle speech transcription
        
        Args:
            text: Transcribed text
        """
        if not text:
            return
            
        if self.debug:
            print(f"\nTranscribed: {text}")
            
        # Check for conversation end
        if text.lower().strip() == "thanks robbie":
            self._return_to_standby()
            return
            
        # Process with conversation module
        if self.conversation:
            # Set state but keep listening
            self._set_state(RobotState.PROCESSING)
            
            # Get AI response
            response = self.conversation.chat(text)
            
            if response:
                print(f"\nRobbie: {response}")
                
                # Stop listening before speaking
                if self.speech:
                    if self.debug:
                        print("Pausing speech recognition for speaking")
                    self.speech.stop_listening()
                    
                # Speak response
                self._set_state(RobotState.SPEAKING)
                if self.voice:
                    if self.debug:
                        print("Starting speech...")
                    self.voice.say(response, blocking=False)  # Use non-blocking speech
            else:
                print("\nNo response from AI")
                # Keep listening
                self._set_state(RobotState.LISTENING)
                
    def _on_speech_complete(self):
        """Handle speech completion"""
        if self.debug:
            print("Speech complete, returning to listening")
            
        # Return to listening mode
        self._set_state(RobotState.LISTENING)
        if self.speech:
            if self.debug:
                print("Resuming speech recognition")
            self.speech.start_listening()
            
    def _return_to_standby(self):
        """Return to standby mode"""
        if self.debug:
            print("Returning to standby mode")
            
        # Stop speech recognition
        if self.speech:
            if self.debug:
                print("Stopping speech recognition")
            self.speech.stop_listening()
            
        # Start wake word detection
        if self.wake_word:
            if self.debug:
                print("Starting wake word detection")
            self.wake_word.start_listening()
            
        # Set state last
        self._set_state(RobotState.STANDBY)
        
    def _cleanup(self):
        """Clean up resources"""
        if self.motor:
            self.motor.cleanup()
        if self.leds:
            self.leds.cleanup()
        if self.audio:
            self.audio.cleanup()
        if self.voice:
            self.voice.cleanup()
        if self.conversation:
            self.conversation.cleanup()
        if self.wake_word:
            self.wake_word.cleanup()
        if self.speech:
            self.speech.cleanup()

if __name__ == "__main__":
    robot = RobotController(debug=True)
    robot.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        robot.stop()
