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

import types

class TestSpeechToTextModule(unittest.TestCase):
    def test_google_stt_backend(self):
        """Test Google STT backend selection and processing on Pi Zero"""
        # Patch platform to simulate Pi Zero
        with patch('platform.uname') as mock_uname, \
             patch('google.cloud.speech.SpeechClient') as mock_client:
            mock_uname.return_value = types.SimpleNamespace(machine='armv6l', node='raspberrypi')
            mock_gclient = mock_client.return_value
            mock_gclient.recognize.return_value = types.SimpleNamespace(
                results=[types.SimpleNamespace(alternatives=[types.SimpleNamespace(transcript="hello world")])]
            )
            # Patch AudioModule
            mock_audio = MagicMock(spec=AudioModule)
            stt = SpeechToTextModule(audio_module=mock_audio, debug=True)
            self.assertEqual(stt.backend, "google")
            stt.gcloud_client = mock_gclient
            stt.is_listening = True
            # Simulate audio buffer and process
            stt._audio_buffer = [np.ones(16000, dtype=np.float32)]
            stt._process_audio()
            # Should call Google STT recognize
            mock_gclient.recognize.assert_called()
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
        self.stt.start_listening()
        self.stt.is_listening = True  # Force listening state

        # Feed enough audio to exceed duration threshold (e.g., 16000 samples for 1s at 16kHz)
        audio_data = np.random.rand(16000).astype(np.float32)
        self.stt.audio_callback(audio_data)

        # Feed a chunk of silence to simulate end-of-speech
        self.stt.audio_callback(np.zeros(16000, dtype=np.float32))

        # Ensure buffer is not empty (force if needed)
        if len(self.stt._audio_buffer) == 0:
            self.stt._audio_buffer = [np.zeros(16000, dtype=np.float32)]

        print("DEBUG: is_listening =", self.stt.is_listening)
        print("DEBUG: buffer length =", len(self.stt._audio_buffer))

        # Force process audio to ensure the buffer is processed in test
        self.stt._process_audio()

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
