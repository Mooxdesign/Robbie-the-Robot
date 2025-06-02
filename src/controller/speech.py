from modules.wake_word import WakeWordModule
from modules.speech_to_text import SpeechToTextModule
from modules.voice import VoiceModule
from .state import RobotState

class SpeechController:
    def __init__(self, parent, audio_module, debug=False):
        import os
        self.parent = parent  # Reference to RobotController
        self.debug = debug
        # Retrieve Picovoice access key from config or environment
        access_key = None
        if hasattr(parent, 'config'):
            access_key = parent.config.get('picovoice', 'access_key', default=None)
        if not access_key:
            access_key = os.environ.get('PICOVOICE_API_KEY') or os.environ.get('PICOVOICE_ACCESS_KEY')
        self.wake_word = WakeWordModule(
            audio_module=audio_module,
            wake_word="porcupine",
            access_key=access_key,
            debug=debug
        )
        self.speech_to_text = SpeechToTextModule(
            audio_module=audio_module,
            debug=debug
        )
        self.voice = VoiceModule(debug=debug)
        # Register callbacks (only once)
        self._callbacks_registered = False
        self._register_callbacks()

    def _register_callbacks(self):
        if not self._callbacks_registered:
            self.wake_word.add_detection_callback(self.on_wake_word)
            self.speech_to_text.add_transcription_callback(self.on_transcription)
            self.speech_to_text.add_audio_level_callback(self.parent._on_audio_level)
            self.speech_to_text.add_timeout_callback(self.on_speech_complete)
            self.voice.add_completion_callback(self.on_speech_complete)
            self._callbacks_registered = True

    def on_wake_word(self):
        if self.debug:
            print(f"[SpeechController] Wake word detected (state: {self.parent._state})")
        if self.parent._state != RobotState.STANDBY:
            if self.debug:
                print(f"Ignoring wake word in {self.parent._state} state")
            return
        self.wake_word.stop_listening()
        if self.debug:
            print("Starting speech recognition")
        self.speech_to_text.start_listening()
        self.parent._set_state(RobotState.LISTENING)

    def on_transcription(self, text):
        if not text:
            return
        self.parent._send_ws_command({"type": "update_transcription", "last_transcription": text})
        if self.debug:
            print(f"\nTranscribed: {text}")
        if text.lower().strip() == "thanks robbie":
            self.parent._return_to_standby()
            return
        self.parent._set_state(RobotState.PROCESSING)
        response = self.parent.conversation.chat(text)
        if response:
            print(f"\nRobbie: {response}")
            self.speech_to_text.stop_listening()
            self.parent._set_state(RobotState.SPEAKING)
            print(f"[SpeechController] About to call self.voice.say with: {response}")
            self.voice.say(response, blocking=False)
        else:
            print("\nNo response from AI")
            self.parent._set_state(RobotState.LISTENING)

    def on_speech_complete(self):
        # Always start listening after speech completes, and set state to LISTENING
        if self.debug:
            print("[on_speech_complete] Speech finished. Transitioning to LISTENING and starting speech-to-text.")
        self.parent._set_state(RobotState.LISTENING)
        self.speech_to_text.start_listening()
        # Do NOT return to standby here. Standby should only be triggered by the silence timeout callback from SpeechToTextModule.

    def cleanup(self):
        self.wake_word.cleanup()
        self.speech_to_text.cleanup()
        self.voice.cleanup()
