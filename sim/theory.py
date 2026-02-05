"""
theory.py: Fundamentos teóricos de ondas electromagnéticas e interferencias

Este módulo proporciona funciones y constantes para el estudio de:
- Propagación de ondas de radio
- Modelos de pérdida de trayectoria
- Fundamentos de interferencia electromagnética

Referencia: Los conceptos aquí implementados se basan en teoría de 
telecomunicaciones y electromagnetismo.
"""

import numpy as np

# ============================================================================
# CONSTANTES FÍSICAS
# ============================================================================

# Velocidad de la luz en el vacío (m/s)
SPEED_OF_LIGHT = 299_792_458  # m/s

# Frecuencias de radio comunes (Hz)
FREQUENCIES = {
    'AM_radio': 1e6,           # 1 MHz - Radio AM
    'FM_radio': 100e6,         # 100 MHz - Radio FM
    'WiFi_2.4GHz': 2.4e9,      # 2.4 GHz - WiFi
    'WiFi_5GHz': 5e9,          # 5 GHz - WiFi 5G
    'LTE': 1.8e9,              # 1.8 GHz - LTE típico
    '5G_mmWave': 28e9,         # 28 GHz - 5G mmWave
}

# Constantes de propagación
BOLTZMANN_CONSTANT = 1.380649e-23  # J/K - Constante de Boltzmann


# ============================================================================
# FUNCIONES DE PROPAGACIÓN DE ONDAS
# ============================================================================

def wavelength(frequency: float) -> float:
    """
    Calcula la longitud de onda de una señal electromagnética.
    
    La longitud de onda (λ) está relacionada con la frecuencia (f) por:
        λ = c / f
    
    donde c es la velocidad de la luz en el vacío.
    
    Parameters:
        frequency (float): Frecuencia de la onda en Hz.
        
    Returns:
        float: Longitud de onda en metros.
        
    Example:
        >>> wavelength(2.4e9)  # WiFi 2.4 GHz
        0.125  # aproximadamente 12.5 cm
    """
    if frequency <= 0:
        raise ValueError("La frecuencia debe ser positiva")
    return SPEED_OF_LIGHT / frequency


def path_loss_free_space(distance: float, frequency: float) -> float:
    """
    Calcula la pérdida de trayectoria en espacio libre (FSPL).
    
    El modelo de espacio libre (Friis) describe la atenuación de una señal
    electromagnética cuando se propaga sin obstáculos:
    
        FSPL(dB) = 20·log₁₀(d) + 20·log₁₀(f) + 20·log₁₀(4π/c)
    
    donde:
        - d: distancia en metros
        - f: frecuencia en Hz
        - c: velocidad de la luz
    
    Este modelo es ideal y no considera reflexiones, difracción ni absorción.
    
    Parameters:
        distance (float): Distancia entre transmisor y receptor en metros.
        frequency (float): Frecuencia de operación en Hz.
        
    Returns:
        float: Pérdida de trayectoria en decibelios (dB).
        
    Example:
        >>> path_loss_free_space(100, 2.4e9)
        80.04  # aproximadamente 80 dB a 100m con WiFi
    """
    if distance <= 0 or frequency <= 0:
        raise ValueError("Distancia y frecuencia deben ser positivas")
    
    # Fórmula FSPL: 20*log10(4*pi*d*f/c)
    lambda_m = wavelength(frequency)
    fspl = 20 * np.log10(4 * np.pi * distance / lambda_m)
    return fspl


def path_loss_log_distance(distance: float, frequency: float, 
                           d0: float = 1.0, n: float = 2.0,
                           sigma: float = 0.0) -> float:
    """
    Calcula la pérdida de trayectoria usando el modelo Log-Distance.
    
    Este modelo es más realista que el espacio libre, ya que considera
    el exponente de pérdida de trayectoria (n) que varía según el entorno:
    
        PL(d) = PL(d₀) + 10·n·log₁₀(d/d₀) + Xσ
    
    donde:
        - PL(d₀): pérdida en la distancia de referencia
        - n: exponente de pérdida (típico: 2=espacio libre, 2.7-3.5=urbano, 4-6=interior)
        - Xσ: variable aleatoria para shadowing (opcional)
    
    Valores típicos del exponente n:
        - Espacio libre: n = 2.0
        - Urbano (celda pequeña): n = 2.7 - 3.5
        - Interior con obstrucciones: n = 4 - 6
        - Interior con línea de vista: n = 1.6 - 1.8
    
    Parameters:
        distance (float): Distancia TX-RX en metros.
        frequency (float): Frecuencia en Hz.
        d0 (float): Distancia de referencia en metros (default: 1m).
        n (float): Exponente de pérdida de trayectoria (default: 2.0).
        sigma (float): Desviación estándar para shadowing en dB (default: 0).
        
    Returns:
        float: Pérdida de trayectoria en dB.
        
    Example:
        >>> path_loss_log_distance(100, 2.4e9, n=3.0)  # Entorno urbano
        100.0  # Mayor pérdida que espacio libre
    """
    if distance <= 0 or frequency <= 0 or d0 <= 0:
        raise ValueError("Distancia, frecuencia y d0 deben ser positivas")
    
    # Pérdida en distancia de referencia (usando espacio libre)
    pl_d0 = path_loss_free_space(d0, frequency)
    
    # Pérdida adicional por distancia
    if distance <= d0:
        return pl_d0
    
    pl = pl_d0 + 10 * n * np.log10(distance / d0)
    
    # Añadir shadowing si se especifica
    if sigma > 0:
        pl += np.random.normal(0, sigma)
    
    return pl


