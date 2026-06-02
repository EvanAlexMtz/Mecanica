
"""
gui.py — Interfaz Gráfica Principal  (v2)
==========================================
Mejoras en esta versión:
  - Lista de cargas con posición en tiempo real (actualizada al soltar drag).
  - Callback on_drag_released inyectado en CanvasElectrostatico.
  - Recálculo automático de fuerzas y campos después del arrastre.
  - Mismo diseño visual y paleta de colores que v1.
"""
 
import tkinter as tk
from tkinter import ttk, messagebox
from model import EstadoSimulador, SistemaElectrostatico, Vector
from canvas import CanvasElectrostatico, COLORES
 
# ─────────────────────────────────────────────
#  PALETA (sin cambios)
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
 
FUENTE_MONO    = ("Courier New", 9)
FUENTE_LABEL   = ("Segoe UI", 9)
FUENTE_TITULO  = ("Segoe UI", 10, "bold")
FUENTE_SECCION = ("Segoe UI", 8, "bold")
 
 
# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
 
def _entry(parent, textvariable=None, width=14, **kw):
    return tk.Entry(
        parent, textvariable=textvariable, width=width,
        bg=PALETA["bg_entrada"], fg=PALETA["texto"],
        insertbackground=PALETA["texto"],
        relief=tk.FLAT, bd=0,
        highlightthickness=1,
        highlightcolor=PALETA["acento"],
        highlightbackground=PALETA["borde"],
        font=FUENTE_MONO, **kw
    )
 
def _label(parent, text, color=None, font=None, **kw):
    return tk.Label(
        parent, text=text,
        bg=PALETA["bg_panel"],
        fg=color or PALETA["texto"],
        font=font or FUENTE_LABEL, **kw
    )
 
def _boton(parent, text, command, color=None, hover=None, width=None, **kw):
    color = color or PALETA["acento"]
    hover = hover or PALETA["boton_hover"]
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg="#ffffff",
        activeforeground="#ffffff", activebackground=hover,
        relief=tk.FLAT, bd=0,
        padx=10, pady=5, cursor="hand2",
        font=FUENTE_SECCION, width=width or 0, **kw
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn
 
def _sep(parent):
    return tk.Frame(parent, height=1, bg=PALETA["separador"])
 
def _sec(parent, titulo):
    return tk.LabelFrame(
        parent, text=f"  {titulo}  ",
        bg=PALETA["bg_panel"], fg=PALETA["texto_dim"],
        font=FUENTE_SECCION,
        relief=tk.FLAT, bd=0,
        highlightthickness=1, highlightbackground=PALETA["borde"],
        padx=8, pady=6
    )
 
 
# ─────────────────────────────────────────────
#  PANEL DE CONTROL (izquierdo)
# ─────────────────────────────────────────────
 
