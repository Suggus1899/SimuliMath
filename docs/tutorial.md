# Tutorial de SimuliMath
Bienvenido al tutorial de SimuliMath. Este documento te guiará a través de las funcionalidades principales de la aplicación y los pasos para instalar, ejecutar y solucionar errores comunes.
## Contenido
- Introducción
- Requisitos
- Instalación y ejecución (Windows)
- Uso básico
- Pestaña Experimentos
- Exportación de resultados
- Solución de problemas comunes
- Capturas y documentación
---
## Introducción
SimuliMath es una herramienta para simular interferencias en sistemas de comunicación inalámbrica. Incluye una interfaz gráfica (Tkinter), visualizaciones con Matplotlib y opciones para configurar jammers, modulaciones y métricas como BER y SNR empírico.
## Requisitos
- Python 3.8+ (se recomienda 3.10+)
- Paquetes listados en `requirements.txt` (numpy, scipy, matplotlib, pandas, pytest)
- En Windows, `tkinter` suele incluirse con Python; si falta, reinstala Python seleccionando Tcl/Tk.
## Instalación y ejecución (Windows)
1. Clona o descarga el proyecto y abre PowerShell en la carpeta raíz del proyecto.
2. Crear y activar un entorno virtual:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
3. Instalar dependencias:
```powershell
pip install -r requirements.txt
```
4. Ejecutar la aplicación:
```powershell
python simulimath_gui.py
```
Atajos dentro de la app:
## Instalación y ejecución

Las instrucciones siguientes cubren Windows, Linux (Ubuntu/Debian, Fedora, Arch) y macOS. En todos los casos se recomienda crear un entorno virtual y usar `pip install -r requirements.txt`.

### Windows

1. Clona o descarga el proyecto y abre PowerShell en la carpeta raíz del proyecto.

2. Crear y activar un entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

4. Ejecutar la aplicación:

```powershell
python simulimath_gui.py
```

### Linux (Ubuntu / Debian)

1. Instala las dependencias del sistema (si falta `tkinter`):

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip python3-tk
```

2. Crear y activar un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instalar dependencias Python y ejecutar:

```bash
pip install -r requirements.txt
python simulimath_gui.py
```

### Linux (Fedora / CentOS)

```bash
sudo dnf install python3 python3-venv python3-pip python3-tkinter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python simulimath_gui.py
```

### Linux (Arch)

```bash
sudo pacman -Syu python tk
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python simulimath_gui.py
```

### macOS

1. Recomendado: usar Homebrew para instalar Python si no lo tienes:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python tcl-tk
```

2. Crear y activar un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instalar dependencias y ejecutar:

```bash
pip install -r requirements.txt
python simulimath_gui.py
```

Nota: en macOS, si la interfaz no aparece correctamente, puede ser necesario instalar `tcl-tk` desde Homebrew y configurar variables de entorno para que Python use la versión correcta de Tcl/Tk; en la mayoría de instalaciones recientes de Homebrew esto se gestiona automáticamente.

Atajos dentro de la app:
- `Ctrl+O`: Abrir configuración JSON
- `Ctrl+S`: Guardar configuración (config/settings.json)
- `F1`: Abrir guía de uso
---
## Uso básico
1. En la pestaña "Simulación básica" ajusta `Bits` y `SNR [dB]`.
2. Selecciona la `Modulación` y el `Tipo de Interferencia` si procede.
3. Pulsa `Correr simulación` para ejecutar y visualizar señal/espéctro.
## Pestaña Experimentos
Permite ejecutar múltiples repeticiones (`n_runs`) y obtener métricas estadísticas:
- Define `Número de bits`, `SNR`, `Modulación` y `Tipo de Jammer`.
- Indica `Repeticiones (n_runs)` para ejecutar varias corridas.
- Marca `Guardar resultados` y selecciona `Archivo destino` si quieres exportar CSV.
- Al pulsar `Ejecutar Experimento` se mostrará una barra de progreso y un resumen con BER medio y SNR empírico.

