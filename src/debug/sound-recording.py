import sounddevice as sd
from scipy.io.wavfile import write

# Settings
fs = 44100  # Sample rate
seconds = 5  # Duration of recording

print("Recording...")
recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
sd.wait()  # Wait until recording is finished
print("Recording complete, saving to 'test_recording.wav'.")

write('test_recording.wav', fs, recording)
print("Saved as 'test_recording.wav'.")