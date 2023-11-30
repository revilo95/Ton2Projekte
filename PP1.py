import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

rate, data = sp.io.wavfile.read('Datei_G.wav')
n = 1/rate #Schrittweite des arrays
normedData = (data/n)/2**15 #Normieren der Daten

print(normedData)

lenght = len(normedData)#Länge des Arrays
duration = lenght/rate
print(f"Länge(sek): {duration}")
Energie = np.sum(np.square(data))/rate
print(f"Energie(Joule): {Energie}")


#Um werte für T10 zu erhalten. Später: T15-T5
t5 = None
t15 = None
LE_Werte = list()
Zeit_Werte = list()

for z in range(0, duration, 100):
    E = np.sum(np.square(normedData[z:]))/rate  # zeitabhängige Energie-Abnahme, hundert erste Werte in einem Array speichern
    LE_t = 10*np.log10(E/duration)     # Berechnung LE(t) in dB
    LE_Werte.append(LE_t)
    Zeit_Werte.append(z/rate)

# T5 und T15
    if LE_t <= -5:   # Energie fällt auf -5dB
        if t5 is None:     # Wird nur 1x überschrieben
            t5 = z/rate

    if LE_t <= -15:  # Energie fällt auf -15dB
        if t15 is None:     # Wird nur 1x überschrieben
            t15 = z/rate




plt.plot(normedData)
plt.show()