Consejo: usar `n_runs` >= 10 para estadísticas más estables.
## Exportación de resultados

- CSV: desde la pestaña Experimentos (opción `Guardar resultados`).
- Exportar configuración: `Archivo → Exportar configuración...` guarda `params` en JSON.
---
## Solución de problemas comunes

1) Error: `_tkinter.TclError: couldn't open "assets/run_icon.png"`

- Causa: faltan archivos en la carpeta `assets`.
- Solución: crea `assets` en la raíz del proyecto y coloca `run_icon.png`, `save_icon.png`, `reset_icon.png`.
- Si no tienes iconos, crea marcadores de posición (PowerShell):
```powershell
$b=[Convert]::FromBase64String("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6X5VtcAAAAASUVORK5CYII="); [IO.File]::WriteAllBytes("assets/save_icon.png", $b)
[IO.File]::WriteAllBytes("assets/run_icon.png", $b)
[IO.File]::WriteAllBytes("assets/reset_icon.png", $b)
```
2) Error: `couldn't recognize data in image file "assets/save_icon.png"`

- Causa: imagen corrupta o formato no compatible.
- Solución: reemplaza el archivo por otro PNG válido.
3) Error: `ModuleNotFoundError: No module named 'tkinter'`

- En Windows, reinstala Python y asegúrate de incluir Tcl/Tk.
4) Error al guardar: permiso denegado
- Ejecuta PowerShell con permisos adecuados o elige una carpeta de usuario (Documentos) en `Configuración → Rutas por defecto`.
---
## Capturas y documentación visual

Para documentar la interfaz, captura pantallas con `Win+Shift+S` y guarda en `assets/`:
- `assets/screenshot_main.png`: interfaz principal
- `assets/screenshot_experiments.png`: pestaña Experimentos
Inserta las imágenes en Markdown así:
```markdown
![Interfaz principal](../assets/screenshot_main.png)
![Experimentos](../assets/screenshot_experiments.png)
```
---
Si quieres que incluya las capturas automáticamente o una sección para crear un instalador con `pyinstaller`, dime cuál prefieres y lo añado.
# Tutorial de SimuliMath

Bienvenido al tutorial de SimuliMath. Este documento te guiará a través de las funcionalidades principales de la aplicación.

## Introducción
SimuliMath es una herramienta diseñada para simular interferencias en sistemas de comunicación inalámbrica. Ofrece una interfaz gráfica intuitiva y soporte para múltiples técnicas de modulación, métricas avanzadas y visualizaciones interactivas.

---

## Contenido
1. **Configuración inicial**
2. **Simulación básica**
3. **Uso de interferencias (jammers)**
4. **Visualizaciones avanzadas**
5. **Exportación de resultados**

---

## 1. Configuración inicial
1. Descarga e instala SimuliMath.
2. Ejecuta el archivo `simulimath_gui.py`.
3. Familiarízate con la interfaz gráfica.

---

## 2. Simulación básica
1. Ve a la pestaña "Simulación básica".
2. Configura los parámetros como número de bits y SNR.
3. Haz clic en "Ejecutar" para iniciar la simulación.

---

## 3. Uso de interferencias (jammers)
1. Ve a la pestaña "Interferencias".
2. Selecciona el tipo de jammer (CW, Pulsed, Broadband, etc.).
3. Ajusta los parámetros específicos del jammer.
4. Haz clic en "Aplicar" para visualizar los efectos.

---

## 4. Visualizaciones avanzadas
1. Usa las pestañas "Diagrama de Ojo" y "Gráfico de Dispersión" para analizar las señales.
2. Utiliza las herramientas de zoom y selección para explorar los gráficos.

---

## 5. Exportación de resultados
1. Ve a la sección de exportación en la interfaz.
2. Selecciona el formato deseado (Excel, etc.).
3. Guarda los resultados en tu computadora.

---

¡Gracias por usar SimuliMath! Para más información, consulta la documentación completa.