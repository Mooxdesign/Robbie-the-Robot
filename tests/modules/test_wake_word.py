import sys
import os
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import time
from src.modules.wake_word import WakeWordModule
from src.modules.audio import AudioModule

class TestWakeWordModule(unittest.TestCase):
    @patch('pvporcupine.create')
    @patch('pyaudio.PyAudio')
    @patch.object(AudioModule, 'close_stream')
    def setUp(self, mock_close_stream, mock_pyaudio, mock_porcupine):
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
        
        # Mock AudioModule
        mock_close_stream.side_effect = lambda stream: (self.mock_stream.stop_stream(), self.mock_stream.close())
        
        # Create wake word detector
        self.wake_word_called = False
        def on_wake_word():
            self.wake_word_called = True
        
        self.wake_word = WakeWordModule(
            wake_word="test wake word",
            debug=True
        )
        self.wake_word.add_detection_callback(on_wake_word)

        # Patch create_stream to register the mock stream in _streams
        def fake_create_stream(*args, **kwargs):
            stream_id = "test_stream_id"
            self.wake_word.audio._streams[stream_id] = {"stream": self.mock_stream, "callback": None}
            return stream_id
        self.wake_word.audio.create_stream = fake_create_stream

    def test_wake_word_detection(self):
        """Test wake word detection triggers callback"""
        self.wake_word.start_listening()
        
        # Simulate wake word detection
        self.mock_porcupine.process.return_value = 0
        
        # Send test audio
        test_audio = np.zeros(512, dtype=np.int16).tobytes()
        self.wake_word._audio_callback(test_audio, 512, None, None)
        
        # Give the processing thread time to run
        time.sleep(0.1)
        
        # Check if callback was called
        self.assertTrue(self.wake_word_called)
        
    def test_start_stop(self):
        """Test starting and stopping the detector"""
        # Start detector
        self.wake_word.start_listening()
        self.assertTrue(self.wake_word.is_listening)
        self.assertTrue(self.wake_word.has_active_stream)  # Public: check stream creation
        
        # Stop detector
        self.wake_word.stop_listening()
        self.assertFalse(self.wake_word.is_listening)
        self.assertFalse(self.wake_word.has_active_stream)  # Public: check stream cleanup
        self.mock_stream.stop_stream.assert_called_once()
        self.mock_stream.close.assert_called_once()
        
    def test_audio_processing(self):
        """Test audio processing pipeline"""
        self.wake_word.start_listening()
        
        # Send multiple audio chunks
        test_audio = np.zeros(512, dtype=np.int16).tobytes()
        for _ in range(3):
            self.wake_word._audio_callback(test_audio, 512, None, None)
            
        # Verify Porcupine processes each chunk
        self.assertEqual(self.mock_porcupine.process.call_count, 3)
        
    def test_error_handling(self):
        """Test error handling in audio processing"""
        self.wake_word.start_listening()
        
        # Simulate processing error
        self.mock_porcupine.process.side_effect = Exception("Test error")
        
        # Send test audio
        test_audio = np.zeros(512, dtype=np.int16).tobytes()
        self.wake_word._audio_callback(test_audio, 512, None, None)
        
        # Verify detector continues running despite error
        self.assertTrue(self.wake_word.is_listening)
        
    def tearDown(self):
        """Clean up after each test"""
        self.wake_word.stop_listening()
        self.wake_word.cleanup()


if __name__ == '__main__':
    unittest.main()
