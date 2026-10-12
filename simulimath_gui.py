"""
simulimath_gui.py: Esqueleto Tkinter para SimuliMath
- Ventana principal con tabs para simulación básica y jammers
- Panel de controles a la izquierda, gráficos a la derecha
- Usa matplotlib embebido (FigureCanvasTkAgg)
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import webbrowser
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import RectangleSelector
from matplotlib.pyplot import scatter
import pandas as pd
from tkinter import PhotoImage

# Importar módulos de simulación
from sim.core import generate_bits, bpsk_mod, add_awgn, bpsk_demod, ber
from sim.jammer import jammer_cw, jammer_pulsed, jammer_broadband, jammer_sweep, jammer_chirp, jammer_multitone
from sim.metrics import empirical_snr, packet_error_rate, empirical_sinr
from sim.quality import (
    overall_quality,
    classify_ber,
    classify_snr,
    get_quality_indicator,
    QUALITY_COLORS,
    BER_THRESHOLDS,
    SNR_THRESHOLDS,
    PER_THRESHOLDS,
)
from sim.interference import (
    calculate_jammer_impact,
    signal_to_interference_ratio,
    jammer_to_signal_ratio,
    interference_severity,
)
from sim.theory import get_theory_text, get_all_topics, THEORY_INFO

class SimuliMathApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SimuliMath GUI")
        self.geometry("1100x700")
        # rutas de configuración
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "settings.json"
        # Parámetros por defecto
        self.params = {
            "n_bits": 2000,
            "snr_db": 5.0,
            "modulation": "BPSK",
            "jammer": "None",
            "fj": 1000.0,
            "Aj": 1.0,
            "duty": 0.5,
            "prf": 50.0,
            "bandwidth": 2000.0,
            "fstart": 500.0,
            "fstop": 2000.0,
            "sweep_rate": 1.0,
            "seed": 123,
            "freqs": [1000.0, 2000.0, 3000.0],
            "p_signal_dbm": 10.0,
            "p_jammer_dbm": 0.0,
            "d_signal_m": 100.0,
            "d_jammer_m": 50.0,
            "frequency_hz": 2.4e9,
            "bandwidth_hz": 1e6,
            "path_loss_exp": 2.0,
            "quality_thresholds": {
                "ber": {
                    "excellent": BER_THRESHOLDS["excellent"],
                    "good": BER_THRESHOLDS["good"],
                    "fair": BER_THRESHOLDS["fair"],
                    "poor": BER_THRESHOLDS["poor"],
                },
                "snr": {
                    "excellent": SNR_THRESHOLDS["excellent"],
                    "good": SNR_THRESHOLDS["good"],
                    "fair": SNR_THRESHOLDS["fair"],
                    "poor": SNR_THRESHOLDS["poor"],
                },
                "per": {
                    "excellent": PER_THRESHOLDS["excellent"],
                    "good": PER_THRESHOLDS["good"],
                    "fair": PER_THRESHOLDS["fair"],
                    "poor": PER_THRESHOLDS["poor"],
                },
            },
        }
        # Paleta y estilos
        self.colors = {
            "bg": "#0f172a",
            "panel": "#111827",
            "accent": "#38bdf8",
            "text": "#e5e7eb",
            "muted": "#94a3b8",
            "warn": "#f59e0b",
        }
        # cargar configuraciones (si existen) antes de configurar estilo
        self._load_settings()
        try:
            self._apply_quality_thresholds(self.params.get("quality_thresholds"))
        except (ValueError, TypeError):
            # Umbrales corruptos en settings.json: se ignoran y se usan
            # los valores por defecto en vez de impedir el arranque.
            self.params.pop("quality_thresholds", None)
        self._configure_style()
        # Construir UI después de definir params
        self._build_menu()
        self._build_layout()

        # Validación de entradas en tiempo real
        self.n_bits_var = tk.IntVar(value=self.params["n_bits"])
        self._validate_entry(self.n_bits_var, "int")
        self.snr_var = tk.DoubleVar(value=self.params["snr_db"])
        self._validate_entry(self.snr_var, "float")

        # Atajos de teclado
        self.bind_all("<Control-s>", lambda e: self._save_current_settings())
        self.bind_all("<Control-o>", lambda e: self._open_file())
        self.bind_all("<F1>", lambda e: self._show_help())

    def _load_settings(self):
        """Carga configuraciones desde config/settings.json si existe."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                # Aplicar valores guardados (solo algunos ejemplos)
                self.params.update(cfg.get("params", {}))
                theme = cfg.get("theme")
                if theme == "light":
                    self.colors["bg"] = "#f8fafc"
                    self.colors["panel"] = "#ffffff"
                    self.colors["text"] = "#0f172a"
            except Exception:
                pass

    def _save_settings(self, extra: dict | None = None):
        """Guarda configuraciones mínimas en config/settings.json."""
        data = {"params": self.params}
        if extra:
            data.update(extra)
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _save_current_settings(self):
        """Atajo público que guarda el estado actual de parámetros en settings.json."""
        self.params["n_bits"] = int(self.n_bits_var.get()) if hasattr(self, "n_bits_var") else self.params["n_bits"]
        self.params["snr_db"] = float(self.snr_var.get()) if hasattr(self, "snr_var") else self.params["snr_db"]
        self._save_settings()
        messagebox.showinfo("Configuración", "Configuración guardada en config/settings.json")

    def _build_menu(self):
        menubar = tk.Menu(self)

        # Menú Archivo (más completo)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Abrir configuración...\tCtrl+O", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Guardar configuración...\tCtrl+S", command=self._save_current_settings, accelerator="Ctrl+S")
        file_menu.add_command(label="Exportar configuración...", command=self._export_settings)
        file_menu.add_separator()
        recent_menu = tk.Menu(file_menu, tearoff=0)
        recent_menu.add_command(label="(vacío)")
        file_menu.add_cascade(label="Recientes", menu=recent_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.destroy)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # Menú Configuración (avanzada)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Parámetros...", command=self._open_settings)
        settings_menu.add_command(label="Umbrales de calidad...", command=self._open_quality_thresholds)
        settings_menu.add_command(label="Tema: Claro/Oscuro", command=self._toggle_theme)
        settings_menu.add_command(label="Rutas por defecto", command=self._open_paths_settings)
        settings_menu.add_command(label="Registro/Logging", command=self._open_logging_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label="Restaurar valores por defecto", command=self._restore_defaults)
        menubar.add_cascade(label="Configuración", menu=settings_menu)

        # Menú Ayuda (extendido)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Guía de uso (F1)", command=self._show_help, accelerator="F1")
        help_menu.add_command(label="Atajos de teclado", command=self._show_shortcuts)
        help_menu.add_command(label="Tutoriales (documentación)", command=lambda: webbrowser.open('docs/tutorial.md'))
        help_menu.add_command(label="Reportar un problema", command=self._report_issue)
        help_menu.add_separator()
        help_menu.add_command(label="Acerca de", command=lambda: messagebox.showinfo("SimuliMath", "Simulador académico de interferencias\nVersión: 0.1"))
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        self.config(menu=menubar)

    # --- Acciones del menú: archivos, ayuda y configuración avanzada ---
    def _open_file(self):
        p = filedialog.askopenfilename(title="Abrir configuración", filetypes=[("JSON", "*.json"), ("All files", "*")])
        if not p:
            return
        try:
            with open(p, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            self.params.update(cfg.get('params', {}))
            messagebox.showinfo('Abrir', f'Configuración cargada desde {p}')
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo abrir el archivo: {e}')

    def _export_settings(self):
        p = filedialog.asksaveasfilename(title='Exportar configuración', defaultextension='.json', filetypes=[('JSON', '*.json')])
        if not p:
            return
        try:
            with open(p, 'w', encoding='utf-8') as f:
                json.dump({'params': self.params}, f, indent=2)
            messagebox.showinfo('Exportar', f'Configuración exportada en {p}')
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo exportar: {e}')

    def _show_shortcuts(self):
        text = (
            'Atajos de teclado:\n'
            'Ctrl+O: Abrir configuración\n'
            'Ctrl+S: Guardar configuración\n'
            'F1: Abrir guía de uso\n'
        )
        messagebox.showinfo('Atajos', text)

    def _report_issue(self):
        webbrowser.open('mailto:bugs@example.com?subject=SimuliMath%20Issue')

    def _toggle_theme(self):
        # Simple toggle between dark and light palette
        if self.colors.get('bg') == '#0f172a':
            # switch to light
            self.colors['bg'] = '#f8fafc'
            self.colors['panel'] = '#ffffff'
            self.colors['text'] = '#0f172a'
        else:
            self.colors['bg'] = '#0f172a'
            self.colors['panel'] = '#111827'
            self.colors['text'] = '#e5e7eb'
        self._configure_style()
        messagebox.showinfo('Tema', 'Tema cambiado. Guarda la configuración si quieres conservarlo.')

    def _open_paths_settings(self):
        w = tk.Toplevel(self)
        w.title('Rutas por defecto')
        w.configure(bg=self.colors['bg'])
        ttk.Label(w, text='Carpeta por defecto para exportar:', style='Label.TLabel').pack(anchor=tk.W, padx=10, pady=6)
        default_dir = self.params.get('default_save_dir', str(Path.cwd()))
        dir_var = tk.StringVar(value=default_dir)
        ttk.Entry(w, textvariable=dir_var, width=50).pack(anchor=tk.W, padx=10)
        def _choose():
            d = filedialog.askdirectory()
            if d:
                dir_var.set(d)
        ttk.Button(w, text='Seleccionar...', command=_choose, width=14).pack(padx=10, pady=6)
        def _save():
            self.params['default_save_dir'] = dir_var.get()
            self._save_settings()
            messagebox.showinfo('Rutas', 'Ruta guardada.')
            w.destroy()
        ttk.Button(w, text='Guardar', command=_save, width=14).pack(pady=8)
        w.transient(self); w.grab_set(); self.wait_window(w)

    def _open_logging_settings(self):
        w = tk.Toplevel(self)
        w.title('Logging')
        w.configure(bg=self.colors['bg'])
        enabled = tk.BooleanVar(value=self.params.get('logging_enabled', False))
        ttk.Checkbutton(w, text='Habilitar logging', variable=enabled).pack(anchor=tk.W, padx=10, pady=8)
        ttk.Label(w, text='Nivel:', style='Label.TLabel').pack(anchor=tk.W, padx=10)
        level = tk.StringVar(value=self.params.get('logging_level', 'INFO'))
        ttk.Combobox(w, textvariable=level, values=['DEBUG', 'INFO', 'WARNING', 'ERROR'], state='readonly', width=12).pack(anchor=tk.W, padx=10, pady=6)
        def _save():
            self.params['logging_enabled'] = enabled.get()
            self.params['logging_level'] = level.get()
            self._save_settings()
            messagebox.showinfo('Logging', 'Configuración de logging guardada.')
            w.destroy()
        ttk.Button(w, text='Guardar', command=_save, width=14).pack(pady=8)
        w.transient(self); w.grab_set(); self.wait_window(w)

    def _restore_defaults(self):
        if messagebox.askyesno('Restaurar', 'Restaurar valores predeterminados?'):
            # Reset params to initial defaults
            self.params = {
                "n_bits": 2000,
                "snr_db": 5.0,
                "modulation": "BPSK",
                "jammer": "None",
                "fj": 1000.0,
                "Aj": 1.0,
                "duty": 0.5,
                "prf": 50.0,
                "bandwidth": 2000.0,
                "fstart": 500.0,
                "fstop": 2000.0,
                "sweep_rate": 1.0,
                "seed": 123,
            }
            try:
                if self.config_file.exists():
                    self.config_file.unlink()
            except Exception:
                pass
            messagebox.showinfo('Restaurar', 'Valores predeterminados restaurados.')

    def _show_help(self):
        help_text = (
            "Bienvenido a SimuliMath.\n\n"
            "Esta aplicación permite simular interferencias en comunicaciones inalámbricas.\n"
            "Utilice las pestañas para navegar entre las diferentes funcionalidades.\n"
            "Consulte la documentación para más detalles."
        )
        messagebox.showinfo("Guía de uso", help_text)

    def _open_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Configuración")
        settings_window.geometry("400x300")
        settings_window.configure(bg=self.colors["bg"])

        ttk.Label(settings_window, text="Configuraciones", style="Label.TLabel").pack(pady=10)

        # Ejemplo de configuración: Semilla RNG
        ttk.Label(settings_window, text="Semilla RNG:", style="Label.TLabel").pack(anchor=tk.W, padx=10)
        seed_var = tk.IntVar(value=self.params["seed"])
        ttk.Entry(settings_window, textvariable=seed_var, width=20).pack(anchor=tk.W, padx=10, pady=5)

        # Botón para guardar configuraciones
        def save_settings():
            self.params["seed"] = seed_var.get()
            messagebox.showinfo("Configuración", "Configuraciones guardadas correctamente.")
            settings_window.destroy()

        ttk.Button(settings_window, text="Guardar", command=save_settings, width=16).pack(pady=10)

        settings_window.transient(self)
        settings_window.grab_set()
        self.wait_window(settings_window)

    def _apply_quality_thresholds(self, thresholds: dict | None):
        """Aplica umbrales de calidad a los módulos de clasificación."""
        if not thresholds:
            return

        ber = thresholds.get("ber", {})
        snr = thresholds.get("snr", {})
        per = thresholds.get("per", {})

        for key in ("excellent", "good", "fair", "poor"):
            if key in ber:
                BER_THRESHOLDS[key] = float(ber[key])
            if key in snr:
                SNR_THRESHOLDS[key] = float(snr[key])
            if key in per:
                PER_THRESHOLDS[key] = float(per[key])

    def _open_quality_thresholds(self):
        """Permite editar umbrales de clasificación desde la UI."""
        w = tk.Toplevel(self)
        w.title("Umbrales de calidad")
        w.geometry("420x420")
        w.configure(bg=self.colors["bg"])

        ttk.Label(w, text="Editar umbrales de clasificación", style="Label.TLabel").pack(pady=10)

        def make_section(title, defaults):
            frame = ttk.LabelFrame(w, text=title, style="Label.TLabel")
            frame.pack(fill=tk.X, padx=10, pady=6)
            vars_map = {}
            for key in ("excellent", "good", "fair", "poor"):
                row = ttk.Frame(frame, style="Tab.TFrame")
                row.pack(fill=tk.X, padx=6, pady=2)
                ttk.Label(row, text=key.capitalize(), style="Label.TLabel", width=10).pack(side=tk.LEFT)
                var = tk.DoubleVar(value=float(defaults.get(key, 0)))
                ttk.Entry(row, textvariable=var, width=12).pack(side=tk.LEFT)
                vars_map[key] = var
            return vars_map

        ber_vars = make_section("BER (menor es mejor)", BER_THRESHOLDS)
        snr_vars = make_section("SNR (mayor es mejor)", SNR_THRESHOLDS)
        per_vars = make_section("PER (menor es mejor)", PER_THRESHOLDS)

        def _save():
            try:
                ber_vals = {k: float(v.get()) for k, v in ber_vars.items()}
                snr_vals = {k: float(v.get()) for k, v in snr_vars.items()}
                per_vals = {k: float(v.get()) for k, v in per_vars.items()}
            except ValueError:
                messagebox.showerror("Error", "Umbrales inválidos")
                return

            if not (0 < ber_vals["excellent"] < ber_vals["good"] < ber_vals["fair"] < ber_vals["poor"] < 1.0):
                messagebox.showerror("Error", "BER debe cumplir: excellent < good < fair < poor < 1")
                return
            if not (0 < per_vals["excellent"] < per_vals["good"] < per_vals["fair"] < per_vals["poor"] < 1.0):
                messagebox.showerror("Error", "PER debe cumplir: excellent < good < fair < poor < 1")
                return
            if not (snr_vals["excellent"] > snr_vals["good"] > snr_vals["fair"] > snr_vals["poor"]):
                messagebox.showerror("Error", "SNR debe cumplir: excellent > good > fair > poor")
                return

            thresholds = {
                "ber": ber_vals,
                "snr": snr_vals,
                "per": per_vals,
            }
            self._apply_quality_thresholds(thresholds)
            self.params["quality_thresholds"] = thresholds
            self._save_settings()
            messagebox.showinfo("Umbrales", "Umbrales actualizados")
            w.destroy()

        ttk.Button(w, text="Guardar", style="Accent.TButton", command=_save, width=16).pack(pady=10)
        ttk.Button(w, text="Cancelar", command=w.destroy, width=16).pack()

        w.transient(self)
        w.grab_set()
        self.wait_window(w)

    def _build_layout(self):
        self.configure(bg=self.colors["bg"])
        main = ttk.Frame(self, style="Main.TFrame")
        main.pack(fill=tk.BOTH, expand=True)
        # Panel de controles
        controls = ttk.Frame(main, padding=10, style="Controls.TFrame")
        controls.pack(side=tk.LEFT, fill=tk.Y)
        # Tabs de contenido
        content = ttk.Notebook(main, style="Tabs.TNotebook")
        content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Tab simulación básica
        tab_basic = ttk.Frame(content, style="Tab.TFrame")
        content.add(tab_basic, text="Simulación básica")

        # Tab jammers
        tab_jammer = ttk.Frame(content, style="Tab.TFrame")
        content.add(tab_jammer, text="Interferencias")

        # Controles comunes
        self._add_common_controls(controls)

        # Área de gráficos
        self.fig = Figure(figsize=(7, 5), dpi=100)
        self.ax_time = self.fig.add_subplot(2, 1, 1)
        self.ax_freq = self.fig.add_subplot(2, 1, 2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=tab_basic)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Área de gráficos para jammers
        self.fig_j = Figure(figsize=(7, 5), dpi=100)
        self.ax_j_time = self.fig_j.add_subplot(2, 1, 1)
        self.ax_j_freq = self.fig_j.add_subplot(2, 1, 2)
        self.canvas_j = FigureCanvasTkAgg(self.fig_j, master=tab_jammer)
        self.canvas_j.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab diagrama de ojo
        tab_eye = ttk.Frame(content, style="Tab.TFrame")
        content.add(tab_eye, text="Diagrama de Ojo")
        self.fig_eye = Figure(figsize=(7, 5), dpi=100)
        self.ax_eye = self.fig_eye.add_subplot(1, 1, 1)
        self.canvas_eye = FigureCanvasTkAgg(self.fig_eye, master=tab_eye)
        self.canvas_eye.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab gráfico de dispersión
        tab_scatter = ttk.Frame(content, style="Tab.TFrame")
        content.add(tab_scatter, text="Gráfico de Dispersión")
        self.fig_scatter = Figure(figsize=(7, 5), dpi=100)
        self.ax_scatter = self.fig_scatter.add_subplot(1, 1, 1)
        self.canvas_scatter = FigureCanvasTkAgg(self.fig_scatter, master=tab_scatter)
        self.canvas_scatter.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab experimentos
        self._add_experiment_tab(content)

        # Tab fundamentos teóricos
        self._add_theory_tab(content)

        # Tab análisis de interferencia
        self._add_interference_analysis_tab(content)

        # Habilitar zoom y selección en gráficos
        self._enable_zoom_and_selection()

    def _configure_style(self):
        """Configura la paleta de colores y estilos de la interfaz."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Tab.TFrame", background=self.colors["bg"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 10))
        style.configure("Label.TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 10))
        style.configure("Output.TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 9))

        # Botones con contraste garantizado en todos los estados
        style.configure(
            "TButton",
            background=self.colors["panel"],
            foreground=self.colors["text"],
            padding=6,
            relief="flat",
        )
        style.map(
            "TButton",
            background=[("active", self.colors["accent"]), ("disabled", self.colors["panel"])],
            foreground=[("disabled", self.colors["muted"]), ("!disabled", self.colors["text"])],
        )

        style.configure(
            "Accent.TButton",
            background=self.colors["accent"],
            foreground=self.colors["bg"],
            padding=6,
            relief="flat",
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.colors["warn"]), ("disabled", self.colors["panel"])],
            foreground=[("disabled", self.colors["muted"]), ("!disabled", self.colors["bg"])],
        )

        style.configure(
            "TCombobox",
            fieldbackground=self.colors["panel"],
            foreground=self.colors["text"],
            background=self.colors["panel"],
            arrowcolor=self.colors["text"],
        )

        # Añadir iconos a los botones
        placeholder_icon = "R0lGODlhAQABAPAAAP///wAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw=="  # GIF 1x1 transparente

        def _safe_icon(path: str) -> PhotoImage:
            try:
                return PhotoImage(file=path)
            except tk.TclError:
                return PhotoImage(data=placeholder_icon)

        self.icons = {
            "run": _safe_icon("assets/run_icon.png"),
            "save": _safe_icon("assets/save_icon.png"),
            "reset": _safe_icon("assets/reset_icon.png"),
        }

    def _add_tooltips(self, widget, text):
        """Añade tooltips a los widgets."""
        tooltip = tk.Toplevel(widget, bg=self.colors["bg"], padx=5, pady=5)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        ttk.Label(tooltip, text=text, style="TLabel").pack()

        def show_tooltip(event):
            tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            tooltip.deiconify()

        def hide_tooltip(event):
            tooltip.withdraw()

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    # Validación de entradas en tiempo real
    def _validate_entry(self, var, validation_type):
        """Valida entradas en tiempo real sin romper el callback.

        Se valida la cadena del valor leido: con texto invalido,
        IntVar.get()/DoubleVar.get() lanzan TclError, y con enteros
        validos devuelven int (que no tiene .isdigit()).
        """
        def validate(*args):
            try:
                value = var.get()
            except (tk.TclError, ValueError):
                # Texto intermedio o invalido: no se toca el campo; el
                # llamador (run_simulation, experimentos) valida por su cuenta.
                return
            if validation_type == "int":
                if not str(value).lstrip("+-").isdigit():
                    var.set("0")
            elif validation_type == "float":
                try:
                    float(value)
                except (ValueError, TypeError):
                    var.set("0.0")

        var.trace_add("write", validate)

    def _add_common_controls(self, parent):
        ttk.Label(parent, text="Bits", style="Label.TLabel").pack(anchor=tk.W)
        self.bits_var = tk.IntVar(value=self.params["n_bits"])
        bits_entry = ttk.Entry(parent, textvariable=self.bits_var, width=12)
        bits_entry.pack(anchor=tk.W)
        self._add_tooltips(bits_entry, "Número de bits para la simulación")

        ttk.Label(parent, text="SNR [dB]", style="Label.TLabel").pack(anchor=tk.W, pady=(6, 0))
        self.snr_var = tk.DoubleVar(value=self.params["snr_db"])
        snr_entry = ttk.Entry(parent, textvariable=self.snr_var, width=12)
        snr_entry.pack(anchor=tk.W)
        self._add_tooltips(snr_entry, "Relación señal/ruido en decibelios")

        ttk.Label(parent, text="Modulación", style="Label.TLabel").pack(anchor=tk.W, pady=(6,0))
        self.mod_var = tk.StringVar(value=self.params["modulation"])
        ttk.Combobox(parent, textvariable=self.mod_var, values=["BPSK", "QPSK"], state="readonly", width=10).pack(anchor=tk.W)

        ttk.Label(parent, text="Interferencia", style="Label.TLabel").pack(anchor=tk.W, pady=(6,0))
        self.jam_var = tk.StringVar(value=self.params["jammer"])
        jam_combo = ttk.Combobox(parent, textvariable=self.jam_var, values=["None", "CW", "Pulsed", "Broadband", "Sweep", "Chirp", "Multitone"], state="readonly", width=12)
        jam_combo.pack(anchor=tk.W)
        jam_combo.bind("<<ComboboxSelected>>", lambda e: self._update_jammer_controls())

        ttk.Label(parent, text="Semilla RNG", style="Label.TLabel").pack(anchor=tk.W, pady=(6,0))
        self.seed_var = tk.IntVar(value=self.params["seed"])
        ttk.Entry(parent, textvariable=self.seed_var, width=12).pack(anchor=tk.W)

        # --- Parámetros específicos de jammer ---
        self.jammer_frame = ttk.LabelFrame(parent, text="Parámetros jammer", style="Label.TLabel")
        self.jammer_frame.pack(anchor=tk.W, fill=tk.X, pady=(10,0))
        self._build_jammer_controls()

        # --- Botones ---
        ttk.Button(parent, text="Correr simulación", style="Accent.TButton", command=self.run_simulation, width=20).pack(anchor=tk.W, pady=10)
        ttk.Button(parent, text="Probar jammer", style="Accent.TButton", command=self.run_jammer, width=20).pack(anchor=tk.W)
        ttk.Button(parent, text="Guardar métricas (CSV)", style="TButton", command=self.save_metrics_csv, width=20).pack(anchor=tk.W, pady=(8,0))
        ttk.Button(parent, text="Guardar gráfica (PNG)", style="TButton", command=self.save_plot_png, width=20).pack(anchor=tk.W)
        ttk.Button(parent, text="Guardar reporte (TXT)", style="TButton", command=self.save_report_txt, width=20).pack(anchor=tk.W, pady=(8, 0))

        # --- Exportar resultados ---
        self._add_export_options(parent)

        ttk.Label(parent, text="Salida", style="Label.TLabel").pack(anchor=tk.W, pady=(12,0))
        self.output_var = tk.StringVar(value="Listo")
        ttk.Label(parent, textvariable=self.output_var, wraplength=200, style="Output.TLabel").pack(anchor=tk.W)

        # --- Panel de indicadores de calidad ---
        self._build_quality_panel(parent)

        # --- Panel de interferencia ---
        self._build_interference_panel(parent)

        # --- Cálculo teórico de interferencia ---
        self._build_interference_controls(parent)

    def _build_interference_controls(self, parent):
        """Controles para cálculo teórico de interferencia."""
        frame = ttk.LabelFrame(parent, text="⚡ Cálculo de Interferencia (teórico)", style="Label.TLabel")
        frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(frame, text="Potencia señal TX (dBm)", style="Label.TLabel").pack(anchor=tk.W, padx=6, pady=(4, 0))
        self.p_signal_dbm_var = tk.DoubleVar(value=self.params["p_signal_dbm"])
        p_signal_entry = ttk.Entry(frame, textvariable=self.p_signal_dbm_var, width=12)
        p_signal_entry.pack(anchor=tk.W, padx=6)
        self._add_tooltips(p_signal_entry, "Potencia de la señal deseada en dBm")

        ttk.Label(frame, text="Potencia jammer TX (dBm)", style="Label.TLabel").pack(anchor=tk.W, padx=6, pady=(4, 0))
        self.p_jammer_dbm_var = tk.DoubleVar(value=self.params["p_jammer_dbm"])
        p_jammer_entry = ttk.Entry(frame, textvariable=self.p_jammer_dbm_var, width=12)
        p_jammer_entry.pack(anchor=tk.W, padx=6)
        self._add_tooltips(p_jammer_entry, "Potencia del interferente/jammer en dBm")

        ttk.Label(frame, text="Distancia TX-RX (m)", style="Label.TLabel").pack(anchor=tk.W, padx=6, pady=(4, 0))
        self.d_signal_var = tk.DoubleVar(value=self.params["d_signal_m"])
        d_signal_entry = ttk.Entry(frame, textvariable=self.d_signal_var, width=12)
        d_signal_entry.pack(anchor=tk.W, padx=6)
        self._add_tooltips(d_signal_entry, "Distancia entre transmisor y receptor")

        ttk.Label(frame, text="Distancia Jammer-RX (m)", style="Label.TLabel").pack(anchor=tk.W, padx=6, pady=(4, 0))
        self.d_jammer_var = tk.DoubleVar(value=self.params["d_jammer_m"])
        d_jammer_entry = ttk.Entry(frame, textvariable=self.d_jammer_var, width=12)
        d_jammer_entry.pack(anchor=tk.W, padx=6)
        self._add_tooltips(d_jammer_entry, "Distancia entre jammer e interferido")

        ttk.Label(frame, text="Frecuencia (Hz)", style="Label.TLabel").pack(anchor=tk.W, padx=6, pady=(4, 0))
        self.frequency_var = tk.DoubleVar(value=self.params["frequency_hz"])
        freq_entry = ttk.Entry(frame, textvariable=self.frequency_var, width=12)
        freq_entry.pack(anchor=tk.W, padx=6)
        self._add_tooltips(freq_entry, "Frecuencia de operación en Hz")

        ttk.Label(frame, text="Ancho de banda (Hz)", style="Label.TLabel").pack(anchor=tk.W, padx=6, pady=(4, 0))
        self.bandwidth_if_var = tk.DoubleVar(value=self.params["bandwidth_hz"])
        bw_entry = ttk.Entry(frame, textvariable=self.bandwidth_if_var, width=12)
        bw_entry.pack(anchor=tk.W, padx=6)
        self._add_tooltips(bw_entry, "Ancho de banda del receptor")

        ttk.Label(frame, text="Exponente pérdida (n)", style="Label.TLabel").pack(anchor=tk.W, padx=6, pady=(4, 0))
        self.path_loss_exp_var = tk.DoubleVar(value=self.params["path_loss_exp"])
        n_entry = ttk.Entry(frame, textvariable=self.path_loss_exp_var, width=12)
        n_entry.pack(anchor=tk.W, padx=6)
        self._add_tooltips(n_entry, "Exponente de pérdida de trayectoria")

        ttk.Button(frame, text="Calcular interferencia", style="Accent.TButton", command=self._calculate_interference_theoretical, width=20).pack(anchor=tk.W, padx=6, pady=8)

    def _add_jammer_controls(self, parent):
        """Añade controles específicos para los jammers."""
        ttk.Label(parent, text="Tipo de Jammer:", style="Label.TLabel").pack(anchor=tk.W, padx=10)
        jammer_var = tk.StringVar(value=self.params["jammer"])
        jammer_menu = ttk.Combobox(parent, textvariable=jammer_var, values=["None", "CW", "Pulsed", "Broadband", "Sweep", "Chirp", "Multitone"], state="readonly")
        jammer_menu.pack(anchor=tk.W, padx=10, pady=5)

        # Controles adicionales para parámetros comunes
        ttk.Label(parent, text="Amplitud (Aj):", style="Label.TLabel").pack(anchor=tk.W, padx=10)
        amplitude_var = tk.DoubleVar(value=self.params["Aj"])
        ttk.Entry(parent, textvariable=amplitude_var, width=20).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Label(parent, text="Duty Cycle (Pulsed):", style="Label.TLabel").pack(anchor=tk.W, padx=10)
        duty_var = tk.DoubleVar(value=self.params["duty"])
        ttk.Entry(parent, textvariable=duty_var, width=20).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Label(parent, text="Tasa de Repetición (PRF):", style="Label.TLabel").pack(anchor=tk.W, padx=10)
        prf_var = tk.DoubleVar(value=self.params["prf"])
        ttk.Entry(parent, textvariable=prf_var, width=20).pack(anchor=tk.W, padx=10, pady=5)

        def apply_jammer():
            self.params["jammer"] = jammer_var.get()
            self.params["Aj"] = amplitude_var.get()
            self.params["duty"] = duty_var.get()
            self.params["prf"] = prf_var.get()
            messagebox.showinfo("Configuración", "Parámetros de jammer actualizados.")

        ttk.Button(parent, text="Aplicar", command=apply_jammer, width=16).pack(pady=10)

    def _build_jammer_controls(self):
        # Limpiar frame
        for w in self.jammer_frame.winfo_children():
            w.destroy()
        jam = self.jam_var.get()
        # Común a todos los jammers excepto None
        if jam in ("CW", "Pulsed", "Broadband", "Sweep", "Chirp", "Multitone"):
            ttk.Label(self.jammer_frame, text="Amplitud (Aj)", style="Label.TLabel").pack(anchor=tk.W)
            self.aj_var = tk.DoubleVar(value=self.params["Aj"])
            ttk.Entry(self.jammer_frame, textvariable=self.aj_var, width=10).pack(anchor=tk.W)
        if jam in ("CW", "Pulsed"):
            ttk.Label(self.jammer_frame, text="Frecuencia (fj)", style="Label.TLabel").pack(anchor=tk.W)
            self.fj_var = tk.DoubleVar(value=self.params["fj"])
            ttk.Entry(self.jammer_frame, textvariable=self.fj_var, width=10).pack(anchor=tk.W)
        if jam == "Pulsed":
            ttk.Label(self.jammer_frame, text="Duty cycle (0-1)", style="Label.TLabel").pack(anchor=tk.W)
            self.duty_var = tk.DoubleVar(value=self.params["duty"])
            ttk.Entry(self.jammer_frame, textvariable=self.duty_var, width=10).pack(anchor=tk.W)
            ttk.Label(self.jammer_frame, text="PRF", style="Label.TLabel").pack(anchor=tk.W)
            self.prf_var = tk.DoubleVar(value=self.params["prf"])
            ttk.Entry(self.jammer_frame, textvariable=self.prf_var, width=10).pack(anchor=tk.W)
        if jam == "Broadband":
            ttk.Label(self.jammer_frame, text="Ancho de banda", style="Label.TLabel").pack(anchor=tk.W)
            self.bandwidth_var = tk.DoubleVar(value=self.params["bandwidth"])
            ttk.Entry(self.jammer_frame, textvariable=self.bandwidth_var, width=10).pack(anchor=tk.W)
        if jam == "Sweep":
            ttk.Label(self.jammer_frame, text="fstart", style="Label.TLabel").pack(anchor=tk.W)
            self.fstart_var = tk.DoubleVar(value=self.params["fstart"])
            ttk.Entry(self.jammer_frame, textvariable=self.fstart_var, width=10).pack(anchor=tk.W)
            ttk.Label(self.jammer_frame, text="fstop", style="Label.TLabel").pack(anchor=tk.W)
            self.fstop_var = tk.DoubleVar(value=self.params["fstop"])
            ttk.Entry(self.jammer_frame, textvariable=self.fstop_var, width=10).pack(anchor=tk.W)
            ttk.Label(self.jammer_frame, text="Sweep rate", style="Label.TLabel").pack(anchor=tk.W)
            self.sweep_rate_var = tk.DoubleVar(value=self.params["sweep_rate"])
            ttk.Entry(self.jammer_frame, textvariable=self.sweep_rate_var, width=10).pack(anchor=tk.W)
        if jam == "Chirp":
            ttk.Label(self.jammer_frame, text="Frecuencia inicial", style="Label.TLabel").pack(anchor=tk.W)
            self.f0_var = tk.DoubleVar(value=self.params["fstart"])
            ttk.Entry(self.jammer_frame, textvariable=self.f0_var, width=10).pack(anchor=tk.W)
            ttk.Label(self.jammer_frame, text="Frecuencia final", style="Label.TLabel").pack(anchor=tk.W)
            self.f1_var = tk.DoubleVar(value=self.params["fstop"])
            ttk.Entry(self.jammer_frame, textvariable=self.f1_var, width=10).pack(anchor=tk.W)
        if jam == "Multitone":
            ttk.Label(self.jammer_frame, text="Frecuencias (separadas por comas)", style="Label.TLabel").pack(anchor=tk.W)
            freqs_default = ",".join(str(f) for f in self.params.get("freqs", [1000.0, 2000.0, 3000.0]))
            self.freqs_var = tk.StringVar(value=freqs_default)
            ttk.Entry(self.jammer_frame, textvariable=self.freqs_var, width=30).pack(anchor=tk.W)

    def _update_jammer_controls(self):
        # Reconstruye los controles específicos del jammer en el frame correspondiente
        self._build_jammer_controls()

    def _sync_jammer_params(self):
        """Sincroniza parámetros del jammer desde la UI hacia self.params."""
        if not self._validate_jammer_inputs():
            raise ValueError("Parámetros de jammer inválidos")
        if hasattr(self, "aj_var"):
            self.params["Aj"] = float(self.aj_var.get())
        if hasattr(self, "fj_var"):
            self.params["fj"] = float(self.fj_var.get())
        if hasattr(self, "duty_var"):
            self.params["duty"] = float(self.duty_var.get())
        if hasattr(self, "prf_var"):
            self.params["prf"] = float(self.prf_var.get())
        if hasattr(self, "bandwidth_var") and self.jam_var.get() == "Broadband":
            self.params["bandwidth"] = float(self.bandwidth_var.get())
        if hasattr(self, "fstart_var"):
            self.params["fstart"] = float(self.fstart_var.get())
        if hasattr(self, "fstop_var"):
            self.params["fstop"] = float(self.fstop_var.get())
        if hasattr(self, "sweep_rate_var"):
            self.params["sweep_rate"] = float(self.sweep_rate_var.get())
        if hasattr(self, "f0_var"):
            self.params["fstart"] = float(self.f0_var.get())
        if hasattr(self, "f1_var"):
            self.params["fstop"] = float(self.f1_var.get())
        if hasattr(self, "freqs_var"):
            raw = self.freqs_var.get()
            try:
                freqs = [float(x.strip()) for x in raw.split(",") if x.strip()]
            except ValueError:
                messagebox.showerror("Error", "Frecuencias inválidas. Usa valores numéricos separados por comas.")
                freqs = [1000.0, 2000.0, 3000.0]
            if not freqs:
                messagebox.showerror("Error", "La lista de frecuencias no puede estar vacía.")
                freqs = [1000.0, 2000.0, 3000.0]
            if any(f <= 0 for f in freqs):
                messagebox.showerror("Error", "Todas las frecuencias deben ser > 0.")
                freqs = [f for f in freqs if f > 0] or [1000.0, 2000.0, 3000.0]
            self.params["freqs"] = freqs

    def _validate_jammer_inputs(self) -> bool:
        """Valida rangos físicos de parámetros de jammer."""
        jam = self.jam_var.get()
        errors = []
        if hasattr(self, "aj_var"):
            try:
                aj = float(self.aj_var.get())
                if aj <= 0:
                    errors.append("Amplitud (Aj) debe ser > 0.")
            except ValueError:
                errors.append("Amplitud (Aj) inválida.")
        if hasattr(self, "fj_var"):
            try:
                fj = float(self.fj_var.get())
                if fj <= 0:
                    errors.append("Frecuencia (fj) debe ser > 0.")
            except ValueError:
                errors.append("Frecuencia (fj) inválida.")
        if jam == "Pulsed":
            try:
                duty = float(self.duty_var.get())
                if duty < 0 or duty > 1:
                    errors.append("Duty cycle debe estar entre 0 y 1.")
            except ValueError:
                errors.append("Duty cycle inválido.")
            try:
                prf = float(self.prf_var.get())
                if prf <= 0:
                    errors.append("PRF debe ser > 0.")
            except ValueError:
                errors.append("PRF inválido.")
        if jam == "Broadband":
            try:
                bw = float(self.bandwidth_var.get())
                if bw <= 0:
                    errors.append("Ancho de banda debe ser > 0.")
            except ValueError:
                errors.append("Ancho de banda inválido.")
        if jam == "Sweep":
            try:
                fstart = float(self.fstart_var.get())
                fstop = float(self.fstop_var.get())
                if fstart <= 0 or fstop <= 0:
                    errors.append("fstart y fstop deben ser > 0.")
                if fstart >= fstop:
                    errors.append("fstart debe ser menor que fstop.")
            except ValueError:
                errors.append("fstart/fstop inválidos.")
            try:
                rate = float(self.sweep_rate_var.get())
                if rate <= 0:
                    errors.append("Sweep rate debe ser > 0.")
            except ValueError:
                errors.append("Sweep rate inválido.")
        if jam == "Chirp":
            try:
                f0 = float(self.f0_var.get())
                f1 = float(self.f1_var.get())
                if f0 <= 0 or f1 <= 0:
                    errors.append("Frecuencias de chirp deben ser > 0.")
                if f0 >= f1:
                    errors.append("Frecuencia inicial debe ser menor que final.")
            except ValueError:
                errors.append("Frecuencias de chirp inválidas.")

        if errors:
            messagebox.showerror("Error", "\n".join(errors))
            return False
        return True

    def run_simulation(self):
        try:
            n_bits = int(self.bits_var.get())
            snr_db = float(self.snr_var.get())
            seed = int(self.seed_var.get())
        except ValueError:
            messagebox.showerror("Error", "Parámetros numéricos inválidos")
            return

        if n_bits <= 0 or n_bits > 2_000_000:
            messagebox.showerror("Error", "El número de bits debe estar entre 1 y 2,000,000")
            return
        if snr_db < -20 or snr_db > 60:
            messagebox.showerror("Error", "SNR fuera de rango razonable (-20 a 60 dB)")
            return
        if seed < 0:
            messagebox.showerror("Error", "La semilla RNG debe ser un entero no negativo")
            return

        try:
            self._sync_jammer_params()
        except ValueError:
            return

        bits = generate_bits(n_bits, seed=seed)
        symbols = bpsk_mod(bits)
        jam = self._build_jammer(len(symbols))
        tx = symbols + jam
        rx = add_awgn(tx, snr_db=snr_db, seed=seed)
        bits_rx = bpsk_demod(rx)
        ber_val = ber(bits, bits_rx)
        snr_emp = empirical_snr(symbols, rx - symbols)
        per_val = packet_error_rate(bits, bits_rx, packet_size=max(1, n_bits//10))

        noise = rx - tx
        sinr_emp = empirical_sinr(symbols, jam, noise)

        def power_db(x):
            p = np.mean(np.abs(x) ** 2)
            if p <= 0:
                return float("-inf")
            return 10 * np.log10(p)

        p_signal_db = power_db(symbols)
        p_interf_db = power_db(jam)
        p_noise_db = power_db(noise)

        sir_db = signal_to_interference_ratio(p_signal_db, p_interf_db) if np.isfinite(p_interf_db) else float("inf")
        jsr_db = jammer_to_signal_ratio(p_interf_db, p_signal_db) if np.isfinite(p_interf_db) else float("-inf")
        score, severity, description = interference_severity(sir_db, sinr_emp)

        # Graficar
        self.ax_time.clear()
        self.ax_time.plot(rx[:500])
        self.ax_time.set_title("Señal recibida (muestra)")
        self.ax_freq.clear()
        spectrum = np.abs(np.fft.fft(rx))
        freqs = np.fft.fftfreq(len(rx), d=1.0)
        self.ax_freq.plot(freqs[:len(freqs)//2], spectrum[:len(spectrum)//2])
        self.ax_freq.set_title("Espectro (muestra)")
        self.fig.tight_layout()
        self.canvas.draw()

        # Diagrama de ojo y gráfico de dispersión
        self._add_eye_diagram(rx, samples_per_symbol=10)
        i_signal = np.real(rx)
        q_signal = np.imag(rx)
        self._add_scatter_plot(i_signal, q_signal)

        self.last_metrics = {
            "BER": ber_val,
            "PER": per_val,
            "SNR_emp_dB": snr_emp,
            "SINR_emp_dB": sinr_emp,
            "SIR_dB": sir_db,
            "JSR_dB": jsr_db,
            "Interf_score": score,
            "Interf_level": severity,
            "n_bits": n_bits,
            "snr_db": snr_db,
            "jammer": self.jam_var.get(),
        }
        self.output_var.set(
            f"BER={ber_val:.4e} | PER={per_val:.4f} | SNR_emp={snr_emp:.2f} dB | SINR={sinr_emp:.2f} dB"
        )

        # Actualizar indicadores de calidad
        self._update_quality_indicators(ber_val, snr_emp, per_val)

        # Actualizar indicadores de interferencia
        self._update_interference_indicators(
            sir_db,
            sinr_emp,
            jsr_db,
            score,
            severity,
            description,
            "Empírico",
        )

    def _build_jammer(self, length):
        fs = max(2*int(self.params["fstop"]) if "fstop" in self.params else 10000, 2000)
        jam_type = self.jam_var.get()
        if jam_type == "None":
            return np.zeros(length)
        if jam_type == "CW":
            return jammer_cw(length, fs, fj=self.params["fj"], Aj=self.params["Aj"])
        if jam_type == "Pulsed":
            return jammer_pulsed(length, fs, fj=self.params["fj"], Aj=self.params["Aj"], duty=self.params["duty"], prf=self.params["prf"])
        if jam_type == "Broadband":
            return jammer_broadband(length, fs, bandwidth=self.params["bandwidth"], power=self.params["Aj"])
        if jam_type == "Sweep":
            return jammer_sweep(length, fs, fstart=self.params["fstart"], fstop=self.params["fstop"], rate=self.params["sweep_rate"], Aj=self.params["Aj"])
        if jam_type == "Chirp":
            return jammer_chirp(length, fs, f0=self.params["fstart"], f1=self.params["fstop"], Aj=self.params["Aj"])
        if jam_type == "Multitone":
            return jammer_multitone(length, fs, freqs=self.params["freqs"], Aj=self.params["Aj"])
        return np.zeros(length)

    def run_jammer(self):
        try:
            self._sync_jammer_params()
        except ValueError:
            return
        length = 2000
        fs = 10000
        jam = self._build_jammer(length)
        t = np.arange(length) / fs
        self.ax_j_time.clear()
        self.ax_j_time.plot(t[:500], jam[:500])
        self.ax_j_time.set_title(f"Jammer {self.jam_var.get()} (tiempo)")
        self.ax_j_freq.clear()
        spectrum = np.abs(np.fft.fft(jam))
        freqs = np.fft.fftfreq(len(jam), d=1/fs)
        self.ax_j_freq.plot(freqs[:len(freqs)//2], spectrum[:len(spectrum)//2])
        self.ax_j_freq.set_title(f"Jammer {self.jam_var.get()} (espectro)")
        self.fig_j.tight_layout()
        self.canvas_j.draw()
        self.output_var.set("Jammer graficado")

    def save_metrics_csv(self):
        if not hasattr(self, "last_metrics"):
            messagebox.showinfo("Info", "Primero ejecuta una simulación para generar métricas")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not path:
            return
        header = [
            "n_bits",
            "snr_db",
            "jammer",
            "BER",
            "PER",
            "SNR_emp_dB",
            "SINR_emp_dB",
            "SIR_dB",
            "JSR_dB",
            "Interf_score",
            "Interf_level",
        ]
        values = [self.last_metrics.get(k, "") for k in header]
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(",".join(header) + "\n")
                f.write(",".join(str(v) for v in values) + "\n")
            self.output_var.set(f"Métricas guardadas en {os.path.basename(path)}")
        except OSError as exc:
            messagebox.showerror("Error", f"No se pudo guardar el CSV: {exc}")

    def save_plot_png(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("All", "*.*")])
        if not path:
            return
        try:
            self.fig.savefig(path, dpi=150, bbox_inches="tight")
            self.output_var.set(f"Gráfica guardada en {os.path.basename(path)}")
        except OSError as exc:
            messagebox.showerror("Error", f"No se pudo guardar la imagen: {exc}")

    def save_report_txt(self):
        if not hasattr(self, "last_metrics"):
            messagebox.showinfo("Info", "Primero ejecuta una simulación para generar métricas")
            return

        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt"), ("All", "*.*")])
        if not path:
            return

        metrics = self.last_metrics
        quality = overall_quality(metrics.get("BER", 0.0), metrics.get("SNR_emp_dB", 0.0), metrics.get("PER", 0.0))

        report_lines = [
            "SIMULIMATH - REPORTE DE RESULTADOS",
            "==================================",
            f"Bits: {metrics.get('n_bits', '---')}",
            f"SNR (config): {metrics.get('snr_db', '---')} dB",
            f"Jammer: {metrics.get('jammer', '---')}",
            "",
            "MÉTRICAS EMPÍRICAS",
            "------------------",
            f"BER: {metrics.get('BER', 0.0):.4e}",
            f"PER: {metrics.get('PER', 0.0):.4f}",
            f"SNR empírico: {metrics.get('SNR_emp_dB', 0.0):.2f} dB",
            f"SINR empírico: {metrics.get('SINR_emp_dB', 0.0):.2f} dB",
            f"SIR: {metrics.get('SIR_dB', 0.0):.2f} dB",
            f"JSR: {metrics.get('JSR_dB', 0.0):.2f} dB",
            "",
            "CLASIFICACIÓN DE CALIDAD",
            "-------------------------",
            f"Estado: {quality.get('description', '---')}",
            f"Score: {quality.get('score', 0)}/100",
        ]

        recommendations = quality.get("recommendations", [])
        if recommendations:
            report_lines.append("Recomendaciones:")
            report_lines.extend([f"- {rec}" for rec in recommendations])

        if "Interf_level" in metrics:
            report_lines.extend([
                "",
                "SEVERIDAD DE INTERFERENCIA",
                "---------------------------",
                f"Nivel: {metrics.get('Interf_level', '---')}",
                f"Score: {metrics.get('Interf_score', 0)}/100",
            ])

        report_lines.extend([
            "",
            "Parámetros teóricos usados (si aplica):",
            f"P señal TX (dBm): {self.params.get('p_signal_dbm', '---')}",
            f"P jammer TX (dBm): {self.params.get('p_jammer_dbm', '---')}",
            f"Distancia TX-RX (m): {self.params.get('d_signal_m', '---')}",
            f"Distancia Jammer-RX (m): {self.params.get('d_jammer_m', '---')}",
            f"Frecuencia (Hz): {self.params.get('frequency_hz', '---')}",
            f"Ancho de banda (Hz): {self.params.get('bandwidth_hz', '---')}",
            f"Exponente pérdida (n): {self.params.get('path_loss_exp', '---')}",
        ])

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(report_lines))
            self.output_var.set(f"Reporte guardado en {os.path.basename(path)}")
        except OSError as exc:
            messagebox.showerror("Error", f"No se pudo guardar el reporte: {exc}")

    def _add_export_options(self, parent):
        """Añade opciones para exportar resultados en diferentes formatos."""
        ttk.Label(parent, text="Exportar Resultados:", style="Label.TLabel").pack(anchor=tk.W, padx=10, pady=5)

        def export_to_excel():
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
            if file_path:
                data = {
                    "Tiempo (s)": np.linspace(0, 1, len(self.params["n_bits"])),
                    "Señal": self.params["n_bits"],
                }
                df = pd.DataFrame(data)
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Exportar", f"Resultados exportados a {file_path}")

        ttk.Button(parent, text="Exportar a Excel", command=export_to_excel, width=20).pack(anchor=tk.W, padx=10, pady=5)

    def _enable_zoom_and_selection(self):
        """Habilita el zoom y la selección de regiones en los gráficos."""
        def onselect(eclick, erelease):
            x1, y1 = eclick.xdata, eclick.ydata
            x2, y2 = erelease.xdata, erelease.ydata
            self.ax_time.set_xlim(min(x1, x2), max(x1, x2))
            self.ax_time.set_ylim(min(y1, y2), max(y1, y2))
            self.canvas.draw()

        self.selector = RectangleSelector(
            self.ax_time,
            onselect,
            useblit=True,
            button=[1],  # Botón izquierdo del ratón
            minspanx=5,
            minspany=5,
            spancoords="pixels",
            interactive=True,
        )

        def reset_zoom():
            self.ax_time.set_xlim(auto=True)
            self.ax_time.set_ylim(auto=True)
            self.canvas.draw()

        ttk.Button(self, text="Resetear Zoom", command=reset_zoom, width=18).pack(pady=5)

    def _add_eye_diagram(self, signal, samples_per_symbol):
        """Genera un diagrama de ojo para la señal dada."""
        self.ax_eye.clear()
        for i in range(0, len(signal) - samples_per_symbol, samples_per_symbol):
            self.ax_eye.plot(signal[i:i + samples_per_symbol], color="blue", alpha=0.3)
        self.ax_eye.set_title("Diagrama de Ojo")
        self.ax_eye.grid(True)
        self.canvas_eye.draw()

    def _add_scatter_plot(self, i_signal, q_signal):
        """Genera un gráfico de dispersión para las señales I y Q."""
        self.ax_scatter.clear()
        self.ax_scatter.scatter(i_signal, q_signal, color="red", alpha=0.5)
        self.ax_scatter.set_title("Gráfico de Dispersión")
        self.ax_scatter.grid(True)
        self.canvas_scatter.draw()

    def _add_experiment_tab(self, content):
        """Mejora la pestaña de experimentos con más opciones y diseño intuitivo."""
        tab_experiment = ttk.Frame(content, style="Tab.TFrame")
        content.add(tab_experiment, text="Experimentos")

        # Contenedor principal
        frame = ttk.Frame(tab_experiment, padding=10, style="Controls.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)
        # Encabezado y descripción breve
        ttk.Label(frame, text="Configuración de Experimentos", style="Heading.TLabel").grid(row=0, column=0, columnspan=3, pady=6, sticky=tk.W)
        desc = (
            "Ejecute barridos automáticos o múltiples repeticiones para medir métricas como BER y SNR empírico. "
            "Los experimentos permiten evaluar el efecto de diferentes modulaciones y tipos de jammer."
        )
        ttk.Label(frame, text=desc, style="Label.TLabel", wraplength=520).grid(row=1, column=0, columnspan=3, pady=(0,10), sticky=tk.W)

        # Columnas flexibles
        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=0)
        frame.columnconfigure(2, weight=1)

        # Parámetros principales
        ttk.Label(frame, text="Número de bits:", style="Label.TLabel").grid(row=2, column=0, sticky=tk.W, padx=5, pady=4)
        n_bits_var = tk.IntVar(value=self.params["n_bits"])
        n_bits_entry = ttk.Entry(frame, textvariable=n_bits_var, width=18)
        n_bits_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=4)
        self._add_tooltips(n_bits_entry, "Número de bits por ejecución (ej: 2000)")
        self._validate_entry(n_bits_var, "int")

        ttk.Label(frame, text="SNR (dB):", style="Label.TLabel").grid(row=3, column=0, sticky=tk.W, padx=5, pady=4)
        snr_var = tk.DoubleVar(value=self.params["snr_db"])
        snr_entry = ttk.Entry(frame, textvariable=snr_var, width=18)
        snr_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=4)
        self._add_tooltips(snr_entry, "Relación señal-ruido aplicada en cada ejecución")
        self._validate_entry(snr_var, "float")

        ttk.Label(frame, text="Modulación:", style="Label.TLabel").grid(row=4, column=0, sticky=tk.W, padx=5, pady=4)
        modulation_var = tk.StringVar(value=self.params["modulation"])
        mod_cb = ttk.Combobox(frame, textvariable=modulation_var, values=["BPSK", "QPSK", "QAM"], state="readonly", width=16)
        mod_cb.grid(row=4, column=1, sticky=tk.W, padx=5, pady=4)
        self._add_tooltips(mod_cb, "Tipo de modulación a evaluar")

        ttk.Label(frame, text="Tipo de Jammer:", style="Label.TLabel").grid(row=5, column=0, sticky=tk.W, padx=5, pady=4)
        jammer_var = tk.StringVar(value=self.params["jammer"])
        jammer_cb = ttk.Combobox(frame, textvariable=jammer_var, values=["None", "CW", "Pulsed", "Broadband", "Sweep", "Chirp", "Multitone"], state="readonly", width=16)
        jammer_cb.grid(row=5, column=1, sticky=tk.W, padx=5, pady=4)
        self._add_tooltips(jammer_cb, "Interferencia aplicada durante la ejecución")

        # Parámetros de experimento
        ttk.Label(frame, text="Repeticiones (n_runs):", style="Label.TLabel").grid(row=2, column=2, sticky=tk.W, padx=10, pady=4)
        n_runs_var = tk.IntVar(value=1)
        n_runs_entry = ttk.Entry(frame, textvariable=n_runs_var, width=10)
        n_runs_entry.grid(row=2, column=2, sticky=tk.E, padx=10, pady=4)
        self._add_tooltips(n_runs_entry, "Número de repeticiones del experimento (ej: 10)")
        self._validate_entry(n_runs_var, "int")

        save_var = tk.BooleanVar(value=False)
        save_chk = ttk.Checkbutton(frame, text="Guardar resultados", variable=save_var)
        save_chk.grid(row=3, column=2, sticky=tk.E, padx=10, pady=4)

        ttk.Label(frame, text="Archivo destino:", style="Label.TLabel").grid(row=4, column=2, sticky=tk.W, padx=10, pady=4)
        filename_var = tk.StringVar(value="")
        fname_entry = ttk.Entry(frame, textvariable=filename_var, width=30)
        fname_entry.grid(row=5, column=2, sticky=tk.E, padx=10, pady=4)
        def _choose_file():
            p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if p:
                filename_var.set(p)
        ttk.Button(frame, text="Seleccionar...", command=_choose_file, width=12).grid(row=6, column=2, sticky=tk.E, padx=10, pady=4)

        # Barra de progreso y salida
        progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=520, mode='determinate')
        progress.grid(row=7, column=0, columnspan=3, pady=(12,4), sticky=tk.W+tk.E)
        status_var = tk.StringVar(value="Listo")
        ttk.Label(frame, textvariable=status_var, style="Output.TLabel").grid(row=8, column=0, columnspan=3, sticky=tk.W, pady=(4,0))

        # Botones de control
        ttk.Button(frame, text="Ejecutar Experimento", style="Accent.TButton", command=lambda: self._run_experiment(n_bits_var, snr_var, modulation_var, jammer_var, n_runs_var, save_var, filename_var, progress, status_var), width=22).grid(row=9, column=0, columnspan=2, pady=12, sticky=tk.W)
        ttk.Button(frame, text="Resetear Parámetros", command=lambda: self._reset_experiment_params(n_bits_var, snr_var, modulation_var, jammer_var, n_runs_var, save_var, filename_var, status_var, progress), width=22).grid(row=9, column=2, pady=12, sticky=tk.E)

    # Métodos auxiliares para ejecutar y resetear experimentos
    def _run_experiment(self, n_bits_var, snr_var, modulation_var, jammer_var, n_runs_var, save_var, filename_var, progress, status_var):
        try:
            n_bits = int(n_bits_var.get())
            snr_db = float(snr_var.get())
            n_runs = int(n_runs_var.get())
        except Exception:
            messagebox.showerror("Error", "Parámetros numéricos inválidos para el experimento")
            return

        if n_bits <= 0 or n_bits > 2_000_000:
            messagebox.showerror("Error", "El número de bits debe estar entre 1 y 2,000,000")
            return
        if snr_db < -20 or snr_db > 60:
            messagebox.showerror("Error", "SNR fuera de rango razonable (-20 a 60 dB)")
            return
        if n_runs <= 0 or n_runs > 1000:
            messagebox.showerror("Error", "Número de repeticiones fuera de rango (1 a 1000)")
            return

        if n_bits <= 0 or n_runs <= 0:
            messagebox.showerror("Error", "Número de bits y repeticiones deben ser mayores que 0")
            return

        results = []
        progress['maximum'] = n_runs
        progress['value'] = 0
        seed_base = self.params.get("seed", 123)

        for i in range(n_runs):
            status_var.set(f"Ejecución {i+1}/{n_runs}...")
            self.update_idletasks()
            seed_i = seed_base + i
            bits = generate_bits(n_bits, seed=seed_i)
            symbols = bpsk_mod(bits)
            jam = self._build_jammer(len(symbols))
            tx = symbols + jam
            rx = add_awgn(tx, snr_db=snr_db, seed=seed_i)
            bits_rx = bpsk_demod(rx)
            ber_val = ber(bits, bits_rx)
            snr_emp = empirical_snr(symbols, rx - symbols)
            results.append({"run": i + 1, "ber": ber_val, "snr_emp": snr_emp})
            progress['value'] = i + 1

        # Resumen
        mean_ber = float(np.mean([r['ber'] for r in results])) if results else 0.0
        mean_snr = float(np.mean([r['snr_emp'] for r in results])) if results else 0.0
        status_var.set(f"Completado: BER_mean={mean_ber:.4e}, SNR_emp={mean_snr:.2f} dB")

        # Guardar si corresponde
        if save_var.get():
            path = filename_var.get()
            if not path:
                path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if path:
                df = pd.DataFrame(results)
                df.to_csv(path, index=False)
                messagebox.showinfo("Guardado", f"Resultados guardados en {path}")

        messagebox.showinfo("Experimento", f"Experimento finalizado. BER medio: {mean_ber:.4e}")

    def _reset_experiment_params(self, n_bits_var, snr_var, modulation_var, jammer_var, n_runs_var=None, save_var=None, filename_var=None, status_var=None, progress=None):
        n_bits_var.set(2000)
        snr_var.set(5.0)
        modulation_var.set("BPSK")
        jammer_var.set("None")
        if n_runs_var is not None:
            n_runs_var.set(1)
        if save_var is not None:
            save_var.set(False)
        if filename_var is not None:
            filename_var.set("")
        if status_var is not None:
            status_var.set("Listo")
        if progress is not None:
            try:
                progress['value'] = 0
            except Exception:
                pass
        messagebox.showinfo("Parámetros", "Parámetros reseteados a valores predeterminados.")

    def _add_theory_tab(self, content):
        """Añade la pestaña de fundamentos teóricos con información educativa."""
        tab_theory = ttk.Frame(content, style="Tab.TFrame")
        content.add(tab_theory, text="Fundamentos Teóricos")

        # Contenedor principal con scroll
        canvas = tk.Canvas(tab_theory, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_theory, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Tab.TFrame")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Título principal
        title_frame = ttk.Frame(scrollable_frame, style="Tab.TFrame")
        title_frame.pack(fill=tk.X, padx=20, pady=10)
        ttk.Label(title_frame, text="📡 FUNDAMENTOS DE ONDAS Y ELECTROMAGNETISMO",
                 font=("Segoe UI", 14, "bold"), style="Label.TLabel").pack(anchor=tk.W)
        ttk.Label(title_frame, text="Conceptos clave para entender las interferencias en comunicaciones",
                 style="Label.TLabel").pack(anchor=tk.W)

        # Selector de tema
        topic_frame = ttk.Frame(scrollable_frame, style="Tab.TFrame")
        topic_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(topic_frame, text="Seleccionar tema:", style="Label.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        self.theory_topic_var = tk.StringVar(value="electromagnetic_waves")
        topic_combo = ttk.Combobox(topic_frame, textvariable=self.theory_topic_var,
                                   values=["electromagnetic_waves", "interference", "modulation"],
                                   state="readonly", width=25)
        topic_combo.pack(side=tk.LEFT)

        # Área de texto para mostrar contenido
        text_frame = ttk.Frame(scrollable_frame, style="Tab.TFrame")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.theory_text = tk.Text(text_frame, wrap=tk.WORD, bg=self.colors["panel"],
                                   fg=self.colors["text"], font=("Consolas", 10),
                                   padx=15, pady=15, height=25)
        self.theory_text.pack(fill=tk.BOTH, expand=True)

        # Cargar contenido inicial
        self._update_theory_content()

        # Actualizar cuando cambia el tema
        topic_combo.bind("<<ComboboxSelected>>", lambda e: self._update_theory_content())

        # Sección de fórmulas clave
        formula_frame = ttk.LabelFrame(scrollable_frame, text="Fórmulas Clave", style="Label.TLabel")
        formula_frame.pack(fill=tk.X, padx=20, pady=10)

        formulas = [
            ("Longitud de onda:", "λ = c / f   (donde c = 3×10⁸ m/s)"),
            ("Pérdida espacio libre:", "FSPL = 20log₁₀(d) + 20log₁₀(f) + 20log₁₀(4π/c)"),
            ("BER BPSK:", "Pe = Q(√(2·Eb/N0))"),
            ("Capacidad canal:", "C = B·log₂(1 + SNR)"),
        ]

        for name, formula in formulas:
            row = ttk.Frame(formula_frame, style="Tab.TFrame")
            row.pack(fill=tk.X, padx=10, pady=3)
            ttk.Label(row, text=name, style="Label.TLabel", width=20).pack(side=tk.LEFT)
            ttk.Label(row, text=formula, font=("Consolas", 10), style="Label.TLabel").pack(side=tk.LEFT)

    def _add_interference_analysis_tab(self, content):
        """Añade una pestaña para analizar SIR/SINR vs distancia/potencia."""
        tab_analysis = ttk.Frame(content, style="Tab.TFrame")
        content.add(tab_analysis, text="Análisis Interferencia")

        controls = ttk.Frame(tab_analysis, padding=10, style="Controls.TFrame")
        controls.pack(side=tk.LEFT, fill=tk.Y)

        plot_area = ttk.Frame(tab_analysis, style="Tab.TFrame")
        plot_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(controls, text="Barrido de parámetros", style="Heading.TLabel").pack(anchor=tk.W, pady=(0, 6))

        self.sweep_var = tk.StringVar(value="d_jammer")
        ttk.Label(controls, text="Variable", style="Label.TLabel").pack(anchor=tk.W)
        ttk.Combobox(
            controls,
            textvariable=self.sweep_var,
            values=["d_jammer", "d_signal", "p_jammer"],
            state="readonly",
            width=12,
        ).pack(anchor=tk.W)

        self.sweep_min_var = tk.DoubleVar(value=10.0)
        self.sweep_max_var = tk.DoubleVar(value=500.0)
        self.sweep_steps_var = tk.IntVar(value=25)

        ttk.Label(controls, text="Mínimo", style="Label.TLabel").pack(anchor=tk.W, pady=(6, 0))
        ttk.Entry(controls, textvariable=self.sweep_min_var, width=12).pack(anchor=tk.W)

        ttk.Label(controls, text="Máximo", style="Label.TLabel").pack(anchor=tk.W, pady=(6, 0))
        ttk.Entry(controls, textvariable=self.sweep_max_var, width=12).pack(anchor=tk.W)

        ttk.Label(controls, text="Pasos", style="Label.TLabel").pack(anchor=tk.W, pady=(6, 0))
        ttk.Entry(controls, textvariable=self.sweep_steps_var, width=12).pack(anchor=tk.W)

        ttk.Button(
            controls,
            text="Generar gráfica",
            style="Accent.TButton",
            command=self._run_interference_sweep,
            width=18,
        ).pack(anchor=tk.W, pady=10)

        self.sweep_status_var = tk.StringVar(value="Listo")
        ttk.Label(
            controls,
            textvariable=self.sweep_status_var,
            wraplength=180,
            style="Output.TLabel",
        ).pack(anchor=tk.W)

        self.fig_sweep = Figure(figsize=(7, 5), dpi=100)
        self.ax_sweep = self.fig_sweep.add_subplot(1, 1, 1)
        self.canvas_sweep = FigureCanvasTkAgg(self.fig_sweep, master=plot_area)
        self.canvas_sweep.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _get_theoretical_params(self) -> dict | None:
        """Obtiene parámetros teóricos desde la UI o valores por defecto.

        Devuelve None si alguna entrada no es numerica; el llamador debe
        mostrar el error al usuario.
        """
        try:
            p_signal = float(self.p_signal_dbm_var.get()) if hasattr(self, "p_signal_dbm_var") else self.params["p_signal_dbm"]
            p_jammer = float(self.p_jammer_dbm_var.get()) if hasattr(self, "p_jammer_dbm_var") else self.params["p_jammer_dbm"]
            d_signal = float(self.d_signal_var.get()) if hasattr(self, "d_signal_var") else self.params["d_signal_m"]
            d_jammer = float(self.d_jammer_var.get()) if hasattr(self, "d_jammer_var") else self.params["d_jammer_m"]
            frequency = float(self.frequency_var.get()) if hasattr(self, "frequency_var") else self.params["frequency_hz"]
            bandwidth = float(self.bandwidth_if_var.get()) if hasattr(self, "bandwidth_if_var") else self.params["bandwidth_hz"]
            path_loss_exp = float(self.path_loss_exp_var.get()) if hasattr(self, "path_loss_exp_var") else self.params["path_loss_exp"]
        except (ValueError, tk.TclError):
            return None

        return {
            "p_signal": p_signal,
            "p_jammer": p_jammer,
            "d_signal": d_signal,
            "d_jammer": d_jammer,
            "frequency": frequency,
            "bandwidth": bandwidth,
            "path_loss_exp": path_loss_exp,
        }

    def _run_interference_sweep(self):
        """Genera gráfica de SIR/SINR vs variable seleccionada."""
        try:
            vmin = float(self.sweep_min_var.get())
            vmax = float(self.sweep_max_var.get())
            steps = int(self.sweep_steps_var.get())
        except ValueError:
            messagebox.showerror("Error", "Valores de barrido inválidos")
            return

        if steps < 2:
            messagebox.showerror("Error", "Pasos debe ser >= 2")
            return
        if vmin >= vmax:
            messagebox.showerror("Error", "Mínimo debe ser menor que máximo")
            return
        if vmin <= 0 and self.sweep_var.get() in ("d_jammer", "d_signal"):
            messagebox.showerror("Error", "Las distancias deben ser > 0")
            return

        base = self._get_theoretical_params()
        if base is None:
            messagebox.showerror("Error", "Parametros teoricos invalidos")
            return
        x = np.linspace(vmin, vmax, steps)
        sir_vals = []
        sinr_vals = []
        jsr_vals = []

        for value in x:
            params = dict(base)
            if self.sweep_var.get() == "d_jammer":
                params["d_jammer"] = value
            elif self.sweep_var.get() == "d_signal":
                params["d_signal"] = value
            else:
                params["p_jammer"] = value

            impact = calculate_jammer_impact(
                p_signal=params["p_signal"],
                p_jammer=params["p_jammer"],
                d_signal=params["d_signal"],
                d_jammer=params["d_jammer"],
                frequency=params["frequency"],
                bandwidth=params["bandwidth"],
                path_loss_exponent=params["path_loss_exp"],
            )
            sir_vals.append(impact["sir_db"])
            sinr_vals.append(impact["sinr_db"])
            jsr_vals.append(impact["jsr_db"])

        self.ax_sweep.clear()
        self.ax_sweep.plot(x, sir_vals, label="SIR (dB)")
        self.ax_sweep.plot(x, sinr_vals, label="SINR (dB)")
        self.ax_sweep.plot(x, jsr_vals, label="JSR (dB)", linestyle="--")

        units = "m" if self.sweep_var.get() in ("d_jammer", "d_signal") else "dBm"
        self.ax_sweep.set_xlabel(f"{self.sweep_var.get()} ({units})")
        self.ax_sweep.set_ylabel("dB")
        self.ax_sweep.set_title("SIR / SINR / JSR vs variable")
        self.ax_sweep.grid(True, alpha=0.3)
        self.ax_sweep.legend(loc="best")

        self.fig_sweep.tight_layout()
        self.canvas_sweep.draw()

        self.sweep_status_var.set(
            f"Barrido {self.sweep_var.get()} [{vmin:.2f}, {vmax:.2f}] ({steps} pasos)"
        )

    def _update_theory_content(self):
        """Actualiza el contenido del área de texto con el tema seleccionado."""
        topic = self.theory_topic_var.get()
        content = get_theory_text(topic)
        self.theory_text.config(state=tk.NORMAL)
        self.theory_text.delete(1.0, tk.END)
        self.theory_text.insert(tk.END, content)
        self.theory_text.config(state=tk.DISABLED)

    def _build_quality_panel(self, parent):
        """Construye el panel de indicadores de calidad de comunicación."""
        quality_frame = ttk.LabelFrame(parent, text="📊 Estado de Comunicación", style="Label.TLabel")
        quality_frame.pack(fill=tk.X, pady=(10, 0))

        # Indicador principal
        self.quality_indicator_label = ttk.Label(quality_frame, text="●  ---",
                                                  font=("Segoe UI", 12, "bold"),
                                                  style="Label.TLabel")
        self.quality_indicator_label.pack(anchor=tk.W, padx=10, pady=5)

        # Barra de calidad
        self.quality_bar_var = tk.StringVar(value="░░░░░░░░░░  0/100")
        ttk.Label(quality_frame, textvariable=self.quality_bar_var,
                 font=("Consolas", 10), style="Label.TLabel").pack(anchor=tk.W, padx=10)

        # Métricas individuales
        metrics_frame = ttk.Frame(quality_frame, style="Tab.TFrame")
        metrics_frame.pack(fill=tk.X, padx=10, pady=5)

        self.metric_ber_var = tk.StringVar(value="BER: ---")
        self.metric_snr_var = tk.StringVar(value="SNR: ---")
        self.metric_per_var = tk.StringVar(value="PER: ---")

        ttk.Label(metrics_frame, textvariable=self.metric_ber_var,
                 style="Output.TLabel").pack(anchor=tk.W)
        ttk.Label(metrics_frame, textvariable=self.metric_snr_var,
                 style="Output.TLabel").pack(anchor=tk.W)
        ttk.Label(metrics_frame, textvariable=self.metric_per_var,
                 style="Output.TLabel").pack(anchor=tk.W)

        # Recomendaciones
        self.recommendations_var = tk.StringVar(value="")
        ttk.Label(quality_frame, textvariable=self.recommendations_var,
                 wraplength=200, style="Output.TLabel").pack(anchor=tk.W, padx=10, pady=5)

    def _build_interference_panel(self, parent):
        """Construye el panel de indicadores de interferencia."""
        interference_frame = ttk.LabelFrame(parent, text="📡 Estado de Interferencia", style="Label.TLabel")
        interference_frame.pack(fill=tk.X, pady=(10, 0))

        self.interference_indicator_label = ttk.Label(interference_frame, text="●  ---",
                                                      font=("Segoe UI", 11, "bold"),
                                                      style="Label.TLabel")
        self.interference_indicator_label.pack(anchor=tk.W, padx=10, pady=5)

        self.interference_score_var = tk.StringVar(value="░░░░░░░░░░  0/100")
        ttk.Label(interference_frame, textvariable=self.interference_score_var,
                 font=("Consolas", 10), style="Label.TLabel").pack(anchor=tk.W, padx=10)

        metrics_frame = ttk.Frame(interference_frame, style="Tab.TFrame")
        metrics_frame.pack(fill=tk.X, padx=10, pady=5)

        self.metric_sir_var = tk.StringVar(value="SIR: ---")
        self.metric_sinr_var = tk.StringVar(value="SINR: ---")
        self.metric_jsr_var = tk.StringVar(value="JSR: ---")
        self.metric_interf_source_var = tk.StringVar(value="Fuente: ---")

        ttk.Label(metrics_frame, textvariable=self.metric_sir_var,
                 style="Output.TLabel").pack(anchor=tk.W)
        ttk.Label(metrics_frame, textvariable=self.metric_sinr_var,
                 style="Output.TLabel").pack(anchor=tk.W)
        ttk.Label(metrics_frame, textvariable=self.metric_jsr_var,
                 style="Output.TLabel").pack(anchor=tk.W)
        ttk.Label(metrics_frame, textvariable=self.metric_interf_source_var,
                 style="Output.TLabel").pack(anchor=tk.W)

        self.interference_detail_var = tk.StringVar(value="")
        ttk.Label(interference_frame, textvariable=self.interference_detail_var,
                 wraplength=200, style="Output.TLabel").pack(anchor=tk.W, padx=10, pady=5)

    def _update_quality_indicators(self, ber_val, snr_val, per_val=None):
        """Actualiza los indicadores de calidad basándose en las métricas."""
        # Obtener evaluación completa
        quality = overall_quality(ber_val, snr_val, per_val)

        # Actualizar indicador principal
        emoji_map = {'excellent': '🟢', 'good': '🟡', 'fair': '🟠', 'poor': '🔴', 'critical': '⛔'}
        emoji = emoji_map.get(quality['category'], '⚪')
        self.quality_indicator_label.config(
            text=f"{emoji}  {quality['description'].upper()}"
        )

        # Actualizar barra de calidad
        bar = get_quality_indicator(quality['score'])
        self.quality_bar_var.set(f"{bar}  {quality['score']}/100")

        # Actualizar métricas individuales
        ber_cat, ber_desc, _ = classify_ber(ber_val)
        snr_cat, snr_desc, _ = classify_snr(snr_val)

        self.metric_ber_var.set(f"BER: {ber_val:.2e}  →  {ber_desc}")
        self.metric_snr_var.set(f"SNR: {snr_val:.1f} dB  →  {snr_desc}")
        if per_val is not None:
            self.metric_per_var.set(f"PER: {per_val:.2%}  →  {'Aceptable' if per_val < 0.05 else 'Alto'}")
        else:
            self.metric_per_var.set("PER: ---")

        # Actualizar recomendaciones
        recs = quality.get('recommendations', [])
        self.recommendations_var.set("\n".join(recs[:2]))  # Mostrar máx 2

    def _update_interference_indicators(self, sir_db, sinr_db, jsr_db, score, severity, description, source_label):
        """Actualiza indicadores de interferencia y severidad."""
        severity_map = {
            'none': ('🟢', 'SIN INTERFERENCIA'),
            'low': ('🟡', 'INTERFERENCIA BAJA'),
            'moderate': ('🟠', 'INTERFERENCIA MODERADA'),
            'high': ('🔴', 'INTERFERENCIA ALTA'),
            'critical': ('⛔', 'INTERFERENCIA CRÍTICA'),
        }
        emoji, title = severity_map.get(severity, ('⚪', 'INTERFERENCIA'))
        self.interference_indicator_label.config(text=f"{emoji}  {title}")

        bar = get_quality_indicator(score)
        self.interference_score_var.set(f"{bar}  {score}/100")

        self.metric_sir_var.set(f"SIR: {sir_db:.1f} dB")
        self.metric_sinr_var.set(f"SINR: {sinr_db:.1f} dB")
        self.metric_jsr_var.set(f"JSR: {jsr_db:.1f} dB")
        self.metric_interf_source_var.set(f"Fuente: {source_label}")
        self.interference_detail_var.set(description)

    def _calculate_interference_theoretical(self):
        """Calcula interferencia teórica a partir de entradas del usuario."""
        try:
            p_signal = float(self.p_signal_dbm_var.get())
            p_jammer = float(self.p_jammer_dbm_var.get())
            d_signal = float(self.d_signal_var.get())
            d_jammer = float(self.d_jammer_var.get())
            frequency = float(self.frequency_var.get())
            bandwidth = float(self.bandwidth_if_var.get())
            path_loss_exp = float(self.path_loss_exp_var.get())
        except ValueError:
            messagebox.showerror("Error", "Parámetros de interferencia inválidos")
            return

        if d_signal <= 0 or d_jammer <= 0 or frequency <= 0 or bandwidth <= 0:
            messagebox.showerror("Error", "Distancias, frecuencia y ancho de banda deben ser positivos")
            return
        if path_loss_exp < 1.0 or path_loss_exp > 6.0:
            messagebox.showerror("Error", "Exponente de pérdida debe estar entre 1.0 y 6.0")
            return
        if frequency < 1e3 or frequency > 300e9:
            messagebox.showerror("Error", "Frecuencia fuera de rango (1 kHz a 300 GHz)")
            return
        if bandwidth < 1.0 or bandwidth > 1e9:
            messagebox.showerror("Error", "Ancho de banda fuera de rango (1 Hz a 1 GHz)")
            return

        impact = calculate_jammer_impact(
            p_signal=p_signal,
            p_jammer=p_jammer,
            d_signal=d_signal,
            d_jammer=d_jammer,
            frequency=frequency,
            bandwidth=bandwidth,
            path_loss_exponent=path_loss_exp,
        )

        self.params.update({
            "p_signal_dbm": p_signal,
            "p_jammer_dbm": p_jammer,
            "d_signal_m": d_signal,
            "d_jammer_m": d_jammer,
            "frequency_hz": frequency,
            "bandwidth_hz": bandwidth,
            "path_loss_exp": path_loss_exp,
        })

        self._update_interference_indicators(
            impact["sir_db"],
            impact["sinr_db"],
            impact["jsr_db"],
            impact["severity_score"],
            impact["severity_level"],
            impact["severity_description"],
            "Teórico",
        )

        self.output_var.set(
            f"SIR={impact['sir_db']:.1f} dB | SINR={impact['sinr_db']:.1f} dB | JSR={impact['jsr_db']:.1f} dB"
        )


def main():
    app = SimuliMathApp()
    app.mainloop()

if __name__ == "__main__":
    main()
