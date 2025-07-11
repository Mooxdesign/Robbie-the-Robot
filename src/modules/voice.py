#!/usr/bin/env python3

import threading
import time
import pyttsx3
from typing import Optional, Dict, Any, List, Tuple, Union
import logging

logger = logging.getLogger(__name__)

class VoiceModule(threading.Thread):
    """Text-to-speech module using pyttsx3 with proper event handling"""
    
    def __init__(self, 
                 rate: int = 130,
                 volume: float = 1.0,
                 voice_id: Optional[str] = None,
                 debug: bool = True):
        super().__init__()
        """
        Initialize text-to-speech module
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            voice_id: Specific voice ID to use, None for default
            debug: Enable debug output
        """
        self.debug = debug
        self.bypass = False
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        
        # Threading events and locks
        self._lock = threading.Lock()
        self._cancel = threading.Event()
        self._say = threading.Event()
        self._text_lock = threading.Lock()
        self._is_alive = threading.Event()
        
        # Speech queue and callbacks
        self._text: List[Tuple[str, bool]] = []
        self._completion_callbacks = []
        
        # Start thread
        self._is_alive.set()
        self.engine = None  # Engine will be initialized in run()
        self.start()

    def set_rate(self, rate: int) -> bool:
        """Set the speech rate."""
        with self._lock:
            self.rate = rate
            if self.engine:
                self.engine.setProperty('rate', rate)
            return True

    def set_volume(self, volume: float) -> bool:
        """Set the speech volume."""
        with self._lock:
            # Clamp volume between 0.0 and 1.0
            self.volume = max(0.0, min(volume, 1.0))
            if self.engine:
                self.engine.setProperty('volume', self.volume)
            return True

    def set_voice(self, voice_id: str) -> bool:
        """Set the speech voice by ID."""
        with self._lock:
            voices = self.get_voices()
            if voice_id not in voices:
                if self.debug:
                    logger.warning(f"Voice ID {voice_id} not found")
                return False
            self.voice_id = voice_id
            if self.engine:
                self.engine.setProperty('voice', voice_id)
            return True

    def _init_engine(self) -> Optional[pyttsx3.Engine]:
        """Initialize pyttsx3 engine with properties"""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            # Log all available voices
            voices = engine.getProperty('voices')
            logger.info(f"[VoiceModule] Available voices:")
            for v in voices:
                logger.info(f"- {v.id}: {v.name} (languages={v.languages}, gender={getattr(v, 'gender', None)}, age={getattr(v, 'age', None)})")
            # Always use a known working voice if available
            preferred_names = [
                "Microsoft David Desktop - English (United States)",
                "Microsoft Zira Desktop - English (United States)"
            ]
            selected_voice = None
            for v in voices:
                if v.name in preferred_names:
                    selected_voice = v
                    break
            if selected_voice:
                engine.setProperty('voice', selected_voice.id)
                logger.info(f"[VoiceModule] Selected preferred voice: {selected_voice.name}")
            elif voices:
                engine.setProperty('voice', voices[0].id)
                logger.info(f"[VoiceModule] No preferred voice found. Using fallback: {voices[0].name}")
            else:
                logger.error("[VoiceModule] No voices available for TTS.")
            # Connect event handlers
            engine.connect('finished-utterance', self._on_completed)
            engine.connect('started-word', self._on_cancel)
            logger.info("[VoiceModule] TTS engine initialized")
            return engine
        except Exception as e:
            logger.error(f"[VoiceModule] Failed to initialize TTS engine: {e}")
            return None

        
    def _find_voice_by_gender(self, gender: str) -> Optional[str]:
        """
        Find first available voice by gender
        
        Args:
            gender: Desired voice gender ('male' or 'female')
            
        Returns:
            str: Voice ID if found, None otherwise
        """
        voices = self.get_voices()
        for voice_id, voice_info in voices.items():
            # Handle cases where gender might be None
            voice_gender = voice_info.get('gender', '').lower() if voice_info.get('gender') else ''
            if voice_gender == gender.lower():
                return voice_id
        return None

    def say(self, text: Union[str, List[str]], blocking: bool = False) -> bool:
        """
        Speak text using text-to-speech
        
        Args:
            text: Text to speak (string or list of strings)
            blocking: Wait for speech to complete
            
        Returns:
            bool: True if successful
        """

        logger.debug(f"[VoiceModule] say() called with: {text} (blocking={blocking})")
        logger.debug(f"[VoiceModule] State: is_alive={self._is_alive.is_set()}, engine={self.engine}")

        # Check if engine is initialized and thread is alive
        if not self.engine:
            logger.error("TTS engine not initialized")
            return False
        if not self._is_alive.is_set():
            if self.debug:
                logger.warning("Speech thread not running")
            return False
            
        try:
            # Clear any pending cancellation
            self._cancel.clear()
            
            # Accept both string and list
            if isinstance(text, str):
                text = [(text, blocking)]
            elif isinstance(text, list):
                text = [(t, blocking) if isinstance(t, str) else t for t in text]
            
            # Queue all text items
            with self._text_lock:
                for t in text:
                    self._text.append(t)
                    if self.debug:
                        logger.debug(f"[VoiceModule] Queued speech: '{t[0]}' (blocking={t[1]})")
            
            # Signal speech thread
            self._say.set()
            
            # If blocking, wait for queue to empty
            if blocking:
                while len(self._text) > 0:
                    time.sleep(0.1)
                
            return True
            
        except Exception as e:
            logger.exception(f"[VoiceModule] Exception in say(): {e}")
            return False
            
    def cancel(self):
        """Cancel current speech"""
        self._cancel.set()
        
    def _on_cancel(self):
        """Handle cancellation during word"""
        if self._cancel.is_set():
            self.stop()
            
    def stop(self):
        """Stop current speech"""
        if self.engine:
            self.engine.stop()
            time.sleep(0.5)
            
    def _on_completed(self, name, completed):
        logger.debug(f"[VoiceModule] _on_completed called: name={name}, completed={completed}")
        if completed:
            if self.debug:
                logger.info(f"Speech completed: {name}")
            self._notify_completion()
            logger.debug(f"[VoiceModule] _notify_completion called from _on_completed")
            
    def _notify_completion(self):
        """Notify completion callbacks"""
        logger.debug("[VoiceModule] Notifying completion callbacks")
        for callback in self._completion_callbacks:
            try:
                logger.debug(f"[VoiceModule] Calling completion callback: {callback}")
                callback()
            except Exception as e:
                logger.exception(f"[VoiceModule] Error in completion callback: {e}")
        logger.debug("[VoiceModule] All completion callbacks notified")
                    
    def add_completion_callback(self, callback):
        """Add callback to be called when speech completes"""
        self._completion_callbacks.append(callback)
        
    def cleanup(self):
        """Clean up resources"""
        self._is_alive.clear()
        self._cancel.set()
        self.join()
        
    def get_voices(self) -> Dict[str, Any]:
        """
        Get available voices
        
        Returns:
            dict: Dictionary of available voices
        """
        if not self.engine:
            if self.debug:
                logger.error("TTS engine not initialized")
            return {}
            
        try:
            voices = {}
            for voice in self.engine.getProperty('voices'):
                # Infer gender from voice name for Microsoft voices
                # This is a fallback when the API doesn't provide gender info
                inferred_gender = None
                name = voice.name.lower()
                if 'zira' in name or 'hazel' in name:
                    inferred_gender = 'female'
                elif 'david' in name:
                    inferred_gender = 'male'
                
                voices[voice.id] = {
                    'name': voice.name,
                    'languages': voice.languages,
                    'gender': voice.gender if voice.gender else inferred_gender,
                    'age': voice.age
                }
            return voices
        except Exception as e:
            if self.debug:
                logger.exception(f"Error getting voices: {e}")
            return {}
            

    def change_voice(self, voice_id: Optional[str] = None, gender: Optional[str] = None) -> bool:
        """
        Change the voice used for speech.
        Args:
            voice_id: Specific voice ID to use
            gender: Gender of voice to use ('male' or 'female'), ignored if voice_id is provided
        Returns:
            bool: True if voice was changed successfully
        """
        try:
            if not self.engine:
                if self.debug:
                    logger.error("TTS engine not initialized")
                return False

            # If voice_id provided, use it directly
            if voice_id:
                voices = self.get_voices()
                if voice_id not in voices:
                    if self.debug:
                        logger.warning(f"Voice ID {voice_id} not found")
                    return False
                self.voice_id = voice_id
            # Otherwise try to find voice by gender
            elif gender:
                self.voice_id = self._find_voice_by_gender(gender)
                if not self.voice_id:
                    if self.debug:
                        logger.warning(f"No {gender} voice found")
                    return False
            else:
                if self.debug:
                    logger.warning("Must provide either voice_id or gender")
                return False

            self.engine.setProperty('voice', self.voice_id)
            if self.debug:
                voices = self.get_voices()
                logger.info(f"Changed to voice: {voices[self.voice_id]['name']}")
            return True
        except Exception as e:
            if self.debug:
                logger.exception(f"Error changing voice: {e}")
            return False

    def run(self):
        """Main speech thread loop"""
        self.engine = self._init_engine()
        if not self.engine:
            logger.error("[VoiceModule] TTS engine initialization failed. Exiting speech thread.")
            return  # Exit thread cleanly if engine failed to initialize

        while self._is_alive.is_set():
            # Wait for speech request
            while self._say.wait(0.1):
                self._say.clear()
                # Process all queued text
                while not self._cancel.is_set() and len(self._text):
                    with self._text_lock:
                        text, blocking = self._text.pop(0)
                    try:
                        if self.bypass:
                            import time
                            time.sleep(1)  # Simulate time taken to speak
                            self._notify_completion()
                        else:
                            self.engine.say(text)
                            logger.info(f"[VoiceModule] Called engine.say() for: '{text}'")
                            self.engine.runAndWait()
                            logger.info(f"[VoiceModule] Finished engine.runAndWait() for: '{text}'")

                    except Exception as e:
                        logger.exception(f"[VoiceModule] Error during speech: {e}")
        # Cleanup
        if self.engine:
            try:
                self.engine.stop()
            except Exception as e:
                logger.exception(f"[VoiceModule] Error during cleanup: {e}")
            try:
                self.engine.stop()
            except Exception as e:
                if self.debug:
                    logger.exception(f"Error during cleanup: {e}")
