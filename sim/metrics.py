"""
metrics.py: Cálculo de métricas SNR, BER, PER para SimuliMath
"""
import numpy as np

def empirical_snr(signal, noise):
    power_signal = np.mean(np.abs(signal)**2)
    power_noise = np.mean(np.abs(noise)**2)
    return 10 * np.log10(power_signal / power_noise)

def packet_error_rate(bits_tx, bits_rx, packet_size):
    n_packets = len(bits_tx) // packet_size
    errors = 0
    for i in range(n_packets):
        start = i * packet_size
        end = start + packet_size
        if np.any(bits_tx[start:end] != bits_rx[start:end]):
            errors += 1
    return errors / n_packets if n_packets > 0 else 0.0

def channel_capacity(snr_db, bandwidth):
    """
    Calcula la capacidad del canal en bits por segundo (bps).

    Parameters:
        snr_db (float): Relación señal a ruido en decibelios.
        bandwidth (float): Ancho de banda del canal en Hz.

    Returns:
        float: Capacidad del canal en bps.
    """
    snr_linear = 10**(snr_db / 10)
    return bandwidth * np.log2(1 + snr_linear)

def spectral_efficiency(snr_db):
    """
    Calcula la eficiencia espectral en bits por segundo por Hz (bps/Hz).

    Parameters:
        snr_db (float): Relación señal a ruido en decibelios.

    Returns:
        float: Eficiencia espectral en bps/Hz.
    """
    snr_linear = 10**(snr_db / 10)
    return np.log2(1 + snr_linear)
