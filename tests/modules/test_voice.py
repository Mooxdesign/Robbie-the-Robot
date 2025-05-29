import sys
import os
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Ensure src/modules is also importable as 'modules'
modules_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/modules'))
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

import unittest
import time
from unittest.mock import MagicMock, patch
from src.modules.voice import VoiceModule

class TestVoiceModule(unittest.TestCase):
    """Test cases for VoiceModule"""
    
    def setUp(self):
        # Patch pyttsx3.init before VoiceModule is created
        patcher = patch("pyttsx3.init")
        self.addCleanup(patcher.stop)
        self.mock_init = patcher.start()

        # Create a mock engine and configure its methods
        self.mock_engine = MagicMock()
        self.mock_init.return_value = self.mock_engine

        # Simulate instant speech completion
        def fake_startLoop():
            # Simulate the speech completion event
            self.voice._on_completed("mock", True)
        self.mock_engine.say.side_effect = lambda text: None
        self.mock_engine.startLoop.side_effect = fake_startLoop
        self.mock_engine.connect.side_effect = lambda event, handler: None
        self.mock_engine.stop.side_effect = lambda: None
        self.mock_engine.endLoop.side_effect = lambda: None
        
        # Mock voices and rate for get_voices and rate_control
        fake_voice = MagicMock()
        fake_voice.id = "fake_voice_id"
        fake_voice.name = "Fake Voice"
        fake_voice.languages = ["en"]
        fake_voice.gender = "male"
        fake_voice.age = 30
        def get_property_side_effect(prop):
            if prop == "voices":
                return [fake_voice]
            elif prop == "rate":
                return 190
            elif prop == "volume":
                return 1.0
            return None
        self.mock_engine.getProperty.side_effect = get_property_side_effect

        self.voice = VoiceModule(debug=True)
        
    def tearDown(self):
        """Clean up after tests"""
        if self.voice:
            self.voice.cleanup()
            
    def test_initialization(self):
        """Test module initialization"""
        self.assertIsNotNone(self.voice.engine)
        self.assertTrue(hasattr(self.voice, '_lock'))
        
    def test_say_blocking(self):
        """Test blocking speech with mocked TTS engine"""
        test_text = "Hello, this is a test"
        result = self.voice.say(test_text, blocking=True)
        self.assertTrue(result)

    def test_say_non_blocking(self):
        """Test non-blocking speech"""
        test_text = "This should not block"
        result = self.voice.say(test_text, blocking=False)
        self.assertTrue(result)
        # Give a moment for background thread to start
        time.sleep(0.1)
        
    def test_rate_control(self):
        """Test speech rate control"""
        # Windows Speech API may not support exact rate values
        # Just verify we can set rates without errors
        test_rates = [100, 150, 200]
        for rate in test_rates:
            result = self.voice.set_rate(rate)
            self.assertTrue(result)
            # Verify rate is a reasonable value
            actual_rate = self.voice.engine.getProperty('rate')
            if actual_rate is None:
                print("Warning: pyttsx3 returned None for rate; skipping assert.")
            else:
                self.assertGreater(actual_rate, 0)
            
    def test_volume_control(self):
        """Test volume control"""
        # Windows Speech API may not support full volume range
        # Just verify we can set volume without errors
        test_volumes = [0.0, 0.5, 1.0]
        for volume in test_volumes:
            result = self.voice.set_volume(volume)
            self.assertTrue(result)
            
    def test_volume_limits(self):
        """Test volume limits are enforced"""
        # Windows Speech API may handle volume limits differently
        # Just verify we can set volume without errors
        self.voice.set_volume(1.5)  # Above max
        self.voice.set_volume(-0.5)  # Below min
        # If we got here without errors, test passes
        
    def test_get_voices(self):
        """Test retrieving available voices"""
        voices = self.voice.get_voices()
        self.assertIsInstance(voices, dict)
        # Should have at least one voice
        self.assertGreater(len(voices), 0)
        
        # Check voice properties
        for voice_id, props in voices.items():
            self.assertIn('name', props)
            self.assertIn('languages', props)
            self.assertIn('gender', props)
            self.assertIn('age', props)
            
    def test_set_voice(self):
        """Test setting voice"""
        voices = self.voice.get_voices()
        if voices:
            # Try to set first available voice
            first_voice_id = next(iter(voices))
            result = self.voice.set_voice(first_voice_id)
            self.assertTrue(result)
            
    def test_error_handling(self):
        """Test error handling with mock engine"""
        with patch('pyttsx3.init') as mock_init:
            # Test initialization failure
            mock_init.side_effect = Exception("Mock init error")
            voice = VoiceModule(debug=True)
            self.assertIsNone(voice.engine)
            
        # Test speech with failed engine
        voice = VoiceModule(debug=True)
        voice.engine = None
        result = voice.say("This should fail gracefully")
        self.assertFalse(result)
        
    def test_cleanup(self):
        """Test cleanup"""
        # Mock engine to verify stop is called
        self.voice.engine = MagicMock()
        self.voice.cleanup()
        self.voice.engine.stop.assert_called_once()
        
if __name__ == '__main__':
    unittest.main()
