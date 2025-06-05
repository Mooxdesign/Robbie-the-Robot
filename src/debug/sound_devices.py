import sounddevice as sd
for idx, dev in enumerate(sd.query_devices()):
    print(f"{idx}: {dev['name']} ({dev['max_input_channels']} in, {dev['max_output_channels']} out)")