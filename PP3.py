#Ad a reversed Echo to the soundfile
import numpy as np
from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import sounddevice as sd

#make a sinus
def PlugSine(duration):
    rateArray = np.arange(0, duration, 1 / 48000)
    fade = np.logspace(0, -3, int(48000 * duration), endpoint=False)
    sine = fade * np.sin(2 * np.pi * 440 * rateArray)
    return sine

def reversedEcho(signal, fs, delay, decay):

    delaySamples = int((fs/1000)*delay)
    delayArray = np.zeros(fs*(delay*1000))
    delayArray[0:len(signal)] = signal
    #reversed signal:
    revSignal = signal[::-1]

    for i in range(0, decay):
        delayArray[delaySamples*i:len(revSignal)+delaySamples*i] = revSignal
        revSignal = revSignal * 0.8

    return delayArray


"""
for i in range(0, n):
    delayArray[(len(sine))*i:len(sine)*(i+1)] = sine/i
"""
#################################################################
#sd.play(reversedEcho(PlugSine()[1], PlugSine()[0], 100, 100), PlugSine()[0])
#.wait()
plt.plot(PlugSine())
plt.show()








