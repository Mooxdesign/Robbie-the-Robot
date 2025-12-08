#!/usr/bin/env python3

import os
import sys
import time
import queue
import numpy as np
import pyaudio
import threading
import logging
from typing import Optional, Callable, List, Dict, Tuple

from config import Config

import wave

logger = logging.getLogger(__name__)

class AudioModule:
    """Core audio module for managing audio devices, streams, and routing"""
    
    # Common audio formats
    FORMAT_FLOAT32 = pyaudio.paFloat32
    FORMAT_INT16 = pyaudio.paInt16
    
    def __init__(self, debug: bool = False):
        self._input_audio_level_callbacks: List[Callable[[float], None]] = []
        self._output_audio_level_callbacks: List[Callable[[float], None]] = []
        """
        Initialize audio module
        
        Args:
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        
        # Load config
        config = Config()
        self.default_rate = config.get('audio', 'rate', default=44100)
        self.default_chunk_size = config.get('audio', 'chunk_size', default=1024)
        self.default_channels = config.get('audio', 'channels', default=1)
        self.default_format = self.FORMAT_INT16  # Use int16 for compatibility
        
        # Audio state
        self._pyaudio = None
        self._streams: Dict[str, Dict] = {}  # Store active streams by ID
        
        # Initialize PyAudio
        self._initialize_pyaudio()

        # Debug: List and show selected audio input device
        if self.debug and self._pyaudio:
            logger.info("\n[AudioModule] Listing available audio input devices:")
            for i in range(self._pyaudio.get_device_count()):
                try:
                    dev_info = self._pyaudio.get_device_info_by_index(i)
                    if dev_info.get('maxInputChannels', 0) > 0:
                        logger.info(f"  [{i}] {dev_info['name']} (inputs: {dev_info.get('maxInputChannels', 0)})")
                except Exception as e:
                    logger.error(f"  Error getting device {i} info: {e}")
            try:
                device_info = self._pyaudio.get_default_input_device_info()
                self.input_device_index = device_info['index']
                logger.info(f"[AudioModule] Using audio input device: {device_info['name']} (index: {device_info['index']})")
                logger.info(f"  [AudioModule] Device default sample rate: {device_info['defaultSampleRate']} Hz")
            except Exception as e:
                logger.error(f"[AudioModule] Error getting selected device info: {e}")

        # Start output audio monitoring thread if output_device_index is provided
        self.output_device_index = self.get_first_stereo_mix_device_index()
        logger.info(f"[AudioModule] Using audio output device: {self.output_device_index}")

    def _output_monitor_loop(self, stop_event=None):
        """
        Monitor the output (loopback/Stereo Mix) device for real audio output levels and trigger callbacks.
        Accepts a stop_event to allow clean shutdown when switching devices.
        """
        try:
            # Use the device's default sample rate to reduce host errors on Windows
            open_rate = self.default_rate
            try:
                if self.output_device_index is not None:
                    dev_info = self._pyaudio.get_device_info_by_index(self.output_device_index)
                    open_rate = int(dev_info.get('defaultSampleRate', self.default_rate) or self.default_rate)
            except Exception:
                open_rate = self.default_rate

            stream = self._pyaudio.open(
                format=self.default_format,
                channels=1,
                rate=open_rate,
                input=True,
                input_device_index=self.output_device_index,
                frames_per_buffer=self.default_chunk_size
            )
            if self.debug:
                logger.info(f"[AudioModule] Output monitor started on device index {self.output_device_index} @ {open_rate} Hz")
            logger.info("[AudioModule] _output_monitor_loop is running.")
            while not stop_event.is_set():
                data = stream.read(self.default_chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                rms = np.sqrt(np.mean(audio_data ** 2))
                db = 20 * np.log10(rms) if rms > 0 else -100
                self._trigger_output_audio_level_callbacks(db)
            stream.stop_stream()
            stream.close()
            if self.debug:
                logger.info(f"[AudioModule] Output monitor thread stopped for device index {self.output_device_index}")
        except Exception as e:
            # Disable monitoring for this session to avoid repeated errors
            try:
                if hasattr(self, '_output_monitor_stop_event') and stop_event is not None:
                    stop_event.set()
                # Mark device as unavailable to prevent restarts until explicitly changed
                self.output_device_index = None
            except Exception:
                pass
            logger.warning(f"[AudioModule] Output monitor disabled: {e}")


    def add_input_audio_level_callback(self, callback: Callable[[float], None]) -> None:
        """Register a callback for real-time input audio level (dB)."""
        self._input_audio_level_callbacks.append(callback)

    def add_output_audio_level_callback(self, callback: Callable[[float], None]) -> None:
        """Register a callback for real-time output audio level (dB)."""
        self._output_audio_level_callbacks.append(callback)

    def remove_output_audio_level_callback(self, callback: Callable[[float], None]) -> None:
        """Remove a callback for real-time output audio level (dB)."""
        if callback in self._output_audio_level_callbacks:
            self._output_audio_level_callbacks.remove(callback)

    def _trigger_input_audio_level_callbacks(self, audio_level: float) -> None:
        """Trigger all registered input audio level callbacks with the given dB level."""
        for callback in self._input_audio_level_callbacks:
            try:
                callback(audio_level)
            except Exception as e:
                if self.debug:
                    logger.exception(f"Error in input audio level callback: {e}")

    def _trigger_output_audio_level_callbacks(self, audio_level: float) -> None:
        """Trigger all registered output audio level callbacks with the given dB level."""
        for callback in self._output_audio_level_callbacks:
            try:
                callback(audio_level)
            except Exception as e:
                if self.debug:
                    logger.exception(f"Error in output audio level callback: {e}")
        
    def _initialize_pyaudio(self):
        try:
            self._pyaudio = pyaudio.PyAudio()
            if self.debug:
                logger.info("PyAudio initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PyAudio: {e}")
            
    def list_devices(self):
        """List available audio devices"""
        if not self._pyaudio:
            return
            
        logger.info("Available audio devices:")
        for i in range(self._pyaudio.get_device_count()):
            try:
                dev_info = self._pyaudio.get_device_info_by_index(i)
                logger.info(f"{i}: {dev_info['name']} (inputs: {dev_info.get('maxInputChannels', 0)})")
            except Exception as e:
                logger.error(f"Error getting device {i} info: {e}")
        logger.info("")
        
    def get_device_info(self):
        """Get info about current audio device"""
        if not self._pyaudio:
            return None
            
        try:
            device_info = self._pyaudio.get_device_info_by_index(self.input_device_index) if self.input_device_index is not None else self._pyaudio.get_default_input_device_info()
            logger.info("Using audio input device:")
            logger.info(f"  Name: {device_info['name']}")
            logger.info(f"  Index: {device_info['index']}")
            logger.info(f"  Sample Rate: {int(device_info['defaultSampleRate'])} Hz")
            logger.info(f"  Max Input Channels: {device_info['maxInputChannels']}")
            logger.info("")
            return device_info
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return None
            
    def create_stream(self, 
                     callback: Callable[[np.ndarray], None],
                     rate: Optional[int] = None,
                     channels: Optional[int] = None,
                     format: Optional[int] = None,
                     chunk_size: Optional[int] = None,
                     input: bool = True,
                     output: bool = False) -> str:
        """
        Create a new audio stream with specified parameters
        
        Args:
            callback: Function to call with audio data
            rate: Sample rate (Hz)
            channels: Number of channels
            format: Audio format (e.g. FORMAT_FLOAT32)
            chunk_size: Frames per buffer
            input: Enable input
            output: Enable output
            
        Returns:
            Stream ID string
        """
        if not self._pyaudio:
            raise RuntimeError("Audio system not initialized")
            
        # Use defaults if not specified
        rate = rate or self.default_rate
        channels = channels or self.default_channels
        format = format or self.default_format  # Should be FORMAT_INT16 for input
        chunk_size = chunk_size or self.default_chunk_size
        
        def audio_callback(audio_data, frame_count, time_info, status):
            callback(audio_data, frame_count, time_info, status)
            # Convert bytes to numpy array (assuming 16-bit audio)
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            # Calculate audio level in dB
            if len(audio_np) > 0:
                rms = np.sqrt(np.mean(audio_np ** 2))
                db = 20 * np.log10(rms + 1e-10)  # add epsilon to avoid log(0)
                # if self.debug:
                #     logger.info(f"\rAudio level: {db:.1f} dB", end="")
            return (None, pyaudio.paContinue)
        
        # Determine stream type and device index
        if input and not output:
            stream_type = "input"
            device_index = self.input_device_index
        elif output and not input:
            stream_type = "output"
            device_index = self.output_device_index
        elif input and output:
            stream_type = "duplex"
            device_index = f"in:{self.input_device_index}|out:{self.output_device_index}"
        else:
            stream_type = "unknown"
            device_index = None

        # Create stream
        stream_id = f"{rate}_{channels}_{format}_{chunk_size}_{input}_{output}"
        stream = self._pyaudio.open(format=format,
                               channels=channels,
                               rate=rate,
                               input=input,
                               output=output,
                               frames_per_buffer=chunk_size,
                               stream_callback=audio_callback)
        logger.info(f"[AudioModule] Created stream id={stream_id} type={stream_type} device={device_index} rate={rate}, channels={channels}, format={format}, chunk_size={chunk_size}")
        # Store stream with metadata
        self._streams[stream_id] = {
            "stream": stream,
            "callback": callback,
            "type": stream_type,
            "device_index": device_index
        }
        
        return stream_id
        
    def start_stream(self, stream_id: str):
        """
        Start an audio stream
        
        Args:
            stream_id: ID of stream to start
        """
        if stream_id not in self._streams:
            raise ValueError(f"Unknown stream ID: {stream_id}")
            
        stream = self._streams[stream_id]["stream"]
        stream.start_stream()
        
    def stop_stream(self, stream_id: str):
        """
        Pause an audio stream (can be resumed with start_stream).
        Args:
            stream_id: ID of stream to pause
        """
        if stream_id not in self._streams:
            raise ValueError(f"Unknown stream ID: {stream_id}")
        stream = self._streams[stream_id]["stream"]
        try:
            stream.stop_stream()
        except Exception as e:
            if self.debug:
                logger.error(f"Error stopping stream: {e}")

    def close_stream(self, stream_id: str):
        """
        Stop (if needed) and close an audio stream, permanently releasing resources.
        Args:
            stream_id: ID of stream to close
        """
        if stream_id not in self._streams:
            raise ValueError(f"Unknown stream ID: {stream_id}")
        stream_info = self._streams[stream_id]
        stream = stream_info["stream"]
        stream_type = stream_info.get("type", "unknown")
        device_index = stream_info.get("device_index", None)
        # Stop if not already stopped
        try:
            if stream.is_active():
                stream.stop_stream()
        except Exception:
            pass
        try:
            stream.close()
        except Exception as e:
            if self.debug:
                logger.error(f"Error closing stream: {e}")
        finally:
            if self.debug:
                logger.info(f"[AudioModule] Closed stream (id={stream_id}) type={stream_type} device={device_index}")
            del self._streams[stream_id]

        
    def get_stream_info(self, stream_id: str):
        """
        Retrieve metadata for a given stream (type and device index).
        Returns a dict with keys: type, device_index. Returns None if not found.
        """
        info = self._streams.get(stream_id)
        if info is None:
            return None
        return {
            "type": info.get("type", "unknown"),
            "device_index": info.get("device_index", None)
        }

    def get_volume(self, signal: np.ndarray) -> float:
        """Compute RMS volume of an audio signal."""
        if not isinstance(signal, np.ndarray):
            raise ValueError("Input signal must be a numpy array")
        rms = np.sqrt(np.mean(np.square(signal)))
        return float(rms)

    def get_frequency(self, signal: np.ndarray) -> float:
        """Estimate the dominant frequency of an audio signal using FFT."""
        if not isinstance(signal, np.ndarray):
            raise ValueError("Input signal must be a numpy array")
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal))
        idx = np.argmax(np.abs(fft))
        freq = abs(freqs[idx])
        return float(freq)

    def play_sound(self, filename: str) -> None:
        """Play a WAV sound file."""
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: {filename}")
        with wave.open(filename, 'rb') as wf:
            stream = self._pyaudio.open(
                format=self._pyaudio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            stream.start_stream()
            data = wf.readframes(wf.getnframes())
            stream.write(data)
            stream.stop_stream()
            stream.close()

    def record(self, duration: float = 1.0) -> bytes:
        """Record audio for a given duration (seconds)."""
        if duration <= 0:
            raise ValueError("Duration must be positive")
        stream = self._pyaudio.open(
            format=self.FORMAT_INT16,
            channels=1,
            rate=self.default_rate,
            input=True,
            frames_per_buffer=self.default_chunk_size
        )
        frames = []
        num_frames = int(self.default_rate / self.default_chunk_size * duration)
        for _ in range(num_frames):
            data = stream.read(self.default_chunk_size)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        return b''.join(frames)

    def cleanup(self) -> None:
        """Clean up resources"""
        logger.info("Cleaning up audio resources...")

        # Stop output monitor thread
        if hasattr(self, '_output_monitor_stop_event'):
            self._output_monitor_stop_event.set()
        if hasattr(self, '_output_monitor_thread') and self._output_monitor_thread.is_alive():
            self._output_monitor_thread.join(timeout=2) # Wait for thread to finish

        for stream_id in list(self._streams.keys()):
            stream = self._streams[stream_id]["stream"]
            try:
                stream.stop_stream()
            except Exception:
                pass
            try:
                stream.close()
            except Exception as e:
                if self.debug:
                    logger.error(f"Error closing stream {stream_id}: {e}")
            del self._streams[stream_id]
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
                logger.info("PyAudio terminated")
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")
            self._pyaudio = None

    def start_monitoring(self):
        """Starts the audio output monitoring thread."""
        if self.output_device_index is not None:
            self._output_monitor_stop_event = threading.Event()
            self._output_monitor_thread = threading.Thread(target=self._output_monitor_loop, args=(self._output_monitor_stop_event,), daemon=True)
            self._output_monitor_thread.start()
            logger.info(f"[AudioModule] Started monitoring output device index {self.output_device_index}")
        else:
            logger.info("[AudioModule] No Stereo Mix/loopback device available; output monitoring disabled.")

    def get_first_stereo_mix_device_index(self) -> Optional[int]:
        """Compatibility shim: Return the first Stereo Mix device index, or None if unavailable."""
        devices = self.list_stereo_mix_devices()
        if devices:
            return devices[0][0]
        return None

    def list_stereo_mix_devices(self):
        """Return a list of (index, name) for all Stereo Mix devices."""
        if not self._pyaudio:
            return []
        devices = []
        for i in range(self._pyaudio.get_device_count()):
            dev_info = self._pyaudio.get_device_info_by_index(i)
            if 'loopback' in dev_info['name'].lower() or 'stereo mix' in dev_info['name'].lower():
                devices.append((i, dev_info['name']))
        return devices

    def set_output_device_index(self, index: int):
        """Set the output device index and robustly restart the output monitor thread."""
        with self._lock:
            self.output_device_index = index
            # Stop old monitor thread if running
            if hasattr(self, '_output_monitor_stop_event'):
                self._output_monitor_stop_event.set()
            if hasattr(self, '_output_monitor_thread') and self._output_monitor_thread.is_alive():
                self._output_monitor_thread.join(timeout=2)
            # Start new monitor thread
            self._output_monitor_stop_event = threading.Event()
            self._output_monitor_thread = threading.Thread(target=self._output_monitor_loop, args=(self._output_monitor_stop_event,), daemon=True)
            self._output_monitor_thread.start()
            if self.debug:
                logger.info(f"[AudioModule] Output monitor switched to device index {index}")
            # State update callback for frontend
            if hasattr(self, 'state_update_callback') and self.state_update_callback:
                devices = self.list_stereo_mix_devices()
                dev_name = None
                for idx, name in devices:
                    if idx == index:
                        dev_name = name
                        break
                self.state_update_callback({
                    "type": "update_audio_output_device",
                    "output_device_index": index,
                    "output_device_name": dev_name
                })


    def cycle_stereo_mix_device(self):
        """Cycle to the next available Stereo Mix device."""
        devices = self.list_stereo_mix_devices()
        if not devices:
            return None
        current = self.output_device_index
        indices = [idx for idx, _ in devices]
        if current in indices:
            idx = indices.index(current)
            next_idx = (idx + 1) % len(indices)
        else:
            next_idx = 0
        next_device = devices[next_idx]
        self.set_output_device_index(next_device[0])
        return next_device