"""
core.py: Funciones básicas de generación, modulación y canal para SimuliMath
"""
import numpy as np
from scipy.signal import correlate, firwin, lfilter

def generate_bits(n_bits, seed=None):
    """Genera una secuencia de bits binarios de longitud n_bits."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, 2, size=n_bits, dtype=np.uint8)

def bpsk_mod(bits):
    """Modula una secuencia de bits usando BPSK."""
    return np.where(bits == 0, -1, 1)

def add_awgn(signal, snr_db, seed=None):
    """Añade ruido blanco aditivo gaussiano (AWGN) a una señal dada.

    Para senales complejas (QPSK/QAM) genera ruido complejo propio con
    componentes I/Q independientes de varianza sigma^2/2 cada una.
    """
    rng = np.random.default_rng(seed)
    snr_linear = 10**(snr_db / 10)
    power_signal = np.mean(np.abs(signal)**2)
    noise_power = power_signal / snr_linear
    if np.iscomplexobj(signal):
        sigma = np.sqrt(noise_power / 2)
        noise = rng.normal(0, sigma, size=signal.shape) + 1j * rng.normal(0, sigma, size=signal.shape)
    else:
        noise = rng.normal(0, np.sqrt(noise_power), size=signal.shape).astype(signal.dtype)
    return signal + noise

def bpsk_demod(received):
    """Demodula una señal BPSK a una secuencia de bits binarios."""
    return (received >= 0).astype(np.uint8)

def ber(bits_tx, bits_rx):
    return np.mean(bits_tx != bits_rx)

def validate_models():
    # Validación de generate_bits
    bits = generate_bits(1000, seed=42)
    assert len(bits) == 1000, "Error: Número incorrecto de bits generados"
    assert set(bits).issubset({0, 1}), "Error: Los bits generados no son binarios"

    # Validación de bpsk_mod
    modulated = bpsk_mod(bits)
    assert set(modulated).issubset({-1, 1}), "Error: Modulación BPSK incorrecta"

    # Validación de add_awgn
    signal = bpsk_mod(bits)
    noisy_signal = add_awgn(signal, snr_db=10, seed=42)
    assert len(noisy_signal) == len(signal), "Error: Longitud del ruido no coincide con la señal"

    # Validación de bpsk_demod
    demodulated = bpsk_demod(noisy_signal)
    assert len(demodulated) == len(bits), "Error: Longitud de bits demodulados incorrecta"

    # Validación de BER
    error_rate = ber(bits, demodulated)
    assert 0 <= error_rate <= 1, "Error: BER fuera de rango"

    print("Validación de modelos completada con éxito.")

# Llamar a la validación al ejecutar el script
if __name__ == "__main__":
    validate_models()

def qpsk_mod(bits):
    """Modula una secuencia de bits usando QPSK."""
    if len(bits) % 2 != 0:
        raise ValueError("El número de bits debe ser par para QPSK.")
    # Conversión a entero con signo ANTES de operar: con arrays uint8
    # (p. ej. los de generate_bits), `2*0-1` desborda a 255 (wrap-around)
    # y corrompe los símbolos resultantes.
    symbols = np.asarray(bits, dtype=np.int64).reshape(-1, 2)
    return 1/np.sqrt(2) * ((2*symbols[:, 0] - 1) + 1j * (2*symbols[:, 1] - 1))

def qpsk_demod(received):
    """Demodula una señal QPSK a una secuencia de bits binarios."""
    bits_i = (received.real >= 0).astype(int)
    bits_q = (received.imag >= 0).astype(int)
    return np.column_stack((bits_i, bits_q)).flatten()

def qam_mod(bits, M):
    """Modula una secuencia de bits usando QAM de orden M."""
    if not np.log2(M).is_integer():
        raise ValueError("M debe ser una potencia de 2.")
    bits_per_symbol = int(np.log2(M))
    if len(bits) % bits_per_symbol != 0:
        raise ValueError(f"El número de bits debe ser múltiplo de {bits_per_symbol} para QAM de orden {M}.")
    symbols = bits.reshape(-1, bits_per_symbol)
    decimal_values = symbols.dot(2**np.arange(bits_per_symbol)[::-1])
    I = 2 * (decimal_values % np.sqrt(M)) - np.sqrt(M) + 1
    Q = 2 * (decimal_values // np.sqrt(M)) - np.sqrt(M) + 1
    return (I + 1j * Q) / np.sqrt(2)

def qam_demod(received, M):
    """Demodula una señal QAM de orden M a una secuencia de bits binarios."""
    if not np.log2(M).is_integer():
        raise ValueError("M debe ser una potencia de 2.")
    sqrt_M = int(np.sqrt(M))
    I = np.round((received.real * np.sqrt(2) + sqrt_M - 1) / 2).astype(int)
    Q = np.round((received.imag * np.sqrt(2) + sqrt_M - 1) / 2).astype(int)
    decimal_values = Q * sqrt_M + I
    bits_per_symbol = int(np.log2(M))
    bits = ((decimal_values[:, None] & (1 << np.arange(bits_per_symbol)[::-1])) > 0).astype(int)
    return bits.flatten()

def synchronize_signal(received, reference):
    """
    Sincroniza una señal recibida con una señal de referencia usando correlación cruzada.

    Parameters:
        received (np.ndarray): Señal recibida.
        reference (np.ndarray): Señal de referencia.

    Returns:
        np.ndarray: Señal sincronizada.
    """
    correlation = correlate(received, reference, mode='full')
    delay = np.argmax(correlation) - len(reference) + 1
    return np.roll(received, -delay)

def apply_filter(signal, cutoff, fs, numtaps=101):
    """
    Aplica un filtro FIR pasa-bajas a una señal.

    Parameters:
        signal (np.ndarray): Señal de entrada.
        cutoff (float): Frecuencia de corte del filtro (Hz).
        fs (float): Frecuencia de muestreo (Hz).
        numtaps (int): Número de coeficientes del filtro.

    Returns:
        np.ndarray: Señal filtrada.
    """
    nyquist = 0.5 * fs
    normalized_cutoff = cutoff / nyquist
    fir_coeff = firwin(numtaps, normalized_cutoff)
    return lfilter(fir_coeff, 1.0, signal)
