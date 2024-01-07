#Gruppe 7
#PP3

#importe
import numpy as np
from scipy.io.wavfile import read
from scipy.io.wavfile import write
import matplotlib.pyplot as plt
import sounddevice as sd
import time

#Setze True oder False für die Programme Sinusanalyse, AudioFileAnalyse und ReverseEcho
#Wenn True, dann wird das Programm ausgeführt. Wenn mehrere Programme True sind, dann werden diese nacheinander ausgeführt.
Sinusanalyse = False
AudioFileAnalyse = True
ReverseEcho = False

#Setze Arbeitspunkt und Klirrfaktor-Ordnung für Klipping und Limiter
ArbeitspunktClipping = 0.5
ArbeitspunktLimiter = -5        #Wert zwischen -50 und 0
KlirrfaktorOrdnung = 3

#Testsignale:
def sine(duration):
    rateArray = np.arange(0, duration, 1 / 48000)
    sine = np.sin(2 * np.pi * 3 * rateArray)
    return 48000, sine

def PlugSine(duration):
    rateArray = np.arange(0, duration, 1 / 48000)
    fade = np.logspace(0, -3, int(48000 * duration), endpoint=False)
    sine = fade * np.sin(2 * np.pi * 440 * rateArray)
    return 48000, sine

def AudioFile():
    fs, data = read("PP2Data/MonoTrack.wav")
    data = data / np.max(np.abs(data)) #Normierung
    return fs, data

#Total Harmonic Distortion und Klirrfaktor für Analyse
def THD(vorher, nachher):
    # Berechne die Verzerrungsleistung (Harmonische Verzerrungen)
    verzerrungsleistung = np.sum((nachher - vorher) ** 2)

    # Berechne die Leistung des Grundsignals
    leistung = np.sum(vorher ** 2)

    # Berechne den Klirrfaktor (als Verhältnis der Verzerrungsleistung zur Grundsignal-Leistung)
    THD = np.sqrt(verzerrungsleistung / leistung)
    THD = THD * 100 # Umrechnung in Prozent
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
    harmonic_distortion = harmonic_distortion * 100 # Umrechnung in Prozent

    return harmonic_distortion


#Aufgabenteil A: Clipping
def clip_signal(signal, AP):
    clipped_signal = np.clip(signal, -AP, AP)
    return clipped_signal


#Aufgabenteil B: Limiter
def system_b(file,Komp_Lim,stat_dyn,threshold,ratio,attack,release,makeupgain):

    ## Zentrale Schalter
    #wahl_dynamik = 1  # wenn wahl_dynamik = 1: dynamische Kennlinie, wenn 0: statische Kennlinie
    #wahl_funktion = 'Lim' # Wahl:'Lim:' Limiter, 'Komp': Kompressor

    x_ref = pow(2, 15)-1  #Referenzwert für Pegel

    ####################################
    # Einlesen Testsignal
    #Fs, x = read("PP2Data/MonoTrack.wav")
    Fs = file[0]
    x = file[1]

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

    x_ref = np.abs(np.max(x))  #Referenzwert für Pegel
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

    #dynamische Kennlinie
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

    y_a = (y_a/x_ref)   # normieren, zur grafischen Darstellung


    ###################################
    # Plots:

    dimension = max(g_a)
    fig, ax = plt.subplots()
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None,
                        wspace=None, hspace=0.5)  # Abstand zwischen Subplots

    ax.plot(t, y_a)  # Plotten von y über t
    ax.plot(t, g_a)  # Plotten von gain über t

    # Einrichtung der Achsen:
    ax.set_xlim(0, dauer_s)
    ax.set_ylim(-dimension, dimension)
    ax.set_xlabel('$t$ in s')
    ax.set_ylabel('$y$($t$),$g$($t$) ')
    ax.grid(True)
    plt.show()

    return y_a


#Reversed Echo
def reverseEcho(file, delay, decay):                         # delay = Verzögerungszeit, decay = Abklingzeit

    fs = file[0]
    file = file[1]
    fsDelay = int(delay * fs)                                  # Verzögerung in Abtastpunkten berechnen

    # Reverse Echo
    emptyArr = np.zeros_like(file)
    emptyArr[fsDelay:] = file[:-fsDelay] * decay            # Echo erzeugen
    reverse_echo = emptyArr[::-1]                                      # Echo rückwärts abspielen, Werte von echo in umgekehrter Reihenfolge
    EchoOut = file + reverse_echo                                  # Ausgabe durch Originalsound und reverse Echo
    EchoOut = EchoOut * np.max(np.abs(EchoOut))                     # zurück in den ursprünglichen Wertebereich
    return EchoOut

#Vergleichende Plots von Ein- und Ausgangssignal
def plotInOut(EingangsSignal, AusgangsSignal, title='', fs=48000):
    # Längen der Signale
    length_input = len(EingangsSignal)
    length_output = len(AusgangsSignal)

    # Zeitvektoren
    t_input = np.linspace(0, length_input / fs, length_input, endpoint=False)
    t_output = np.linspace(0, length_output / fs, length_output, endpoint=False)

    # Plot
    plt.figure(figsize=(10, 7))
    #Für Input
    plt.subplot(2, 1, 1)
    plt.plot(t_input, EingangsSignal, label='Eingangssignal')
    plt.title(title + 'Eingangssignal (Original)')
    plt.xlabel('Zeit')
    plt.ylabel('Amplitude')
    plt.legend()

    #Für Output
    plt.subplot(2, 1, 2)
    plt.plot(t_output, AusgangsSignal, label='Ausgangssignal', color='red')
    plt.title(title + 'Ausgangssignal (Bearbeitet)')
    plt.xlabel('Zeit')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.tight_layout()
    plt.show()


