import pyttsx3
import multiprocessing
import time
import queue

def speech_digester_loop(sayQ):
    engine = pyttsx3.init()
    engine.setProperty('rate',500)
    engine.startLoop(False)
    ended=True
    def onEnd(name,completed):
        nonlocal ended
        ended=True
    engine.connect('finished-utterance',onEnd)
    localQ=[]
    while True:
        try:
            nextUtterance=sayQ.get(False)
        except queue.Empty:
            pass
        if nextUtterance:
            localQ.append(nextUtterance)
        if (len(localQ)) and ended:
            if (localQ[0]=="terminate"):
                break
            ended=not localQ[0][1] # if we must wait for end then set ended to false
            engine.stop()
            engine.say(localQ[0][0]) # unfortunately this is blocking on windows
            localQ.pop(0)
        engine.iterate()
    # clean up
    engine.endLoop()

sayQ=None
def output_text(text,waitFinish=False):
    global sayQ
    print (text)
    sayQ.put((text,waitFinish))

def all_text_complete():
    global sayQ
    sayQ.put("terminate")

def start_engine():
    global sayQ
    multiprocessing.freeze_support()
    sayQ = multiprocessing.Queue()
    speechThread = multiprocessing.Process(target=speech_digester_loop,args=(sayQ,))
    speechThread.start()

if __name__=="__main__":
    start_engine()
    output_text("hello world",True)
    output_text("i bet you just copied the code and ran it",True)
    output_text("anyways, the wait for finish doesnt work")
    output_text("maybe you can split the string into words before putting it on the queue")
    all_text_complete()