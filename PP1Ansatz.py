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

print(E_ges)

fig, axes = plt.subplots()
axes.plot(timescale, E_array, label="LE(t)")
plt.grid()
plt.legend()
plt.title("LE(t)")
plt.xlabel("Zeit [s]")
plt.ylabel("Energie [dB]")
plt.show()
