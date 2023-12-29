import numpy as np
from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import sounddevice as sd



#Testsignale:
def sine(duration):
    rateArray = np.arange(0, duration, 1 / 48000)
    sine = np.sin(2 * np.pi * 3 * rateArray)
    return sine

def PlugSine(duration):
    rateArray = np.arange(0, duration, 1 / 48000)
    fade = np.logspace(0, -3, int(48000 * duration), endpoint=False)
    sine = fade * np.sin(2 * np.pi * 440 * rateArray)
    return sine

def AudioFile():
    fs, data = read("PP2Data/MonoTrack.wav")
    return data

#Aufgabenteil A: Clipping
def clip_signal(signal, AP):
    clipped_signal = np.clip(signal, -AP, AP)
    return clipped_signal

#Total Harmonic Distortion und Klirrfaktor für Analyse
def THD(vorher, nachher):
    # Berechne die Verzerrungsleistung (Harmonische Verzerrungen)
    verzerrungsleistung = np.sum((nachher - vorher) ** 2)

    # Berechne die Leistung des Grundsignals
    leistung = np.sum(vorher ** 2)

    # Berechne den Klirrfaktor (als Verhältnis der Verzerrungsleistung zur Grundsignal-Leistung)
    THD = np.sqrt(verzerrungsleistung / leistung)
    return THD


def KlirrfaktorArbeitspunkt(signal, fs, t_arbeitspunkt, delta_t, fundamental_order):
    # Bestimme den Index des Arbeitspunkts im Signal
    index_arbeitspunkt = int(t_arbeitspunkt * fs)

    # Definiere den Bereich um den Arbeitspunkt
    index_start = max(0, index_arbeitspunkt - int(0.5 * delta_t * fs))
    index_end = min(len(signal), index_arbeitspunkt + int(0.5 * delta_t * fs))

    # Extrahiere das Fenster um den Arbeitspunkt
    window_signal = signal[index_start:index_end]

    # Berechne die Fourier-Transformierte des Fensters
    fft_signal = np.fft.fft(window_signal)

    # Bestimme die Amplitude der Grundwelle im Fenster
    fundamental_amplitude = np.abs(fft_signal[fundamental_order])

    # Bestimme die Amplitude der harmonischen Verzerrung im Fenster
    harmonic_amplitude = np.abs(fft_signal[fundamental_order * 2])

    # Berechne den Klirrfaktor der n-ten Ordnung im Fenster um den Arbeitspunkt
    harmonic_distortion = harmonic_amplitude / fundamental_amplitude

    return harmonic_distortion


#Aufgabenteil B: Limiter
def system_b(Komp_Lim,stat_dyn,threshold,ratio,attack,release,makeupgain):

    ## Zentrale Schalter
    #wahl_dynamik = 1  # wenn wahl_dynamik = 1: dynamische Kennlinie, wenn 0: statische Kennlinie
    #wahl_funktion = 'Lim' # Wahl:'Lim:' Limiter, 'Komp': Kompressor

    x_ref = pow(2, 15)-1  #Referenzwert für Pegel

    ####################################
    # Einlesen Testsignal
    Fs, x = read("testsignal_a.wav")
    anz_werte = x.size
    dauer_s = anz_werte/Fs
    deltat = 1./(Fs)  #Zeit-Schritt, float
    t = np.arange(x.size)/float(Fs)

    #umwandeln in float und normieren
    x = np.array(x, dtype=np.float64)
    x_norm = x/x_ref   # Normierung, falls erforderlich/gewünscht


    attack_i = attack*Fs
    release_i = release*Fs

    # smoothing detector filter:
    faktor = np.log10(9)
    a_R = np.e **(-faktor/(attack_i))
    a_T = np.e **(-faktor/(release_i))


    ## x_ref = np.abs(np.max(x))  #Referenzwert für Pegel
    u_thresh = 10**(threshold/20)*x_ref


    if ratio == 0: ratio = 0.1



    ##################
    ## Kompression:
    PegelMin = -95   # Pegelgrenze nach unten in dB

    # Eingangssingal als Pegel:
    Lx = np.zeros(anz_werte)
    Lx[1:] = 20*np.log10(np.abs(x[1:])/x_ref)
    Lx[0] = Lx[1]             # damit nicht log(0)

    # Begrenzung des minimalen Pegels (mathematisch erforderlich)
    for i in range(anz_werte):
        if Lx[i] < PegelMin:
            Lx[i] = PegelMin

    # Vorbereitung der arrays:
    Lx_c = np.zeros(anz_werte)      # Pegel(x) nach statischer Kompressor-Kennlinie
    Lg_c = np.zeros(anz_werte)      # Pegel(gain) statisch (um wieviel wurde Lx gedämpft)
    Lg_s = np.zeros(anz_werte)       # Pegel(gain) dynamisch (smoothed, mit t_attack und t_release)
    Lg_M = np.zeros(anz_werte)       # Pegel(gain) dynamisch (smoothed, mit t_attack und t_release) mit M
    g_a = np.zeros(anz_werte)       # linearer gain dynamisch (smoothed, mit t_attack und t_release)

    # Berechnung der momentanen Verstärkung/Dämpfung
    ## Limiter

    for i in range(anz_werte):
        if Komp_Lim == 'Lim':   ## Limiter
            if Lx[i] >= threshold:
                 Lx_c[i] = threshold
            else:
                 Lx_c[i] = Lx[i]
        else:  # Kompressor
            if Lx[i] > threshold:
                 Lx_c[i] = threshold + (Lx[i]-threshold)/threshold
            else:
                 Lx_c[i] = Lx[i]

        Lg_c[i] = Lx_c[i] - Lx[i]   # Dämpfung von Lx zum Zeitpunkt i

    #  dynamische Kennlinie
        Lg_s[0] = 0.0 #20*np.log10(x[0]/x_ref) #!!! Startwert für dynamische Dämpfung
        if stat_dyn == 1:
            if i > 0:
                if Lg_c[i] > Lg_s[i-1]:     # Release
                    Lg_s[i] = a_T*Lg_s[i-1]+ (1-a_T)*Lg_c[i]
                else:                       # Attack
                    Lg_s[i] = a_R*Lg_s[i-1]+ (1-a_R)*Lg_c[i]
        else:
            Lg_s[i] = Lx_c[i]

    # Anwenden der momentanen Verstärkung/Dämpfung
    if stat_dyn == 1:
       Lg_M = Lg_s + makeupgain

       g_a = 10**(Lg_M/20)        #lineare Verstärkung, zeitabhängig
       y_a = x * g_a             # Ausgangssignal; hier ist das Vorzeichen im x vorhanden
    else:
       g_mu = 10**(makeupgain/20)     # verstärkung ergibt sich aus makeup-gain
       y_a = 10**(Lx_c/20)*x_ref * g_mu     # y ist geclippter Eingang

       for i in range (anz_werte):  # Vorzeichen ist verloren durch log, daher hinzufügen
            if x[i] < 0:
                y_a[i] = -y_a[i]

    y_a = y_a/x_ref   # normieren, zur grafischen Darstellung

