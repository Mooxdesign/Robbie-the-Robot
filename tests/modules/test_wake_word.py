import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import time
import os
import sys

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.modules.wake_word_detector import WakeWordDetector

class TestWakeWordDetector(unittest.TestCase):
    @patch('pvporcupine.create_porcupine')
    @patch('pyaudio.PyAudio')
    def setUp(self, mock_pyaudio, mock_porcupine):
        """Set up test environment with mocked dependencies"""
        # Mock PyAudio
        self.mock_stream = MagicMock()
        self.mock_stream.stop_stream = MagicMock()
        self.mock_stream.close = MagicMock()
        mock_pyaudio.return_value.open.return_value = self.mock_stream
        mock_pyaudio.return_value.get_device_count.return_value = 1
        
        # Mock Porcupine
        self.mock_porcupine = MagicMock()
        self.mock_porcupine.process.return_value = -1  # No wake word by default
        mock_porcupine.return_value = self.mock_porcupine
        
        # Create wake word detector
        self.wake_word_called = False
        def on_wake_word():
            self.wake_word_called = True
        
        self.detector = WakeWordDetector(
            wake_word="test wake word",
            on_wake_word=on_wake_word,
            debug=True
        )
        
    def test_wake_word_detection(self):
        """Test wake word detection triggers callback"""
        self.detector.start()
        
        # Simulate wake word detection
        self.mock_porcupine.process.return_value = 0
        
        # Send test audio
        test_audio = np.zeros(512, dtype=np.int16).tobytes()
        self.detector._audio_callback(test_audio, 512, None, None)
        
        # Give the processing thread time to run
        time.sleep(0.1)
        
        # Check if callback was called
        self.assertTrue(self.wake_word_called)
        
    def test_start_stop(self):
        """Test starting and stopping the detector"""
        # Start detector
        self.detector.start()
        self.assertTrue(self.detector.is_listening)
        self.assertIsNotNone(self.detector.stream)
        
        # Stop detector
        self.detector.stop()
        self.assertFalse(self.detector.is_listening)
        self.mock_stream.stop_stream.assert_called_once()
        self.mock_stream.close.assert_called_once()
        
    def test_audio_processing(self):
        """Test audio processing pipeline"""
        self.detector.start()
        
        # Send multiple audio chunks
        test_audio = np.zeros(512, dtype=np.int16).tobytes()
        for _ in range(3):
            self.detector._audio_callback(test_audio, 512, None, None)
            
        # Verify Porcupine processes each chunk
        self.assertEqual(self.mock_porcupine.process.call_count, 3)
        
    def test_error_handling(self):
        """Test error handling in audio processing"""
        self.detector.start()
        
        # Simulate processing error
        self.mock_porcupine.process.side_effect = Exception("Test error")
        
        # Send test audio
        test_audio = np.zeros(512, dtype=np.int16).tobytes()
        self.detector._audio_callback(test_audio, 512, None, None)
        
        # Verify detector continues running despite error
        self.assertTrue(self.detector.is_listening)
        
    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self.detector, 'stream') and self.detector.stream:
            self.detector.stop()
        self.detector.cleanup()

if __name__ == '__main__':
    unittest.main()
