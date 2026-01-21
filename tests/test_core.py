import pytest
import numpy as np
from sim.core import generate_bits, bpsk_mod, add_awgn, bpsk_demod, ber

def test_generate_bits_extreme():
    """Prueba generar bits con un número extremo de bits."""
    bits = generate_bits(10**6, seed=42)
    assert len(bits) == 10**6
    assert set(bits).issubset({0, 1})

def test_bpsk_mod_extreme():
    """Prueba modulación BPSK con una secuencia larga."""
    bits = np.random.randint(0, 2, size=10**6)
    modulated = bpsk_mod(bits)
    assert len(modulated) == len(bits)
    assert set(modulated).issubset({-1, 1})

def test_add_awgn_low_snr():
    """Prueba añadir ruido con un SNR muy bajo."""
    signal = np.ones(1000)
    noisy_signal = add_awgn(signal, snr_db=-10, seed=42)
    assert len(noisy_signal) == len(signal)

def test_ber_high_error():
    """Prueba BER con una alta tasa de error."""
    bits_tx = np.zeros(1000, dtype=np.uint8)
    bits_rx = np.ones(1000, dtype=np.uint8)
    error_rate = ber(bits_tx, bits_rx)
    assert error_rate == 1.0