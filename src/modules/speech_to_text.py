#!/usr/bin/env python3

import threading
import queue
import numpy as np
import whisper
from typing import Optional, Callable, Dict, List
import time

from .audio import AudioModule

class SpeechToTextModule:
    """Speech-to-text conversion using Whisper"""
    def add_audio_level_callback(self, callback):
        """Register a callback for real-time audio level (dB) via AudioModule."""
        if hasattr(self, 'audio') and hasattr(self.audio, 'add_audio_level_callback'):
            self.audio.add_audio_level_callback(callback)
        else:
            raise AttributeError("AudioModule is not initialized or does not support audio level callbacks.")

    """Speech-to-text conversion using Whisper"""
    
    # Audio level callbacks are now handled by AudioModule. Use audio_module.add_audio_level_callback().
    def register_command(self, command: str, callback):
        """Register a callback for a specific recognized command string."""
        if not hasattr(self, 'command_callbacks'):
            self.command_callbacks = {}
        self.command_callbacks[command] = callback
    
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 2048
    MIN_AUDIO_CHUNKS = 50  # ~2 seconds at 44100Hz, robust buffering
    # Suggestion: try values between 5 and 20 depending on environment and chunk size.
    # If transcriptions are too short, decrease this. If too long/wrong, increase.
    
    def __init__(self,
                 audio_module: Optional[AudioModule] = None,
                #  language: str = "en-US",
                 language: str = "en",
                 debug: bool = False,
                 whisper_model=None):
        """
        Initialize speech-to-text module
        
        Args:
            audio_module: AudioModule instance to use for audio handling. If None, creates new instance
            language: Language code for speech recognition
            debug: Enable debug output
        """
        self.debug = debug
        self.language = language
        self._lock = threading.Lock()
        
        # Use provided audio module or create new one
        self.audio = audio_module if audio_module else AudioModule(debug=debug)
        # Register audio level callback if needed
        if hasattr(self, 'on_audio_level') and callable(getattr(self, 'on_audio_level')):
            self.audio.add_audio_level_callback(self.on_audio_level)
        # Allow test to inject a mock whisper model
        if whisper_model is not None:
            self.whisper = whisper_model
            if self.debug:
                print("Injected Whisper model (test/mock)")
        else:
            try:
                self.whisper = whisper.load_model("base")
                if self.debug:
                    print("Whisper model loaded")
            except Exception as e:
                print(f"Failed to initialize Whisper: {e}")
                self.whisper = None
                return
            
        # Speech processing setup
        self.is_listening = False
        self._audio_buffer = []
        self._last_audio = time.time()
        self._process_thread = None
        self._transcription_callbacks: List[Callable[[str], None]] = []
        self._timeout_callbacks: List[Callable[[], None]] = []
        self._silence_timeout = 20.0  # Seconds of silence before full standby/idle timeout
        self._phrase_timeout = 0.8    # Seconds of silence to trigger phrase segmentation (endpointing)
        self._audio_threshold = -60  # dB threshold for speech detection (temporarily lowered for debug)
        self._buffering_active = False  # Only buffer after speech is detected
        # Pre-buffer: rolling buffer to capture audio before speech is detected
        from collections import deque
        # Calculate number of chunks for 1s pre-buffer
        pre_buffer_seconds = 1.0
        pre_buffer_chunks = int(pre_buffer_seconds * (self.device_sample_rate if hasattr(self, 'device_sample_rate') and self.device_sample_rate else self.SAMPLE_RATE) / self.CHUNK_SIZE)
        self._pre_buffer = deque(maxlen=pre_buffer_chunks)
        # Suggestion: try values between -50 and -30 for typical rooms. Too low = more noise; too high = missed speech.
        if self.debug:
            print(f"[SpeechToTextModule] Audio threshold set to {self._audio_threshold} dB")
        self._stream_id = None
        # Always expose audio_callback for tests
        self.audio_callback = getattr(self, '_test_audio_callback', self._audio_callback)

    def add_transcription_callback(self, callback: Callable[[str], None]):
        """Add callback for transcribed text"""
        self._transcription_callbacks.append(callback)
        
    def add_timeout_callback(self, callback: Callable[[], None]):
        """Add callback for silence timeout"""
        self._timeout_callbacks.append(callback)
        
    def start_listening(self):
        """Start listening and converting speech to text"""
        print("[SpeechToTextModule] start_listening called")
        if self.is_listening:
            if self.debug:
                print("Cannot start speech recognition: already listening")
            return
        # Reset state
        if self._stream_id is not None:
            try:
                self.audio.close_stream(self._stream_id)
                if self.debug:
                    print(f"Closed previous audio stream (id={self._stream_id})")
            except Exception as e:
                if self.debug:
                    print(f"Error closing existing stream: {e}")
            self._stream_id = None
        # Detect device sample rate
        self.device_sample_rate = None
        try:
            info = self.audio.get_device_info()
            if info and 'defaultSampleRate' in info:
                self.device_sample_rate = int(info['defaultSampleRate'])
                print(f"[SpeechToTextModule] Detected device sample rate: {self.device_sample_rate}")
            else:
                self.device_sample_rate = self.SAMPLE_RATE
        except Exception as e:
            print(f"[SpeechToTextModule] Could not detect device sample rate: {e}")
            self.device_sample_rate = self.SAMPLE_RATE
        # Stop any existing processing thread
        if self._process_thread and self._process_thread.is_alive():
            if self.debug:
                print("Waiting for processing thread to finish")
            self._process_thread.join(timeout=1)
        self.is_listening = True
        self._audio_buffer = []
        self._last_audio = time.time()
        self._process_thread = None
        try:
            print(f"[SpeechToTextModule] Creating audio stream with sample_rate={self.device_sample_rate}, chunk_size={self.CHUNK_SIZE}")
            self._stream_id = self.audio.create_stream(
                callback=self._audio_callback,
                rate=self.device_sample_rate,
                chunk_size=self.CHUNK_SIZE,
                format=AudioModule.FORMAT_INT16,  # Use int16 for input
                channels=1
            )
            if self.debug:
                print("Starting speech recognition")
            self.audio.start_stream(self._stream_id)
            print(f"[SpeechToTextModule] Audio stream started (id={self._stream_id})")
        except Exception as e:
            print(f"Failed to start speech recognition: {e}")
            self.is_listening = False
            if hasattr(self, '_stream_id'):
                self._stream_id = None

                
    def stop_listening(self):
        """Stop listening for speech"""
        # Always try to clean up stream regardless of state
        if not self.is_listening and not hasattr(self, '_stream_id'):
            if self.debug:
                print("Cannot stop speech recognition: not listening")
            return
        
        # Only trigger timeout callbacks if we were actually listening
        if self.is_listening:
            self.is_listening = False
            for callback in getattr(self, '_timeout_callbacks', []):
                try:
                    callback()
                except Exception as e:
                    if self.debug:
                        print(f"Error in timeout callback: {e}")
        else:
            self.is_listening = False
        
        # Process any remaining audio before stopping
        if self._audio_buffer and len(self._audio_buffer) >= self.MIN_AUDIO_CHUNKS:
            if self.debug:
                print("Processing remaining audio before stopping")
            self._process_audio()
        self._audio_buffer = []  # Ensure buffer is cleared!
        # Stop audio stream through AudioModule
        if getattr(self, '_stream_id', None) is not None:
            try:
                if self.debug:
                    print(f"[stop_listening] Calling close_stream for stream_id={self._stream_id}, is_listening={self.is_listening}")
                self.audio.close_stream(self._stream_id)
                if self.debug:
                    print("Closed speech recognition stream")
            except Exception as e:
                if self.debug:
                    print(f"Error stopping speech recognition stream: {e}")
            self._stream_id = None
        
        # Clear state
        self._audio_buffer = []
        self._last_audio = 0
        
        import threading
        if self._process_thread and self._process_thread != threading.current_thread():
            self._process_thread.join(timeout=1)
        self._process_thread = None
            
    def _audio_callback(self, in_data, frame_count=None, time_info=None, status_flags=None):
        # print("[SpeechToTextModule] _audio_callback called")
        # If called directly (as in tests), treat in_data as a numpy array chunk
        if isinstance(in_data, np.ndarray):
            if not self.is_listening:
                if self.debug:
                    now = time.time()
                    if not hasattr(self, '_last_not_listening_log') or now - self._last_not_listening_log > 2:
                        print("Audio callback called but not listening (ndarray path)")
                        self._last_not_listening_log = now
                return (None, 0)
            self._audio_buffer.append(in_data)
            print(f"[SpeechToTextModule] Audio buffer appended (ndarray path), buffer size: {len(self._audio_buffer)}")
            self._process_audio()
            return (None, 0)

        if not self.is_listening:
            if self.debug:
                now = time.time()
                if not hasattr(self, '_last_not_listening_log') or now - self._last_not_listening_log > 2:
                    print("Audio callback called but not listening")
                    self._last_not_listening_log = now
            return (None, 0)  # Continue
        try:
            # Convert raw bytes to numpy array (int16 to float32)
            audio_int16 = np.frombuffer(in_data, dtype=np.int16)
            audio_data = audio_int16.astype(np.float32) / 32768.0
            # Only print debug samples occasionally to avoid spamming
            if self.debug:
                now = time.time()
                if not hasattr(self, '_last_debug_samples_log') or now - self._last_debug_samples_log > 2:
                    print(f"[DEBUG] First 10 samples (float32): {audio_data[:10]}")
                    self._last_debug_samples_log = now
            # print(f"[SpeechToTextModule] Received {len(audio_data)} samples in audio callback")
            # Calculate audio level in dB
            if len(audio_data) > 0:
                rms = np.sqrt(np.mean(audio_data**2))
                db = 20 * np.log10(rms) if rms > 0 else -100
                msg = (f"[DEBUG] rms={rms:.5f}, max={np.max(np.abs(audio_data)):.5f}, db={db:.1f}")
                print(msg.ljust(100), end='\r', flush=True)
                # print(f"[DEBUG] rms={rms:.5f}, max={np.max(np.abs(audio_data)):.5f}, db={db:.1f}")

                # print(f"\r[SpeechToTextModule] Audio dB: {db:.1f}, threshold: {self._audio_threshold}    ", end='', flush=True)
                if hasattr(self, '_audio_level_callbacks'):
                    for callback in self._audio_level_callbacks:
                        try:
                            callback(db)
                        except Exception as e:
                            if self.debug:
                                print(f"Error in audio level callback: {e}")
                # Wait for speech before buffering
                with self._lock:
                    # Always pre-buffer audio
                    self._pre_buffer.append(audio_data)
                    if not self._buffering_active:
                        if db > self._audio_threshold:
                            self._buffering_active = True
                            self._last_audio = time.time()
                            # Start phrase buffer with pre-buffered audio
                            self._audio_buffer = list(self._pre_buffer)
                            print(f"[SpeechToTextModule] Speech detected, starting buffer with pre-buffer ({len(self._pre_buffer)} chunks)")
                            self._audio_buffer.append(audio_data)
                    else:
                        # Buffer all audio once speech started
                        self._audio_buffer.append(audio_data)
                        if db > self._audio_threshold:
                            self._last_audio = time.time()
                        # Print buffer duration for diagnostics
                        duration_sec = len(self._audio_buffer) * self.CHUNK_SIZE / (self.device_sample_rate if hasattr(self, 'device_sample_rate') and self.device_sample_rate else self.SAMPLE_RATE)
                        elapsed = time.time() - self._last_audio
                        msg = f"[DEBUG] elapsed={elapsed:.2f}, phrase_timeout={self._phrase_timeout}, db={db:.1f}, buffering_active={self._buffering_active}"
                        print(msg.ljust(100), end='\r', flush=True)
            # Silence endpointing logic: process phrase if silence detected
            elapsed = time.time() - self._last_audio
            # Phrase endpointing: process phrase after short silence
            with self._lock:
                buffer_len = len(self._audio_buffer)
            if elapsed > self._phrase_timeout and buffer_len > 0:
                with self._lock:
                    audio_concat = np.concatenate(self._audio_buffer)
                if np.max(np.abs(audio_concat)) > 0.01:  # adjust threshold as needed
                    print(f"[SpeechToTextModule] Silence detected for {elapsed:.2f}s, processing phrase.")
                    if not getattr(self, '_process_thread', None) or not self._process_thread.is_alive():
                        self._process_thread = threading.Thread(target=self._process_audio)
                        self._process_thread.start()
                    self._buffering_active = False  # Reset to waiting for speech
                    # Clear pre-buffer after phrase
                    self._pre_buffer.clear()
                else:
                    # Buffer is only silence, clear and reset
                    print(f"[SpeechToTextModule] Silence detected for {elapsed:.2f}s, but buffer is silent. Clearing buffer.")
                    with self._lock:
                        self._audio_buffer = []
                    self._last_audio = time.time()
                    self._buffering_active = False
            # Standby/idle timeout logic (optional):
            if elapsed > self._silence_timeout:
                print(f"[SpeechToTextModule] Standby timeout reached after {elapsed:.2f}s, stopping listening.")
                if self.is_listening:
                    self.stop_listening()
                return (None, 0)

        except Exception as e:
            print(f"[SpeechToTextModule] Error processing audio: {e}")
        return (None, 0)  # Continue

    def _process_audio(self):
        with self._lock:
            buffer_len = len(self._audio_buffer)
        print(f"[SpeechToTextModule] _process_audio called (buffer size: {buffer_len})")
        if not self.is_listening:
            if self.debug:
                print("[_process_audio] Called while not listening, skipping.")
            with self._lock:
                self._audio_buffer = []
            return
        if not self.whisper:
            print("[SpeechToTextModule] Whisper model not initialized!")
            return
        import threading as _threading
        try:
            # For test compatibility: process if buffer has any audio
            with self._lock:
                if len(self._audio_buffer) == 0:
                    print(f"[{_threading.current_thread().name}] No audio buffer to process.")
                    return
                # Convert buffer to numpy array
                audio_data = np.concatenate(self._audio_buffer)
                self._audio_buffer = []  # Clear buffer after reading

            # Ensure mono (if multi-channel)
            if audio_data.ndim > 1:
                print(f"[DEBUG] Converting multi-channel ({audio_data.shape}) audio to mono")
                audio_data = np.mean(audio_data, axis=1)

            # Ensure float32 in [-1, 1]
            if audio_data.dtype == np.int16:
                print("[DEBUG] Converting int16 to float32 [-1, 1]")
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.float32:
                # Check if it's already in [-1, 1]
                if np.max(np.abs(audio_data)) > 1.01:
                    print("[WARNING] Float32 audio not in [-1, 1], normalizing")
                    audio_data = audio_data / np.max(np.abs(audio_data))

            # Diagnostics: print buffer stats
            duration_sec = len(audio_data) / (self.device_sample_rate if hasattr(self, 'device_sample_rate') and self.device_sample_rate else self.SAMPLE_RATE)
            print(f"[{_threading.current_thread().name}] Audio buffer stats: len={len(audio_data)}, duration={duration_sec:.3f}s, dtype={audio_data.dtype}, min={np.min(audio_data):.4f}, max={np.max(audio_data):.4f}, mean={np.mean(audio_data):.4f}")
            # Safeguard: skip if too short
            if duration_sec < 0.5:
                print(f"[WARNING] Audio buffer too short ({duration_sec:.3f}s), skipping WAV write and transcription.")
                self._audio_buffer = []
                return
            # Resample if needed
            target_rate = self.SAMPLE_RATE
            if hasattr(self, 'device_sample_rate') and self.device_sample_rate and self.device_sample_rate != target_rate:
                try:
                    import scipy.signal
                    num_samples = int(duration_sec * target_rate)
                    audio_resampled = scipy.signal.resample(audio_data, num_samples)
                    print(f"[SpeechToTextModule] Resampled audio from {self.device_sample_rate} Hz to {target_rate} Hz (len {len(audio_data)} -> {len(audio_resampled)})")
                    audio_data = audio_resampled
                except Exception as e:
                    print(f"[SpeechToTextModule] Resample error: {e}")
            # Save to WAV for offline listening (int16 for easy playback)
            try:
                import wave
                wav_path = "debug_transcription_input.wav"
                # Scale back to int16 for debug WAV
                audio_int16 = np.clip(audio_data * 32767.0, -32768, 32767).astype(np.int16)
                with wave.open(wav_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # int16 = 2 bytes
                    wf.setframerate(target_rate)
                    wf.writeframes(audio_int16.tobytes())
                print(f"[DEBUG] Saved audio buffer to {wav_path}")
            except Exception as e:
                print(f"[DEBUG] Failed to save debug WAV: {e}")

            # Ensure Whisper input is float32 in [-1, 1]
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            audio_data = np.clip(audio_data, -1.0, 1.0)

            print(f"[{_threading.current_thread().name}] Processing {len(audio_data)} samples.")
            # Transcribe
            print(f"[{_threading.current_thread().name}] Transcribing audio...")
            result = self.whisper.transcribe(audio_data, language=self.language)
            text = result["text"]
            print(f"[{_threading.current_thread().name}] Whisper transcription result: '{text}'")
            # Call command callback if text matches a registered command
            if hasattr(self, 'command_callbacks') and isinstance(self.command_callbacks, dict):
                cb = self.command_callbacks.get(text)
                if cb:
                    try:
                        print(f"[{_threading.current_thread().name}] Invoking command callback for text: '{text}'")
                        cb()
                    except Exception as e:
                        print(f"[{_threading.current_thread().name}] Error in command callback: {e}")
            # Notify transcription callbacks
            print(f"[{_threading.current_thread().name}] Transcription callbacks: {getattr(self, '_transcription_callbacks', [])}")
            for callback in getattr(self, '_transcription_callbacks', []):
                try:
                    print(f"[{_threading.current_thread().name}] Invoking transcription callback with text: '{text}' (callback: {callback})")
                    callback(text)
                except RuntimeError as e:
                    print(f"[{_threading.current_thread().name}] RuntimeError in transcription callback: {e}")
                except Exception as e:
                    print(f"[{_threading.current_thread().name}] Error in transcription callback: {e}")
        except Exception as e:
            print(f"[{_threading.current_thread().name}] Error processing audio: {e}")
        finally:
            # Clear audio buffer
            self._audio_buffer = []
            
    def cleanup(self):
        """Clean up resources"""
        # Stop listening if active
        if self.is_listening:
            self.stop_listening()
        
        # Clean up Whisper
        if self.whisper is not None:
            del self.whisper
            self.whisper = None
        
        # Clean up audio stream (for test compatibility)
        if getattr(self, "_stream_id", None) is not None:
            try:
                # Always call stop_stream first if available
                if hasattr(self.audio, 'stop_stream'):
                    try:
                        self.audio.stop_stream(self._stream_id)
                    except Exception:
                        pass
                # Then call close_stream if available
                if hasattr(self.audio, 'close_stream'):
                    try:
                        self.audio.close_stream(self._stream_id)
                    except Exception:
                        pass
                if self.debug:
                    print("Closed speech recognition stream")
            except Exception as e:
                if self.debug:
                    print(f"Error stopping speech recognition stream: {e}")
            self._stream_id = None
