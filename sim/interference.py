"""
interference.py: Cálculos cuantitativos de interferencia para SimuliMath

Este módulo proporciona funciones para calcular y analizar el impacto
de interferencias en sistemas de comunicación inalámbrica.
"""

import numpy as np
from typing import Tuple, Dict


# ============================================================================
# FUNCIONES DE CÁLCULO DE INTERFERENCIA
# ============================================================================

def signal_to_interference_ratio(p_signal: float, p_interference: float) -> float:
    """
    Calcula la Relación Señal a Interferencia (SIR) en dB.
    
    SIR mide qué tan fuerte es la señal deseada respecto a las 
    interferencias NO deseadas (excluyendo ruido térmico).
    
        SIR(dB) = P_signal(dBm) - P_interference(dBm)
    
    Un SIR alto indica que la señal es mucho más fuerte que la 
    interferencia, lo cual es bueno para la comunicación.
    
    Parameters:
        p_signal (float): Potencia de la señal deseada en dBm.
        p_interference (float): Potencia de interferencia en dBm.
        
    Returns:
        float: SIR en dB.
        
    Example:
        >>> signal_to_interference_ratio(-50, -70)
        20.0  # La señal es 100 veces más fuerte que la interferencia
    """
    return p_signal - p_interference


def jammer_to_signal_ratio(p_jammer: float, p_signal: float) -> float:
    """
    Calcula la Relación Jammer a Señal (JSR o J/S) en dB.
    
    JSR es la métrica inversa al SIR, útil para evaluar la efectividad
    de un jammer. Un JSR positivo indica que el jammer es más fuerte
    que la señal.
    
        JSR(dB) = P_jammer(dBm) - P_signal(dBm)
    
    Parameters:
        p_jammer (float): Potencia del jammer en dBm.
        p_signal (float): Potencia de la señal deseada en dBm.
        
    Returns:
        float: JSR en dB.
        
    Example:
        >>> jammer_to_signal_ratio(-40, -50)
        10.0  # El jammer es 10 dB más fuerte que la señal
    """
    return p_jammer - p_signal


def sinr(p_signal: float, p_interference: float, p_noise: float) -> float:
    """
    Calcula la Relación Señal a Interferencia más Ruido (SINR) en dB.
    
    SINR es la métrica más completa porque considera tanto la 
    interferencia como el ruido térmico:
    
        SINR = P_signal / (P_interference + P_noise)
        
    En dB, se calcula convirtiendo potencias a lineal.
    
    Parameters:
        p_signal (float): Potencia de señal en dBm.
        p_interference (float): Potencia de interferencia en dBm.
        p_noise (float): Potencia de ruido en dBm.
        
    Returns:
        float: SINR en dB.
        
    Example:
        >>> sinr(-50, -70, -90)
        19.96  # Aproximadamente 20 dB
    """
    # Convertir de dBm a mW (lineal)
    s_linear = 10 ** (p_signal / 10)
    i_linear = 10 ** (p_interference / 10)
    n_linear = 10 ** (p_noise / 10)
    
    # Calcular SINR y convertir a dB
    sinr_linear = s_linear / (i_linear + n_linear)
    return 10 * np.log10(sinr_linear)


def link_budget(p_tx: float, g_tx: float, g_rx: float, 
                path_loss: float, noise_figure: float = 0.0,
                implementation_loss: float = 0.0) -> Dict[str, float]:
    """
    Calcula el presupuesto del enlace de radio completo.
    
    El presupuesto del enlace determina si una comunicación es viable
    calculando la potencia recibida y comparándola con la sensibilidad
    del receptor.
    
        P_rx = P_tx + G_tx + G_rx - PL - NF - IL
    
    Parameters:
        p_tx (float): Potencia de transmisión en dBm.
        g_tx (float): Ganancia de antena TX en dBi.
        g_rx (float): Ganancia de antena RX en dBi.
        path_loss (float): Pérdida de trayectoria en dB.
        noise_figure (float): Figura de ruido del receptor en dB.
        implementation_loss (float): Pérdidas de implementación en dB.
        
    Returns:
        Dict con:
            - eirp: Potencia isotrópica radiada efectiva (dBm)
            - received_power: Potencia recibida (dBm)
            - total_loss: Pérdidas totales (dB)
    """
    eirp = p_tx + g_tx
    total_loss = path_loss + noise_figure + implementation_loss
    received_power = eirp + g_rx - total_loss
    
    return {
        'eirp': eirp,
        'received_power': received_power,
        'total_loss': total_loss,
        'p_tx': p_tx,
        'g_tx': g_tx,
        'g_rx': g_rx,
        'path_loss': path_loss
    }