def received_power(p_tx: float, g_tx: float, g_rx: float, 
                   path_loss: float) -> float:
    """
    Calcula la potencia recibida usando la ecuación de Friis.
    
    La potencia recibida depende de:
        P_rx = P_tx + G_tx + G_rx - PL
    
    donde todos los valores están en dB/dBm.
    
    Parameters:
        p_tx (float): Potencia de transmisión en dBm.
        g_tx (float): Ganancia de antena TX en dBi.
        g_rx (float): Ganancia de antena RX en dBi.
        path_loss (float): Pérdida de trayectoria en dB.
        
    Returns:
        float: Potencia recibida en dBm.
        
    Example:
        >>> received_power(20, 2, 2, 80)  # 20 dBm TX, antenas +2dBi, 80dB pérdida
        -56  # dBm recibidos
    """
    return p_tx + g_tx + g_rx - path_loss


def thermal_noise_power(bandwidth: float, temperature: float = 290.0) -> float:
    """
    Calcula la potencia de ruido térmico (Johnson-Nyquist).
    
    El ruido térmico es el límite fundamental de cualquier sistema de 
    comunicación y está dado por:
    
        N = k·T·B  (en Watts)
        N(dBm) = 10·log₁₀(k·T·B) + 30
    
    A temperatura ambiente (290K), el piso de ruido es aproximadamente
    -174 dBm/Hz.
    
    Parameters:
        bandwidth (float): Ancho de banda del receptor en Hz.
        temperature (float): Temperatura en Kelvin (default: 290K = 17°C).
        
    Returns:
        float: Potencia de ruido en dBm.
        
    Example:
        >>> thermal_noise_power(20e6)  # 20 MHz de ancho de banda
        -101  # aproximadamente -101 dBm
    """
    if bandwidth <= 0 or temperature <= 0:
        raise ValueError("Ancho de banda y temperatura deben ser positivos")
    
    noise_watts = BOLTZMANN_CONSTANT * temperature * bandwidth
    noise_dbm = 10 * np.log10(noise_watts) + 30  # +30 para convertir W a mW
    return noise_dbm


# ============================================================================
# INFORMACIÓN EDUCATIVA
# ============================================================================

THEORY_INFO = {
    'electromagnetic_waves': """
    ONDAS ELECTROMAGNÉTICAS
    =======================
    
    Las ondas electromagnéticas son perturbaciones que se propagan a través 
    del espacio transportando energía. Están formadas por campos eléctricos 
    y magnéticos oscilantes perpendiculares entre sí.
    
    Características principales:
    - Velocidad en el vacío: c = 299,792,458 m/s
    - No requieren medio material para propagarse
    - Frecuencia (f) y longitud de onda (λ) relacionadas por: c = f·λ
    
    Espectro de radio:
    - VLF (3-30 kHz): Comunicación submarina
    - LF (30-300 kHz): Navegación, radiodifusión
    - MF (300 kHz - 3 MHz): Radio AM
    - HF (3-30 MHz): Comunicación de larga distancia
    - VHF (30-300 MHz): Radio FM, TV
    - UHF (300 MHz - 3 GHz): TV, celular, WiFi
    - SHF (3-30 GHz): Satélite, radar, 5G
    - EHF (30-300 GHz): Investigación, 5G mmWave
    """,
    
    'interference': """
    INTERFERENCIA ELECTROMAGNÉTICA
    ===============================
    
    La interferencia ocurre cuando una señal no deseada afecta la recepción 
    de la señal deseada. Tipos principales:
    
    1. INTERFERENCIA CO-CANAL
       Señales en la misma frecuencia de diferentes transmisores.
       Muy problemática porque no se puede filtrar.
    
    2. INTERFERENCIA DE CANAL ADYACENTE
       Señales en frecuencias cercanas que se solapan.
       Puede mitigarse con buenos filtros.
    
    3. INTERFERENCIA INTENCIONAL (JAMMING)
       Señales diseñadas específicamente para bloquear comunicaciones.
       - CW (Continuous Wave): Tono continuo en frecuencia fija
       - Pulsada: Interferencia intermitente
       - Banda ancha: Ruido que cubre todo el canal
       - Barrido (Sweep): Señal que barre frecuencias
    
    Métricas de interferencia:
    - SNR (Signal-to-Noise Ratio): Señal vs ruido térmico
    - SIR (Signal-to-Interference Ratio): Señal vs interferencia
    - SINR: Señal vs (Interferencia + Ruido)
    """,
    
    'modulation': """
    MODULACIÓN DIGITAL
    ==================
    
    La modulación permite transmitir bits sobre ondas electromagnéticas:
    
    BPSK (Binary Phase Shift Keying):
    - 1 bit por símbolo
    - Cambio de fase: 0° o 180°
    - Robusta pero baja eficiencia espectral
    
    QPSK (Quadrature PSK):
    - 2 bits por símbolo
    - Fases: 45°, 135°, 225°, 315°
    - Doble eficiencia que BPSK
    
    QAM (Quadrature Amplitude Modulation):
    - Combina amplitud y fase
    - 16-QAM: 4 bits/símbolo
    - 64-QAM: 6 bits/símbolo
    - Mayor eficiencia pero más sensible a ruido
    
    Relación BER vs Eb/N0:
    Para BPSK en canal AWGN: Pe = Q(√(2·Eb/N0))
    donde Q(x) es la función Q de Marcum.
    """
}


def get_theory_text(topic: str) -> str:
    """
    Obtiene el texto educativo para un tema específico.
    
    Parameters:
        topic: Uno de 'electromagnetic_waves', 'interference', 'modulation'
        
    Returns:
        Texto explicativo del tema.
    """
    return THEORY_INFO.get(topic, "Tema no encontrado")


def get_all_topics() -> list:
    """Retorna la lista de temas disponibles."""
    return list(THEORY_INFO.keys())