####################################################### Programmablauf #######################################################

if Sinusanalyse:
    print(f"\n****Sinusanalyse****\nEine Sinusfunktion (3 Hz) wird in dem von ihnen gewählten Arbeitspunkt: {ArbeitspunktClipping} geclipped. Es wird der Klirrfaktor ({KlirrfaktorOrdnung}. Ordnung) und die THD berechnet.\nSie erhalten außerdem einen Plot des bearbeiteten Signals.")
    time.sleep(5)
    plotInOut(sine(1)[1], clip_signal(sine(1)[1], ArbeitspunktClipping), 'Clipped Sinus-')
    print(f"\nSinus THD: {round(THD(sine(1)[1], clip_signal(sine(1)[1], ArbeitspunktClipping)), 2)} %")
    print(f"Sinus Klirrfaktor: {round(KlirrfaktorArbeitspunkt(sine(1)[1], 48000, ArbeitspunktClipping, 0.1, KlirrfaktorOrdnung), 2)} %")
    time.sleep(2)
    print(f"\nDer Sinus wird nun mit dem Limiter bearbeitet. Es wird der Klirrfaktor und die THD berechnet.\nSie erhalten auch hiervon einen Plot des Signales.")
    time.sleep(4)
    x = system_b(sine(1),'Lim',0, ArbeitspunktLimiter,2,1,5,5)
    plotInOut(sine(1)[1], x, 'Compressed Sinus-')
    print(f"\nSinus THD: {round(THD(sine(1)[1], x),2)} %")
    print(f"Sinus Klirrfaktor: {round(KlirrfaktorArbeitspunkt(x, 48000, ArbeitspunktClipping, 0.1, KlirrfaktorOrdnung), 2)} %")
    print("\nEnde der Sinusanalyse!")

if AudioFileAnalyse:
    print(f"\n****Analyse eines Audiofiles****\nEin Audiofile wird in dem von ihnen gewählten Arbeitspunkt: {ArbeitspunktClipping} geclipped. Es wird der Klirrfaktor ({KlirrfaktorOrdnung}. Ordnung) und die THD berechnet.\nSie erhalten außerdem einen Plot des bearbeiteten Signals.")
    time.sleep(5)
    plotInOut(AudioFile()[1], clip_signal(AudioFile()[1], ArbeitspunktClipping), 'Clipped Audiofile-')
    print(f"\nAudio Datei THD: {round(THD(AudioFile()[1], clip_signal(AudioFile()[1], ArbeitspunktClipping)), 2)} %")
    print(f"Audio Datei Klirrfaktor: {round(KlirrfaktorArbeitspunkt(AudioFile()[1], AudioFile()[0], ArbeitspunktClipping, 0.1, KlirrfaktorOrdnung), 2)} %")
    time.sleep(3)
    print(f"\nDas Audiofile wird nun mit dem Limiter bearbeitet. Es wird der Klirrfaktor und die THD berechnet.\nSie erhalten auch hiervon einen Plot des Signales.")
    time.sleep(4)
    x = system_b(AudioFile(),'Lim',1, ArbeitspunktLimiter ,0,0.01,0.2,0)
    plotInOut(AudioFile()[1], x, 'Compressed Audiofile-')
    print(f"\nAudio Datei THD: {round(THD(AudioFile()[1], x),2)} %")
    print(f"Audio Datei Klirrfaktor: {round(KlirrfaktorArbeitspunkt(x, 48000, ArbeitspunktClipping, 0.1, KlirrfaktorOrdnung), 2)} %")
    time.sleep(3)
    print("\nJetzt hören sie das bearbeitete Audiofile. Zuerst das Original, dann das clipping und dann das Limiter Signal.")
    #Abspielen der bearbeiteten Audiodatei
    sd.play(AudioFile()[1])
    sd.wait()
    sd.play(clip_signal(AudioFile()[1], ArbeitspunktClipping))
    sd.wait()
    sd.play(x)
    sd.wait()
    print("\nFertig!")

    #Reverse Echo mit Audiodatei

if ReverseEcho:
    print(f"\n****Reverse Echo****\nEin Audiofile wird mit einem Echo bearbeitet. Es wird ein Echo mit den Parametern Delay = 0.5s und Decay = 0.5s erzeugt.\nSie erhalten außerdem einen Plot des bearbeiteten Signals.")
    time.sleep(5)
    plotInOut(AudioFile()[1], reverseEcho(AudioFile(), 0.5, 0.5), 'Reversed Echo Audiofile-')
    sd.play(AudioFile()[1])
    sd.wait()
    sd.play(reverseEcho(AudioFile(), 0.5, 0.5))
    sd.wait()

    print(f"\nNun wird nochmal ein Anschauliches Signal bearbeitet. Es wird ein Echo mit den Parametern Delay = 0.5s und Decay = 0.5s erzeugt.\nSie erhalten außerdem einen Plot des bearbeiteten Signals.")
    time.sleep(5)
    plotInOut(PlugSine(1)[1], reverseEcho(PlugSine(1), 0.5, 0.5), 'Reversed Echo PlugSinus-')
    sd.play(PlugSine(1)[1])
    sd.wait()
    time.sleep(1)
    sd.play(reverseEcho(PlugSine(1), 0.5, 0.5))
    sd.wait()
    print("\nEnde des Reverse Echo Programmes!")




