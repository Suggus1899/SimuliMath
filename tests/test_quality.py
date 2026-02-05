"""
test_quality.py: Tests para el módulo de calidad de comunicación
"""
import pytest
from sim.quality import (
    classify_ber, classify_snr, classify_per,
    overall_quality, get_quality_indicator,
    BER_THRESHOLDS, SNR_THRESHOLDS
)


class TestClassifyBER:
    """Tests para la clasificación de BER."""

    def test_excellent_ber(self):
        """BER muy bajo debe clasificarse como excelente."""
        category, desc, color = classify_ber(1e-7)
        assert category == 'excellent'
        assert desc == 'Excelente'
        assert color.startswith('#')

    def test_good_ber(self):
        """BER bajo debe clasificarse como bueno."""
        category, _, _ = classify_ber(1e-5)
        assert category == 'good'

    def test_fair_ber(self):
        """BER moderado debe clasificarse como regular."""
        category, _, _ = classify_ber(5e-4)
        assert category == 'fair'

    def test_poor_ber(self):
        """BER alto debe clasificarse como malo."""
        category, _, _ = classify_ber(5e-3)
        assert category == 'poor'

    def test_critical_ber(self):
        """BER muy alto debe clasificarse como crítico."""
        category, _, _ = classify_ber(0.1)
        assert category == 'critical'

    def test_boundary_ber(self):
        """Valores en los límites deben clasificarse correctamente."""
        # Exactamente en el límite de excellent/good
        category, _, _ = classify_ber(BER_THRESHOLDS['excellent'])
        assert category == 'good'  # >= umbral va a la siguiente categoría


class TestClassifySNR:
    """Tests para la clasificación de SNR."""

    def test_excellent_snr(self):
        """SNR muy alto debe clasificarse como excelente."""
        category, desc, _ = classify_snr(25.0)
        assert category == 'excellent'

    def test_good_snr(self):
        """SNR bueno debe clasificarse correctamente."""
        category, _, _ = classify_snr(15.0)
        assert category == 'good'

    def test_fair_snr(self):
        """SNR moderado debe clasificarse como regular."""
        category, _, _ = classify_snr(7.0)
        assert category == 'fair'

    def test_poor_snr(self):
        """SNR bajo debe clasificarse como malo."""
        category, _, _ = classify_snr(2.0)
        assert category == 'poor'

    def test_critical_snr(self):
        """SNR negativo debe clasificarse como crítico."""
        category, _, _ = classify_snr(-5.0)
        assert category == 'critical'


class TestOverallQuality:
    """Tests para la evaluación general de calidad."""

    def test_overall_excellent(self):
        """Calidad excelente con métricas óptimas."""
        result = overall_quality(ber=1e-7, snr_db=25.0)
        assert result['score'] >= 80
        assert result['category'] == 'excellent'
        assert 'color' in result

    def test_overall_critical(self):
        """Calidad crítica con métricas malas."""
        result = overall_quality(ber=0.2, snr_db=-5.0)
        assert result['score'] <= 20
        assert result['category'] == 'critical'

    def test_overall_with_per(self):
        """Evaluación incluyendo PER."""
        result = overall_quality(ber=1e-5, snr_db=15.0, per=0.02)
        assert 'metrics' in result
        assert result['metrics']['per'] is not None

    def test_recommendations_present(self):
        """Las recomendaciones deben estar presentes."""
        result = overall_quality(ber=0.1, snr_db=2.0)
        assert 'recommendations' in result
        assert len(result['recommendations']) > 0


class TestQualityIndicator:
    """Tests para el indicador visual de calidad."""

    def test_full_bar(self):
        """Score 100 debe dar barra llena."""
        bar = get_quality_indicator(100)
        assert '▓' in bar
        assert bar.count('▓') == 10

    def test_empty_bar(self):
        """Score 0 debe dar barra vacía."""
        bar = get_quality_indicator(0)
        assert bar.count('░') == 10

    def test_half_bar(self):
        """Score 50 debe dar barra mitad llena."""
        bar = get_quality_indicator(50)
        assert bar.count('▓') == 5
        assert bar.count('░') == 5
