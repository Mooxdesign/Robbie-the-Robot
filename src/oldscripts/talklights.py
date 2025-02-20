#!/usr/env/python3
 
import speech_recognition as sr
from openai import OpenAI

import subprocess
import numpy as np
import pyaudio
import unicornhat as unicorn

# Initialize global variables for max and min volume
max_volume = float('-inf')
min_volume = float('inf')



client = OpenAI()
# import unicornhat as unicorn

r = sr.Recognizer()
m = sr.Microphone(0)

# r.energy_threshold = 140
# r.dynamic_energy_threshold = True  

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 22050

p = pyaudio.PyAudio()

unicorn.brightness(1)

# Function to control LEDs based on volume
def control_leds(volume):
    # print(volume)
    global max_volume, min_volume
    
    # Update max and min volume
    max_volume = max(max_volume, volume)
    min_volume = min(min_volume, volume)
    
    if max_volume == min_volume:
        normalized_volume = 0
    else:
        normalized_volume = (volume - min_volume) / (max_volume - min_volume)

    normalized_volume = 0.1 + 0.5*normalized_volume 
    # Use the normalized value to adjust brightness
    unicorn.set_all(0, int(255 * normalized_volume), 0)
    unicorn.show()  # Update the display

# Main function
if __name__ == "__main__":
    try:
        print("A moment of silence, please...")
        # with m as source: 
        #     print("Please wait. Calibrating microphone...")   
            # listen for 5 seconds and create the ambient noise energy level   
            # r.adjust_for_ambient_noise(source, duration=5)  
            # r.dynamic_energy_threshold = True  
        while True:

            print("Say something!")
            # unicorn.set_all(0,255,0)
            # unicorn.show()
            with m as source: 
                r.adjust_for_ambient_noise(source, duration=6)
                r.energy_threshold += 180
                audio = r.listen(source)
                print(r.energy_threshold)
            # unicorn.set_all(255,191,0)
            # unicorn.show()
            print("Got it! Now to recognize it...")
            try:
                value = r.recognize_google(audio, language='en-GB')

                if str is bytes:
                    value = format(value).encode("utf-8")

                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                        "role": "system",
                        "content": "You are Robbie the Robot, a robot who is being built by Heidi and Heidi's daddy. Your responses should be funny, kind and helpful, and suitable for a first-grade student."
                        # "content": "You are Robbie the Robot. Your responses should be rude but funny. I keep procrastinating and should get on with my work"
                        },
                        {
                        "role": "user",
                        "content": value
                        }
                    ],
                    temperature=0,
                    max_tokens=92,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )

                message = completion.choices[0].message.content
                print(message)

                aconnect_process = subprocess.Popen(['aconnect', '-x'])
                espeak_process = subprocess.Popen(['espeak', '-s', '140', '--stdout', message], stdout=subprocess.PIPE)

                stream = p.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True,
                    frames_per_buffer=CHUNK
                )

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

                unicorn.set_all(0, 0, 0)
                unicorn.show()  # Update the display
                
                # os.system('espeak -s 140 "'+message+'"')


                # printing audio
                # output = "You said " + value

                # print(output)
                # os.system('espeak "'+output+'"')

            except sr.UnknownValueError:
                print("Oops! Didn't catch that")
                # unicorn.set_all(255,0,0)
                # unicorn.show()
                # os.system('espeak "pardon?"')
            except sr.RequestError as e:
                print("Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
                # unicorn.set_all(255,0,0)
                # unicorn.show()
    except KeyboardInterrupt:
        pass

p.terminate()
