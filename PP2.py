
import numpy as np
from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import sounddevice as sd
import PP2Gui as gui



fs, y = read("PP2Data/StereoTrack.wav")

#Überprüfung ob Mono oder Stereo und ggf. Konvertierung
print(f"Anzahl der Kanäle des Wave-Files: {y.ndim}")
if y.ndim == 1:
    LR = np.zeros((len(y), 2))
    LR[:, 0] = y[:, 0]
    LR[:, 1] = y[:, 0]
    print(f"**Converted to Stereo**")
else:
    LR = y
    print(f"**Stereo**")
LRBackup = LR
#Lineares Panning

def linear_pan(LR, grad):
    RAD = grad*(np.pi/180) #Umrechnung von Grad in Radiant
    for i in range(len(LR[:, 0])):
        LR[:, 0][i] *= (2 / np.pi) * (np.pi / 2 - RAD)
        LR[:, 1][i] *= (2 / np.pi) * RAD






def play():
    sd.play(LR, fs)
    sd.wait()

linear_pan(LRBackup, 120)
play()