def interference_margin(snr_required: float, snr_actual: float) -> float:
    """
    Calcula el margen de interferencia disponible.
    
    El margen indica cuánta degradación adicional puede tolerar
    el sistema antes de fallar.
    
        Margen = SNR_actual - SNR_requerido
    
    - Margen > 0: Sistema funcionando con reserva
    - Margen = 0: Sistema en el límite
    - Margen < 0: Sistema fallando
    
    Parameters:
        snr_required (float): SNR mínimo requerido para comunicación (dB).
        snr_actual (float): SNR actual medido (dB).
        
    Returns:
        float: Margen en dB.
    """
    return snr_actual - snr_required


def interference_severity(sir_db: float, sinr_db: float) -> Tuple[int, str, str]:
    """
    Evalúa la severidad de la interferencia basándose en SIR y SINR.
    
    Retorna una puntuación de 0-100 y una descripción cualitativa
    del impacto de la interferencia.
    
    Parameters:
        sir_db (float): Relación señal/interferencia en dB.
        sinr_db (float): Relación señal/(interferencia+ruido) en dB.
        
    Returns:
        Tuple[int, str, str]: (score 0-100, severidad, descripción)
        
    Severidades:
        - 'none': Sin interferencia significativa (score >= 80)
        - 'low': Interferencia baja (score 60-79)
        - 'moderate': Interferencia moderada (score 40-59)
        - 'high': Interferencia alta (score 20-39)
        - 'critical': Interferencia crítica (score < 20)
    """
    # Calcular score basado en SIR y SNR
    # SIR: cada 5 dB sobre 0 suma 10 puntos (max 50 puntos)
    # SINR: cada 5 dB sobre 0 suma 10 puntos (max 50 puntos)
    
    sir_score = min(50, max(0, (sir_db + 10) * 2.5))  # -10dB=0pts, 10dB=50pts
    sinr_score = min(50, max(0, (sinr_db) * 2.5))       # 0dB=0pts, 20dB=50pts
    
    total_score = int(sir_score + sinr_score)
    total_score = min(100, max(0, total_score))
    
    # Determinar severidad
    if total_score >= 80:
        severity = 'none'
        description = "Sin interferencia significativa. Comunicación óptima."
    elif total_score >= 60:
        severity = 'low'
        description = "Interferencia baja. Comunicación buena con mínima degradación."
    elif total_score >= 40:
        severity = 'moderate'
        description = "Interferencia moderada. Posibles errores ocasionales."
    elif total_score >= 20:
        severity = 'high'
        description = "Interferencia alta. Degradación significativa de la comunicación."
    else:
        severity = 'critical'
        description = "Interferencia crítica. Comunicación severamente comprometida."
    
    return total_score, severity, description


def calculate_jammer_impact(p_signal: float, p_jammer: float, 
                           d_signal: float, d_jammer: float,
                           frequency: float,
                           bandwidth: float = 1e6,
                           path_loss_exponent: float = 2.0) -> Dict:
    """
    Calcula el impacto completo de un jammer en una comunicación.
    
    Esta función es el cálculo principal que une todos los conceptos:
    considera las potencias transmitidas, las distancias, y calcula
    qué tan dañina es la interferencia del jammer.
    
    Parameters:
        p_signal (float): Potencia de la señal TX en dBm.
        p_jammer (float): Potencia del jammer en dBm.
        d_signal (float): Distancia TX-RX en metros.
        d_jammer (float): Distancia Jammer-RX en metros.
        frequency (float): Frecuencia de operación en Hz.
        bandwidth (float): Ancho de banda del receptor en Hz (default: 1 MHz).
        path_loss_exponent (float): Exponente de pérdida (default: 2.0).
        
    Returns:
        Dict con todas las métricas calculadas.
    """
    from sim.theory import path_loss_log_distance, thermal_noise_power
    
    # Calcular pérdidas de trayectoria
    pl_signal = path_loss_log_distance(d_signal, frequency, n=path_loss_exponent)
    pl_jammer = path_loss_log_distance(d_jammer, frequency, n=path_loss_exponent)
    
    # Potencias recibidas (asumiendo antenas omnidireccionales 0 dBi)
    p_signal_rx = p_signal - pl_signal
    p_jammer_rx = p_jammer - pl_jammer
    
    # Ruido térmico
    p_noise = thermal_noise_power(bandwidth)
    
    # Calcular métricas
    sir = signal_to_interference_ratio(p_signal_rx, p_jammer_rx)
    jsr = jammer_to_signal_ratio(p_jammer_rx, p_signal_rx)
    sinr_val = sinr(p_signal_rx, p_jammer_rx, p_noise)
    score, severity, description = interference_severity(sir, sinr_val)
    
    return {
        'p_signal_rx': p_signal_rx,
        'p_jammer_rx': p_jammer_rx,
        'p_noise': p_noise,
        'path_loss_signal': pl_signal,
        'path_loss_jammer': pl_jammer,
        'sir_db': sir,
        'jsr_db': jsr,
        'sinr_db': sinr_val,
        'severity_score': score,
        'severity_level': severity,
        'severity_description': description
    }
