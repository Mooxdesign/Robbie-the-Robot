#!/usr/bin/env python3

import sys
import os
import time
import threading
import colorsys
import numpy as np
from typing import Tuple, List, Optional

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import Config
from utils.hardware import LED_AVAILABLE

if LED_AVAILABLE:
    from unicornhatmini import UnicornHATMini
    print("Unicorn HAT Mini detected")
else:
    print("No LED matrix detected - running in simulation mode")
    from simulation.hardware import SimulatedUnicornHATMini as UnicornHATMini

class LedsModule:
    """
    Controls the Unicorn pHAT LED matrix with various patterns and animations
    """
    
    def __init__(self, brightness: float = 0.5, debug: bool = False):
        self.current_color = (0, 0, 0)
        """
        Initialize LED module
        
        Args:
            brightness: LED brightness (0.0 to 1.0)
            debug: Enable debug output
        """
        self.debug = debug
        self._lock = threading.Lock()
        self.width = Config().get('lights', 'width', default=8)
        self.height = Config().get('lights', 'height', default=4)
        
        # Initialize LED hardware
        try:
            self.unicorn = UnicornHATMini()
            self.unicorn.set_brightness(brightness)
            if self.debug:
                print("LED matrix initialized")
        except Exception as e:
            print(f"Failed to initialize LED matrix: {e}")
            self.unicorn = None
            
        # Animation state
        self.current_animation = None
        self.animation_thread = None
        self.is_animating = False
        
        # Pattern buffers
        self.buffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.prev_buffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Audio visualization state
        self.max_volume = float('-inf')
        self.min_volume = float('inf')
        self.volume_decay = 0.05  # How quickly volume range adapts
        self.volume_smoothing = 0.3  # Smoothing factor for volume changes
        self.last_volume = 0
        
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int):
        """Set color of a single pixel"""
        with self._lock:
            if 0 <= x < self.width and 0 <= y < self.height:
                self.buffer[y, x] = [r, g, b]
                if self.unicorn:
                    self.unicorn.set_pixel(x, y, r, g, b)
    
    def set_all(self, r: int, g: int, b: int):
        """Set all pixels to the same color"""
        self.requested_color = (r, g, b)
        brightness = getattr(self.unicorn, 'brightness', 1.0) if hasattr(self, 'unicorn') and self.unicorn else 1.0
        scaled = (round(r * brightness), round(g * brightness), round(b * brightness))
        self.current_color = scaled
        with self._lock:
            self.buffer = np.full((self.height, self.width, 3), [r, g, b], dtype=np.uint8)
            if self.unicorn:
                for y in range(self.height):
                    for x in range(self.width):
                        self.unicorn.set_pixel(x, y, *scaled)
    
    def clear(self):
        """Turn off all pixels"""
        self.set_all(0, 0, 0)
        self.show()
    
    def show(self):
        """Update the display with current buffer"""
        if self.unicorn:
            self.unicorn.show()
    
    def start_animation(self, animation_name: str, **kwargs):
        """
        Start a predefined animation
        
        Args:
            animation_name: Name of the animation to run
            **kwargs: Animation-specific parameters
        """
        if self.is_animating:
            self.stop_animation()
            
        animation_map = {
            'rainbow': self._rainbow_animation,
            'pulse': self._pulse_animation,
            'wave': self._wave_animation,
            'sparkle': self._sparkle_animation
        }
        
        if animation_name in animation_map:
            self.is_animating = True
            self.current_animation = animation_name
            self.animation_thread = threading.Thread(
                target=animation_map[animation_name],
                kwargs=kwargs,
                daemon=True
            )
            self.animation_thread.start()
            if self.debug:
                print(f"Started animation: {animation_name}")
    
    def stop_animation(self):
        """Stop current animation"""
        self.is_animating = False
        if self.animation_thread:
            self.animation_thread.join(timeout=1)
            self.animation_thread = None
        if self.debug:
            print("Animation stopped")
    
    def _rainbow_animation(self, speed: float = 0.01):
        """Rainbow color cycle animation"""
        hue = 0
        while self.is_animating:
            hue = (hue + speed) % 1.0
            rgb = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
            self.set_all(*rgb)
            self.show()
            time.sleep(0.05)
    
    def _pulse_animation(self, color: Tuple[int, int, int] = (255, 0, 0), speed: float = 0.05):
        """Pulsing brightness animation"""
        brightness = 0
        direction = 1
        while self.is_animating:
            brightness = max(0, min(1, brightness + direction * speed))
            if brightness >= 1 or brightness <= 0:
                direction *= -1
            r = int(color[0] * brightness)
            g = int(color[1] * brightness)
            b = int(color[2] * brightness)
            self.set_all(r, g, b)
            self.show()
            time.sleep(0.05)
    
    def _wave_animation(self, color: Tuple[int, int, int] = (0, 0, 255), speed: float = 0.1):
        """Horizontal wave animation"""
        phase = 0
        while self.is_animating:
            for x in range(self.width):
                brightness = (np.sin(phase + x * 0.5) + 1) / 2
                r = int(color[0] * brightness)
                g = int(color[1] * brightness)
                b = int(color[2] * brightness)
                for y in range(self.height):
                    self.set_pixel(x, y, r, g, b)
            self.show()
            phase += speed
            time.sleep(0.05)
    
    def _sparkle_animation(self, color: Tuple[int, int, int] = (255, 255, 255), 
                         density: float = 0.1):
        """Random sparkling animation"""
        while self.is_animating:
            self.clear()
            for y in range(self.height):
                for x in range(self.width):
                    if np.random.random() < density:
                        self.set_pixel(x, y, *color)
            self.show()
            time.sleep(0.05)
    
    def visualize_audio(self, volume: float, color: Tuple[int, int, int] = (0, 255, 0)):
        """
        Visualize audio volume on LED matrix
        
        Args:
            volume: Current audio volume level
            color: RGB color tuple for visualization
        """
        with self._lock:
            # Update volume range with decay
            self.max_volume = max(volume, self.max_volume * (1 - self.volume_decay))
            self.min_volume = min(volume, self.min_volume * (1 + self.volume_decay))
            
            # Normalize volume
            if self.max_volume == self.min_volume:
                normalized = 0
            else:
                normalized = (volume - self.min_volume) / (self.max_volume - self.min_volume)
                
            # Smooth changes
            normalized = (normalized * (1 - self.volume_smoothing) + 
                        self.last_volume * self.volume_smoothing)
            self.last_volume = normalized
            
            # Scale to full range and add minimum brightness
            brightness = 0.1 + 0.9 * normalized
            
            # Set LED colors
            r, g, b = [int(c * brightness) for c in color]
            self.set_all(r, g, b)
            self.show()
            
    def start_audio_visualization(self, color: Tuple[int, int, int] = (0, 255, 0)):
        """
        Start continuous audio visualization
        
        Args:
            color: RGB color tuple for visualization
        """
        import pyaudio
        import numpy as np
        
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 22050
        
        def audio_callback(in_data, frame_count, time_info, status):
            # Calculate volume from audio data
            data = np.frombuffer(in_data, dtype=np.int16)
            volume = np.abs(data).mean()
            self.visualize_audio(volume, color)
            return (in_data, pyaudio.paContinue)
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Open stream
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=audio_callback
        )
        
        # Start stream
        stream.start_stream()
        
        return stream, p
        
    def stop_audio_visualization(self, stream, p):
        """Stop audio visualization and cleanup"""
        if stream.is_active():
            stream.stop_stream()
        stream.close()
        p.terminate()
        self.clear()
    
    def visualize_audio(self, audio_data: np.ndarray, threshold: float = 0.1):
        """
        Visualize audio data on the LED matrix
        
        Args:
            audio_data: Numpy array of audio samples
            threshold: Minimum amplitude to trigger visualization
        """
        if len(audio_data) == 0:
            return
            
        # Normalize audio data
        audio_data = np.abs(audio_data)
        max_amp = np.max(audio_data)
        if max_amp > threshold:
            # Scale to LED height
            scaled = (audio_data / max_amp * self.height).astype(int)
            
            # Clear display
            self.clear()
            
            # Draw visualization
            for x in range(min(self.width, len(scaled))):
                height = min(scaled[x], self.height)
                for y in range(height):
                    # Color gradient from blue to red
                    hue = (y / self.height) * 0.7  # Hue range for blue-red
                    rgb = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
                    self.set_pixel(x, y, *rgb)
            
            self.show()
    
    def start_pulse(self, r: int, g: int, b: int, duration: float = 1.0):
        """Start a pulse animation with the given color and duration (seconds)."""
        if self.is_animating:
            self.stop_animation()
        self.is_animating = True
        color = (r, g, b)
        def run_pulse():
            self._pulse_animation(color=color, speed=duration/20)
            self.is_animating = False
        self.animation_thread = threading.Thread(target=run_pulse, daemon=True)
        self.animation_thread.start()
        if self.debug:
            print(f"Started pulse animation: color={color}, duration={duration}")

    def start_rainbow(self, duration: float = 1.0):
        """Start a rainbow animation for the specified duration (seconds)."""
        if self.is_animating:
            self.stop_animation()
        self.is_animating = True
        def run_rainbow():
            start = time.time()
            while time.time() - start < duration:
                self._rainbow_animation(speed=duration/20)
            self.is_animating = False
        self.animation_thread = threading.Thread(target=run_rainbow, daemon=True)
        self.animation_thread.start()
        if self.debug:
            print(f"Started rainbow animation: duration={duration}")

    def set_brightness(self, value: float):
        """Set the brightness of the LED matrix."""
        if hasattr(self, 'unicorn') and self.unicorn:
            try:
                self.unicorn.set_brightness(value)
                if hasattr(self, 'requested_color'):
                    r, g, b = self.requested_color
                    self.set_color(r, g, b)
                if self.debug:
                    print(f"LED brightness set to {value}")
            except Exception as e:
                if self.debug:
                    print(f"Failed to set brightness: {e}")

    def set_color(self, r: int, g: int, b: int):
        """Set all LEDs to the specified color (with validation)."""
        for val in (r, g, b):
            if not (0 <= val <= 255):
                raise ValueError("Color values must be between 0 and 255")
        self.set_all(r, g, b)

    @property
    def animation_running(self) -> bool:
        """Return True if an animation is running."""
        return self.is_animating

    def cleanup(self):
        """Clean up resources and turn off LEDs"""
        self.stop_animation()
        self.clear()
        if self.debug:
            print("LED cleanup completed")
