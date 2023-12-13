#Description: locate the direction of the sound source

import numpy as np
from scipy.io.wavfile import read
import matplotlib.pyplot as plt

max_values =[]
max_values_times = []

fs, y = read("PP2Data/MonoTrack.wav")

#Überprüfung ob Mono oder Stereo und ggf. Konvertierung
print(f"Anzahl der Kanäle des Wave-Files: {y.ndim}")
if y.ndim == 1:
    y = np.column_stack((y,y))
    n_tracks = len(y[0])
    print(f"**Converted to Stereo**")


for i in range(0, n_tracks):
    plt.plot(y[:,i])
    plt.title(f"Track: {i}")
    plt.show()
    #return max value and its time
    max_value = np.max(y[:,i])
    max_values.append(max_value)
    max_value_time = np.argmax(y[:,i])/fs
    max_values_times.append(max_value_time)
    print(f"Track: {i}\nmax value: {max_value}\nmax value time: {max_value_time}")

print(max_values)
print(max_values_times)

#Ermittlung des Winkels über Laufzeitdifferenz
if(max_values_times[0] < max_values_times[1]):
    print("Schallquelle befindet sich links")
    differenz = max_values_times[1] - max_values_times[0]

else:
    print("Schallquelle befindet sich rechts")






