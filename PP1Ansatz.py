import numpy as np
from scipy.io.wavfile import read
import matplotlib.pyplot as plt

fs, y = read("Datei_G.wav")

y_normiert = (y*fs)/((2**15)-1)
n = 1/fs
n_anzahl = len(y)
E_ges = np.sum(np.square(y_normiert))/fs
E_array = []
timescale = np.linspace(0, n_anzahl/fs , num=n_anzahl)

for i in range(0, len(y)):
    E = np.sum(np.square(y_normiert[i:]))/fs
    E_log = 10*np.log10(E/E_ges)
    E_array.append(E_log)

#search the time where the energy is -10dB
t10 = None
for i in range(0, len(E_array)):
    if E_array[i] <= -10:
        if t10 is None:
            t10 = i/fs

t20 = None
for i in range(0, len(E_array)):
    if E_array[i] <= -20:
        if t20 is None:
            t20 = i/fs

T60 = (60*(t20-t10))/10
print(f" t10: {t10}\n t20: {t20}\n T60: {T60}")

#Sprachverständlichkeit C50 und C80
C50 = np.sum(np.square(y_normiert[0:round(fs/2)]))/fs
C80 = np.sum(np.square(y_normiert[0:round(fs*0.8)]))/fs
print(f" C50: {C50}\n C80: {C80}\n Gesamtenergie: {E_ges}")


fig, axes = plt.subplots()
axes.plot(timescale, E_array, label="LE(t)")
plt.grid()
plt.legend()
plt.title("LE(t)")
plt.xlabel("Zeit [s]")
plt.ylabel("Energie [dB]")
plt.show()
