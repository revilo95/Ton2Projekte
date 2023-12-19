#Ad a reversed Echo to the soundfile
import numpy as np
from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import sounddevice as sd

#make a sinus

freq = 440
fs = 48000
duration = 1
n = 15

rateArray = np.arange(0, duration, 1 / fs)
fade = np.logspace(0, -3, int(fs * duration), endpoint=False)
sine = fade * np.sin(2 * np.pi * freq * rateArray)


delayArray = np.zeros(fs*duration*n)
dings = int((fs/1000)*500)
delayArray[0:len(sine)] = sine
#reversed sine:
revsine = sine[::-1]

for i in range(0, n):
    delayArray[dings*i:len(revsine)+dings*i] = revsine
    revsine = revsine * 0.8





"""
for i in range(0, n):
    delayArray[(len(sine))*i:len(sine)*(i+1)] = sine/i
"""
#################################################################
sd.play(delayArray, fs)
sd.wait()
plt.plot(delayArray)
plt.show()








