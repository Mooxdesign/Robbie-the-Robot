#!/usr/bin/env python3

import os
import sys
import time
import threading
import queue
import wave
import pyaudio
import pyttsx3
import speech_recognition as sr
from typing import Optional, Callable

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import Config

class VoiceController:
    """
    Handles speech recognition, text-to-speech, and voice command processing
    """
    
    def __init__(self, 
                 wake_word: str = "hey robot",
                 language: str = "en-US",
                 debug: bool = False):
        """
        Initialize voice control system
        
        Args:
            wake_word: Wake word to activate voice commands
            language: Language code for speech recognition
            debug: Enable debug output
        """
        self.debug = debug
        self.wake_word = wake_word.lower()
        self.language = language
        self._lock = threading.Lock()
        
        # Load config
        config = Config()
        self.speech_rate = config.get('voice', 'speech_rate', default=150)
        
        # Initialize speech recognition
        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.energy_threshold = 4000
            
            # Initialize microphone
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                
            if self.debug:
                print("Speech recognition initialized")
                
        except Exception as e:
            print(f"Failed to initialize speech recognition: {e}")
            self.recognizer = None
            self.microphone = None
            
        # Initialize text-to-speech
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.speech_rate)
            
            if self.debug:
                print("Text-to-speech initialized")
                
        except Exception as e:
            print(f"Failed to initialize text-to-speech: {e}")
            self.engine = None
            
        # Command processing
        self.command_queue = queue.Queue()
        self.is_listening = False
        self.command_handlers = {}
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_commands,
            daemon=True
        )
        self.processing_thread.start()
        
        if self.debug:
            print("Voice controller initialized")

    def start_listening(self):
        """Start listening for voice commands"""
        if not self.is_listening:
            self.is_listening = True
            threading.Thread(target=self._listen_loop, daemon=True).start()
            if self.debug:
                print("Started listening for commands")

    def stop_listening(self):
        """Stop listening for voice commands"""
        self.is_listening = False
        if self.debug:
            print("Stopped listening for commands")

    def speak(self, text: str, blocking: bool = False):
        """
        Convert text to speech
        
        Args:
            text: Text to speak
            blocking: Wait for speech to complete
        """
        if self.engine:
            if blocking:
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                threading.Thread(
                    target=lambda: (self.engine.say(text), self.engine.runAndWait()),
                    daemon=True
                ).start()

    def add_command_handler(self, command: str, handler: Callable[[str], None]):
        """
        Add a handler for a specific voice command
        
        Args:
            command: Command phrase to trigger handler
            handler: Function to call when command is recognized
        """
        self.command_handlers[command.lower()] = handler
        if self.debug:
            print(f"Added handler for command: {command}")

    def _listen_loop(self):
        """Main listening loop for voice commands"""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.is_listening:
                try:
                    if self.debug:
                        print("Listening...")
                        
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio, language=self.language).lower()
                    
                    if self.debug:
                        print(f"Recognized: {text}")
                    
                    if self.wake_word in text:
                        self.speak("Yes?")
                        command_audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)
                        command = self.recognizer.recognize_google(command_audio, language=self.language).lower()
                        self.command_queue.put(command)
                        
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")
                except Exception as e:
                    print(f"Error in voice recognition: {e}")

    def _process_commands(self):
        """Process voice commands from the queue"""
        while True:
            try:
                command = self.command_queue.get()
                if self.debug:
                    print(f"Processing command: {command}")
                
                # Check for exact matches first
                if command in self.command_handlers:
                    self.command_handlers[command](command)
                    continue
                
                # Check for partial matches
                for cmd, handler in self.command_handlers.items():
                    if cmd in command:
                        handler(command)
                        break
                else:
                    if self.debug:
                        print(f"No handler found for command: {command}")
                
            except Exception as e:
                print(f"Error processing command: {e}")

    def listen(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Listen for speech and convert to text
        
        Args:
            timeout: How long to wait before giving up
            
        Returns:
            Recognized text or None if no speech detected
        """
        if not self.recognizer or not self.microphone:
            return None
            
        try:
            with self.microphone as source:
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=timeout)
                
            print("Recognizing...")
            text = self.recognizer.recognize_google(audio, language=self.language)
            print(f"Recognized: {text}")
            return text
            
        except sr.WaitTimeoutError:
            print("No speech detected")
            return None
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Recognition error: {e}")
            return None
        except Exception as e:
            print(f"Error during speech recognition: {e}")
            return None

    def record_audio(self, output_file: str, duration: Optional[int] = None):
        """
        Record audio to a file
        
        Args:
            output_file: Path to save the audio file
            duration: Recording duration in seconds (default: self.record_seconds)
        """
        if duration is None:
            duration = 5
            
        p = pyaudio.PyAudio()
        
        stream = p.open(format=pyaudio.paInt16,
                       channels=1,
                       rate=16000,
                       input=True,
                       frames_per_buffer=1024)
        
        frames = []
        
        for i in range(0, int(16000 / 1024 * duration)):
            data = stream.read(1024)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        wf = wave.open(output_file, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        if self.debug:
            print(f"Recorded audio saved to: {output_file}")

    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        if self.engine:
            self.engine.stop()
