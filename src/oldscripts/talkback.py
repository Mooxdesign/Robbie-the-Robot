import os
from openai import OpenAI




#!/usr/env/python3
 
import speech_recognition as sr

client = OpenAI()
# import unicornhat as unicorn
import os

r = sr.Recognizer()
m = sr.Microphone()

for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))


# unicorn.set_layout(unicorn.AUTO)
# unicorn.rotation(0)
# unicorn.brightness(0.4)
try:
    print("A moment of silence, please...")
    with m as source: 
        r.adjust_for_ambient_noise(source, duration=6)
        r.energy_threshold += 180
        print(r.energy_threshold)
        
    while True:
        print("Say something!")
        # unicorn.set_all(0,255,0)
        # unicorn.show()
        with m as source:
            audio = r.listen(source)
        print("Got it! Now to recognize it...")
        # unicorn.set_all(255,191,0)
        # unicorn.show()
        try:
            value = r.recognize_google(audio, language='en-GB')
            print(value)

            if str is bytes:
                value = format(value).encode("utf-8")

            completion = client.chat.completions.create(
              model="gpt-3.5-turbo",
              messages=[
                {
                  "role": "system",
                  "content": "You are Robbie the Robot, a robot who is being built by Heidi and Heidi's daddy. Your responses should be funny, kind and helpful, and suitable for a first-grade student."
                  # "content": "You are Robbie the Robot. Your responses should be rude but funny. My friend Jethro keeps procrastinating and should get on with his work. He is not here though."
                },
                {
                  "role": "user",
                  "content": value
                }
              ],
              temperature=0,
              max_tokens=128,
              top_p=1,
              frequency_penalty=0,
              presence_penalty=0
            )

            message = completion.choices[0].message.content
            print(message)
            os.system('espeak -s 140 "'+message+'"')


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