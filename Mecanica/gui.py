"""
gui.py — Interfaz Gráfica Principal
=====================================
Define la ventana principal y todos los paneles de la aplicación:

  - Panel de Control Izquierdo : Formularios para agregar cargas y puntos de prueba.
  - Canvas Central             : Visualización interactiva (delegada a canvas.py).
  - Panel de Resultados Derecho: Tablas numéricas de fuerzas y campos.
  - Barra Superior             : Selector de dimensión (1D / 2D) con persistencia de estado.

Estilo visual: dark-mode científico con fuentes monoespaciadas para los resultados.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from model import EstadoSimulador, SistemaElectrostatico, Vector
from canvas import CanvasElectrostatico, COLORES

# ─────────────────────────────────────────────
#  ESTILOS GLOBALES
# ─────────────────────────────────────────────
PALETA = {
    "bg_ventana":    "#0d1117",
    "bg_panel":      "#161b27",
    "bg_widget":     "#1c2233",
    "bg_entrada":    "#0f1722",
    "borde":         "#2a3050",
    "acento":        "#4a7cdc",
    "acento2":       "#50e896",
    "acento_neg":    "#e05c5c",
    "texto":         "#d0d4e8",
    "texto_dim":     "#6b7194",
    "texto_titulo":  "#e8ebf5",
    "carga_pos":     "#e05c5c",
    "carga_neg":     "#5c9ee0",
    "campo":         "#c97af5",
    "separador":     "#22273a",
    "boton_hover":   "#354870",
    "exito":         "#50e896",
    "alerta":        "#f0c040",
    "error":         "#e05c5c",
}

FUENTE_MONO = ("Courier New", 9)
FUENTE_LABEL = ("Segoe UI", 9)
FUENTE_TITULO = ("Segoe UI", 10, "bold")
FUENTE_SECCION = ("Segoe UI", 8, "bold")


# ─────────────────────────────────────────────
#  HELPERS DE WIDGETS
# ─────────────────────────────────────────────

def _entry(parent, textvariable=None, width=14, **kwargs) -> tk.Entry:
    """Entry con estilo dark-mode."""
    return tk.Entry(
        parent,
        textvariable=textvariable,
        width=width,
        bg=PALETA["bg_entrada"],
        fg=PALETA["texto"],
        insertbackground=PALETA["texto"],
        relief=tk.FLAT,
        bd=0,
        highlightthickness=1,
        highlightcolor=PALETA["acento"],
        highlightbackground=PALETA["borde"],
        font=FUENTE_MONO,
        **kwargs
    )


def _label(parent, text, color=None, font=None, **kwargs) -> tk.Label:
    return tk.Label(
        parent, text=text,
        bg=PALETA["bg_panel"],
        fg=color or PALETA["texto"],
        font=font or FUENTE_LABEL,
        **kwargs
    )


def _boton(parent, text, command, color=None, hover=None,
           width=None, **kwargs) -> tk.Button:
    color = color or PALETA["acento"]
    hover = hover or PALETA["boton_hover"]
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg="#ffffff", activeforeground="#ffffff",
        activebackground=hover,
        relief=tk.FLAT, bd=0,
        padx=10, pady=5,
        cursor="hand2",
        font=FUENTE_SECCION,
        width=width or 0,
        **kwargs
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def _separador(parent) -> tk.Frame:
    return tk.Frame(parent, height=1, bg=PALETA["separador"])


def _seccion(parent, titulo: str) -> tk.LabelFrame:
    return tk.LabelFrame(
        parent, text=f"  {titulo}  ",
        bg=PALETA["bg_panel"], fg=PALETA["texto_dim"],
        font=FUENTE_SECCION,
        relief=tk.FLAT, bd=0,
        highlightthickness=1,
        highlightbackground=PALETA["borde"],
        padx=8, pady=6
    )


# ─────────────────────────────────────────────
#  PANEL DE CONTROL IZQUIERDO
# ─────────────────────────────────────────────

class PanelControl(tk.Frame):
    """
    Panel lateral izquierdo con formularios para:
      - Agregar / eliminar cargas.
      - Agregar / eliminar puntos de prueba.
      - Seleccionar la carga objetivo para calcular fuerzas.
    """

    def __init__(self, parent, controlador, **kwargs):
        super().__init__(parent, bg=PALETA["bg_panel"], **kwargs)
        self.ctrl = controlador  # referencia a VentanaPrincipal
        self._construir()

    def _construir(self):
        # ─ Título panel ──────────────────────
        tk.Label(self, text="PANEL DE CONTROL",
                 bg=PALETA["bg_panel"], fg=PALETA["acento"],
                 font=("Segoe UI", 10, "bold")).pack(fill=tk.X, pady=(10, 2))
        _separador(self).pack(fill=tk.X, padx=8, pady=4)

        # ─ Sección: agregar carga ─────────────
        sec_carga = _seccion(self, "⚡ Nueva carga")
        sec_carga.pack(fill=tk.X, padx=8, pady=4)

        _label(sec_carga, "Etiqueta:").grid(row=0, column=0, sticky="w", pady=2)
        self.var_etiqueta_c = tk.StringVar()
        _entry(sec_carga, self.var_etiqueta_c, width=13).grid(row=0, column=1, pady=2)

        _label(sec_carga, "Magnitud q [C]:").grid(row=1, column=0, sticky="w", pady=2)
        self.var_magnitud = tk.StringVar()
        _entry(sec_carga, self.var_magnitud, width=13).grid(row=1, column=1, pady=2)

        _label(sec_carga, "Posición x [m]:").grid(row=2, column=0, sticky="w", pady=2)
        self.var_x_c = tk.StringVar()
        _entry(sec_carga, self.var_x_c, width=13).grid(row=2, column=1, pady=2)

        _label(sec_carga, "Posición y [m]:").grid(row=3, column=0, sticky="w", pady=2)
        self.var_y_c = tk.StringVar()
        self.entry_y_c = _entry(sec_carga, self.var_y_c, width=13)
        self.entry_y_c.grid(row=3, column=1, pady=2)

        _boton(sec_carga, "Agregar carga", self.ctrl.agregar_carga,
               color=PALETA["acento"]).grid(row=4, column=0, columnspan=2,
                                            sticky="ew", pady=(6, 0))

        # ─ Sección: lista de cargas ─────────────
        sec_lista = _seccion(self, "📋 Cargas en el sistema")
        sec_lista.pack(fill=tk.X, padx=8, pady=4)

        frame_lista = tk.Frame(sec_lista, bg=PALETA["bg_panel"])
        frame_lista.pack(fill=tk.X)

        scroll_lista = tk.Scrollbar(frame_lista, orient=tk.VERTICAL)
        self.lista_cargas = tk.Listbox(
            frame_lista,
            bg=PALETA["bg_entrada"], fg=PALETA["texto"],
            selectbackground=PALETA["acento"],
            selectforeground="#ffffff",
            relief=tk.FLAT, bd=0,
            font=FUENTE_MONO, height=5,
            activestyle="none",
            yscrollcommand=scroll_lista.set,
            exportselection=False
        )
        scroll_lista.config(command=self.lista_cargas.yview)
        self.lista_cargas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scroll_lista.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_cargas.bind("<<ListboxSelect>>", self.ctrl.al_seleccionar_carga)

        frame_btns_c = tk.Frame(sec_lista, bg=PALETA["bg_panel"])
        frame_btns_c.pack(fill=tk.X, pady=(4, 0))
        _boton(frame_btns_c, "Calcular fuerzas",
               self.ctrl.calcular_fuerzas,
               color="#2d5a27").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        _boton(frame_btns_c, "Eliminar",
               self.ctrl.eliminar_carga,
               color=PALETA["acento_neg"]).pack(side=tk.RIGHT, expand=True, fill=tk.X)

        # ─ Sección: puntos de prueba ──────────────
        sec_punto = _seccion(self, "◈ Nuevo punto de prueba")
        sec_punto.pack(fill=tk.X, padx=8, pady=4)

        _label(sec_punto, "Etiqueta:").grid(row=0, column=0, sticky="w", pady=2)
        self.var_etiqueta_p = tk.StringVar()
        _entry(sec_punto, self.var_etiqueta_p, width=13).grid(row=0, column=1, pady=2)

        _label(sec_punto, "Posición x [m]:").grid(row=1, column=0, sticky="w", pady=2)
        self.var_x_p = tk.StringVar()
        _entry(sec_punto, self.var_x_p, width=13).grid(row=1, column=1, pady=2)

        _label(sec_punto, "Posición y [m]:").grid(row=2, column=0, sticky="w", pady=2)
        self.var_y_p = tk.StringVar()
        self.entry_y_p = _entry(sec_punto, self.var_y_p, width=13)
        self.entry_y_p.grid(row=2, column=1, pady=2)

        _boton(sec_punto, "Agregar punto", self.ctrl.agregar_punto_prueba,
               color="#4a3578").grid(row=3, column=0, columnspan=2,
                                     sticky="ew", pady=(6, 0))

        # ─ Sección: lista puntos de prueba ──────────
        sec_lpunto = _seccion(self, "◈ Puntos de prueba")
        sec_lpunto.pack(fill=tk.X, padx=8, pady=4)

        frame_lp = tk.Frame(sec_lpunto, bg=PALETA["bg_panel"])
        frame_lp.pack(fill=tk.X)
        scroll_lp = tk.Scrollbar(frame_lp, orient=tk.VERTICAL)
        self.lista_puntos = tk.Listbox(
            frame_lp,
            bg=PALETA["bg_entrada"], fg=COLORES["punto_prueba"],
            selectbackground=PALETA["acento"],
            relief=tk.FLAT, bd=0,
            font=FUENTE_MONO, height=3,
            activestyle="none",
            yscrollcommand=scroll_lp.set,
            exportselection=False
        )
        scroll_lp.config(command=self.lista_puntos.yview)
        self.lista_puntos.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scroll_lp.pack(side=tk.RIGHT, fill=tk.Y)

        frame_btns_p = tk.Frame(sec_lpunto, bg=PALETA["bg_panel"])
        frame_btns_p.pack(fill=tk.X, pady=(4, 0))
        _boton(frame_btns_p, "Calcular campos",
               self.ctrl.calcular_campos,
               color="#4a3578").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        _boton(frame_btns_p, "Eliminar",
               self.ctrl.eliminar_punto_prueba,
               color=PALETA["acento_neg"]).pack(side=tk.RIGHT, expand=True, fill=tk.X)

        # ─ Botón limpiar todo ────────────────────
        _separador(self).pack(fill=tk.X, padx=8, pady=6)
        _boton(self, "🗑  Limpiar sistema",
               self.ctrl.limpiar_sistema,
               color="#3a1e1e",
               hover="#5a2a2a").pack(fill=tk.X, padx=8, pady=(0, 10))

    def actualizar_lista_cargas(self, cargas):
        """Refresca el Listbox con la lista actual de cargas."""
        self.lista_cargas.delete(0, tk.END)
        for c in cargas:
            signo = "+" if c.es_positiva else "−"
            texto = f"[{c.id_carga}] {c.etiqueta}  {signo}{abs(c.magnitud):.2e} C"
            self.lista_cargas.insert(tk.END, texto)

    def actualizar_lista_puntos(self, puntos):
        """Refresca el Listbox con la lista actual de puntos de prueba."""
        self.lista_puntos.delete(0, tk.END)
        for p in puntos:
            pos = " | ".join(f"{v:.3g}" for v in p.posicion)
            texto = f"[{p.id_punto}] {p.etiqueta}  ({pos}) m"
            self.lista_puntos.insert(tk.END, texto)

    def set_modo_dimension(self, dimension: int):
        """Habilita/deshabilita el campo Y según la dimensión activa."""
        estado = tk.NORMAL if dimension == 2 else tk.DISABLED
        color_fg = PALETA["texto"] if dimension == 2 else PALETA["texto_dim"]
        self.entry_y_c.config(state=estado, fg=color_fg)
        self.entry_y_p.config(state=estado, fg=color_fg)
        if dimension == 1:
            self.var_y_c.set("0")
            self.var_y_p.set("0")

    def get_id_carga_seleccionada(self) -> int | None:
        """Devuelve el ID de la carga seleccionada en el Listbox."""
        seleccion = self.lista_cargas.curselection()
        if not seleccion:
            return None
        texto = self.lista_cargas.get(seleccion[0])
        # Formato: "[id] etiqueta ..."
        try:
            return int(texto.split("]")[0].replace("[", "").strip())
        except ValueError:
            return None

    def get_id_punto_seleccionado(self) -> int | None:
        """Devuelve el ID del punto de prueba seleccionado."""
        seleccion = self.lista_puntos.curselection()
        if not seleccion:
            return None
        texto = self.lista_puntos.get(seleccion[0])
        try:
            return int(texto.split("]")[0].replace("[", "").strip())
        except ValueError:
            return None


# ─────────────────────────────────────────────
#  PANEL DE RESULTADOS DERECHO
# ─────────────────────────────────────────────

class PanelResultados(tk.Frame):
    """
    Panel lateral derecho que muestra tablas numéricas de resultados.
    Incluye:
      - Tabla de fuerzas individuales (Fx, Fy, |F|, ángulo).
      - Resumen de fuerza neta.
      - Tabla de campos eléctricos (Ex, Ey, |E|, ángulo).
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=PALETA["bg_panel"], **kwargs)
        self._construir()

    def _construir(self):
        tk.Label(self, text="RESULTADOS NUMÉRICOS",
                 bg=PALETA["bg_panel"], fg=PALETA["acento2"],
                 font=("Segoe UI", 10, "bold")).pack(fill=tk.X, pady=(10, 2))
        _separador(self).pack(fill=tk.X, padx=8, pady=4)

        # ─ Fuerzas individuales ──────────────────
        sec_f = _seccion(self, "⚡ Fuerzas individuales sobre carga objetivo  [N]")
        sec_f.pack(fill=tk.X, padx=8, pady=4)

        self.tabla_fuerzas = self._crear_tabla(
            sec_f,
            columnas=("Fuente", "Fx [N]", "Fy [N]", "|F| [N]", "θ [°]"),
            alto=5
        )

        # ─ Fuerza neta ───────────────────────────
        sec_fn = _seccion(self, "∑F  —  Fuerza Neta  [N]")
        sec_fn.pack(fill=tk.X, padx=8, pady=4)

        self.texto_neta = tk.Text(
            sec_fn, height=4, width=36,
            bg=PALETA["bg_entrada"], fg=PALETA["exito"],
            font=FUENTE_MONO, relief=tk.FLAT, bd=0,
            state=tk.DISABLED,
            wrap=tk.WORD,
            padx=6, pady=4
        )
        self.texto_neta.pack(fill=tk.X)

        # ─ Campos eléctricos ─────────────────────
        sec_e = _seccion(self, "E  —  Campo Eléctrico en puntos de prueba  [N/C]")
        sec_e.pack(fill=tk.X, padx=8, pady=4)

        self.tabla_campos = self._crear_tabla(
            sec_e,
            columnas=("Punto", "Ex [N/C]", "Ey [N/C]", "|E| [N/C]", "θ [°]"),
            alto=5
        )

        # ─ Información física ─────────────────────
        sec_info = _seccion(self, "ℹ  Constantes físicas")
        sec_info.pack(fill=tk.X, padx=8, pady=(4, 10))

        info_txt = (
            "k = 8.99 × 10⁹  N·m²/C²\n"
            "Ley de Coulomb:  F = k·q₁·q₂/r²\n"
            "Campo eléctrico: E = k·q/r²"
        )
        tk.Label(
            sec_info, text=info_txt,
            bg=PALETA["bg_panel"], fg=PALETA["texto_dim"],
            font=("Courier New", 8), justify=tk.LEFT
        ).pack(anchor="w")

    def _crear_tabla(self, parent, columnas: tuple, alto: int) -> ttk.Treeview:
        """Crea un Treeview estilizado como tabla científica."""
        estilo = ttk.Style()
        estilo.theme_use("default")
        nombre_estilo = f"Tabla{id(parent)}.Treeview"
        estilo.configure(
            nombre_estilo,
            background=PALETA["bg_entrada"],
            foreground=PALETA["texto"],
            fieldbackground=PALETA["bg_entrada"],
            rowheight=22,
            font=FUENTE_MONO,
        )
        estilo.configure(
            f"{nombre_estilo}.Heading",
            background=PALETA["bg_widget"],
            foreground=PALETA["texto_dim"],
            font=FUENTE_SECCION,
            relief="flat",
        )
        estilo.map(nombre_estilo,
                   background=[("selected", PALETA["acento"])],
                   foreground=[("selected", "#ffffff")])

        frame = tk.Frame(parent, bg=PALETA["bg_panel"])
        frame.pack(fill=tk.X)

        scroll = tk.Scrollbar(frame, orient=tk.VERTICAL)
        tabla = ttk.Treeview(
            frame,
            columns=columnas,
            show="headings",
            height=alto,
            style=nombre_estilo,
            yscrollcommand=scroll.set,
            selectmode="browse"
        )
        scroll.config(command=tabla.yview)

        for col in columnas:
            tabla.heading(col, text=col, anchor="center")
            tabla.column(col, width=90, anchor="center", stretch=True)

        tabla.column(columnas[0], width=70, anchor="center")

        tabla.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        return tabla

    # ── API de actualización ──────────────────

    def mostrar_fuerzas(self, fuerzas, fuerza_neta: Vector | None,
                        cargas_dict: dict):
        """
        Puebla la tabla de fuerzas y el cuadro de fuerza neta.
        cargas_dict: {id_carga: Carga}
        """
        # Limpiar tabla
        for row in self.tabla_fuerzas.get_children():
            self.tabla_fuerzas.delete(row)

        for resultado in fuerzas:
            fuente = cargas_dict.get(resultado.carga_fuente_id)
            nombre = fuente.etiqueta if fuente else f"q{resultado.carga_fuente_id}"
            v = resultado.vector_fuerza
            ang = v.angulo_grados

            self.tabla_fuerzas.insert("", tk.END, values=(
                nombre,
                f"{v.x:.4e}",
                f"{v.y:.4e}",
                f"{v.magnitud:.4e}",
                f"{ang:.2f}°"
            ))

        # Fuerza neta
        self.texto_neta.config(state=tk.NORMAL)
        self.texto_neta.delete("1.0", tk.END)
        if fuerza_neta:
            txt = (
                f"Fx = {fuerza_neta.x:.4e} N\n"
                f"Fy = {fuerza_neta.y:.4e} N\n"
                f"|F| = {fuerza_neta.magnitud:.4e} N\n"
                f"θ = {fuerza_neta.angulo_grados:.2f}°"
            )
        else:
            txt = "—  Sin datos  —"
        self.texto_neta.insert("1.0", txt)
        self.texto_neta.config(state=tk.DISABLED)

    def mostrar_campos(self, campos, puntos_dict: dict):
        """Puebla la tabla del campo eléctrico."""
        for row in self.tabla_campos.get_children():
            self.tabla_campos.delete(row)

        for resultado in campos:
            punto = puntos_dict.get(resultado.punto_id)
            nombre = punto.etiqueta if punto else f"P{resultado.punto_id}"
            v = resultado.vector_campo
            ang = v.angulo_grados

            self.tabla_campos.insert("", tk.END, values=(
                nombre,
                f"{v.x:.4e}",
                f"{v.y:.4e}",
                f"{v.magnitud:.4e}",
                f"{ang:.2f}°"
            ))

    def limpiar(self):
        """Limpia todas las tablas y cuadros de resultado."""
        for row in self.tabla_fuerzas.get_children():
            self.tabla_fuerzas.delete(row)
        for row in self.tabla_campos.get_children():
            self.tabla_campos.delete(row)
        self.texto_neta.config(state=tk.NORMAL)
        self.texto_neta.delete("1.0", tk.END)
        self.texto_neta.config(state=tk.DISABLED)


