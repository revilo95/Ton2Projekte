
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

"""
def linearPanning(RKanal, LKanal, panning):
    print(panning)
    LR = np.zeros((len(RKanal), 2))
    RKanal = RKanal * 0.5
    LKanal = LKanal * 0.5
    LKanal = LKanal * ((100 - panning) * 0.01)
    RKanal = RKanal * (panning*0.01)
    LR[:, 0] = (2 / np.pi) * (np.pi / 2 + LKanal)
    LR[:, 1] = (2 / np.pi) *  RKanal


    #LR = np.hstack((LKanal, RKanal))
    sd.play(LR, fs)
    sd.wait()

linearPanning(RechterKanal, LinkerKanal, 10)
"""


"""
#Normierung
y_normiert = (y*fs)/((2**15)-1)
E_ges = np.sum(np.square(y_normiert))/fs

sd.play(y, fs)
sd.wait()

print("Is cooking...")
for i in range(0, len(y_normiert), 100):
    E = np.sum(np.square(y_normiert[i:]))/fs
    E_log = 10*np.log10(E/E_ges)
    E_array = np.append(E_array, E_log)
print("...done")

for i in range(0, y_normiert.ndim):
    #Plot der Signale
    plt.subplot(2, 1, i+1)
    plt.plot(y_normiert[:,i])
    plt.title(f"Track: {i}")


    #return max value and its time
    max_value = np.max(y_normiert[:,i])
    max_values.append(max_value)
    max_value_time = np.argmax(y_normiert[:,i])/fs
    max_values_times.append(max_value_time)
    print(f"Track: {i}\nmax value: {max_value}\nmax value time: {max_value_time}")

#Plot der Energien
plt.show()

#Ermittlung des Winkels über Laufzeitdifferenz
if(max_values_times[0] < max_values_times[1]):
    print("Schallquelle befindet sich links")
    differenz = max_values_times[1] - max_values_times[0]

else:
    print("Schallquelle befindet sich rechts")
"""





