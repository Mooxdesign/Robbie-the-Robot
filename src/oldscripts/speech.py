#!/usr/env/python3
 
import speech_recognition as sr
# import unicornhat as unicorn
import os

r = sr.Recognizer()
m = sr.Microphone()

# unicorn.set_layout(unicorn.AUTO)
# unicorn.rotation(0)
# unicorn.brightness(0.4)
try:
    print("A moment of silence, please...")
    with m as source: 
        r.adjust_for_ambient_noise(source)
        r.adjust_for_ambient_noise(source, duration=6)
        r.energy_threshold += 180
        print(r.energy_threshold)
        
    while True:
        print("Say something!")
        print(r.energy_threshold)
        # unicorn.set_all(0,255,0)
        # unicorn.show()
        with m as source: audio = r.listen(source)
        print("Got it! Now to recognize it...")
        # unicorn.set_all(255,191,0)
        # unicorn.show()
        try:
            value = r.recognize_google(audio, language='en-GB')

            if str is bytes:
                value = format(value).encode("utf-8")
            # printing audio
            output = "You said " + value

            print(output)
            os.system('espeak "'+output+'"')

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

