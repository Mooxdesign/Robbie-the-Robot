import subprocess
import numpy as np
import pyaudio
import unicornhat as unicorn

# Initialize global variables for max and min volume
max_volume = float('-inf')
min_volume = float('inf')

# Function to control LEDs based on volume
def control_leds(volume):
    print(volume)
    global max_volume, min_volume
    
    # Update max and min volume
    max_volume = max(max_volume, volume)
    min_volume = min(min_volume, volume)
    
    if max_volume == min_volume:
        normalized_volume = 0
    else:
        normalized_volume = (volume - min_volume) / (max_volume - min_volume)

    normalized_volume = 0.2 + 0.4*normalized_volume 
    # Use the normalized value to adjust brightness
    unicorn.brightness(normalized_volume)
    unicorn.set_all(11, 211, 44)
    unicorn.show()  # Update the display

# Main function
if __name__ == "__main__":
    try:
        message = """
Paw Patrol, Paw Patrol, we'll be there on the double
Whenever there's a problem 'round Adventure Bay
Ryder and his team of pups will come and save the day
Marshall, Rubble, Chase, Rocky, Zuma, Skye, they're on the way
Paw patrol, Paw Patrol, whenever you're in trouble
Paw Patrol Paw Patrol, we'll be there on the double
No job's too big, no pup's too small
Paw Patrol, we're on the roll
So here we go Paw Patrol!
        """
        aconnect_process = subprocess.Popen(['aconnect', '-x'])
        espeak_process = subprocess.Popen(['espeak', '-s', '140', '--stdout', message], stdout=subprocess.PIPE)

        # aplay_process = subprocess.Popen(['aplay', '-q'], stdin=espeak_process.stdout)
        
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 22050

        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        frames_per_buffer=CHUNK)

        data = espeak_process.stdout.read(CHUNK)
        # play stream (3)
        while len(data) > 0:
            stream.write(data)
            audiodata = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(audiodata.astype(np.float32) ** 2))  # Calculate RMS across the entire array
            control_leds(rms)


            data = espeak_process.stdout.read(CHUNK)

        # stop stream (4)
        stream.stop_stream()
        stream.close()

        stream.stop_stream()
        stream.close()
        p.terminate()
    except subprocess.CalledProcessError as e:
        print("Error:", e.output.decode('utf-8'))  # Print error output