# ─────────────────────────────────────────────
#  BARRA SUPERIOR (selector de dimensión)
# ─────────────────────────────────────────────

class BarraSuperior(tk.Frame):
    """
    Barra de encabezado con el título de la aplicación y
    el selector de dimensión 1D / 2D.
    """

    def __init__(self, parent, controlador, **kwargs):
        super().__init__(parent, bg="#0a0d14", height=52, **kwargs)
        self.pack_propagate(False)
        self.ctrl = controlador
        self._construir()

    def _construir(self):
        # Título
        tk.Label(
            self,
            text="⚛  SIMULADOR DE ELECTROSTÁTICA",
            bg="#0a0d14", fg=PALETA["texto_titulo"],
            font=("Segoe UI", 13, "bold"),
            padx=16
        ).pack(side=tk.LEFT, pady=10)

        tk.Label(
            self,
            text="Ley de Coulomb  ·  Principio de Superposición",
            bg="#0a0d14", fg=PALETA["texto_dim"],
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT, pady=10)

        # Selector de dimensión (derecha)
        frame_dim = tk.Frame(self, bg="#0a0d14")
        frame_dim.pack(side=tk.RIGHT, padx=16)

        tk.Label(frame_dim, text="Dimensión:",
                 bg="#0a0d14", fg=PALETA["texto_dim"],
                 font=FUENTE_SECCION).pack(side=tk.LEFT, padx=(0, 6))

        self.var_dim = tk.IntVar(value=2)

        self.btn_1d = tk.Button(
            frame_dim, text="1D",
            command=lambda: self.ctrl.cambiar_dimension(1),
            bg=PALETA["bg_widget"], fg=PALETA["texto_dim"],
            activebackground=PALETA["acento"],
            relief=tk.FLAT, bd=0,
            padx=12, pady=4,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2"
        )
        self.btn_1d.pack(side=tk.LEFT)

        self.btn_2d = tk.Button(
            frame_dim, text="2D",
            command=lambda: self.ctrl.cambiar_dimension(2),
            bg=PALETA["acento"], fg="#ffffff",
            activebackground=PALETA["boton_hover"],
            relief=tk.FLAT, bd=0,
            padx=12, pady=4,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2"
        )
        self.btn_2d.pack(side=tk.LEFT, padx=(2, 0))

    def actualizar_botones_dim(self, dimension: int):
        """Resalta el botón de la dimensión activa."""
        if dimension == 1:
            self.btn_1d.config(bg=PALETA["acento"], fg="#ffffff")
            self.btn_2d.config(bg=PALETA["bg_widget"], fg=PALETA["texto_dim"])
        else:
            self.btn_2d.config(bg=PALETA["acento"], fg="#ffffff")
            self.btn_1d.config(bg=PALETA["bg_widget"], fg=PALETA["texto_dim"])


