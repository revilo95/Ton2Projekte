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


#Erzeugung eines exponentiell abklingenden Sinus
rateArray = np.arange(0, duration, 1 / fs)
fade = np.logspace(0, -3, int(fs * duration), endpoint=False)
sine = fade * np.sin(2 * np.pi * freq * rateArray)


delayArray = np.zeros(fs*duration*n)

delayInMs = 200
timeInSamples = int((fs/1000)*delayInMs)

#reversed sine:
revAudio = sine[::-1]
plt.plot(revAudio)
plt.plot(sine)
plt.show()


for i in range(0, n):
    delayArray[timeInSamples*i:len(revAudio)+timeInSamples*i] = revAudio
    revAudio = revAudio * 0.8
#delayArray[0:len(sine)] = sine


for i in range(0, n):
    delayArray[(len(sine))*i:len(sine)*(i+1)] = sine/i


#################################################################
sd.play(delayArray, fs)
sd.wait()
plt.plot(delayArray)
plt.show()








