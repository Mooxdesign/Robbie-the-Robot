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
            logger.info(f"[SpeechController] Wake word detected (state: {self.parent._state})")
        self.parent.wake_up()

    def on_transcription(self, text):
        try:
            # Synchronize with speech_to_text lock and transcription_in_progress flag
            with self.speech_to_text._lock:
                self.speech_to_text.transcription_in_progress = False  # Mark as done
                if not text:
                    return None
                # Notify API/server of transcription update
            if hasattr(self.parent, 'state_update_callback') and self.parent.state_update_callback:
                self.parent.state_update_callback({"type": "update_transcription", "last_transcription": text})
                if self.debug:
                    logger.info(f"Transcribed: {text}")
                if text.lower().strip() == "thanks robbie":
                    self.parent._return_to_standby()
                    return None
                self.parent._set_state(RobotState.PROCESSING)
                response = self.parent.conversation.chat(text)
                if response:
                    logger.info(f"Robbie: {response}")
                    logger.info(f"[DEBUG] Type of response: {type(response)} Value: {repr(response)}")
                    logger.debug("[DEBUG] About to attempt stop_listening and state change")
                    try:
                        self.speech_to_text.stop_listening()
                        logger.info("[DEBUG] Called stop_listening()")
                    except Exception as e:
                        logger.error(f"[DEBUG] stop_listening() raised: {e}")
                    try:
                        self.parent._set_state(RobotState.SPEAKING)
                        logger.info("[DEBUG] Called _set_state(SPEAKING)")
                    except Exception as e:
                        logger.error(f"[DEBUG] _set_state(SPEAKING) raised: {e}")
                    try:
                        logger.debug(f"[SpeechController] About to call self.voice.say with: {response}")
                        self.voice.say(response, blocking=False)
                        logger.debug(f"[SpeechController] self.voice.say call complete")
                    except Exception as e:
                        logger.error(f"[SpeechController] Error calling self.voice.say: {str(e)}")
                    return response
                else:
                    logger.warning("No response from AI")
                    self.parent._set_state(RobotState.LISTENING)
                    return None
        except Exception as e:
            logger.exception(f"[SpeechController] Unhandled exception in on_transcription: {e}")
            try:
                logger.debug(f"[SpeechController] About to call self.voice.say with: {response}")
                self.voice.say(response, blocking=False)
                logger.debug(f"[SpeechController] self.voice.say call complete")
            except Exception as e:
                logger.error(f"[SpeechController] Error calling self.voice.say: {str(e)}")
            else:
                logger.warning("No response from AI")
                self.parent._set_state(RobotState.LISTENING)
            return None

    def on_speech_complete(self):
        # Always start listening after speech completes, and set state to LISTENING
        if self.debug:
            logger.info("[on_speech_complete] Speech finished. Transitioning to LISTENING and starting speech-to-text.")
        self.parent._set_state(RobotState.LISTENING)
        self.speech_to_text.start_listening()
        # Do NOT return to standby here. Standby should only be triggered by the silence timeout callback from SpeechToTextModule.

    def on_silence_timeout(self):
        # Called when silence timeout is triggered in SpeechToTextModule
        with self.speech_to_text._lock:
            if self.speech_to_text.transcription_in_progress:
                logger.info("[SpeechController] Silence timeout ignored: transcription in progress")
                return
            if self.debug:
                logger.info("[on_silence_timeout] Silence timeout occurred. Returning to STANDBY.")
            self.parent._return_to_standby()

    def cleanup(self):
        for mod in (self.wake_word, self.speech_to_text, self.voice):
            if mod:
                mod.cleanup()
