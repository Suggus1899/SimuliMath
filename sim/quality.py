"""
quality.py: Clasificación de calidad de comunicación para SimuliMath

Este módulo proporciona funciones para categorizar la calidad de una
comunicación basándose en métricas como BER, SNR, PER y SIR.
Los resultados incluyen categorías descriptivas y códigos de color
para una visualización intuitiva.
"""

import numpy as np
from typing import Tuple, Dict, Optional


# ============================================================================
# UMBRALES DE CLASIFICACIÓN (CONFIGURABLES)
# ============================================================================

# Umbrales de BER (Bit Error Rate)
# Valores típicos para diferentes aplicaciones:
# - Voz: BER < 1e-3 aceptable
# - Datos: BER < 1e-6 requerido
# - Video: BER < 1e-4 típico
BER_THRESHOLDS = {
    'excellent': 1e-6,   # BER < 1e-6: Calidad excelente
    'good': 1e-4,        # BER < 1e-4: Calidad buena
    'fair': 1e-3,        # BER < 1e-3: Calidad aceptable
    'poor': 1e-2,        # BER < 1e-2: Calidad pobre
    'critical': 1.0      # BER >= 1e-2: Crítico
}

# Umbrales de SNR (Signal-to-Noise Ratio) en dB
# Basados en requisitos típicos de modulaciones:
# - BPSK: requiere ~9.6 dB para BER=1e-5
# - QPSK: requiere ~9.6 dB para BER=1e-5
# - 16-QAM: requiere ~13.4 dB para BER=1e-5
SNR_THRESHOLDS = {
    'excellent': 20.0,   # SNR > 20 dB: Excelente
    'good': 10.0,        # SNR > 10 dB: Bueno
    'fair': 5.0,         # SNR > 5 dB: Aceptable
    'poor': 0.0,         # SNR > 0 dB: Pobre
    'critical': -np.inf  # SNR < 0 dB: Crítico
}

# Umbrales de PER (Packet Error Rate)
PER_THRESHOLDS = {
    'excellent': 0.001,  # PER < 0.1%
    'good': 0.01,        # PER < 1%
    'fair': 0.05,        # PER < 5%
    'poor': 0.10,        # PER < 10%
    'critical': 1.0      # PER >= 10%
}

# Colores para indicadores visuales (formato hex)
QUALITY_COLORS = {
    'excellent': '#22c55e',  # Verde brillante
    'good': '#84cc16',       # Verde lima
    'fair': '#eab308',       # Amarillo
    'poor': '#f97316',       # Naranja
    'critical': '#ef4444'    # Rojo
}

# Descripciones para cada categoría
QUALITY_DESCRIPTIONS = {
    'excellent': 'Excelente',
    'good': 'Buena',
    'fair': 'Regular',
    'poor': 'Mala',
    'critical': 'Crítica'
}

QUALITY_DETAILS = {
    'excellent': 'Comunicación óptima. Sin errores perceptibles.',
    'good': 'Comunicación buena. Errores mínimos y ocasionales.',
    'fair': 'Comunicación aceptable. Algunos errores presentes.',
    'poor': 'Comunicación degradada. Errores frecuentes.',
    'critical': 'Comunicación fallando. Errores muy frecuentes o pérdida total.'
}


# ============================================================================
# FUNCIONES DE CLASIFICACIÓN
# ============================================================================

def classify_ber(ber_value: float) -> Tuple[str, str, str]:
    """
    Clasifica la calidad basándose en el BER (Bit Error Rate).
    
    Parameters:
        ber_value (float): Valor de BER (entre 0 y 1).
        
    Returns:
        Tuple[str, str, str]: (categoría, descripción, color_hex)
        
    Example:
        >>> classify_ber(1e-5)
        ('good', 'Buena', '#84cc16')
    """
    if ber_value < 0 or ber_value > 1:
        ber_value = max(0, min(1, ber_value))
    
    if ber_value < BER_THRESHOLDS['excellent']:
        category = 'excellent'
    elif ber_value < BER_THRESHOLDS['good']:
        category = 'good'
    elif ber_value < BER_THRESHOLDS['fair']:
        category = 'fair'
    elif ber_value < BER_THRESHOLDS['poor']:
        category = 'poor'
    else:
        category = 'critical'
    
    return (category, QUALITY_DESCRIPTIONS[category], QUALITY_COLORS[category])


def classify_snr(snr_db: float) -> Tuple[str, str, str]:
    """
    Clasifica la calidad basándose en el SNR (Signal-to-Noise Ratio).
    
    Parameters:
        snr_db (float): Valor de SNR en decibelios.
        
    Returns:
        Tuple[str, str, str]: (categoría, descripción, color_hex)
        
    Example:
        >>> classify_snr(15.0)
        ('good', 'Buena', '#84cc16')
    """
    if snr_db >= SNR_THRESHOLDS['excellent']:
        category = 'excellent'
    elif snr_db >= SNR_THRESHOLDS['good']:
        category = 'good'
    elif snr_db >= SNR_THRESHOLDS['fair']:
        category = 'fair'
    elif snr_db >= SNR_THRESHOLDS['poor']:
        category = 'poor'
    else:
        category = 'critical'
    
    return (category, QUALITY_DESCRIPTIONS[category], QUALITY_COLORS[category])


