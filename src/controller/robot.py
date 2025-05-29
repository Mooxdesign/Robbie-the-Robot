import threading
import json
import websocket  # websocket-client package
from config import Config
from modules.vision import VisionModule
from modules.audio import AudioModule
from .state import RobotState
from .speech import SpeechController
from .conversation import ConversationController

class RobotController:
    """Main robot controller that coordinates all subsystems"""
    def __init__(self, debug: bool = False, api_enabled: bool = False):
        self._lock = threading.Lock()
        self.debug = debug
        self._state = RobotState.STANDBY
        self._terminal_input_thread = None
        self._stop_terminal_input = threading.Event()

        # Load config
        self.config = Config()

        # Initialize modules
        self.audio = AudioModule(debug=debug)
        self.speech = SpeechController(self, self.audio, debug=debug)
        self.conversation = ConversationController(debug=debug)
        self.leds = LedsModule(debug=debug)
        self.vision = VisionModule(debug=debug)

        # Start WebSocket thread for backend updates (only if API enabled)
        self._ws_url = "ws://localhost:8000/ws"
        self._ws = None
        self._ws_thread = None
        if api_enabled:
            self._ws_thread = threading.Thread(target=self._start_ws_client, daemon=True)
            self._ws_thread.start()

    def _start_ws_client(self):
        while True:
            try:
                self._ws = websocket.WebSocket()
                self._ws.connect(self._ws_url)
                break
            except Exception as e:
                if self.debug:
                    print(f"WebSocket connection failed: {e}, retrying...")
                import time; time.sleep(2)

    def _send_ws_command(self, command):
        try:
            if self.debug:
                print(f"[DEBUG] _send_ws_command sending: {command}")
            if self._ws and self._ws.connected:
                self._ws.send(json.dumps(command))
        except Exception as e:
            if self.debug:
                print(f"WebSocket send failed: {e}")

    def start(self):
        if self.debug:
            print("Starting robot...")
        self._stop_terminal_input = threading.Event()
        self._terminal_input_thread = threading.Thread(target=self._handle_terminal_input)
        self._terminal_input_thread.daemon = True
        self._terminal_input_thread.start()
        if self.speech:
            self.speech.prepare_for_listening()
        # Enter standby mode and begin wake word detection
        self._return_to_standby()

    def stop(self):
        if self.debug:
            print("Stopping robot...")
        self._stop_terminal_input.set()
        if self._terminal_input_thread:
            self._terminal_input_thread.join(timeout=2)
        self._cleanup()

    def _set_state(self, new_state: RobotState):
        """
        Set robot state and update LEDs
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

    # Wake word, transcription, and speech completion are now handled by SpeechController

    # Transcription and conversation logic handled by SpeechController and ConversationController

    # Speech completion handled by SpeechController

    def _return_to_standby(self):
        """Return to standby mode"""
        if self.debug:
            print("Returning to standby mode")
        # Stop speech recognition
        if self.speech:
            self.speech.speech_to_text.stop_listening()
        # Start wake word detection
        if self.speech:
            self.speech.wake_word.start_listening()
        # Set state last
        self._set_state(RobotState.STANDBY)

    def _handle_terminal_input(self):
        """Handle input from terminal"""
        while not self._stop_terminal_input.is_set():
            try:
                # Read input from terminal
                text = input()
                # Only process if in listening state
                if self._state == RobotState.LISTENING and text.strip():
                    # Process text same way as speech input
                    self.speech.on_transcription(text)
            except EOFError:
                break  # Exit if input stream is closed
            except Exception as e:
                if self.debug:
                    print(f"Error handling terminal input: {e}")

    def _on_audio_level(self, audio_level: float):
        """Handle real-time audio level updates from the audio module."""
        import time
        now = time.time()
        # Throttle: only send if 100ms have passed or value changed by >1 dB
        if not hasattr(self, '_last_audio_level_sent'):
            self._last_audio_level_sent = None
            self._last_audio_level_time = 0
        send = False
        if (
            self._last_audio_level_sent is None or
            abs(audio_level - self._last_audio_level_sent) > 1 or
            now - self._last_audio_level_time > 0.1
        ):
            send = True
        if send:
            self._last_audio_level_sent = audio_level
            self._last_audio_level_time = now
            if self.debug:
                print(f"[DEBUG] _on_audio_level sending dB: {audio_level}")
            self._send_ws_command({"type": "update_audio_level", "audio_level": float(audio_level)})
        else:
            if self.debug:
                print(f"[DEBUG] _on_audio_level throttled dB: {audio_level}")

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
