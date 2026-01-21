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
from sim.metrics import empirical_snr, packet_error_rate

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
        """Valida entradas en tiempo real."""
        def validate(*args):
            value = var.get()
            if validation_type == "int" and not value.isdigit():
                var.set("0")
            elif validation_type == "float":
                try:
                    float(value)
                except ValueError:
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

        # --- Exportar resultados ---
        self._add_export_options(parent)

        ttk.Label(parent, text="Salida", style="Label.TLabel").pack(anchor=tk.W, pady=(12,0))
        self.output_var = tk.StringVar(value="Listo")
        ttk.Label(parent, textvariable=self.output_var, wraplength=200, style="Output.TLabel").pack(anchor=tk.W)

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
            self.freqs_var = tk.StringVar(value="1000,2000,3000")
            ttk.Entry(self.jammer_frame, textvariable=self.freqs_var, width=30).pack(anchor=tk.W)

    def _update_jammer_controls(self):
        # Reconstruye los controles específicos del jammer en el frame correspondiente
        self._build_jammer_controls()

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

        bits = generate_bits(n_bits, seed=seed)
        symbols = bpsk_mod(bits)
        jam = self._build_jammer(len(symbols))
        tx = symbols + jam
        rx = add_awgn(tx, snr_db=snr_db, seed=seed)
        bits_rx = bpsk_demod(rx)
        ber_val = ber(bits, bits_rx)
        snr_emp = empirical_snr(symbols, rx - symbols)
        per_val = packet_error_rate(bits, bits_rx, packet_size=max(1, n_bits//10))

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
            "n_bits": n_bits,
            "snr_db": snr_db,
            "jammer": self.jam_var.get(),
        }
        self.output_var.set(f"BER={ber_val:.4e} | PER={per_val:.4f} | SNR_emp={snr_emp:.2f} dB")

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
        header = ["n_bits", "snr_db", "jammer", "BER", "PER", "SNR_emp_dB"]
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

def main():
    app = SimuliMathApp()
    app.mainloop()

if __name__ == "__main__":
    main()
