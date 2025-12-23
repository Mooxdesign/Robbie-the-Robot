from modules.wake_word import WakeWordModule, WakeWordInitError
from modules.speech_to_text import SpeechToTextModule
from modules.voice import VoiceModule
from .state import RobotState
import logging
logger = logging.getLogger(__name__)

class SpeechController:
    def __init__(self, parent, audio_module, debug=False, backend=None):
        import os
        self.parent = parent  # Reference to RobotController
        self.debug = debug
        # Retrieve Picovoice access key from config or environment
        access_key = None
        if hasattr(parent, 'config'):
            access_key = parent.config.get('picovoice', 'access_key', default=None)
        if not access_key:
            access_key = os.environ.get('PICOVOICE_API_KEY') or os.environ.get('PICOVOICE_ACCESS_KEY')
        self.wake_word = None
        if access_key:
            try:
                candidate = WakeWordModule(
                    audio_module=audio_module,
                    wake_word="porcupine",
                    access_key=access_key,
                    debug=debug
                )
                self.wake_word = candidate
            except WakeWordInitError as e:
                if debug:
                    logger.info(f"WakeWordModule initialization failed: {e}")
                self.wake_word = None
        else:
            if debug:
                logger.info("No Picovoice access key found. Wake word detection disabled.")
        self.speech_to_text = SpeechToTextModule(
            audio_module=audio_module,
            debug=debug,
            backend=backend
        )
        self.audio = audio_module
        self.voice = VoiceModule(debug=debug)  # Loads config automatically
        # Register callbacks (only once)
        self._callbacks_registered = False
        self._register_callbacks()

    def set_backend(self, backend: str):
        """Switch the speech-to-text backend at runtime."""
        if self.speech_to_text:
            self.speech_to_text.cleanup()
        self.speech_to_text = SpeechToTextModule(
            audio_module=self.parent.audio,
            debug=self.debug,
            backend=backend
        )
        self._register_callbacks()

    def _register_callbacks(self):
        if not self._callbacks_registered:
            if self.wake_word:
                self.wake_word.add_detection_callback(self.on_wake_word)
            self.speech_to_text.add_transcription_callback(self.on_transcription)
            self.speech_to_text.add_input_audio_level_callback(self.parent._on_input_audio_level)
            self.speech_to_text.add_timeout_callback(self.on_silence_timeout)
            self.voice.add_completion_callback(self.on_speech_complete)
            self._callbacks_registered = True

    def on_wake_word(self):
        if self.debug:
            logger.info("[SpeechController] Wake word detected")
        self.parent.wake_up()

    def on_transcription(self, text):
        if self.debug:
            logger.debug(f"[SpeechController] Transcription received: '{text}' (state: {self.parent._state})")
        
        try:
            with self.speech_to_text._lock:
                self.speech_to_text.transcription_in_progress = False
                if not text:
                    logger.warning("[SpeechController] Empty transcription received")
                    return None
            
            if hasattr(self.parent, 'state_update_callback') and self.parent.state_update_callback:
                self.parent.state_update_callback({"type": "update_transcription", "last_transcription": text})
            
            if self.debug:
                logger.info(f"Transcribed: {text}")
            
            if text.lower().strip() == "thanks robbie":
                if self.debug:
                    logger.info("[SpeechController] Exit phrase detected, returning to standby")
                self.parent._return_to_standby()
                return None
            
            self.parent._set_state(RobotState.PROCESSING)
            response = self.parent.conversation.chat(text)
            
            if response:
                try:
                    self.speech_to_text.stop_listening()
                except Exception as e:
                    logger.error(f"[SpeechController] Failed to stop listening: {e}")
                
                try:
                    self.parent._set_state(RobotState.SPEAKING)
                    self.voice.say(response, blocking=False)
                except Exception as e:
                    logger.error(f"[SpeechController] Failed to speak response: {e}")
                
                return response
            else:
                logger.warning("[SpeechController] No response from AI")
                self.parent._set_state(RobotState.LISTENING)
                return None
                
        except Exception as e:
            logger.error(f"[SpeechController] Error in transcription callback: {e}", exc_info=True)
            self.parent._set_state(RobotState.LISTENING)
            return None

    def on_speech_complete(self):
        if self.debug:
            logger.info("[SpeechController] Speech complete - transitioning to LISTENING")
        self.parent._set_state(RobotState.LISTENING)
        self.speech_to_text.start_listening()

    def on_silence_timeout(self):
        with self.speech_to_text._lock:
            if self.speech_to_text.transcription_in_progress:
                if self.debug:
                    logger.debug("[SpeechController] Silence timeout ignored: transcription in progress")
                return
        
        if self.debug:
            logger.info("[SpeechController] Silence timeout - returning to STANDBY")
        self.parent._return_to_standby()

    def cleanup(self):
        for mod in (self.wake_word, self.speech_to_text, self.voice):
            if mod:
                mod.cleanup()
