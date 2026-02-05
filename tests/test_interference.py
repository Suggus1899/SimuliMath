"""
test_interference.py: Tests para el módulo de interferencia
"""
import pytest
import numpy as np
from sim.interference import (
    signal_to_interference_ratio,
    jammer_to_signal_ratio,
    sinr,
    link_budget,
    interference_margin,
    interference_severity
)


class TestSIR:
    """Tests para el cálculo de SIR."""

    def test_sir_positive(self):
        """Señal más fuerte que interferencia da SIR positivo."""
        sir = signal_to_interference_ratio(-50, -70)
        assert sir == 20.0

    def test_sir_negative(self):
        """Interferencia más fuerte que señal da SIR negativo."""
        sir = signal_to_interference_ratio(-70, -50)
        assert sir == -20.0

    def test_sir_zero(self):
        """Señal igual a interferencia da SIR cero."""
        sir = signal_to_interference_ratio(-60, -60)
        assert sir == 0.0


class TestJSR:
    """Tests para el cálculo de JSR (inverso de SIR)."""

    def test_jsr_positive(self):
        """Jammer más fuerte que señal da JSR positivo."""
        jsr = jammer_to_signal_ratio(-40, -50)
        assert jsr == 10.0

    def test_jsr_negative(self):
        """Señal más fuerte que jammer da JSR negativo."""
        jsr = jammer_to_signal_ratio(-60, -50)
        assert jsr == -10.0


class TestSINR:
    """Tests para el cálculo de SINR."""

    def test_sinr_no_interference(self):
        """Sin interferencia significativa, SINR similar a SNR."""
        # Con interferencia despreciable (-100 dBm)
        sinr_val = sinr(-50, -100, -90)
        # Debería ser dominado por el ruido
        assert sinr_val > 35  # Aproximadamente 40 dB

    def test_sinr_high_interference(self):
        """Alta interferencia reduce SINR significativamente."""
        sinr_val = sinr(-50, -50, -90)
        # Interferencia igual a señal
        assert sinr_val < 5  # Aproximadamente 3 dB

    def test_sinr_conversion(self):
        """Verificar conversión correcta de dBm a lineal."""
        # -50 dBm señal, -60 dBm interferencia, -70 dBm ruido
        sinr_val = sinr(-50, -60, -70)
        # Cálculo manual: 10^(-5) / (10^(-6) + 10^(-7)) = 10/1.1 ≈ 9.58 dB
        assert 9 < sinr_val < 10


class TestLinkBudget:
    """Tests para el cálculo de presupuesto de enlace."""

    def test_link_budget_basic(self):
        """Cálculo básico de presupuesto de enlace."""
        result = link_budget(p_tx=20, g_tx=2, g_rx=2, path_loss=80)
        assert result['eirp'] == 22  # 20 + 2
        assert result['received_power'] == -56  # 22 + 2 - 80

    def test_link_budget_with_losses(self):
        """Presupuesto con pérdidas adicionales."""
        result = link_budget(p_tx=20, g_tx=2, g_rx=2, path_loss=80,
                           noise_figure=3, implementation_loss=2)
        assert result['total_loss'] == 85  # 80 + 3 + 2
        assert result['received_power'] == -61  # 22 + 2 - 85


class TestInterferenceMargin:
    """Tests para el cálculo de margen de interferencia."""

    def test_positive_margin(self):
        """Margen positivo cuando SNR actual > requerido."""
        margin = interference_margin(snr_required=10, snr_actual=15)
        assert margin == 5.0

    def test_negative_margin(self):
        """Margen negativo cuando SNR actual < requerido."""
        margin = interference_margin(snr_required=15, snr_actual=10)
        assert margin == -5.0

    def test_zero_margin(self):
        """Margen cero cuando SNR actual = requerido."""
        margin = interference_margin(snr_required=10, snr_actual=10)
        assert margin == 0.0


class TestInterferenceSeverity:
    """Tests para la clasificación de severidad de interferencia."""

    def test_no_interference(self):
        """Buenas condiciones dan severidad 'none'."""
        score, severity, desc = interference_severity(sir_db=20, snr_db=25)
        assert score >= 80
        assert severity == 'none'

    def test_critical_interference(self):
        """Malas condiciones dan severidad 'critical'."""
        score, severity, desc = interference_severity(sir_db=-15, snr_db=-5)
        assert score < 20
        assert severity == 'critical'

    def test_moderate_interference(self):
        """Condiciones intermedias dan severidad moderada."""
        score, severity, desc = interference_severity(sir_db=0, snr_db=5)
        assert 30 <= score <= 70
        assert severity in ['low', 'moderate', 'high']

    def test_score_bounds(self):
        """Score siempre entre 0 y 100."""
        # Valores extremos
        score1, _, _ = interference_severity(sir_db=50, snr_db=50)
        score2, _, _ = interference_severity(sir_db=-50, snr_db=-50)
        assert 0 <= score1 <= 100
        assert 0 <= score2 <= 100
