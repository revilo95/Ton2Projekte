
import numpy as np
from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import sounddevice as sd
import PP2Gui as gui


max_values =[]
max_values_times = []
E_array = []

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

#Lineares Panning
def left_channel(θ):
    return (2 / np.pi) * (np.pi / 2 - θ)
def right_channel(θ):
    return (2 / np.pi) * θ
grad = 45
# Apply panning to the audio samples
panning_angle = grad*(np.pi/180)
for i in range(len(LR[:, 0])):
    LR[:, 0][i] *= left_channel(panning_angle)
    LR[:, 1][i] *= right_channel(panning_angle)

sd.play(LR, fs)
sd.wait()







