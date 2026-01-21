import time
import numpy as np
from sim.core import generate_bits, bpsk_mod, add_awgn, bpsk_demod, ber

def test_performance_generate_bits():
    """Prueba de rendimiento para la generación de bits."""
    start_time = time.time()
    generate_bits(10**7, seed=42)
    duration = time.time() - start_time
    assert duration < 2, f"Generar bits tomó demasiado tiempo: {duration:.2f} segundos"

def test_performance_bpsk_mod():
    """Prueba de rendimiento para la modulación BPSK."""
    bits = np.random.randint(0, 2, size=10**7)
    start_time = time.time()
    bpsk_mod(bits)
    duration = time.time() - start_time
    assert duration < 2, f"Modulación BPSK tomó demasiado tiempo: {duration:.2f} segundos"

def test_performance_add_awgn():
    """Prueba de rendimiento para añadir ruido AWGN."""
    signal = np.ones(10**7)
    start_time = time.time()
    add_awgn(signal, snr_db=10, seed=42)
    duration = time.time() - start_time
    assert duration < 2, f"Añadir AWGN tomó demasiado tiempo: {duration:.2f} segundos"

def test_performance_ber():
    """Prueba de rendimiento para el cálculo de BER."""
    bits_tx = np.random.randint(0, 2, size=10**7, dtype=np.uint8)
    bits_rx = np.random.randint(0, 2, size=10**7, dtype=np.uint8)
    start_time = time.time()
    ber(bits_tx, bits_rx)
    duration = time.time() - start_time
    assert duration < 2, f"Cálculo de BER tomó demasiado tiempo: {duration:.2f} segundos"