import sys
import os
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import time
import sys
import os
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
modules_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/modules'))
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

from src.modules.speech_to_text import SpeechToTextModule
from src.modules.audio import AudioModule

class TestSpeechToTextModule(unittest.TestCase):
    def setUp(self):
        """Set up test environment with mocked dependencies"""
        # Patch whisper.load_model
        patcher = patch('whisper.load_model')
        self.addCleanup(patcher.stop)
        mock_whisper_load_model = patcher.start()
        self.mock_whisper = MagicMock()
        self.mock_whisper.transcribe.return_value = {"text": ""}
        mock_whisper_load_model.return_value = self.mock_whisper

        # Mock AudioModule
        self.mock_audio = MagicMock(spec=AudioModule)
        self.mock_audio.close_stream = self.mock_audio.stop_stream  # Track both as the same mock
        self.audio_callback = None

        def mock_start_stream(callback):
            self.audio_callback = callback
            return "dummy_stream_id"

        self.mock_audio.start_stream.side_effect = mock_start_stream

        # Create SpeechToTextModule with mocked dependencies and inject mock whisper
        self.stt = SpeechToTextModule(
            audio_module=self.mock_audio,
            debug=True,
            whisper_model=self.mock_whisper
        )

            
    def test_command_registration(self):
        """Test command registration and callback system"""
        # Setup command callback
        callback = MagicMock()
        self.stt.register_command("test command", callback)
        
        # Verify command was registered
        self.assertIn("test command", self.stt.command_callbacks)
        
        # Start listening
        self.stt.start_listening()
        
        # Verify audio stream was started
        self.mock_audio.start_stream.assert_called_once()
        self.assertIsNotNone(self.audio_callback)
        
        # Simulate audio data with speech
        self.mock_whisper.transcribe.return_value = {"text": "test command"}
        audio_data = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        self.stt.audio_callback(audio_data)
        
        # Give the processing thread time to run
        time.sleep(0.1)
        
        # Verify callback was called
        callback.assert_called_once()
        
    def test_audio_processing(self):
        """Test audio processing pipeline"""
        # Start listening
        self.stt.start_listening()
        
        # Simulate multiple chunks of audio data
        chunks = [np.random.rand(1000).astype(np.float32) for _ in range(5)]
        
        # Feed audio chunks
        for chunk in chunks:
            self.stt.audio_callback(chunk)
            
        # Verify Whisper was called with concatenated audio
        time.sleep(0.1)  # Give processing thread time to run
        self.mock_whisper.transcribe.assert_called()
        
    def test_stop_listening(self):
        """Test stopping the speech recognition"""
        # Start and then stop listening
        self.stt.start_listening()
        self.stt.stop_listening()
        
        # Verify audio stream was stopped
        self.mock_audio.stop_stream.assert_called_once()
        
        # Verify no more audio processing occurs
        self.mock_whisper.transcribe.reset_mock()
        audio_data = np.zeros(1000, dtype=np.float32)
        self.stt.audio_callback(audio_data)
        
        time.sleep(0.1)
        self.mock_whisper.transcribe.assert_not_called()
        
    def test_cleanup(self):
        """Test resource cleanup"""
        self.stt.start_listening()
        self.stt.cleanup()
        
        # Verify proper cleanup
        self.mock_audio.stop_stream.assert_called_once()
        self.assertFalse(self.stt.is_listening)
        
    def tearDown(self):
        """Clean up after each test"""
        self.stt.cleanup()

if __name__ == '__main__':
    unittest.main()
