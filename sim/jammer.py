"""
jammer.py: Generadores de interferencia para SimuliMath
"""
import numpy as np

def jammer_cw(length, fs, fj, Aj=1.0, seed=None):
    t = np.arange(length) / fs
    return Aj * np.cos(2 * np.pi * fj * t)

def jammer_pulsed(length, fs, fj, Aj=1.0, duty=0.5, prf=100, seed=None):
    t = np.arange(length) / fs
    pulse = ((np.sin(2 * np.pi * prf * t) > 0) * 1.0) * duty
    return Aj * np.cos(2 * np.pi * fj * t) * pulse

def jammer_broadband(length, fs, bandwidth, power=1.0, seed=None):
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, np.sqrt(power), size=length)
    # Filtro pasa banda (simple)
    from scipy.signal import butter, lfilter
    nyq = 0.5 * fs
    low = (nyq - bandwidth/2) / nyq
    high = (nyq + bandwidth/2) / nyq
    b, a = butter(4, [low, high], btype='band')
    return lfilter(b, a, noise)

def jammer_sweep(length, fs, fstart, fstop, rate=1.0, Aj=1.0):
    """
    Genera un jammer de barrido lineal repetido.

    La fase se integra (phi = 2*pi*(fstart*t + (fstop-fstart)*t**2/(2*T)))
    para que la frecuencia instantanea recorra fstart -> fstop; la version
    anterior usaba cos(2*pi*f(t)*t), que terminaba en 2*fstop-fstart.

    Parameters:
        length (int): Numero de muestras.
        fs (float): Frecuencia de muestreo.
        fstart (float): Frecuencia inicial del barrido.
        fstop (float): Frecuencia final del barrido.
        rate (float): Numero de barridos completos en la duracion total.
        Aj (float): Amplitud del jammer.

    Returns:
        np.ndarray: Senal de interferencia de barrido.
    """
    T = length / fs
    frac = (np.arange(length) / length * rate) % 1.0   # 0..1 en cada barrido
    t_seg = frac * (T / rate)                          # tiempo dentro del barrido
    phase = 2 * np.pi * (fstart * t_seg + 0.5 * (fstop - fstart) * t_seg**2 / (T / rate))
    return Aj * np.cos(phase)

def jammer_chirp(length, fs, f0, f1, Aj=1.0):
    """
    Genera un jammer tipo chirp (barrido de frecuencia lineal).
    
    Parameters:
        length (int): Número de muestras.
        fs (float): Frecuencia de muestreo.
        f0 (float): Frecuencia inicial del chirp.
        f1 (float): Frecuencia final del chirp.
        Aj (float): Amplitud del jammer.

    Returns:
        np.ndarray: Señal de interferencia chirp.
    """
    t = np.arange(length) / fs
    T = length / fs
    # Fase integrada de un chirp lineal: f_inst(t) = f0 + (f1-f0)*t/T.
    # La version anterior usaba cos(2*pi*f(t)*t) y terminaba en 2*f1-f0.
    phase = 2 * np.pi * (f0 * t + 0.5 * (f1 - f0) * t**2 / T)
    return Aj * np.cos(phase)

def jammer_multitone(length, fs, freqs, Aj=1.0):
    """
    Genera un jammer compuesto por múltiples tonos.

    Parameters:
        length (int): Número de muestras.
        fs (float): Frecuencia de muestreo.
        freqs (list): Lista de frecuencias de los tonos.
        Aj (float): Amplitud del jammer.

    Returns:
        np.ndarray: Señal de interferencia multitone.
    """
    t = np.arange(length) / fs
    signal = np.zeros(length)
    for f in freqs:
        signal += Aj * np.cos(2 * np.pi * f * t)
    return signal / len(freqs)