class PanelControl(tk.Frame):
    """
    Panel izquierdo: formularios de entrada y listas de cargas/puntos.
    La lista de cargas ahora muestra posición en tiempo real.
    """
 
    def __init__(self, parent, controlador, **kw):
        super().__init__(parent, bg=PALETA["bg_panel"], **kw)
        self.ctrl = controlador
        self._construir()
 
    def _construir(self):
        # ── Título ──────────────────────────────
        tk.Label(self, text="PANEL DE CONTROL",
                 bg=PALETA["bg_panel"], fg=PALETA["acento"],
                 font=("Segoe UI", 10, "bold")).pack(fill=tk.X, pady=(10, 2))
        _sep(self).pack(fill=tk.X, padx=8, pady=4)
 
        # ── Nueva carga ──────────────────────────
        sc = _sec(self, "⚡ Nueva carga")
        sc.pack(fill=tk.X, padx=8, pady=4)
 
        _label(sc, "Etiqueta:").grid(row=0, column=0, sticky="w", pady=2)
        self.var_etiqueta_c = tk.StringVar()
        _entry(sc, self.var_etiqueta_c, 13).grid(row=0, column=1, pady=2)
 
        _label(sc, "Magnitud q [C]:").grid(row=1, column=0, sticky="w", pady=2)
        self.var_magnitud = tk.StringVar()
        _entry(sc, self.var_magnitud, 13).grid(row=1, column=1, pady=2)
 
        _label(sc, "Posición x [m]:").grid(row=2, column=0, sticky="w", pady=2)
        self.var_x_c = tk.StringVar()
        _entry(sc, self.var_x_c, 13).grid(row=2, column=1, pady=2)
 
        _label(sc, "Posición y [m]:").grid(row=3, column=0, sticky="w", pady=2)
        self.var_y_c = tk.StringVar()
        self.entry_y_c = _entry(sc, self.var_y_c, 13)
        self.entry_y_c.grid(row=3, column=1, pady=2)
 
        _boton(sc, "Agregar carga", self.ctrl.agregar_carga,
               color=PALETA["acento"]).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(6, 0))
 
        # ── Lista de cargas ──────────────────────
        sl = _sec(self, "📋 Cargas en el sistema")
        sl.pack(fill=tk.X, padx=8, pady=4)
 
        f_lista = tk.Frame(sl, bg=PALETA["bg_panel"])
        f_lista.pack(fill=tk.X)
        scr = tk.Scrollbar(f_lista, orient=tk.VERTICAL)
        self.lista_cargas = tk.Listbox(
            f_lista,
            bg=PALETA["bg_entrada"], fg=PALETA["texto"],
            selectbackground=PALETA["acento"], selectforeground="#ffffff",
            relief=tk.FLAT, bd=0, font=FUENTE_MONO, height=5,
            activestyle="none", yscrollcommand=scr.set,
            exportselection=False
        )
        scr.config(command=self.lista_cargas.yview)
        self.lista_cargas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scr.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_cargas.bind("<<ListboxSelect>>", self.ctrl.al_seleccionar_carga)
 
        fb = tk.Frame(sl, bg=PALETA["bg_panel"])
        fb.pack(fill=tk.X, pady=(4, 0))
        _boton(fb, "Calcular fuerzas", self.ctrl.calcular_fuerzas,
               color="#2d5a27").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        _boton(fb, "Eliminar", self.ctrl.eliminar_carga,
               color=PALETA["acento_neg"]).pack(side=tk.RIGHT, expand=True, fill=tk.X)
 
        # ── Nuevo punto de prueba ────────────────
        sp = _sec(self, "◈ Nuevo punto de prueba")
        sp.pack(fill=tk.X, padx=8, pady=4)
 
        _label(sp, "Etiqueta:").grid(row=0, column=0, sticky="w", pady=2)
        self.var_etiqueta_p = tk.StringVar()
        _entry(sp, self.var_etiqueta_p, 13).grid(row=0, column=1, pady=2)
 
        _label(sp, "Posición x [m]:").grid(row=1, column=0, sticky="w", pady=2)
        self.var_x_p = tk.StringVar()
        _entry(sp, self.var_x_p, 13).grid(row=1, column=1, pady=2)
 
        _label(sp, "Posición y [m]:").grid(row=2, column=0, sticky="w", pady=2)
        self.var_y_p = tk.StringVar()
        self.entry_y_p = _entry(sp, self.var_y_p, 13)
        self.entry_y_p.grid(row=2, column=1, pady=2)
 
        _boton(sp, "Agregar punto", self.ctrl.agregar_punto_prueba,
               color="#4a3578").grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
 
        # ── Lista puntos prueba ──────────────────
        slp = _sec(self, "◈ Puntos de prueba")
        slp.pack(fill=tk.X, padx=8, pady=4)
 
        flp = tk.Frame(slp, bg=PALETA["bg_panel"])
        flp.pack(fill=tk.X)
        scr2 = tk.Scrollbar(flp, orient=tk.VERTICAL)
        self.lista_puntos = tk.Listbox(
            flp,
            bg=PALETA["bg_entrada"], fg=COLORES["punto_prueba"],
            selectbackground=PALETA["acento"],
            relief=tk.FLAT, bd=0, font=FUENTE_MONO, height=3,
            activestyle="none", yscrollcommand=scr2.set,
            exportselection=False
        )
        scr2.config(command=self.lista_puntos.yview)
        self.lista_puntos.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scr2.pack(side=tk.RIGHT, fill=tk.Y)
 
        fbp = tk.Frame(slp, bg=PALETA["bg_panel"])
        fbp.pack(fill=tk.X, pady=(4, 0))
        _boton(fbp, "Calcular campos", self.ctrl.calcular_campos,
               color="#4a3578").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        _boton(fbp, "Eliminar", self.ctrl.eliminar_punto_prueba,
               color=PALETA["acento_neg"]).pack(side=tk.RIGHT, expand=True, fill=tk.X)
 
        # ── Limpiar ──────────────────────────────
        _sep(self).pack(fill=tk.X, padx=8, pady=6)
        _boton(self, "🗑  Limpiar sistema", self.ctrl.limpiar_sistema,
               color="#3a1e1e", hover="#5a2a2a").pack(
            fill=tk.X, padx=8, pady=(0, 10))
 
    # ── API de actualización ──────────────────────
 
    def actualizar_lista_cargas(self, cargas, dimension: int = 2):
        """
        Refresca el Listbox con posición en tiempo real.
        Formato 1D: [id] etiqueta | q: X C | x=... m
        Formato 2D: [id] etiqueta | q: X C | (x=..., y=...) m
        """
        # Guardar índice seleccionado para restaurarlo
        sel = self.lista_cargas.curselection()
        idx_sel = sel[0] if sel else None
 
        self.lista_cargas.delete(0, tk.END)
        for c in cargas:
            signo = "+" if c.es_positiva else "−"
            q_str = f"{signo}{abs(c.magnitud):.2e}"
            if dimension == 1:
                x = c.posicion[0]
                pos_str = f"x={x:.3g} m"
            else:
                x = c.posicion[0]
                y = c.posicion[1] if len(c.posicion) > 1 else 0.0
                pos_str = f"x={x:.3g}, y={y:.3g} m"
            texto = f"[{c.id_carga}] {c.etiqueta} | q:{q_str} C | {pos_str}"
            self.lista_cargas.insert(tk.END, texto)
 
        # Restaurar selección
        if idx_sel is not None and idx_sel < self.lista_cargas.size():
            self.lista_cargas.selection_set(idx_sel)
            self.lista_cargas.activate(idx_sel)
 
    def actualizar_lista_puntos(self, puntos, dimension: int = 2):
        sel = self.lista_puntos.curselection()
        idx_sel = sel[0] if sel else None
 
        self.lista_puntos.delete(0, tk.END)
        for p in puntos:
            if dimension == 1:
                pos_str = f"x={p.posicion[0]:.3g} m"
            else:
                x = p.posicion[0]
                y = p.posicion[1] if len(p.posicion) > 1 else 0.0
                pos_str = f"({x:.3g}, {y:.3g}) m"
            texto = f"[{p.id_punto}] {p.etiqueta}  {pos_str}"
            self.lista_puntos.insert(tk.END, texto)
 
        if idx_sel is not None and idx_sel < self.lista_puntos.size():
            self.lista_puntos.selection_set(idx_sel)
 
    def set_modo_dimension(self, dimension: int):
        estado = tk.NORMAL if dimension == 2 else tk.DISABLED
        color  = PALETA["texto"] if dimension == 2 else PALETA["texto_dim"]
        self.entry_y_c.config(state=estado, fg=color)
        self.entry_y_p.config(state=estado, fg=color)
        if dimension == 1:
            self.var_y_c.set("0")
            self.var_y_p.set("0")
 
    def get_id_carga_seleccionada(self) -> int | None:
        sel = self.lista_cargas.curselection()
        if not sel:
            return None
        try:
            return int(self.lista_cargas.get(sel[0]).split("]")[0].replace("[", "").strip())
        except ValueError:
            return None
 
    def get_id_punto_seleccionado(self) -> int | None:
        sel = self.lista_puntos.curselection()
        if not sel:
            return None
        try:
            return int(self.lista_puntos.get(sel[0]).split("]")[0].replace("[", "").strip())
        except ValueError:
            return None
 
 
