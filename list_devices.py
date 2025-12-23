#!/usr/bin/env python3
import pyaudio

p = pyaudio.PyAudio()
print("\nAll audio input devices:")
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info.get('maxInputChannels', 0) > 0:
        print(f"[{i}] '{info['name']}' (maxInputChannels: {info['maxInputChannels']})")
p.terminate()
