#!/usr/bin/env python3

import threading
import queue
import numpy as np
import platform
if platform.machine() not in ('armv6l', 'armv7l', 'aarch64'):
    import whisper
try:
    from google.cloud import speech as google_speech
except ImportError:
    google_speech = None
import io
import logging
from typing import Optional, Callable, Dict, List
import time

logger = logging.getLogger(__name__)

from .audio import AudioModule

class SpeechToTextModule:
    """Speech-to-text conversion using Whisper or Google STT (Pi Zero)"""
    def __init__(self, *args, **kwargs):
        self._transcription_callbacks = []
    def add_input_audio_level_callback(self, callback):
        """Register a callback for real-time input audio level (dB) via AudioModule."""
        if hasattr(self, 'audio') and hasattr(self.audio, 'add_input_audio_level_callback'):
            self.audio.add_input_audio_level_callback(callback)
        else:
            raise AttributeError("AudioModule is not initialized or does not support input audio level callbacks.")

    def add_output_audio_level_callback(self, callback):
        """Register a callback for real-time output audio level (dB) via AudioModule."""
        if hasattr(self, 'audio') and hasattr(self.audio, 'add_output_audio_level_callback'):
            self.audio.add_output_audio_level_callback(callback)
        else:
            raise AttributeError("AudioModule is not initialized or does not support output audio level callbacks.")

    """Speech-to-text conversion using Whisper"""
    
    # Audio level callbacks are now handled by AudioModule. Use audio_module.add_audio_level_callback().
    def register_command(self, command: str, callback):
        """Register a callback for a specific recognized command string."""
        if not hasattr(self, 'command_callbacks'):
            self.command_callbacks = {}
        self.command_callbacks[command] = callback
    
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 2048
    MIN_AUDIO_CHUNKS = 5  # Lowered for debugging: triggers processing quickly - 50
    # Suggestion: try values between 5 and 20 depending on environment and chunk size.
    # If transcriptions are too short, decrease this. If too long/wrong, increase.
    
    def __init__(self,
                 audio_module: Optional[AudioModule] = None,
                 language: str = "en",
                 debug: bool = False,
                 whisper_model=None,
                 backend: Optional[str] = None):
        self._lock = threading.RLock()
        self.transcription_in_progress = False
        """
        Initialize speech-to-text module
        
        Args:
            audio_module: AudioModule instance to use for audio handling. If None, creates new instance
            language: Language code for speech recognition
            debug: Enable debug output
            backend: Explicitly select backend (whisper or google). If None, auto-detect.
        """
        self.debug = debug
        self.language = language
        self._lock = threading.RLock()
        if self.debug:
            logger.debug("[SpeechToTextModule] Using threading.RLock for _lock (reentrant)")
        
        # Use provided audio module or create new one
        self.audio = audio_module if audio_module else AudioModule(debug=debug)
        # Register audio level callback if needed
        if hasattr(self, 'on_audio_level') and callable(getattr(self, 'on_audio_level')):
            self.audio.add_input_audio_level_callback(self.on_audio_level)
        
        # Backend selection
        if backend is not None:
            self.backend = backend.lower()
            logger.info(f"[SpeechToTextModule] Using backend: {self.backend}")
            if self.debug:
                logger.info(f"[SpeechToTextModule] Backend explicitly set to {self.backend}")
        else:
            # Pi Zero specific: Always prefer Google STT on Pi Zero
            pi_zero_detected = self._is_pi_zero()
            logger.info(f"[SpeechToTextModule] Pi Zero detection: {pi_zero_detected}")
            logger.info(f"[SpeechToTextModule] Available backends - whisper: {'whisper' in globals()}, google: {google_speech is not None}")
            
            if pi_zero_detected and google_speech is not None:
                self.backend = "google"
                logger.info("[SpeechToTextModule] Using backend: google (Pi Zero auto-detected)")
                if self.debug:
                    logger.info("[SpeechToTextModule] Pi Zero detected, forcing Google STT backend for performance.")
            elif 'whisper' in globals():
                self.backend = "whisper"
                if pi_zero_detected and google_speech is not None:
                    self.backend = "google"
                    logger.info("[SpeechToTextModule] Using backend: google (auto-detected)")
                    if self.debug:
                        logger.info("[SpeechToTextModule] Pi Zero detected, using Google STT backend.")
                else:
                    logger.info("[SpeechToTextModule] Using backend: whisper (default)")
                    if self.debug:
                        logger.info("[SpeechToTextModule] Using Whisper backend.")
            elif google_speech is not None:
                self.backend = "google"
                logger.info("[SpeechToTextModule] Using backend: google (fallback, no whisper)")
            else:
                logger.error("[SpeechToTextModule] No available STT backend (neither whisper nor google_speech found)")
                self.backend = None

        # Whisper model setup
        if self.backend == "whisper":
            if whisper_model is not None:
                self.whisper = whisper_model
                if self.debug:
                    logger.info("Injected Whisper model (test/mock)")
            else:
                try:
                    self.whisper = whisper.load_model("base")
                    if self.debug:
                        logger.info("Whisper model loaded")
                except Exception as e:
                    logger.error(f"Failed to initialize Whisper: {e}")
                    self.whisper = None
                    return
        else:
            self.whisper = None
            # Google STT client setup
            if google_speech is not None:
                self.gcloud_client = google_speech.SpeechClient()
            else:
                self.gcloud_client = None

        # Speech processing setup
        self.is_listening = False
        self._audio_buffer = []
        self._last_audio = time.time()
        self._process_thread = None
        self._transcription_callbacks: List[Callable[[str], None]] = []
        self._timeout_callbacks: List[Callable[[], None]] = []
        self._silence_timeout = 20.0  # Seconds of silence before full standby/idle timeout
        self._phrase_timeout = 1    # Seconds of silence to trigger phrase segmentation (endpointing)
        self._audio_threshold = -50  # dB threshold for speech detection (temporarily lowered for debug)
        self._buffering_active = False  # Only buffer after speech is detected
        # Pre-buffer: rolling buffer to capture audio before speech is detected
        from collections import deque
        # Calculate number of chunks for 1s pre-buffer
        pre_buffer_seconds = 1.0
        pre_buffer_chunks = int(pre_buffer_seconds * (self.device_sample_rate if hasattr(self, 'device_sample_rate') and self.device_sample_rate else self.SAMPLE_RATE) / self.CHUNK_SIZE)
        self._pre_buffer = deque(maxlen=pre_buffer_chunks)
        # Suggestion: try values between -50 and -30 for typical rooms. Too low = more noise; too high = missed speech.
        if self.debug:
            logger.debug(f"[SpeechToTextModule] Audio threshold set to {self._audio_threshold} dB")
        self._stream_id = None
        # Always expose audio_callback for tests
        self.audio_callback = getattr(self, '_test_audio_callback', self._audio_callback)

    def _is_pi_zero(self):
        # Detect Pi Zero by platform string
        return "armv6l" in platform.uname().machine or "raspberrypi" in platform.uname().node

    def add_transcription_callback(self, callback: Callable[[str], None]):
        """Add callback for transcribed text"""
        self._transcription_callbacks.append(callback)
        
    def add_timeout_callback(self, callback: Callable[[], None]):
        """Add callback for silence timeout"""
        self._timeout_callbacks.append(callback)

    def _set_transcription_in_progress(self, value: bool):
        with self._lock:
            self.transcription_in_progress = value
            logger.debug(f"[SpeechToTextModule] transcription_in_progress set to {value}")

    def is_transcription_in_progress(self):
        with self._lock:
            return self.transcription_in_progress

    def safe_notify_timeout_callbacks(self):
        with self._lock:
            if self.transcription_in_progress:
                logger.info("[SpeechToTextModule] Silence timeout ignored: transcription in progress")
                return
            for callback in self._timeout_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"[SpeechToTextModule] Error in timeout callback: {e}")
        
    def start_listening(self):
        """Start listening and converting speech to text"""
        with self._lock:
            if self.is_listening:
                if self.debug:
                    logger.warning("[SpeechToTextModule] Already listening!")
                return
            self.is_listening = True
            self._audio_buffer = []
            self._last_audio = time.time()
            self.transcription_in_progress = False
            if self.debug:
                logger.info("[SpeechToTextModule] start_listening called")
            # Start audio stream and processing thread
            self._process_thread = threading.Thread(target=self._process_audio)
            self._process_thread.start()
        
        # Use standard sample rate - AudioModule handles device compatibility
        self.device_sample_rate = 48000
        logger.info(f"[SpeechToTextModule] Using sample rate: {self.device_sample_rate} Hz")
        
        # Stop any existing processing thread
        if self._process_thread and self._process_thread.is_alive():
            if self.debug:
                logger.info("Waiting for processing thread to finish")
            self._process_thread.join(timeout=1)
        try:
            logger.info(f"[SpeechToTextModule] Creating audio stream with sample_rate={self.device_sample_rate}, chunk_size={self.CHUNK_SIZE}")
            self._stream_id = self.audio.create_stream(
                callback=self._audio_callback,
                rate=self.device_sample_rate,
                chunk_size=self.CHUNK_SIZE,
                format=AudioModule.FORMAT_INT16,  # Use int16 for input
                channels=1
            )
            if self.debug:
                logger.info("Starting speech recognition")
            self.audio.start_stream(self._stream_id)
            logger.info(f"[SpeechToTextModule] Audio stream started (id={self._stream_id})")
        except Exception as e:
            logger.error(f"Failed to start speech recognition: {e}")
            self.is_listening = False
            if hasattr(self, '_stream_id'):
                self._stream_id = None

                
    def stop_listening(self):
        """Stop listening for speech"""
        logger.debug("[SpeechToTextModule] stop_listening: ENTER")
        try:
            with self._lock:
                logger.debug("[SpeechToTextModule] stop_listening: acquired _lock")
                if not self.is_listening:
                    if self.debug:
                        logger.warning("[SpeechToTextModule] Not listening!")
                    logger.debug("[SpeechToTextModule] stop_listening: EXIT (was not listening)")
                    return
                self.is_listening = False
                self.transcription_in_progress = False
                if self.debug:
                    logger.info("[SpeechToTextModule] stop_listening called")
                stream_id = getattr(self, '_stream_id', None)
                stream_info = None
                logger.debug(f"[SpeechToTextModule] stop_listening: stream_id={stream_id}")
                if hasattr(self.audio, 'get_stream_info') and stream_id is not None:
                    logger.debug("[SpeechToTextModule] stop_listening: about to get stream_info")
                    stream_info = self.audio.get_stream_info(stream_id)
                    logger.debug(f"[SpeechToTextModule] stop_listening: got stream_info={stream_info}")
                if hasattr(self.audio, 'close_stream') and stream_id is not None:
                    logger.debug("[SpeechToTextModule] stop_listening: about to close_stream")
                    self.audio.close_stream(stream_id)
                    logger.debug("[SpeechToTextModule] stop_listening: closed stream")
                self._stream_id = None
                logger.debug("[SpeechToTextModule] stop_listening: set _stream_id to None")
            logger.debug("[SpeechToTextModule] stop_listening: EXIT (success)")
        except Exception as e:
            logger.error(f"[SpeechToTextModule] stop_listening: Exception: {e}", exc_info=True)
            stream_type = stream_info["type"] if stream_info else "unknown"
            device_index = stream_info["device_index"] if stream_info else None
            if self.debug:
                logger.info(f"[SpeechToTextModule] stop_listening: stream_id={stream_id}, type={stream_type}, device={device_index}")
            if stream_type == "input":
                if hasattr(self.audio, 'stop_stream') and stream_id is not None:
                    try:
                        self.audio.stop_stream(stream_id)
                    except Exception as e:
                        if self.debug:
                            logger.error(f"[SpeechToTextModule] Error stopping stream: {e}")
                if hasattr(self.audio, 'close_stream') and stream_id is not None:
                    try:
                        self.audio.close_stream(stream_id)
                    except Exception as e:
                        if self.debug:
                            logger.error(f"[SpeechToTextModule] Error closing stream: {e}")
                self._stream_id = None
                if self.debug:
                    logger.info("[SpeechToTextModule] Listening stopped and input stream closed.")
            else:
                if self.debug:
                    logger.info(f"[SpeechToTextModule] Not closing stream_id={stream_id} because type is not 'input' (type={stream_type})")
        # Process any remaining audio before stopping
        if self._audio_buffer and len(self._audio_buffer) >= self.MIN_AUDIO_CHUNKS:
            if self.debug:
                logger.info("Processing remaining audio before stopping")
            self._process_audio()
        self._audio_buffer = []  # Ensure buffer is cleared!
        # Notify timeout callbacks
        self.safe_notify_timeout_callbacks()
        
        # Clear state
        self._audio_buffer = []
        # self._last_audio = 0
        
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
                        logger.warning("Audio callback called but not listening (ndarray path)")
                        self._last_not_listening_log = now
                return (None, 0)
            self._audio_buffer.append(in_data)
            logger.debug(f"[SpeechToTextModule] Audio buffer appended (ndarray path), buffer size: {len(self._audio_buffer)}")
            self._process_audio()
            return (None, 0)

        if not self.is_listening:
            if self.debug:
                now = time.time()
                if not hasattr(self, '_last_not_listening_log') or now - self._last_not_listening_log > 2:
                    logger.warning("Audio callback called but not listening")
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
                    # logger.debug(f"[DEBUG] First 10 samples (float32): {audio_data[:10]}")
                    self._last_debug_samples_log = now
            # print(f"[SpeechToTextModule] Received {len(audio_data)} samples in audio callback")
            # Calculate audio level in dB
            if len(audio_data) > 0:
                rms = np.sqrt(np.mean(audio_data**2))
                db = 20 * np.log10(rms) if rms > 0 else -100
                msg = (f"[DEBUG] rms={rms:.5f}, max={np.max(np.abs(audio_data)):.5f}, db={db:.1f}")
                # print(msg.ljust(100), end='\r', flush=True)
                # print(f"[DEBUG] rms={rms:.5f}, max={np.max(np.abs(audio_data)):.5f}, db={db:.1f}")

                # print(f"\r[SpeechToTextModule] Audio dB: {db:.1f}, threshold: {self._audio_threshold}    ", end='', flush=True)
                # Call input audio level callbacks registered via AudioModule
                if hasattr(self, 'audio') and hasattr(self.audio, '_trigger_input_audio_level_callbacks'):
                    self.audio._trigger_input_audio_level_callbacks(db)
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
                            logger.info(f"[SpeechToTextModule] Speech detected, starting buffer with pre-buffer ({len(self._pre_buffer)} chunks)")
                            self._audio_buffer.append(audio_data)
                    else:
                        # Buffer all audio once speech started
                        self._audio_buffer.append(audio_data)
                        # logger.debug(f"[SpeechToTextModule] Buffering audio (buffer size: {len(self._audio_buffer)})")

                        # logger.debug(f"[SpeechToTextModule] Audio dB: {db:.1f}, threshold: {self._audio_threshold}")
                        if db > self._audio_threshold:
                            self._last_audio = time.time()
                        # Print buffer duration for diagnostics
                        elapsed = time.time() - self._last_audio
                        msg = f"[DEBUG] elapsed={elapsed:.2f}, phrase_timeout={self._phrase_timeout}, db={db:.1f}, buffering_active={self._buffering_active}"
                        # print(msg.ljust(100), end='\r', flush=True)
            # Silence endpointing logic: process phrase if silence detected
            elapsed = time.time() - self._last_audio
            # Phrase endpointing: process phrase after short silence
            with self._lock:
                buffer_len = len(self._audio_buffer)
            if elapsed > self._phrase_timeout and buffer_len > 0:
                with self._lock:
                    audio_concat = np.concatenate(self._audio_buffer)
                # Convert dB threshold to linear amplitude threshold
                # linear = 10 ** (dB / 20)
                linear_threshold = 10 ** (self._audio_threshold / 20)
                max_amplitude = np.max(np.abs(audio_concat))

                if max_amplitude > linear_threshold:
                    msg = f"[SpeechToTextModule] Silence detected for {elapsed:.2f}s, processing phrase."
                    logger.info(msg)
                    # logger.info(f"[SpeechToTextModule] Buffer details: size={len(self._audio_buffer)}, max_amplitude={max_amplitude:.6f}, threshold={linear_threshold:.6f}")
                    # logger.info(f"[SpeechToTextModule] Thread state: {getattr(self, '_process_thread', None)}")
                    if getattr(self, '_process_thread', None):
                        logger.info(f"[SpeechToTextModule] Process thread alive: {self._process_thread.is_alive()}")
                    if not getattr(self, '_process_thread', None) or not self._process_thread.is_alive():
                        logger.debug(f"[SpeechToTextModule] Starting _process_audio thread (buffer size: {len(self._audio_buffer)})")
                        self._process_thread = threading.Thread(target=self._process_audio)
                        self._process_thread.start()
                        logger.info(f"[SpeechToTextModule] Process thread started: {self._process_thread.name}")
                    else:
                        logger.warning(f"[SpeechToTextModule] Process thread already running, skipping new transcription")
                    self._buffering_active = False  # Reset to waiting for speech
                    # Clear pre-buffer after phrase
                    self._pre_buffer.clear()
                else:
                    if self.debug:
                        # Buffer is only silence, clear and reset
                        logger.info(f"[SpeechToTextModule] Silence detected for {elapsed:.2f}s, but buffer is silent. Clearing buffer. (max_amplitude={max_amplitude:.5f}, threshold={linear_threshold:.5f}, dB={self._audio_threshold})")
                    with self._lock:
                        self._audio_buffer = []
                    self._last_audio = time.time()
                    self._buffering_active = False
            # Standby/idle timeout logic (optional):
            if elapsed > self._silence_timeout:
                logger.warning(f"[SpeechToTextModule] Standby timeout reached after {elapsed:.2f}s, stopping listening.")
                if self.is_listening:
                    self.stop_listening()
                return (None, 0)

        except Exception as e:
            logger.error(f"[SpeechToTextModule] Error processing audio: {e}")
            logger.exception(f"[SpeechToTextModule] Full traceback in audio callback:")
        return (None, 0)  # Continue

    def _process_audio(self):
        import threading as _threading
        thread_name = _threading.current_thread().name
        with self._lock:
            buffer_len = len(self._audio_buffer)
        logger.info(f"[{thread_name}] === STARTING _process_audio (buffer size: {buffer_len}) ===")
        logger.info(f"[{thread_name}] transcription_in_progress: {self.transcription_in_progress}")
        logger.info(f"[{thread_name}] is_listening: {self.is_listening}")
        logger.info(f"[{thread_name}] backend: {self.backend}")
        if not self.is_listening:
            logger.warning(f"[{thread_name}] Called while not listening, skipping.")
            with self._lock:
                self._audio_buffer = []
            return
        import threading as _threading
        try:
            with self._lock:
                if len(self._audio_buffer) == 0:
                    logger.warning(f"[{thread_name}] No audio buffer to process.")
                    return
                audio_data = np.concatenate(self._audio_buffer)
                logger.info(f"[{thread_name}] Audio buffer concatenated: shape={audio_data.shape}, dtype={audio_data.dtype}")
                logger.info(f"[{thread_name}] Audio stats: min={audio_data.min():.6f}, max={audio_data.max():.6f}, mean={audio_data.mean():.6f}")
                self._audio_buffer = []
            # Ensure mono
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.float32 and np.max(np.abs(audio_data)) > 1.01:
                audio_data = audio_data / np.max(np.abs(audio_data))
            duration_sec = len(audio_data) / (self.device_sample_rate if hasattr(self, 'device_sample_rate') and self.device_sample_rate else self.SAMPLE_RATE)
            if duration_sec < 0.5:
                logger.warning(f"[{thread_name}] Audio buffer too short ({duration_sec:.3f}s), skipping transcription.")
                return
            
            logger.info(f"[{thread_name}] Audio duration: {duration_sec:.3f}s, proceeding with transcription")
            target_rate = self.SAMPLE_RATE
            if hasattr(self, 'device_sample_rate') and self.device_sample_rate and self.device_sample_rate != target_rate:
                try:
                    import scipy.signal
                    num_samples = int(duration_sec * target_rate)
                    audio_resampled = scipy.signal.resample(audio_data, num_samples)
                    audio_data = audio_resampled
                except Exception as e:
                    logger.error(f"[SpeechToTextModule] Resample error: {e}")
            # Google STT expects 16-bit PCM WAV bytes
            text = None
            if self.backend == "whisper":
                if not self.whisper:
                    logger.error(f"[{thread_name}] Whisper model not initialized!")
                    return
                logger.info(f"[{thread_name}] === STARTING WHISPER TRANSCRIPTION ===")
                start_time = time.time()
                self._set_transcription_in_progress(True)
                try:
                    logger.info(f"[{thread_name}] Calling whisper.transcribe()...")
                    result = self.whisper.transcribe(audio_data, language=self.language)
                    end_time = time.time()
                    logger.info(f"[{thread_name}] Whisper completed in {end_time - start_time:.2f}s")
                    text = result["text"]
                    logger.info(f"[{thread_name}] Whisper result: '{text}'")
                except Exception as e:
                    end_time = time.time()
                    logger.error(f"[{thread_name}] Whisper transcription error after {end_time - start_time:.2f}s: {e}")
                    logger.exception(f"[{thread_name}] Full traceback:")
            elif self.backend == "google" and self.gcloud_client is not None:
                logger.info(f"[{thread_name}] === STARTING GOOGLE STT TRANSCRIPTION (Pi Zero) ===")
                start_time = time.time()
                self._set_transcription_in_progress(True)
                logger.info(f"[{thread_name}] Pi Zero detected - using Google Cloud Speech backend")
                try:
                    import wave
                    logger.info(f"[{thread_name}] Converting audio to WAV format for Google STT...")
                    
                    # Pi Zero specific: Check audio data before conversion
                    logger.info(f"[{thread_name}] Pre-conversion audio stats: shape={audio_data.shape}, dtype={audio_data.dtype}")
                    logger.info(f"[{thread_name}] Pre-conversion range: [{audio_data.min():.6f}, {audio_data.max():.6f}]")
                    
                    wav_buf = io.BytesIO()
                    audio_int16 = np.clip(audio_data * 32767.0, -32768, 32767).astype(np.int16)
                    
                    # Pi Zero specific: Check converted audio
                    logger.info(f"[{thread_name}] Converted to int16: min={audio_int16.min()}, max={audio_int16.max()}")
                    logger.info(f"[{thread_name}] Zero-crossings: {np.sum(np.diff(np.sign(audio_int16)) != 0)}")
                    
                    with wave.open(wav_buf, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(target_rate)
                        wf.writeframes(audio_int16.tobytes())
                    wav_bytes = wav_buf.getvalue()
                    logger.info(f"[{thread_name}] WAV buffer created: {len(wav_bytes)} bytes ({len(wav_bytes)/1024:.1f} KB)")
                    
                    # Pi Zero specific: Check if we have reasonable audio data
                    if len(wav_bytes) < 1000:  # Less than 1KB seems suspicious
                        logger.warning(f"[{thread_name}] WAV buffer seems too small for Pi Zero: {len(wav_bytes)} bytes")
                    
                    # Create Google STT request
                    logger.info(f"[{thread_name}] Creating Google STT request objects...")
                    audio = google_speech.RecognitionAudio(content=wav_bytes)
                    config = google_speech.RecognitionConfig(
                        encoding=google_speech.RecognitionConfig.AudioEncoding.LINEAR16,
                        sample_rate_hertz=target_rate,
                        language_code=self.language if self.language else "en-US",
                        # Pi Zero specific: Enable enhanced models for better performance
                        enable_automatic_punctuation=True,
                        model="command_and_search"  # Better for short commands on Pi Zero
                    )
                    
                    logger.info(f"[{thread_name}] Google STT config: sample_rate={target_rate}, language={config.language_code}")
                    logger.info(f"[{thread_name}] Calling Google Cloud Speech recognize() (this may take time on Pi Zero)...")
                    
                    # Pi Zero specific: Add timeout warning after 10 seconds
                    import threading
                    def timeout_warning():
                        time.sleep(10)
                        if self.transcription_in_progress:
                            logger.warning(f"[{thread_name}] Google STT taking >10s on Pi Zero - may be network or resource issue")
                    
                    warning_thread = threading.Thread(target=timeout_warning, daemon=True)
                    warning_thread.start()
                    
                    response = self.gcloud_client.recognize(config=config, audio=audio)
                    end_time = time.time()
                    logger.info(f"[{thread_name}] Google STT completed in {end_time - start_time:.2f}s")
                    
                    # Check response validity
                    if not response.results:
                        logger.warning(f"[{thread_name}] Google STT returned empty results")
                        text = ""
                    else:
                        text = " ".join([result.alternatives[0].transcript for result in response.results])
                        logger.info(f"[{thread_name}] Google STT result: '{text}' (confidence: {response.results[0].alternatives[0].confidence:.2f})")
                        
                except Exception as e:
                    end_time = time.time()
                    logger.error(f"[{thread_name}] Google STT error after {end_time - start_time:.2f}s: {e}")
                    logger.exception(f"[{thread_name}] Full traceback:")
                    
                    # Pi Zero specific: Common issues
                    if "timeout" in str(e).lower():
                        logger.error(f"[{thread_name}] Pi Zero Google STT timeout - check network connection")
                    if "quota" in str(e).lower():
                        logger.error(f"[{thread_name}] Google Cloud quota exceeded - check billing/API key")
                    if "audio" in str(e).lower():
                        logger.error(f"[{thread_name}] Audio format issue - check microphone/input on Pi Zero")
            if text:
                if hasattr(self, 'command_callbacks') and isinstance(self.command_callbacks, dict):
                    cb = self.command_callbacks.get(text)
                    if cb:
                        try:
                            cb()
                        except Exception as e:
                            logger.error(f"[{_threading.current_thread().name}] Error in command callback: {e}")
                for callback in getattr(self, '_transcription_callbacks', []):
                    try:
                        callback(text)
                    except Exception as e:
                        logger.error(f"[{_threading.current_thread().name}] Error in transcription callback: {e}")
        except Exception as e:
            logger.error(f"[{thread_name}] Error processing audio: {e}")
            logger.exception(f"[{thread_name}] Full traceback:")
        finally:
            logger.info(f"[{thread_name}] === FINISHING _process_audio ===")
            with self._lock:
                self.transcription_in_progress = False
                logger.info(f"[{thread_name}] transcription_in_progress set to False")
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
                    logger.info("Closed speech recognition stream")
            except Exception as e:
                if self.debug:
                    logger.error(f"Error stopping speech recognition stream: {e}")
            self._stream_id = None
