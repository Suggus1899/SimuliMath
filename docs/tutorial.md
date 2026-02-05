# Tutorial de SimuliMath

Guía práctica y técnica para usar SimuliMath, con fundamentos de ondas, interferencia y uso de la interfaz.

## Contenido
- Introducción
- Fundamentos técnicos (ondas e interferencia)
- Requisitos
- Instalación y ejecución
- Uso básico
- Cálculo de interferencia (teórico y empírico)
- Categorización de resultados
- Experimentos y exportación
- Solución de problemas

---
## Introducción
SimuliMath es una herramienta para simular interferencias en comunicaciones inalámbricas. Incluye una interfaz gráfica (Tkinter), visualizaciones con Matplotlib y métricas como BER, SNR, SIR y SINR.

---
## Fundamentos técnicos (ondas e interferencia)
### Ondas electromagnéticas (radio)
- Una onda de radio es una perturbación electromagnética que se propaga a velocidad $c$.
- Relación fundamental: $\lambda = c / f$.
- La potencia recibida se reduce con la distancia debido a pérdidas de trayectoria.

### Interferencia en comunicaciones
- La interferencia ocurre cuando una señal no deseada se suma a la señal útil.
- Tipos comunes: co-canal, canal adyacente y jamming intencional.

### Métricas clave
- **SNR**: relación señal/ruido térmico.
- **SIR**: relación señal/interferencia.
- **SINR**: relación señal/(interferencia + ruido).
- **JSR**: relación jammer/señal (útil para medir severidad del jammer).

Interpretación rápida: valores altos en SIR y SINR indican mejor comunicación; un JSR positivo indica jammer más fuerte que la señal.

---
## Requisitos
- Python 3.8+ (se recomienda 3.10+)
- Paquetes listados en requirements.txt
- En Windows, tkinter suele incluirse con Python

---
## Instalación y ejecución
### Windows
1. Crear y activar entorno virtual:
```powershell
python -m venv .venv
\.venv\Scripts\Activate.ps1
```
2. Instalar dependencias:
```powershell
pip install -r requirements.txt
```
3. Ejecutar:
```powershell
python simulimath_gui.py
```

### Linux / macOS
1. Crear entorno virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
2. Instalar y ejecutar:
```bash
pip install -r requirements.txt
python simulimath_gui.py
```

Atajos dentro de la app:
- Ctrl+O: Abrir configuración JSON
- Ctrl+S: Guardar configuración
- F1: Guía rápida

---
## Uso básico
1. En "Simulación básica" ajusta Bits y SNR.
2. Selecciona Modulación y el tipo de interferencia.
3. Pulsa "Correr simulación" para ver señal, espectro y métricas.

---
## Cálculo de interferencia (teórico y empírico)
### Teórico (panel "Cálculo de Interferencia")
Ingresa potencia de señal y jammer, distancias, frecuencia y ancho de banda. El sistema calcula SIR, SINR y JSR, además de una severidad cualitativa.

### Empírico (simulación)
Cuando ejecutas una simulación, se estiman SIR/SINR usando las señales generadas, y se muestra una severidad basada en la degradación.

---
## Categorización de resultados
La UI muestra estados:
- **Buena / Regular / Mala / Crítica** para calidad general (BER/SNR/PER).
- **Interferencia baja / moderada / alta / crítica** para impacto del jammer (SIR/SINR/JSR).

---
## Experimentos y exportación
### Experimentos
- Ejecuta múltiples repeticiones para estadísticas más estables.
- Recomendación: n_runs >= 10.

### Exportación
- CSV desde Experimentos.
- Exportar configuración en JSON desde el menú Archivo.

---
## Solución de problemas
- Si falta tkinter, reinstala Python con Tcl/Tk.
- Si hay errores de permisos al guardar, usa una carpeta de usuario.

---
Si necesitas ejemplos con valores reales o interpretación de resultados, indícalo y lo añadimos.