# ─────────────────────────────────────────────
#  PANEL DE RESULTADOS (derecho)
# ─────────────────────────────────────────────
 
class PanelResultados(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=PALETA["bg_panel"], **kw)
        self._construir()
 
    def _construir(self):
        tk.Label(self, text="RESULTADOS NUMÉRICOS",
                 bg=PALETA["bg_panel"], fg=PALETA["acento2"],
                 font=("Segoe UI", 10, "bold")).pack(fill=tk.X, pady=(10, 2))
        _sep(self).pack(fill=tk.X, padx=8, pady=4)
 
        sf = _sec(self, "⚡ Fuerzas individuales sobre carga objetivo  [N]")
        sf.pack(fill=tk.X, padx=8, pady=4)
        self.tabla_fuerzas = self._tabla(
            sf, ("Fuente", "Fx [N]", "Fy [N]", "|F| [N]", "θ [°]"), 5)
 
        sfn = _sec(self, "∑F  —  Fuerza Neta  [N]")
        sfn.pack(fill=tk.X, padx=8, pady=4)
        self.texto_neta = tk.Text(
            sfn, height=4, width=36,
            bg=PALETA["bg_entrada"], fg=PALETA["exito"],
            font=FUENTE_MONO, relief=tk.FLAT, bd=0,
            state=tk.DISABLED, wrap=tk.WORD, padx=6, pady=4
        )
        self.texto_neta.pack(fill=tk.X)
 
        se = _sec(self, "E  —  Campo Eléctrico en puntos de prueba  [N/C]")
        se.pack(fill=tk.X, padx=8, pady=4)
        self.tabla_campos = self._tabla(
            se, ("Punto", "Ex [N/C]", "Ey [N/C]", "|E| [N/C]", "θ [°]"), 5)
 
        si = _sec(self, "ℹ  Constantes físicas")
        si.pack(fill=tk.X, padx=8, pady=(4, 10))
        tk.Label(
            si,
            text=("k = 8.99 × 10⁹  N·m²/C²\n"
                  "Ley de Coulomb:  F = k·q₁·q₂/r²\n"
                  "Campo eléctrico: E = k·q/r²"),
            bg=PALETA["bg_panel"], fg=PALETA["texto_dim"],
            font=("Courier New", 8), justify=tk.LEFT
        ).pack(anchor="w")
 
    def _tabla(self, parent, columnas, alto):
        est = ttk.Style()
        est.theme_use("default")
        nombre = f"T{id(parent)}.Treeview"
        est.configure(nombre,
                      background=PALETA["bg_entrada"],
                      foreground=PALETA["texto"],
                      fieldbackground=PALETA["bg_entrada"],
                      rowheight=22, font=FUENTE_MONO)
        est.configure(f"{nombre}.Heading",
                      background=PALETA["bg_widget"],
                      foreground=PALETA["texto_dim"],
                      font=FUENTE_SECCION, relief="flat")
        est.map(nombre,
                background=[("selected", PALETA["acento"])],
                foreground=[("selected", "#ffffff")])
 
        frame = tk.Frame(parent, bg=PALETA["bg_panel"])
        frame.pack(fill=tk.X)
        scr = tk.Scrollbar(frame, orient=tk.VERTICAL)
        tv = ttk.Treeview(frame, columns=columnas, show="headings",
                          height=alto, style=nombre,
                          yscrollcommand=scr.set, selectmode="browse")
        scr.config(command=tv.yview)
        for col in columnas:
            tv.heading(col, text=col, anchor="center")
            tv.column(col, width=90, anchor="center", stretch=True)
        tv.column(columnas[0], width=70, anchor="center")
        tv.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scr.pack(side=tk.RIGHT, fill=tk.Y)
        return tv
 
    def mostrar_fuerzas(self, fuerzas, fuerza_neta, cargas_dict):
        for row in self.tabla_fuerzas.get_children():
            self.tabla_fuerzas.delete(row)
        for r in fuerzas:
            fuente = cargas_dict.get(r.carga_fuente_id)
            nombre = fuente.etiqueta if fuente else f"q{r.carga_fuente_id}"
            v = r.vector_fuerza
            self.tabla_fuerzas.insert("", tk.END, values=(
                nombre, f"{v.x:.4e}", f"{v.y:.4e}",
                f"{v.magnitud:.4e}", f"{v.angulo_grados:.2f}°"
            ))
        self.texto_neta.config(state=tk.NORMAL)
        self.texto_neta.delete("1.0", tk.END)
        if fuerza_neta:
            txt = (f"Fx = {fuerza_neta.x:.4e} N\n"
                   f"Fy = {fuerza_neta.y:.4e} N\n"
                   f"|F| = {fuerza_neta.magnitud:.4e} N\n"
                   f"θ  = {fuerza_neta.angulo_grados:.2f}°")
        else:
            txt = "—  Sin datos  —"
        self.texto_neta.insert("1.0", txt)
        self.texto_neta.config(state=tk.DISABLED)
 
    def mostrar_campos(self, campos, puntos_dict):
        for row in self.tabla_campos.get_children():
            self.tabla_campos.delete(row)
        for r in campos:
            punto = puntos_dict.get(r.punto_id)
            nombre = punto.etiqueta if punto else f"P{r.punto_id}"
            v = r.vector_campo
            self.tabla_campos.insert("", tk.END, values=(
                nombre, f"{v.x:.4e}", f"{v.y:.4e}",
                f"{v.magnitud:.4e}", f"{v.angulo_grados:.2f}°"
            ))
 
    def limpiar(self):
        for row in self.tabla_fuerzas.get_children():
            self.tabla_fuerzas.delete(row)
        for row in self.tabla_campos.get_children():
            self.tabla_campos.delete(row)
        self.texto_neta.config(state=tk.NORMAL)
        self.texto_neta.delete("1.0", tk.END)
        self.texto_neta.config(state=tk.DISABLED)
 
 
