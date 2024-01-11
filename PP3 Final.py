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
Sinusanalyse = True
SinHz = 440
AudioFileAnalyse = True
ReverseEcho = True

testdata = 'PP2Data/MonoTrack.wav'

#Setze Arbeitspunkt und Klirrfaktor-Ordnung für Clipping und Limiter
ArbeitspunktClipping = 0.5
KlirrfaktorOrdnung = 2


lim_kompr ='Lim'                #Wahl zwischen Limiter und Kompressor; Eingabe 'Lim' oder 'Komp'
stat_dyn =1                     #Wahl zwischen statischer oder dynamischer Kennlinie; Eingabe 0 oder 1
ArbeitspunktLimiter = -15        #Wert zwischen -50 und 0dB
Ratio =2                        #Verhältnis, in dem der Pegel der Werte, die den Arbeitspunkt überschreiten, verkleinert werden (wird zu 0 bei Limiter)
Attack =0.002                   #Eingabe 0.00002 ... 0.01
Release =0.05                   #Eingabe 0.001 ... 5
MakeUpGain = 3                    #Verstärkung des vorher komprimierten Signals



def sine(duration, Hz=SinHz):
    rateArray = np.arange(0, duration, 1 / 48000)
    sine = np.sin(2 * np.pi * Hz * rateArray)
    return 48000, sine

def PlugSine(duration):
    rateArray = np.arange(0, duration, 1 / 48000)
    fade = np.logspace(0, -3, int(48000 * duration), endpoint=False)
    sine = fade * np.sin(2 * np.pi * 440 * rateArray)
    return 48000, sine

def AudioFile():
    fs, data = read(testdata)
    data = data / np.max(np.abs(data)) #Normierung
    return fs, data


#Klirrfaktor und THD
def klirrfaktorTHD(signal, Frequenz):

    FreqBereich = np.fft.fft(signal)

    f = [0,0,0] # Erstelle ein leeres Array für Oberschwingungen
    for i in range(1, 4):
        f[i - 1] = abs(FreqBereich[i * Frequenz]) # Berechne die Oberschwingungen aus Grundschwingung

    THD = np.round(100 * (np.sqrt((f[1]**2 + f[2]**2) / (f[0]**2))), 2)  #Berechne THD mit gegebener Formel
    klirr = np.round(100 * (np.sqrt((f[1]**2 + f[2]**2) / (f[0]**2 + f[1]**2 + f[2]**2))), 2)   #Berechne klirrfaktor mit gegebener Formel
    return THD, klirr


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
                 Lx_c[i] = threshold + (Lx[i]-threshold)/ratio
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
    ax.plot(t, g_a, label='Gain')  # Plotten von gain über t

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

def plotInOut(EingangsSignal, AusgangsSignal,  title1='', title2='',DrittesSignal=None, start_time=None, end_time=None, fs=48000):
    # Längen der Signale
    length_input = len(EingangsSignal)
    length_output = len(AusgangsSignal)

    # Zeitvektoren
    t_input = np.linspace(0, length_input / fs, length_input, endpoint=False)
    t_output = np.linspace(0, length_output / fs, length_output, endpoint=False)

    # Festlegung der Zeitgrenzen
    if start_time is None:
        start_time = 0
    if end_time is None:
        end_time = length_input / fs

    # Indizes für den Ausschnitt
    start_index = int(start_time * fs)
    end_index = int(end_time * fs)

    # Ausschnitt der Zeitvektoren
    t_input = t_input[start_index:end_index]
    t_output = t_output[start_index:end_index]

    dimension = max(EingangsSignal[start_index:end_index])

    # Plot
    plt.figure(figsize=(10, 10))

    # Für Input
    plt.subplot(3, 1, 1)
    plt.plot(t_input, EingangsSignal[start_index:end_index], label='Eingangssignal')
    plt.title('Eingangssignal (Original)')
    plt.xlabel('Zeit')
    plt.ylabel('Amplitude')
    plt.legend()

    # Für Output
    plt.subplot(3, 1, 2)
    plt.plot(t_output, AusgangsSignal[start_index:end_index], label='Ausgangssignal', color='red')
    plt.title(title1 + 'Ausgangssignal (Bearbeitet)')
    plt.xlabel('Zeit')
    plt.ylabel('Amplitude')
    plt.ylim(-dimension, dimension)
    plt.legend()

    # Für das dritte Signal
    if DrittesSignal is not None:
        length_third = len(DrittesSignal)
        t_third = np.linspace(0, length_third / fs, length_third, endpoint=False)
        t_third = t_third[start_index:end_index]

        plt.subplot(3, 1, 3)
        plt.plot(t_third, DrittesSignal[start_index:end_index], label='Compressed Signal', color='green')
        plt.title(title2 + 'Signal')
        plt.xlabel('Zeit')
        plt.ylabel('Amplitude')
        plt.legend()

    plt.tight_layout()
    plt.show()
