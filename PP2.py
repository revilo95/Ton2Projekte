
import numpy as np
from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import sounddevice as sd
#import PP2Gui as gui



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
LRBackup = LR.copy()

############################################  PANNING DURCH PEGELDIFFERENZEN

#Lineares Panning
def linear_pan(Arr, grad):
    RAD = grad*(np.pi/180) #Umrechnung von Grad in Radiant
    for i in range(len(Arr[:, 0])):
        Arr[:, 0][i] *= (2 / np.pi) * (np.pi / 2 - RAD)
        Arr[:, 1][i] *= (2 / np.pi) * RAD
    return Arr

#Panning mit Konstanter Leistung
def konstant_pan(Arr, grad):
    RAD = grad*(np.pi/180) #Umrechnung von Grad in Radiant
    for i in range(len(Arr[:, 0])):
        Arr[:, 0][i] *= np.cos(RAD)
        Arr[:, 1][i] *= np.sin(RAD)
    return Arr
#-4.5dB Panning: Mix aus Konstant und Linear
def mix_pan(Arr, grad):
    RAD = grad*(np.pi/180) #Umrechnung von Grad in Radiant
    for i in range(len(Arr[:, 0])):
        Arr[:, 0][i] *= np.sqrt((2/np.pi) * (np.pi/2 - RAD) * np.cos(RAD))
        Arr[:, 1][i] *= np.sqrt((2/np.pi) * RAD * np.sin(RAD))
    return Arr

#Ton wandert von links nach rechts  unelegante Lösung
for i in range(0, 90, 5):
    LR = LRBackup.copy()
    sig = linear_pan(LR, i)
    print(i)
    # konstant_pan(LR, i)
    # Mix_pan(LR, i)
    sd.play(sig,fs)
    sd.wait()
    LR = LRBackup

############################################  PANNING DURCH LAUFZEITDIFFERENZEN






