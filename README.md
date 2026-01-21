# SimuliMath — Simulador académico de interferencias electromagnéticas

Resumen
- Objetivo general: Crear una simulación matemática y visual (Python) que muestre cómo distintas interferencias afectan una comunicación inalámbrica, entregando métricas (SNR, BER, PER/pérdida de paquetes) y visualizaciones (dominio tiempo/frecuencia, espectrogramas, constelaciones, mapas de calor).
- Restricción: Proyecto netamente académico/simulador, sin transmisión RF real ni acciones operativas.

Tecnologías y librerías recomendadas (global)
- Lenguaje: Python 3.9+
- Interfaz actual: Tkinter + matplotlib (embebido)
- Cálculo y señal: numpy, scipy (scipy.signal)
- Gráficos: matplotlib
- Data & export: pandas (CSV)
- Tests: pytest
- Control de versiones / reproducibilidad: git, requirements.txt / pip, conda env (opcional)

Formato de entregables sugeridos
- Código: módulos Python (sim/*.py) + app Tkinter (simulimath_gui.py)
- Configuraciones: config/*.json
- Resultados: results/*.csv, results/*.png
- Documentación: README.md, report.pdf, slides

---

## Fase 0 — Preparación y alcance (Kickoff)
- Objetivo:
  - Alinear alcance, tipos de interferencia, métricas obligatorias y roles del equipo.
- Tareas:
  - Definir modulaciones mínimas (BPSK; opcional QPSK), lista de jammers (CW, pulsed, broadband, sweep).
  - Especificar métricas: SNR, BER, PER, throughput (opcional).
  - Inicializar repositorio y plantilla (app Tkinter y módulos).
- Entregables:
  - Documento de especificación corto y archivo de parámetros (config/params.json).
- Tecnologías:
  - git, README.md, Tkinter
- Criterio de aceptación:
  - Documento aprobado y repo inicializado con estructura.

## Fase 1 — Diseño del modelo de señal y canal
- Objetivo:
  - Formalizar modelos matemáticos (modulación, Eb/N0, AWGN, atenuación).
- Tareas:
  - Definir fs, symbol_rate, cálculo de Eb, relación con SNR.
  - Documentar fórmulas (BER teórica BPSK).
- Entregables:
  - Documento técnico y pseudocódigo (TX → canal → RX).
- Tecnologías:
  - Markdown, numpy, scipy

## Ejemplos visuales de las fórmulas aplicadas

### Relación Eb/N0 y SNR
La relación entre la energía por bit ($E_b$) y la densidad espectral de potencia de ruido ($N_0$) está dada por:

$$
\text{SNR} = 10 \cdot \log_{10}\left(\frac{E_b}{N_0}\right)
$$

#### Ejemplo:
Si $E_b = 1$ y $N_0 = 0.1$, entonces:

$$
\text{SNR} = 10 \cdot \log_{10}(10) = 10 \text{ dB}
$$

### Probabilidad de error de bit (BER) para BPSK
La probabilidad de error de bit para BPSK en un canal AWGN está dada por:

$$
P_e = Q\left(\sqrt{2 \cdot \frac{E_b}{N_0}}\right)
$$

Donde $Q(x)$ es la función Q:

$$
Q(x) = \frac{1}{\sqrt{2\pi}} \int_x^\infty e^{-\frac{t^2}{2}} dt
$$

#### Ejemplo:
Si $E_b/N_0 = 10$ dB, entonces:

$$
P_e = Q\left(\sqrt{2 \cdot 10}\right) \approx 7.62 \times 10^{-6}
$$

Estas fórmulas son fundamentales para entender el impacto del ruido en la comunicación inalámbrica y se utilizan en las simulaciones de SimuliMath.

## Fase 2 — Implementación básica: generador, modulador y canal AWGN
- Objetivo:
  - Cadena mínima end-to-end reproducible: bits → modulación → AWGN → demodulación → BER.
- Tareas:
  - Implementar funciones: generate_bits(), bpsk_mod(), add_awgn(), bpsk_demod().
  - Integrar en la app Tkinter una simulación básica BER vs Eb/N0.
- Entregables:
  - sim/core.py, simulimath_gui.py
- Tecnologías:
  - numpy, scipy, matplotlib (Tkinter embedding), pytest (tests básicos)
- Criterio de aceptación:
  - La app muestra resultados coherentes de BER vs Eb/N0 en el GUI.

## Fase 3 — Módulos de interferencia (jammers)
- Objetivo:
  - Implementar jammers paramétricos: CW, pulsed, broadband, sweep y combinaciones.
- Tareas:
  - Implementar generadores: CW(fj, Aj), pulsed(duty, PRF), broadband(bandwidth, power), sweep(fstart,fstop,rate).
  - Visualizar señales y FFTs de cada interferencia en el GUI.
- Entregables:
  - sim/jammer.py, simulimath_gui.py
- Tecnologías:
  - numpy, scipy.signal, matplotlib (Tkinter embedding)
- Criterio de aceptación:
  - Visualizaciones y parámetros documentados; jammers integrables en la cadena TX→canal dentro del GUI.

## Fase 4 — Receptor y cálculo de métricas
- Objetivo:
  - Filtrado en recepción, sincronización básica y cálculo de SNR, BER y PER.
- Tareas:
  - Implementar matched filter / bandpass, sincronizador simple, demodulación robusta.
  - Implementar cálculo empírico de SNR (medición de potencias) y PER (por paquetes).
  - Registro de ejecución (logs con semilla RNG) y visualización en GUI.
- Entregables:
  - sim/receiver.py, sim/metrics.py, simulimath_gui.py
- Tecnologías:
  - scipy.signal, numpy, pandas (logs/resultados), matplotlib (Tkinter)
- Criterio de aceptación:
  - Métricas reproducibles y visibles en la app GUI.

## Fase 5 — Visualizaciones tiempo/frecuencia y análisis pedagógico
- Objetivo:
  - Crear visuales didácticos: tiempo, FFT, espectrogramas, constelaciones y heatmaps.
- Tareas:
  - Implementar utilidades: plot_time(), plot_fft(), plot_spectrogram(), plot_constellation(), heatmap_ber().
  - Añadir anotaciones educativas en la app GUI.
- Entregables:
  - sim/plots.py (opcional), simulimath_gui.py
- Tecnologías:
  - matplotlib (Tkinter embedding)
- Criterio de aceptación:
  - Visualizaciones claras en el GUI que muestren el impacto de cada interferencia.

## Fase 6 — Experimentos paramétricos y mapas de rendimiento
- Objetivo:
  - Ejecutar barridos sistemáticos y generar mapas (BER vs P_jammer/Δf, PER vs duty cycle).
- Tareas:
  - Diseñar experimentos (grids), automatizar campañas, exportar resultados.
  - Generar reportes gráficos comparativos y CSV/JSON de resultados.
- Entregables:
  - bin/run_experiments.py (opcional), results/*.csv
- Tecnologías:
  - pandas, numpy, matplotlib, seaborn, joblib/multiprocessing (para paralelizar)
- Criterio de aceptación:
  - Experimentos reproducibles con scripts y resultados guardados.

## Fase 7 — Validación, QA y rendimiento
- Objetivo:
  - Asegurar robustez numérica, reproducibilidad y pruebas automatizadas.
- Tareas:
  - Escribir tests (pytest), validar límites, perfilar tiempos de ejecución.
  - Documentar supuestos y fuentes de error.
- Entregables:
  - tests/, reportes de validación, guía de limitaciones.
- Tecnologías:
  - pytest, timeit/profile, CI opcional (GitHub Actions)
- Criterio de aceptación:
  - Suite de tests que pasa y documento de validación.

## Fase 8 — Documentación y material didáctico
- Objetivo:
  - Empaquetar README, instrucciones de ejecución y material docente.
- Tareas:
  - Generar README con pasos reproducibles (pip install -r requirements.txt).
  - Crear documentación explicativa paso a paso, presentación y guion de demo.
- Entregables:
  - README.md, requirements.txt, slides.
- Tecnologías:
  - Markdown, Binder (opcional)
- Criterio de aceptación:
  - Revisor externo puede reproducir 3 escenarios básicos siguiendo el README.

---

Apéndice: Ejemplo rápido de requerimientos (requirements.txt sugerido)
```text
numpy
scipy
matplotlib
seaborn
pandas
pytest
librosa   # opcional para spectrograms/visualización
plotly    # opcional
scikit-learn  # opcional para clasificación de interferencias
```