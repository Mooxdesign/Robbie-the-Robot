import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import wave
import os
import sys

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.modules.audio import AudioModule

class TestAudioModule(unittest.TestCase):
    @patch('pyaudio.PyAudio')
    def setUp(self, mock_pyaudio):
        """Set up test environment"""
        # Mock PyAudio
        self.mock_stream = MagicMock()
        mock_pyaudio.return_value.open.return_value = self.mock_stream
        
        self.ac = AudioModule(debug=True)
        
    def test_play_sound(self):
        """Test playing sound file"""
        # Create test WAV data
        test_data = np.zeros(1000, dtype=np.int16).tobytes()
        
        # Mock wave.open
        mock_wave = MagicMock()
        mock_wave.getnframes.return_value = 1000
        mock_wave.getframerate.return_value = 44100
        mock_wave.getsampwidth.return_value = 2
        mock_wave.getnchannels.return_value = 1
        mock_wave.readframes.return_value = test_data
        
        with patch('wave.open', return_value=mock_wave):
            self.ac.play_sound("test.wav")
            
        # Verify stream was opened and started
        self.mock_stream.start_stream.assert_called_once()
        self.mock_stream.write.assert_called_with(test_data)
        
    def test_record_audio(self):
        """Test audio recording"""
        # Mock incoming audio data
        test_data = np.zeros(1000, dtype=np.int16).tobytes()
        self.mock_stream.read.return_value = test_data
        
        # Record for 0.1 seconds
        recording = self.ac.record(duration=0.1)
        
        # Verify recording length
        self.assertGreater(len(recording), 0)
        
    def test_audio_processing(self):
        """Test audio signal processing"""
        # Create test signal
        test_signal = np.sin(np.linspace(0, 2*np.pi, 1000))
        
        # Test volume detection
        volume = self.ac.get_volume(test_signal)
        self.assertGreater(volume, 0)
        
        # Test frequency detection
        freq = self.ac.get_frequency(test_signal)
        self.assertGreater(freq, 0)
        
    def test_error_handling(self):
        """Test error handling"""
        # Test invalid file
        with self.assertRaises(FileNotFoundError):
            self.ac.play_sound("nonexistent.wav")
            
        # Test invalid recording duration
        with self.assertRaises(ValueError):
            self.ac.record(duration=-1)
            
    def test_cleanup(self):
        """Test cleanup"""
        self.ac.cleanup()
        self.mock_stream.stop_stream.assert_called_once()
        self.mock_stream.close.assert_called_once()
        
    def tearDown(self):
        """Clean up after each test"""
        self.ac.cleanup()

if __name__ == '__main__':
    unittest.main()
