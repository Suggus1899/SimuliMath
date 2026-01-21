"""
receiver.py: Funciones de recepción y filtrado para SimuliMath
"""
import numpy as np
from scipy.signal import lfilter, firwin

def matched_filter(signal, num_taps=64):
    # Filtro rectangular simple
    taps = np.ones(num_taps) / num_taps
    return lfilter(taps, 1.0, signal)

def simple_sync(signal):
    # Sincronización básica: máximo absoluto
    return np.argmax(np.abs(signal))
