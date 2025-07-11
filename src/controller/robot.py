import threading
import json
from config import Config
from modules.vision import VisionModule
from modules.audio import AudioModule
from modules.leds import LedsModule
from enum import Enum, auto
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

from .state import RobotState
from .speech import SpeechController
from .conversation import ConversationController

robot_instance = None

class RobotController:
    """Main robot controller that coordinates all subsystems"""
    def __init__(self, debug: bool = False, api_enabled: bool = False, state_update_callback: Optional[Callable[[dict], None]] = None):
        """
        Main robot controller that coordinates all subsystems.
        state_update_callback: function to call with updated robot state (for WebSocket broadcast)
        """
        # Callback for state updates (should be set by API layer)
        self.state_update_callback = state_update_callback
        
        self.config = Config()
        self._lock = threading.Lock()
        self.debug = debug
        self._state = RobotState.STANDBY
        self.audio = AudioModule(debug=debug)
        self.speech = SpeechController(self, self.audio, debug=debug)
        self.audio.add_output_audio_level_callback(self._on_output_audio_level)
        self.conversation = ConversationController(debug=debug)
        self.leds = LedsModule(debug=debug)
        self.vision = VisionModule(debug=debug)

        # Register global instance for API access
        global robot_instance
        robot_instance = self


    def start(self):
        if self.debug:
            logger.info("Starting robot...")
        # Enter standby mode and begin wake word detection
        self._return_to_standby()

    def stop(self):
        if self.debug:
            logger.info("Stopping robot...")
        self._cleanup()

    def _set_state(self, new_state: RobotState):
        """
        Set robot state and update LEDs
        """
        if self.debug:
            logger.info(f"State transition: {self._state} -> {new_state}")
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

    # Wake word, transcription, and speech completion are now handled by SpeechController

    # Transcription and conversation logic handled by SpeechController and ConversationController

    # Speech completion handled by SpeechController

    def _return_to_standby(self):
        """Return to standby mode"""
        if self.debug:
            logger.info("Returning to standby mode")
        # Stop speech recognition
        if self.speech and self.speech.speech_to_text:
            self.speech.speech_to_text.stop_listening()
        # Start wake word detection
        if self.speech and self.speech.wake_word:
            self.speech.wake_word.start_listening()
        # Set state last
        self._set_state(RobotState.STANDBY)

    def wake_up(self):
        """Wake up the robot from STANDBY, as if the wake word was detected or UI button pressed."""
        if self._state != RobotState.STANDBY:
            if self.debug:
                logger.debug(f"[wake_up] Ignored: not in STANDBY (current state: {self._state})")
            return
        if self.debug:
            logger.info("[wake_up] Triggered: transitioning to LISTENING and starting speech recognition.")
        if self.speech:
            # Stop wake word detection
            if self.speech.wake_word:
                self.speech.wake_word.stop_listening()
            # Start speech recognition
            if self.speech.speech_to_text:
                self.speech.speech_to_text.start_listening()
        self._set_state(RobotState.LISTENING)

    def _on_input_audio_level(self, input_audio_level_db: float):
        """Handle real-time input audio level updates from the audio input module (in dB)."""
        import time
        now = time.time()
        # Throttle: only send if 100ms have passed or value changed by >1 dB
        if not hasattr(self, '_last_input_audio_level_sent'):
            self._last_input_audio_level_sent = None
            self._last_input_audio_level_time = 0
        send = False
        if (
            self._last_input_audio_level_sent is None or
            abs(input_audio_level_db - self._last_input_audio_level_sent) > 1 or
            now - self._last_input_audio_level_time > 0.1
        ):
            send = True
        if send:
            self._last_input_audio_level_sent = input_audio_level_db
            self._last_input_audio_level_time = now
            # if self.debug:
            #     print(f"[DEBUG] _on_input_audio_level sending input_audio_level_db: {input_audio_level_db}")
            # Notify API/server of input audio level update
        if self.state_update_callback:
            self.state_update_callback({"type": "update_audio_level", "input_audio_level_db": float(input_audio_level_db)})
        # else:
        #     if self.debug:
        #         print(f"[DEBUG] _on_input_audio_level throttled input_audio_level_db: {input_audio_level_db}")

    def _on_output_audio_level(self, output_audio_level_db: float):
        """Handle real-time output audio level updates from the output (loopback) device (in dB)."""
        import time
        now = time.time()
        # Throttle: only send if 100ms have passed or value changed by >1 dB
        if not hasattr(self, '_last_output_audio_level_sent'):
            self._last_output_audio_level_sent = None
            self._last_output_audio_level_time = 0
        send = False
        if (
            self._last_output_audio_level_sent is None or
            abs(output_audio_level_db - self._last_output_audio_level_sent) > 1 or
            now - self._last_output_audio_level_time > 0.1
        ):
            send = True
        if send:
            self._last_output_audio_level_sent = output_audio_level_db
            self._last_output_audio_level_time = now
            # if self.debug:
                # print(f"[DEBUG] _on_output_audio_level sending output_audio_level_db: {output_audio_level_db}")
            # Notify API/server of output audio level update
        if self.state_update_callback:
            self.state_update_callback({"type": "update_audio_level", "output_audio_level_db": float(output_audio_level_db)})
        # else:
        #     if self.debug:
                # print(f"[DEBUG] _on_output_audio_level throttled output_audio_level_db: {output_audio_level_db}")

    def _cleanup(self):
        if self.leds:
            self.leds.cleanup()
        if self.speech:
            self.speech.cleanup()
        if self.conversation:
            self.conversation.cleanup()
        if self.vision:
            self.vision.cleanup()
        if self.audio:
            self.audio.cleanup()
