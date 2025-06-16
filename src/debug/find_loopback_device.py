import pyaudio

print("Available audio devices:")
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"{i}: {info['name']} (inputs: {info['maxInputChannels']}, outputs: {info['maxOutputChannels']})")
    if 'loopback' in info['name'].lower() or 'stereo mix' in info['name'].lower():
        print("    >>> POSSIBLE LOOPBACK DEVICE <<<")
p.terminate()

print("\nLook for devices labeled 'Stereo Mix', 'Loopback', 'What U Hear', or similar. Note the index for use in AudioModule.")