def reverse_echo(delay, decay):                         # delay = Verzögerungszeit, decay = Abklingzeit

    fs, datei = read("PP2Data/MonoTrack.wav")
    #datei = PlugSine(1)
    #fs = 48000
    datei = datei/np.max(np.abs(datei))                             # Datei auf [-1, 1] normalisieren
    sample_delay = int(delay * fs)                                  # Verzögerung in Abtastpunkten berechnen

    # Echo
    echo1 = np.zeros_like(datei)
    echo1[sample_delay:] = datei[:-sample_delay] * decay            # Echo erzeugen
    output1 = datei + echo1                                         # Ausgabe durch Originalsound und Echo
    output1 = output1 * np.max(np.abs(output1))                     # zurück in den ursprünglichen Wertebereich

    # Reverse Echo
    echo2 = np.zeros_like(datei)
    echo2[sample_delay:] = datei[:-sample_delay] * decay            # Echo erzeugen
    reverse_echo = echo2[::-1]                                      # Echo rückwärts abspielen, Werte von echo in umgekehrter Reihenfolge
    output2 = datei + reverse_echo                                  # Ausgabe durch Originalsound und reverse Echo
    output2 = output2 * np.max(np.abs(output2))                     # zurück in den ursprünglichen Wertebereich

    datei = datei * np.max(np.abs(datei))
    return output1



#Vergleich der Signale Für Clipping und Limiter
def plotInOut(EingangsSignal, AusgangsSignal):
    # Zeitbereich
    t = np.linspace(0, 1, 48000, endpoint=False)
    # Plot
    plt.figure(figsize=(10, 7))

    plt.subplot(2, 1, 1)
    plt.plot(t, EingangsSignal, label='Eingangssignal')
    plt.title('Eingangssignal')
    plt.xlabel('Zeit')
    plt.ylabel('Amplitude')
    plt.legend()

    plt.subplot(2, 1, 2)
    plt.plot(t, AusgangsSignal, label='Ausgangssignal')
    plt.title('Ausgangssignal')
    plt.xlabel('Zeit')
    plt.ylabel('Amplitude')
    plt.legend()

    plt.tight_layout()
    plt.show()


Sinusanalyse = True
Arbeitspunkt = 0.5

if Sinusanalyse:
    plotInOut(sine(1), clip_signal(sine(1), Arbeitspunkt))
    print(f"THD: {THD(sine(1), clip_signal(sine(1), Arbeitspunkt))}")
    print(f"Klirrfaktor: {KlirrfaktorArbeitspunkt(sine(1), 48000, Arbeitspunkt, 0.1, 10)}")



plt.show()