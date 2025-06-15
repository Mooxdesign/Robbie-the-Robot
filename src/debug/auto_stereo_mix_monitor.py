import numpy as np
import sounddevice as sd

# Automatically select the best Stereo Mix or Microphone device

def find_device(preferred_names):
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        name = dev['name'].lower()
        for pref in preferred_names:
            if pref in name:
                print(f"Selected device: {dev['name']} (index {idx})")
                return idx
    print(f"No preferred device found for: {preferred_names}")
    return None

def audio_callback(indata, frames, time, status):
    volume_norm = np.linalg.norm(indata) / frames
    db = 20 * np.log10(volume_norm) if volume_norm > 0 else -100
    print(f"[MONITOR] Output volume RMS: {volume_norm:.3f} ({db:.1f} dB)")

def main():
    # Try to find Stereo Mix first, then fallback to Microphone
    preferred_inputs = ["stereo mix", "monitor", "loopback", "speakers"]
    fallback_inputs = ["microphone", "mic array"]

    device = find_device(preferred_inputs)
    if device is None:
        print("Falling back to microphone...")
        device = find_device(fallback_inputs)
    if device is None:
        print("No suitable input device found. Exiting.")
        return

    samplerate = 44100
    channels = 2
    print(f"Using device index: {device}")
    with sd.InputStream(device=device, channels=channels, samplerate=samplerate, callback=audio_callback, blocksize=1024):
        print("Monitoring input (Ctrl+C to stop)...")
        while True:
            sd.sleep(1000)

if __name__ == "__main__":
    main()