# ─────────────────────────────────────────────
#  BARRA SUPERIOR
# ─────────────────────────────────────────────
 
class BarraSuperior(tk.Frame):
    def __init__(self, parent, controlador, **kw):
        super().__init__(parent, bg="#0a0d14", height=52, **kw)
        self.pack_propagate(False)
        self.ctrl = controlador
        self._construir()
 
    def _construir(self):
        tk.Label(self, text="⚛  SIMULADOR DE ELECTROSTÁTICA",
                 bg="#0a0d14", fg=PALETA["texto_titulo"],
                 font=("Segoe UI", 13, "bold"), padx=16).pack(side=tk.LEFT, pady=10)
        tk.Label(self, text="Ley de Coulomb  ·  Principio de Superposición",
                 bg="#0a0d14", fg=PALETA["texto_dim"],
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, pady=10)
 
        fd = tk.Frame(self, bg="#0a0d14")
        fd.pack(side=tk.RIGHT, padx=16)
        tk.Label(fd, text="Dimensión:", bg="#0a0d14", fg=PALETA["texto_dim"],
                 font=FUENTE_SECCION).pack(side=tk.LEFT, padx=(0, 6))
 
        self.btn_1d = tk.Button(
            fd, text="1D", command=lambda: self.ctrl.cambiar_dimension(1),
            bg=PALETA["bg_widget"], fg=PALETA["texto_dim"],
            activebackground=PALETA["acento"],
            relief=tk.FLAT, bd=0, padx=12, pady=4,
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        self.btn_1d.pack(side=tk.LEFT)
 
        self.btn_2d = tk.Button(
            fd, text="2D", command=lambda: self.ctrl.cambiar_dimension(2),
            bg=PALETA["acento"], fg="#ffffff",
            activebackground=PALETA["boton_hover"],
            relief=tk.FLAT, bd=0, padx=12, pady=4,
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        self.btn_2d.pack(side=tk.LEFT, padx=(2, 0))
 
    def actualizar_botones_dim(self, dim: int):
        if dim == 1:
            self.btn_1d.config(bg=PALETA["acento"],    fg="#ffffff")
            self.btn_2d.config(bg=PALETA["bg_widget"], fg=PALETA["texto_dim"])
        else:
            self.btn_2d.config(bg=PALETA["acento"],    fg="#ffffff")
            self.btn_1d.config(bg=PALETA["bg_widget"], fg=PALETA["texto_dim"])
 
 
# ─────────────────────────────────────────────
#  BARRA DE ESTADO
# ─────────────────────────────────────────────
 
class BarraEstado(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg="#080b12", height=26, **kw)
        self.pack_propagate(False)
        self._var = tk.StringVar(value="Listo.")
        self._lbl = tk.Label(self, textvariable=self._var,
                             bg="#080b12", fg=PALETA["texto_dim"],
                             font=("Segoe UI", 8), anchor="w", padx=12)
        self._lbl.pack(fill=tk.BOTH, expand=True)
 
    def info(self, msg):   self._lbl.config(fg=PALETA["texto_dim"]); self._var.set(f"ℹ  {msg}")
    def exito(self, msg):  self._lbl.config(fg=PALETA["exito"]);     self._var.set(f"✓  {msg}")
    def error(self, msg):  self._lbl.config(fg=PALETA["error"]);     self._var.set(f"✗  {msg}")
    def alerta(self, msg): self._lbl.config(fg=PALETA["alerta"]);    self._var.set(f"⚠  {msg}")
    def drag(self, msg):   self._lbl.config(fg=PALETA["acento"]);    self._var.set(f"↔  {msg}")
 
 
# ─────────────────────────────────────────────
#  VENTANA PRINCIPAL (Controlador)
# ─────────────────────────────────────────────
 
class VentanaPrincipal(tk.Tk):
    """
    Orquestador principal.
    Novedades v2:
      - Inyecta on_drag_released al canvas para recálculo diferido.
      - actualizar_lista_cargas incluye posición en tiempo real.
      - Recálculo automático post-drag de fuerzas y campos.
    """
 
    def __init__(self):
        super().__init__()
        self.estado = EstadoSimulador()
        self._configurar_ventana()
        self._construir_ui()
        self._sincronizar_ui()
 
    def _configurar_ventana(self):
        self.title("Simulador de Electrostática — Mecánica y Electromagnetismo")
        self.geometry("1280x740")
        self.minsize(1050, 640)
        self.configure(bg=PALETA["bg_ventana"])
 
    def _construir_ui(self):
        self.barra_sup = BarraSuperior(self, self)
        self.barra_sup.pack(fill=tk.X)
        _sep(self).pack(fill=tk.X)
 
        frame_main = tk.Frame(self, bg=PALETA["bg_ventana"])
        frame_main.pack(fill=tk.BOTH, expand=True)
 
        # Panel izquierdo
        self.panel_ctrl = PanelControl(frame_main, self)
        self.panel_ctrl.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1), ipadx=2)
        tk.Frame(frame_main, width=1, bg=PALETA["separador"]).pack(side=tk.LEFT, fill=tk.Y)
 
        # Canvas central
        frame_canvas = tk.Frame(frame_main, bg=PALETA["bg_ventana"])
        frame_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
 
        # Inyectar el callback de drag-released
        self.canvas_vis = CanvasElectrostatico(
            frame_canvas,
            self.estado.sistema_activo,
            on_drag_released=self._tras_drag
        )
 
        # Panel derecho
        tk.Frame(frame_main, width=1, bg=PALETA["separador"]).pack(side=tk.LEFT, fill=tk.Y)
        self.panel_res = PanelResultados(frame_main)
        self.panel_res.pack(side=tk.RIGHT, fill=tk.Y, padx=(1, 0))
 
        _sep(self).pack(fill=tk.X)
        self.barra_estado = BarraEstado(self)
        self.barra_estado.pack(fill=tk.X)
 
    # ── Sincronización UI ──────────────────────────
 
    def _sincronizar_ui(self):
        dim     = self.estado.dimension_activa
        sistema = self.estado.sistema_activo
 
        self.barra_sup.actualizar_botones_dim(dim)
        self.panel_ctrl.set_modo_dimension(dim)
        self.panel_ctrl.actualizar_lista_cargas(sistema.cargas, dim)
        self.panel_ctrl.actualizar_lista_puntos(sistema.puntos_prueba, dim)
        self.canvas_vis.set_sistema(sistema)
        self.canvas_vis.set_resultados([], None, [])
        self.canvas_vis.actualizar()
        self.panel_res.limpiar()
        self.barra_estado.info(
            f"Modo {dim}D activo — {len(sistema.cargas)} carga(s), "
            f"{len(sistema.puntos_prueba)} punto(s) de prueba."
        )
 
    # ── Callback drag & drop ───────────────────────
 
    def _tras_drag(self, id_carga: int):
        """
        Llamado por el canvas al soltar una carga arrastrada.
        Actualiza la lista de cargas (con nueva posición) y
        recalcula fuerzas y campos si ya había resultados activos.
        """
        sistema = self.estado.sistema_activo
        dim     = self.estado.dimension_activa
 
        # Actualizar lista con posición nueva
        self.panel_ctrl.actualizar_lista_cargas(sistema.cargas, dim)
 
        # Si esta carga era el objetivo de cálculo, recalcular fuerzas
        if id_carga == self.canvas_vis._carga_seleccionada_id:
            try:
                fuerzas, neta = sistema.calcular_fuerza_neta(id_carga)
                cargas_dict   = {c.id_carga: c for c in sistema.cargas}
                self.canvas_vis.set_resultados(
                    fuerzas, neta, self.canvas_vis._campos)
                self.canvas_vis.actualizar()
                self.panel_res.mostrar_fuerzas(fuerzas, neta, cargas_dict)
                self.barra_estado.exito(
                    f"Carga [id={id_carga}] movida — "
                    f"|F_neta| = {neta.magnitud:.4e} N")
            except ValueError:
                self.canvas_vis.set_resultados([], None, self.canvas_vis._campos)
                self.canvas_vis.actualizar()
                self.panel_res.limpiar()
                self.barra_estado.alerta(
                    f"Carga [id={id_carga}] movida. "
                    "Recalcula fuerzas si es necesario.")
        else:
            self.barra_estado.exito(
                f"Carga [id={id_carga}] movida a nueva posición.")
 
        # Recalcular campos si había puntos de prueba
        if sistema.puntos_prueba and sistema.cargas:
            try:
                campos = sistema.calcular_todos_los_campos()
                fuerzas_prev = self.canvas_vis._fuerzas_individuales
                neta_prev    = self.canvas_vis._fuerza_neta
                self.canvas_vis.set_resultados(fuerzas_prev, neta_prev, campos)
                self.canvas_vis.actualizar()
                puntos_dict = {p.id_punto: p for p in sistema.puntos_prueba}
                self.panel_res.mostrar_campos(campos, puntos_dict)
            except ValueError:
                pass
 
    # ── Acciones del usuario ───────────────────────
 
    def cambiar_dimension(self, nueva_dim: int):
        if nueva_dim == self.estado.dimension_activa:
            return
        self.estado.cambiar_dimension(nueva_dim)
        self.panel_res.limpiar()
        self.canvas_vis.set_resultados([], None, [])
        self._sincronizar_ui()
        self.barra_estado.exito(
            f"Cambiado a modo {nueva_dim}D. Estado anterior conservado.")
 
    def agregar_carga(self):
        sistema = self.estado.sistema_activo
        dim     = self.estado.dimension_activa
 
        try:
            magnitud = float(self.panel_ctrl.var_magnitud.get().strip())
        except ValueError:
            self.barra_estado.error("Magnitud inválida (ej: -1.6e-19).")
            return
        try:
            x = float(self.panel_ctrl.var_x_c.get().strip())
        except ValueError:
            self.barra_estado.error("Posición x inválida.")
            return
        if dim == 2:
            try:
                y = float(self.panel_ctrl.var_y_c.get().strip())
            except ValueError:
                self.barra_estado.error("Posición y inválida.")
                return
            posicion = (x, y)
        else:
            posicion = (x,)
 
        etiqueta = self.panel_ctrl.var_etiqueta_c.get().strip()
        try:
            nueva = sistema.agregar_carga(magnitud, posicion, etiqueta)
            self.panel_ctrl.actualizar_lista_cargas(sistema.cargas, dim)
            # Invalidar resultados previos (el campo cambió)
            self.canvas_vis.set_resultados([], None, [])
            self.canvas_vis.actualizar()
            self.panel_res.limpiar()
            self.barra_estado.exito(
                f"'{nueva.etiqueta}' agregada: q={magnitud:.3e} C en {posicion} m.")
            self.panel_ctrl.var_magnitud.set("")
            self.panel_ctrl.var_x_c.set("")
            self.panel_ctrl.var_y_c.set("")
            self.panel_ctrl.var_etiqueta_c.set("")
        except ValueError as e:
            self.barra_estado.error(str(e))
 
    def eliminar_carga(self):
        id_sel  = self.panel_ctrl.get_id_carga_seleccionada()
        if id_sel is None:
            self.barra_estado.alerta("Selecciona una carga para eliminar.")
            return
        sistema = self.estado.sistema_activo
        dim     = self.estado.dimension_activa
        if sistema.eliminar_carga(id_sel):
            self.panel_ctrl.actualizar_lista_cargas(sistema.cargas, dim)
            self.canvas_vis.set_resultados([], None, [])
            self.canvas_vis.set_carga_seleccionada(None)
            self.canvas_vis.actualizar()
            self.panel_res.limpiar()
            self.barra_estado.exito(f"Carga [id={id_sel}] eliminada.")
        else:
            self.barra_estado.error(f"No se encontró carga con id={id_sel}.")
 
    def agregar_punto_prueba(self):
        sistema = self.estado.sistema_activo
        dim     = self.estado.dimension_activa
        try:
            x = float(self.panel_ctrl.var_x_p.get().strip())
        except ValueError:
            self.barra_estado.error("Posición x inválida.")
            return
        if dim == 2:
            try:
                y = float(self.panel_ctrl.var_y_p.get().strip())
            except ValueError:
                self.barra_estado.error("Posición y inválida.")
                return
            posicion = (x, y)
        else:
            posicion = (x,)
        etiqueta = self.panel_ctrl.var_etiqueta_p.get().strip()
        try:
            nuevo = sistema.agregar_punto_prueba(posicion, etiqueta)
            self.panel_ctrl.actualizar_lista_puntos(sistema.puntos_prueba, dim)
            self.canvas_vis.actualizar()
            self.barra_estado.exito(
                f"Punto '{nuevo.etiqueta}' agregado en {posicion} m.")
            self.panel_ctrl.var_x_p.set("")
            self.panel_ctrl.var_y_p.set("")
            self.panel_ctrl.var_etiqueta_p.set("")
        except ValueError as e:
            self.barra_estado.error(str(e))
 
    def eliminar_punto_prueba(self):
        id_sel  = self.panel_ctrl.get_id_punto_seleccionado()
        if id_sel is None:
            self.barra_estado.alerta("Selecciona un punto de prueba para eliminar.")
            return
        sistema = self.estado.sistema_activo
        dim     = self.estado.dimension_activa
        if sistema.eliminar_punto_prueba(id_sel):
            self.panel_ctrl.actualizar_lista_puntos(sistema.puntos_prueba, dim)
            self.canvas_vis.actualizar()
            self.barra_estado.exito(f"Punto [id={id_sel}] eliminado.")
        else:
            self.barra_estado.error(f"No se encontró punto con id={id_sel}.")
 
    def al_seleccionar_carga(self, event=None):
        id_sel = self.panel_ctrl.get_id_carga_seleccionada()
        self.canvas_vis.set_carga_seleccionada(id_sel)

        sistema = self.estado.sistema_activo

        if id_sel is not None and len(sistema.cargas) >= 2:
            try:
                fuerzas, neta = sistema.calcular_fuerza_neta(id_sel)
                self.canvas_vis.set_resultados(
                    fuerzas,
                    neta,
                    self.canvas_vis._campos
                )
                cargas_dict = {c.id_carga: c for c in sistema.cargas}
                self.panel_res.mostrar_fuerzas(fuerzas, neta, cargas_dict)
            except ValueError:
                self.canvas_vis.set_resultados([], None, self.canvas_vis._campos)

        self.canvas_vis.actualizar()
 
    def calcular_fuerzas(self):
        id_sel  = self.panel_ctrl.get_id_carga_seleccionada()
        if id_sel is None:
            self.barra_estado.alerta(
                "Selecciona la carga objetivo en la lista.")
            return
        sistema = self.estado.sistema_activo
        try:
            fuerzas, neta = sistema.calcular_fuerza_neta(id_sel)
        except ValueError as e:
            self.barra_estado.error(str(e))
            return
 
        self.canvas_vis.set_carga_seleccionada(id_sel)
        self.canvas_vis.set_resultados(fuerzas, neta, self.canvas_vis._campos)
        self.canvas_vis.actualizar()
        cargas_dict = {c.id_carga: c for c in sistema.cargas}
        self.panel_res.mostrar_fuerzas(fuerzas, neta, cargas_dict)
        self.barra_estado.exito(
            f"F_neta sobre [id={id_sel}]: "
            f"|F| = {neta.magnitud:.4e} N  (θ = {neta.angulo_grados:.2f}°)")
 
    def calcular_campos(self):
        sistema = self.estado.sistema_activo
        if not sistema.puntos_prueba:
            self.barra_estado.alerta("No hay puntos de prueba.")
            return
        if not sistema.cargas:
            self.barra_estado.alerta("Agrega al menos una carga.")
            return
        campos = sistema.calcular_todos_los_campos()
        self.canvas_vis.set_resultados(
            self.canvas_vis._fuerzas_individuales,
            self.canvas_vis._fuerza_neta,
            campos
        )
        self.canvas_vis.actualizar()
        puntos_dict = {p.id_punto: p for p in sistema.puntos_prueba}
        self.panel_res.mostrar_campos(campos, puntos_dict)
        mags = [r.magnitud for r in campos]
        prom = sum(mags) / len(mags) if mags else 0
        self.barra_estado.exito(
            f"Campo calculado en {len(campos)} punto(s). "
            f"|E| prom = {prom:.4e} N/C")
 
    def limpiar_sistema(self):
        dim = self.estado.dimension_activa
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Limpiar todo el modo {dim}D?\nNo se puede deshacer.",
            icon="warning"
        ):
            return
        self.estado.sistema_activo.limpiar()
        self.canvas_vis.set_resultados([], None, [])
        self.canvas_vis.set_carga_seleccionada(None)
        self._sincronizar_ui()
        self.panel_res.limpiar()
        self.barra_estado.info("Sistema limpiado.")