def classify_per(per_value: float) -> Tuple[str, str, str]:
    """
    Clasifica la calidad basándose en el PER (Packet Error Rate).
    
    Parameters:
        per_value (float): Valor de PER (entre 0 y 1).
        
    Returns:
        Tuple[str, str, str]: (categoría, descripción, color_hex)
    """
    if per_value < 0 or per_value > 1:
        per_value = max(0, min(1, per_value))
    
    if per_value < PER_THRESHOLDS['excellent']:
        category = 'excellent'
    elif per_value < PER_THRESHOLDS['good']:
        category = 'good'
    elif per_value < PER_THRESHOLDS['fair']:
        category = 'fair'
    elif per_value < PER_THRESHOLDS['poor']:
        category = 'poor'
    else:
        category = 'critical'
    
    return (category, QUALITY_DESCRIPTIONS[category], QUALITY_COLORS[category])


def overall_quality(ber: float, snr_db: float, 
                   per: Optional[float] = None,
                   sir_db: Optional[float] = None) -> Dict:
    """
    Evaluación completa de la calidad de comunicación.
    
    Combina múltiples métricas para dar una evaluación global
    incluyendo:
    - Score numérico (0-100)
    - Categoría general
    - Clasificación individual de cada métrica
    - Recomendaciones
    
    Parameters:
        ber (float): Bit Error Rate.
        snr_db (float): SNR en dB.
        per (float, optional): Packet Error Rate.
        sir_db (float, optional): Signal-to-Interference Ratio en dB.
        
    Returns:
        Dict con evaluación completa.
    """
    # Clasificar cada métrica
    ber_cat, ber_desc, ber_color = classify_ber(ber)
    snr_cat, snr_desc, snr_color = classify_snr(snr_db)
    
    # Calcular score (0-100)
    # BER contribuye 40%, SNR contribuye 40%, PER/SIR contribuyen 20%
    category_scores = {
        'excellent': 100,
        'good': 75,
        'fair': 50,
        'poor': 25,
        'critical': 0
    }
    
    ber_score = category_scores[ber_cat]
    snr_score = category_scores[snr_cat]
    
    if per is not None:
        per_cat, per_desc, per_color = classify_per(per)
        per_score = category_scores[per_cat]
        total_score = int(0.35 * ber_score + 0.35 * snr_score + 0.30 * per_score)
    else:
        per_cat, per_desc, per_color = None, None, None
        total_score = int(0.50 * ber_score + 0.50 * snr_score)
    
    # Determinar categoría general (basada en la peor métrica principal)
    categories_order = ['excellent', 'good', 'fair', 'poor', 'critical']
    worst_idx = max(categories_order.index(ber_cat), 
                    categories_order.index(snr_cat))
    if per_cat:
        worst_idx = max(worst_idx, categories_order.index(per_cat))
    
    overall_category = categories_order[worst_idx]
    
    # Generar recomendaciones
    recommendations = []
    if snr_cat in ['poor', 'critical']:
        recommendations.append("⚠️ SNR muy bajo. Considere aumentar potencia TX o reducir distancia.")
    if ber_cat in ['poor', 'critical']:
        recommendations.append("⚠️ BER alto. Considere usar modulación más robusta (BPSK).")
    if per_cat in ['poor', 'critical']:
        recommendations.append("⚠️ PER alto. Considere reducir interferencia o usar FEC.")
    if sir_db is not None and sir_db < 5:
        recommendations.append("⚠️ SIR bajo. La interferencia está afectando significativamente.")
    if not recommendations:
        recommendations.append("✅ Sistema operando dentro de parámetros aceptables.")
    
    return {
        'score': total_score,
        'category': overall_category,
        'description': QUALITY_DESCRIPTIONS[overall_category],
        'detail': QUALITY_DETAILS[overall_category],
        'color': QUALITY_COLORS[overall_category],
        'metrics': {
            'ber': {
                'value': ber,
                'category': ber_cat,
                'description': ber_desc,
                'color': ber_color
            },
            'snr': {
                'value': snr_db,
                'category': snr_cat,
                'description': snr_desc,
                'color': snr_color
            },
            'per': {
                'value': per,
                'category': per_cat,
                'description': per_desc,
                'color': per_color
            } if per is not None else None
        },
        'recommendations': recommendations
    }


def get_quality_indicator(score: int) -> str:
    """
    Genera un indicador visual de texto para un score dado.
    
    Parameters:
        score (int): Puntuación de 0 a 100.
        
    Returns:
        str: Barra visual de texto (ej: "▓▓▓▓▓▓░░░░")
    """
    filled = int(score / 10)
    empty = 10 - filled
    return "▓" * filled + "░" * empty


def get_quality_emoji(category: str) -> str:
    """
    Retorna un emoji representativo de la categoría.
    """
    emojis = {
        'excellent': '🟢',
        'good': '🟡',
        'fair': '🟠',
        'poor': '🔴',
        'critical': '⛔'
    }
    return emojis.get(category, '⚪')
