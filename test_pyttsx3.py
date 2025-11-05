import pyttsx3
import time
import gc
for i in range(3):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    print(f"Saying utterance {i+1}")
    engine.say(f"This is utterance number {i+1}")
    engine.runAndWait()
    engine.stop()
