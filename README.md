# SimuliMath — Simulador académico de interferencias electromagnéticas

[![Estado](https://img.shields.io/badge/estado-en%20desarrollo-blue)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![Tests](https://img.shields.io/badge/tests-pytest-green)]()
[![Licencia](https://img.shields.io/badge/licencia-MIT-lightgrey)]()

## Tabla de contenidos
- [Resumen](#resumen)
- [Características](#características)
- [Tecnologías](#tecnologías)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Instalación rápida](#instalación-rápida)
- [Uso](#uso)
- [Roadmap por fases](#roadmap-por-fases)
- [Fórmulas clave](#fórmulas-clave)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

## Resumen
SimuliMath es un simulador **académico** en Python para estudiar cómo distintas interferencias afectan una comunicación inalámbrica. Proporciona métricas (SNR, BER, PER/pérdida de paquetes) y visualizaciones (dominio tiempo/frecuencia, espectrogramas, constelaciones, mapas de calor). No realiza transmisión RF real; su uso es exclusivamente educativo.

## Características
- Cadena TX→canal→RX reproducible con BPSK (QPSK opcional).
- Interferencias/jammers: CW, pulsada, banda ancha, sweep y combinaciones.
- Métricas: SNR, BER, PER, throughput (opcional).
- Visualizaciones didácticas: tiempo, FFT, espectrogramas, constelaciones, heatmaps.
- Experimentos paramétricos y exportación de resultados (CSV/PNG).

## Tecnologías
- **Lenguaje:** Python 3.9+
- **GUI:** Tkinter + matplotlib (embebido)
- **Señal:** numpy, scipy (scipy.signal)
- **Gráficos:** matplotlib, seaborn (opcional)
- **Datos:** pandas (CSV)
- **Tests:** pytest
- **Entornos:** requirements.txt (pip) y conda (opcional)
- **CI (opcional):** GitHub Actions

## Estructura del repositorio
```
sim/                 # Núcleo de señal, canal, jammers, métricas
  core.py
  jammer.py
  receiver.py
  metrics.py
  plots.py            # utilidades de visualización
config/              # Parámetros y presets (.json)
results/             # CSV/PNG generados
bin/                 # Scripts de experimentos (run_experiments.py)
tests/               # Pruebas con pytest
simulimath_gui.py    # Aplicación Tkinter principal
README.md
requirements.txt
```

## Instalación rápida
```bash
# Clonar
git clone https://github.com/Suggus1899/SimuliMath.git
cd SimuliMath

# Crear entorno (opcional)
python -m venv .venv
.venv\Scripts\activate  # Windows

# Dependencias
pip install -r requirements.txt
```

## Uso
```bash
# Ejecutar la app GUI
python simulimath_gui.py
```
- Configura parámetros en la GUI (modulación, Eb/N0, tipo de jammer, etc.).
- Genera y visualiza métricas (BER/SNR/PER) y gráficas (tiempo, FFT, espectrograma, constelación).
- Exporta resultados a `results/` (CSV/PNG).

## Roadmap por fases
- **Fase 0 — Kickoff:** alcance, modulaciones mínimas (BPSK; QPSK opcional), jammers (CW, pulsada, banda ancha, sweep), métricas (SNR, BER, PER, throughput opcional). Entregables: `config/params.json`, estructura inicial.
- **Fase 1 — Modelo de señal/canal:** fs, symbol_rate, Eb/N0, SNR, BER teórica BPSK. Documento técnico y pseudocódigo TX→canal→RX.
- **Fase 2 — Implementación básica:** `generate_bits()`, `bpsk_mod()`, `add_awgn()`, `bpsk_demod()`. GUI con curva BER vs Eb/N0. Entregables: `sim/core.py`, `simulimath_gui.py`.
- **Fase 3 — Jammers:** CW, pulsada, banda ancha, sweep. Visualización tiempo/FFT. Entregables: `sim/jammer.py`, GUI integrada.
- **Fase 4 — Receptor y métricas:** filtros (matched/bandpass), sincronización simple, SNR empírico, PER. Logs con semilla. Entregables: `sim/receiver.py`, `sim/metrics.py`.
- **Fase 5 — Visualizaciones:** tiempo, FFT, espectrograma, constelación, heatmaps BER. Entregables: `sim/plots.py`, GUI.
- **Fase 6 — Experimentos:** barridos y mapas (BER vs P_jammer/Δf, PER vs duty). Scripts en `bin/`, resultados CSV/PNG en `results/`.
- **Fase 7 — QA y rendimiento:** pytest, validaciones de límites, profiling, reproducibilidad.
- **Fase 8 — Documentación:** README reproducible, slides, guía de demo. Requisito: reproducir 3 escenarios básicos desde README.

## Fórmulas clave
- **Relación Eb/N0 y SNR:**
  \[
  \text{SNR (dB)} = 10 \log_{10}\left(\frac{E_b}{N_0}\right)
  \]
- **BER BPSK en AWGN:**
  \[
  P_e = Q\!\left(\sqrt{2 \cdot \frac{E_b}{N_0}}\right),\quad
  Q(x)=\frac{1}{\sqrt{2\pi}}\int_x^\infty e^{-\tfrac{t^2}{2}}\,dt
  \]

## Contribuir
1) Haz fork y crea una rama: `git checkout -b feat/tu-feature`.  
2) Añade/actualiza tests en `tests/`.  
3) Abre un PR describiendo cambios, supuestos y cómo probarlos.

## Licencia
MIT. Ver `LICENSE`.