####################################################### Programmablauf #######################################################

if Sinusanalyse:
    print(f"\n****Sinusanalyse****\nEine Sinusfunktion (3 Hz) wird in dem von ihnen gewählten Arbeitspunkt: {ArbeitspunktClipping} geclipped. Es wird der Klirrfaktor ({KlirrfaktorOrdnung}. Ordnung) und die THD berechnet.\nSie erhalten außerdem einen Plot des bearbeiteten Signals.")
    time.sleep(5)
    print(f"\nSinus THD: {klirrfaktorTHD(clip_signal(sine(1)[1], ArbeitspunktClipping), SinHz)[0]} %")
    print(f"Sinus Klirrfaktor: {klirrfaktorTHD(clip_signal(sine(1)[1], ArbeitspunktClipping), SinHz)[1]} %\n Sie Hören nun den Sinus:")
    time.sleep(2)
    sd.play(clip_signal(sine(1)[1], ArbeitspunktClipping))
    sd.wait()
    print(f"\nDer Sinus wird nun mit dem Limiter bearbeitet. Es wird der Klirrfaktor und die THD berechnet.\nSie erhalten auch hiervon einen Plot des Signales.")
    time.sleep(4)
    x = system_b(sine(1),lim_kompr,stat_dyn,ArbeitspunktLimiter,Ratio,Attack,Release,MakeUpGain)
    plotInOut(sine(1)[1],clip_signal(sine(1)[1], ArbeitspunktClipping), 'Clippped Sinus-', 'Compressed Sinus-', x,0, 0.01)
    sd.play(x)
    sd.wait()
    print(f"\nSinus THD: {klirrfaktorTHD(x, SinHz)[0]} %")
    print(f"Sinus Klirrfaktor: {klirrfaktorTHD(x, SinHz)[1]} %")
    print("\nEnde der Sinusanalyse!")

if AudioFileAnalyse:
    print(f"\n****Analyse eines Audiofiles****\nEin Audiofile wird in dem von ihnen gewählten Arbeitspunkt: {ArbeitspunktClipping} geclipped.\nSie erhalten einen Plot des bearbeiteten Signals.")
    print(f"\nDas Audiofile wird nun mit dem Limiter bearbeitet.\nSie erhalten auch hiervon einen Plot des Signales.")
    time.sleep(4)
    x = system_b(AudioFile(),lim_kompr,stat_dyn,ArbeitspunktLimiter,Ratio,Attack,Release,MakeUpGain)
    plotInOut(AudioFile()[1],clip_signal(AudioFile()[1], ArbeitspunktClipping), 'Clipped Audiofile-', 'Compressed Audiofile-', x)
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
    plotInOut(AudioFile()[1], reverseEcho(AudioFile(), 0.5, 0.5), 'Reversed Echo Audiofile-','Lol')
    sd.play(AudioFile()[1])
    sd.wait()
    sd.play(reverseEcho(AudioFile(), 0.5, 0.5))
    sd.wait()

    print(f"\nNun wird nochmal ein Anschauliches Signal bearbeitet. Es wird ein Echo mit den Parametern Delay = 0.5s und Decay = 0.5s erzeugt.\nSie erhalten außerdem einen Plot des bearbeiteten Signals.")
    time.sleep(5)
    plotInOut(PlugSine(1)[1], reverseEcho(PlugSine(1), 0.5, 0.5), 'Reversed Echo PlugSinus-', 'Lol')
    sd.play(PlugSine(1)[1])
    sd.wait()
    time.sleep(1)
    sd.play(reverseEcho(PlugSine(1), 0.5, 0.5))
    sd.wait()
    print("\nEnde des Reverse Echo Programmes!")