# ─────────────────────────────────────────────
#  BARRA DE ESTADO INFERIOR
# ─────────────────────────────────────────────

class BarraEstado(tk.Frame):
    """Barra de mensajes de estado en la parte inferior de la ventana."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#080b12", height=26, **kwargs)
        self.pack_propagate(False)
        self._var_msg = tk.StringVar(value="Listo.")
        self._var_color = tk.StringVar()
        self._lbl = tk.Label(
            self, textvariable=self._var_msg,
            bg="#080b12", fg=PALETA["texto_dim"],
            font=("Segoe UI", 8), anchor="w", padx=12
        )
        self._lbl.pack(fill=tk.BOTH, expand=True)

    def info(self, msg: str):
        self._lbl.config(fg=PALETA["texto_dim"])
        self._var_msg.set(f"ℹ  {msg}")

    def exito(self, msg: str):
        self._lbl.config(fg=PALETA["exito"])
        self._var_msg.set(f"✓  {msg}")

    def error(self, msg: str):
        self._lbl.config(fg=PALETA["error"])
        self._var_msg.set(f"✗  {msg}")

    def alerta(self, msg: str):
        self._lbl.config(fg=PALETA["alerta"])
        self._var_msg.set(f"⚠  {msg}")


# ─────────────────────────────────────────────
#  VENTANA PRINCIPAL (Controlador)
# ─────────────────────────────────────────────

class VentanaPrincipal(tk.Tk):
    """
    Orquestador principal de la aplicación.

    Inicializa el estado del simulador, construye todos los widgets
    y gestiona los eventos de usuario:
      - Agregar/eliminar cargas y puntos de prueba.
      - Cambiar dimensión preservando el estado.
      - Calcular y visualizar fuerzas y campos.
    """

    def __init__(self):
        super().__init__()

        # Motor de física (mantiene estado por dimensión)
        self.estado = EstadoSimulador()

        self._configurar_ventana()
        self._construir_ui()
        self._sincronizar_ui()

    # ── Configuración de ventana ──────────────

    def _configurar_ventana(self):
        self.title("Simulador de Electrostática — Mecánica y Electromagnetismo")
        self.geometry("1260x720")
        self.minsize(1000, 620)
        self.configure(bg=PALETA["bg_ventana"])

        # Icono (si existe un .ico, puede cargarse aquí)
        # self.iconbitmap("icon.ico")

    # ── Construcción de la UI ─────────────────

    def _construir_ui(self):
        # Barra superior
        self.barra_sup = BarraSuperior(self, self)
        self.barra_sup.pack(fill=tk.X)

        _separador(self).pack(fill=tk.X)

        # Contenedor principal: 3 columnas
        frame_main = tk.Frame(self, bg=PALETA["bg_ventana"])
        frame_main.pack(fill=tk.BOTH, expand=True)

        # Panel izquierdo (control)
        self.panel_ctrl = PanelControl(frame_main, self)
        self.panel_ctrl.pack(side=tk.LEFT, fill=tk.Y,
                             padx=(0, 1), ipadx=2)

        # Divisor visual
        tk.Frame(frame_main, width=1, bg=PALETA["separador"]).pack(
            side=tk.LEFT, fill=tk.Y)

        # Canvas central
        frame_canvas = tk.Frame(frame_main, bg=PALETA["bg_ventana"])
        frame_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_vis = CanvasElectrostatico(
            frame_canvas, self.estado.sistema_activo
        )

        # Divisor visual
        tk.Frame(frame_main, width=1, bg=PALETA["separador"]).pack(
            side=tk.LEFT, fill=tk.Y)

        # Panel derecho (resultados)
        self.panel_res = PanelResultados(frame_main)
        self.panel_res.pack(side=tk.RIGHT, fill=tk.Y, padx=(1, 0))

        # Barra de estado
        _separador(self).pack(fill=tk.X)
        self.barra_estado = BarraEstado(self)
        self.barra_estado.pack(fill=tk.X)

    # ── Sincronización UI ─────────────────────

    def _sincronizar_ui(self):
        """Actualiza todos los elementos de la UI con el estado actual."""
        dim = self.estado.dimension_activa
        sistema = self.estado.sistema_activo

        self.barra_sup.actualizar_botones_dim(dim)
        self.panel_ctrl.set_modo_dimension(dim)
        self.panel_ctrl.actualizar_lista_cargas(sistema.cargas)
        self.panel_ctrl.actualizar_lista_puntos(sistema.puntos_prueba)
        self.canvas_vis.set_sistema(sistema)
        self.canvas_vis.set_resultados([], None, [])
        self.canvas_vis.actualizar()
        self.panel_res.limpiar()
        self.barra_estado.info(
            f"Modo {dim}D activo — "
            f"{len(sistema.cargas)} carga(s), "
            f"{len(sistema.puntos_prueba)} punto(s) de prueba."
        )

    # ── Acciones del usuario ──────────────────

    def cambiar_dimension(self, nueva_dim: int):
        """Cambia la dimensión activa sin perder el estado de ninguna."""
        if nueva_dim == self.estado.dimension_activa:
            return
        self.estado.cambiar_dimension(nueva_dim)
        self.panel_res.limpiar()
        self.canvas_vis.set_resultados([], None, [])
        self._sincronizar_ui()
        self.barra_estado.exito(f"Cambiado a modo {nueva_dim}D. Estado anterior conservado.")

    def agregar_carga(self):
        """Valida el formulario y agrega una nueva carga al sistema activo."""
        sistema = self.estado.sistema_activo
        dim = self.estado.dimension_activa

        # ── Validaciones de entrada ──────────────
        try:
            magnitud = float(self.panel_ctrl.var_magnitud.get().strip())
        except ValueError:
            self.barra_estado.error("Magnitud inválida: ingresa un número (p.ej. -1.6e-19).")
            return

        try:
            x = float(self.panel_ctrl.var_x_c.get().strip())
        except ValueError:
            self.barra_estado.error("Posición x inválida: ingresa un número.")
            return

        if dim == 2:
            try:
                y = float(self.panel_ctrl.var_y_c.get().strip())
            except ValueError:
                self.barra_estado.error("Posición y inválida: ingresa un número.")
                return
            posicion = (x, y)
        else:
            posicion = (x,)

        etiqueta = self.panel_ctrl.var_etiqueta_c.get().strip()

        # ── Agregar al sistema ────────────────────
        try:
            nueva = sistema.agregar_carga(magnitud, posicion, etiqueta)
            self.panel_ctrl.actualizar_lista_cargas(sistema.cargas)
            self.canvas_vis.actualizar()
            self.barra_estado.exito(
                f"Carga '{nueva.etiqueta}' agregada: "
                f"q={magnitud:.3e} C en {posicion} m."
            )
            # Limpiar formulario
            self.panel_ctrl.var_magnitud.set("")
            self.panel_ctrl.var_x_c.set("")
            self.panel_ctrl.var_y_c.set("")
            self.panel_ctrl.var_etiqueta_c.set("")

        except ValueError as e:
            self.barra_estado.error(str(e))

    def eliminar_carga(self):
        """Elimina la carga seleccionada en el Listbox."""
        id_sel = self.panel_ctrl.get_id_carga_seleccionada()
        if id_sel is None:
            self.barra_estado.alerta("Selecciona una carga en la lista para eliminar.")
            return

        sistema = self.estado.sistema_activo
        if sistema.eliminar_carga(id_sel):
            self.panel_ctrl.actualizar_lista_cargas(sistema.cargas)
            self.canvas_vis.set_resultados([], None, [])
            self.canvas_vis.set_carga_seleccionada(None)
            self.canvas_vis.actualizar()
            self.panel_res.limpiar()
            self.barra_estado.exito(f"Carga [id={id_sel}] eliminada.")
        else:
            self.barra_estado.error(f"No se encontró carga con id={id_sel}.")

    def agregar_punto_prueba(self):
        """Valida y agrega un punto de prueba al sistema activo."""
        sistema = self.estado.sistema_activo
        dim = self.estado.dimension_activa

        try:
            x = float(self.panel_ctrl.var_x_p.get().strip())
        except ValueError:
            self.barra_estado.error("Posición x del punto inválida.")
            return

        if dim == 2:
            try:
                y = float(self.panel_ctrl.var_y_p.get().strip())
            except ValueError:
                self.barra_estado.error("Posición y del punto inválida.")
                return
            posicion = (x, y)
        else:
            posicion = (x,)

        etiqueta = self.panel_ctrl.var_etiqueta_p.get().strip()

        try:
            nuevo = sistema.agregar_punto_prueba(posicion, etiqueta)
            self.panel_ctrl.actualizar_lista_puntos(sistema.puntos_prueba)
            self.canvas_vis.actualizar()
            self.barra_estado.exito(
                f"Punto '{nuevo.etiqueta}' agregado en {posicion} m."
            )
            self.panel_ctrl.var_x_p.set("")
            self.panel_ctrl.var_y_p.set("")
            self.panel_ctrl.var_etiqueta_p.set("")

        except ValueError as e:
            self.barra_estado.error(str(e))

    def eliminar_punto_prueba(self):
        """Elimina el punto de prueba seleccionado."""
        id_sel = self.panel_ctrl.get_id_punto_seleccionado()
        if id_sel is None:
            self.barra_estado.alerta("Selecciona un punto de prueba para eliminar.")
            return

        sistema = self.estado.sistema_activo
        if sistema.eliminar_punto_prueba(id_sel):
            self.panel_ctrl.actualizar_lista_puntos(sistema.puntos_prueba)
            self.canvas_vis.actualizar()
            self.barra_estado.exito(f"Punto [id={id_sel}] eliminado.")
        else:
            self.barra_estado.error(f"No se encontró punto con id={id_sel}.")

    def al_seleccionar_carga(self, event=None):
        """Callback cuando el usuario selecciona una carga en el Listbox."""
        id_sel = self.panel_ctrl.get_id_carga_seleccionada()
        self.canvas_vis.set_carga_seleccionada(id_sel)
        self.canvas_vis.actualizar()

    def calcular_fuerzas(self):
        """Calcula la fuerza neta sobre la carga seleccionada y actualiza la UI."""
        id_sel = self.panel_ctrl.get_id_carga_seleccionada()
        if id_sel is None:
            self.barra_estado.alerta(
                "Selecciona la carga objetivo en la lista para calcular fuerzas."
            )
            return

        sistema = self.estado.sistema_activo

        try:
            fuerzas, neta = sistema.calcular_fuerza_neta(id_sel)
        except ValueError as e:
            self.barra_estado.error(str(e))
            return

        # Actualizar canvas
        self.canvas_vis.set_carga_seleccionada(id_sel)
        self.canvas_vis.set_resultados(fuerzas, neta, self.canvas_vis._campos)
        self.canvas_vis.actualizar()

        # Actualizar tabla
        cargas_dict = {c.id_carga: c for c in sistema.cargas}
        self.panel_res.mostrar_fuerzas(fuerzas, neta, cargas_dict)

        self.barra_estado.exito(
            f"Fuerza neta sobre carga [id={id_sel}]: "
            f"|F| = {neta.magnitud:.4e} N  "
            f"(θ = {neta.angulo_grados:.2f}°)"
        )

    def calcular_campos(self):
        """Calcula el campo eléctrico en todos los puntos de prueba."""
        sistema = self.estado.sistema_activo

        if not sistema.puntos_prueba:
            self.barra_estado.alerta("No hay puntos de prueba en el sistema.")
            return
        if not sistema.cargas:
            self.barra_estado.alerta("Agrega al menos una carga para calcular el campo.")
            return

        campos = sistema.calcular_todos_los_campos()

        # Mantener resultados previos de fuerzas
        fuerzas_prev = self.canvas_vis._fuerzas_individuales
        neta_prev = self.canvas_vis._fuerza_neta

        self.canvas_vis.set_resultados(fuerzas_prev, neta_prev, campos)
        self.canvas_vis.actualizar()

        puntos_dict = {p.id_punto: p for p in sistema.puntos_prueba}
        self.panel_res.mostrar_campos(campos, puntos_dict)

        magnitudes = [r.magnitud for r in campos]
        promedio = sum(magnitudes) / len(magnitudes) if magnitudes else 0
        self.barra_estado.exito(
            f"Campo eléctrico calculado en {len(campos)} punto(s). "
            f"|E| promedio = {promedio:.4e} N/C"
        )

    def limpiar_sistema(self):
        """Limpia el sistema activo previa confirmación."""
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Deseas limpiar todas las cargas y puntos de prueba del modo {self.estado.dimension_activa}D?\n"
            "Esta acción no se puede deshacer.",
            icon="warning"
        ):
            return

        self.estado.sistema_activo.limpiar()
        self.canvas_vis.set_resultados([], None, [])
        self.canvas_vis.set_carga_seleccionada(None)
        self._sincronizar_ui()
        self.panel_res.limpiar()
        self.barra_estado.info("Sistema limpiado.")