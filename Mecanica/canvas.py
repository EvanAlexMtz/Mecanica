import math
import tkinter as tk
import sys
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.colors import Normalize
from model import (
    SistemaElectrostatico, Carga, PuntoPrueba,
    ResultadoFuerza, ResultadoCampo, Vector, K_COULOMB, DISTANCIA_MINIMA
)

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
except ImportError:
    FigureCanvasTkAgg = None
    NavigationToolbar2Tk = None
class NavigationToolbarSinZoom(NavigationToolbar2Tk):
    toolitems = [
        item for item in NavigationToolbar2Tk.toolitems
        if item[0] != "Zoom"
    ]

# ─────────────────────────────────────────────
#  PALETA DE COLORES  (idéntica a v1)
# ─────────────────────────────────────────────
COLORES = {
    "fondo":            "#0f1117",
    "fondo_figura":     "#141720",
    "grid":             "#1e2230",
    "ejes":             "#3a3f5c",
    "texto":            "#c8cde4",
    "texto_dim":        "#6b7194",
    "carga_pos":        "#e05c5c",
    "carga_neg":        "#5c9ee0",
    "carga_pos_glow":   "#ff9090",
    "carga_neg_glow":   "#90c4ff",
    "punto_prueba":     "#78dce8",
    "fuerza_ind":       "#f0c040",
    "fuerza_neta":      "#50e896",
    "campo_e":          "#c97af5",
    "campo_e_glow":     "#e5b0ff",
    "borde_seleccion":  "#ffffff",
    "quiver":           "#9b6fd4",   # violeta más oscuro para el quiver de fondo
}

TAMANO_CARGA = 180
TAMANO_PUNTO = 80
QUIVER_GRID   = 18    # resolución de la cuadrícula del quiver (NxN en 2D, N en 1D)
RADIO_CLICK   = 0.08  # fracción del rango visible para seleccionar carga con clic


# ─────────────────────────────────────────────
#  CLASE PRINCIPAL
# ─────────────────────────────────────────────
class CanvasElectrostatico:
    """
    Widget de visualización embebido en un Frame de Tkinter.

    Nuevas responsabilidades (v2):
      - Quiver plot automático del campo eléctrico.
      - Drag & drop de cargas con actualización diferida.
      - Zoom y paneo via NavigationToolbar2Tk.
    """

    def __init__(self, parent_frame: tk.Frame, sistema: SistemaElectrostatico,
             on_drag_released=None, on_point_drag_released=None):
        self.parent = parent_frame
        self.sistema = sistema

        # Callback opcional que la GUI puede inyectar para recalcular
        # fuerzas y campos cuando el usuario suelta la carga arrastrada.
        self.on_drag_released = on_drag_released  # firma: (id_carga) -> None
        self.on_point_drag_released = on_point_drag_released

        # ── Estado interno de resultados ──────
        self._carga_seleccionada_id: int | None = None
        self._fuerzas_individuales: list[ResultadoFuerza] = []
        self._fuerza_neta: Vector | None = None
        self._campos: list[ResultadoCampo] = []

        # ── Estado de drag & drop ─────────────
        self._drag_carga: Carga | None = None          # carga siendo arrastrada
        self._drag_punto: PuntoPrueba | None = None
        self._drag_pos_previa: tuple | None = None
        self._drag_scatter = None                       # artista scatter temporal
        self._drag_label   = None                       # texto temporal
        self._toolbar_activa = False                    # si NavigationToolbar tiene herramienta activa

        # ── Límites guardados (para restaurar tras limpiar) ───
        self._limites_guardados: dict | None = None

        self._construir_figura()
        self._conectar_eventos()

    # ════════════════════════════════════════════
    #  CONSTRUCCIÓN DE FIGURA
    # ════════════════════════════════════════════

    def _construir_figura(self):
        """Inicializa la figura con su toolbar de navegación."""
        self.fig = Figure(figsize=(7, 6), dpi=100, facecolor=COLORES["fondo_figura"])
        self.ax  = self.fig.add_subplot(111, facecolor=COLORES["fondo"])
        self._estilizar_ejes()

        # Canvas Tkinter
        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ── NavigationToolbar (zoom / pan) ──────
        toolbar_frame = tk.Frame(self.parent, bg=COLORES["fondo_figura"])
        toolbar_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.toolbar = NavigationToolbarSinZoom(self.canvas_widget, toolbar_frame)
        self.toolbar.config(bg=COLORES["fondo_figura"])
        self.toolbar.update()
        # Estilizar botones de la toolbar
        for child in self.toolbar.winfo_children():
            try:
                if sys.platform == "darwin":
                    child.config(
                        bg=COLORES["fondo_figura"],
                        fg=COLORES["texto_dim"],
                        highlightbackground=COLORES["fondo_figura"],
                        activebackground="#2a3050"
                    )
                else:
                    child.config(
                        bg=COLORES["fondo_figura"],
                        fg=COLORES["texto_dim"],
                        activebackground="#2a3050"
                    )
            except tk.TclError:
                pass
                # Botón personalizado para alejar la vista
        self.btn_alejar = tk.Button(
            toolbar_frame,
            text="Alejar −",
            command=self.alejar_vista,
            bg=COLORES["fondo_figura"],
            fg=COLORES["texto_dim"],
            activebackground="#2a3050",
            activeforeground=COLORES["texto"],
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
            font=("Segoe UI", 8, "bold")
        )
        self.btn_alejar.pack(side=tk.LEFT, padx=(8, 2))
        
        self.btn_acercar = tk.Button(
            toolbar_frame,
            text="Acercar +",
            command=self.acercar_vista,
            bg=COLORES["fondo_figura"],
            fg=COLORES["texto_dim"],
            activebackground="#2a3050",
            activeforeground=COLORES["texto"],
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
            font=("Segoe UI", 8, "bold")
        )
        self.btn_acercar.pack(side=tk.LEFT, padx=(2, 2))
        

        self.fig.subplots_adjust(
    left=0.10,
    right=0.96,
    bottom=0.12,
    top=0.90
)
        self._renderizar_vacio()
    
    def acercar_vista(self, factor: float = 0.80):
        """
        Acerca la vista actual manteniendo el centro.
        Después redibuja el campo para que cubra todo el plano visible.
        """
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()

        centro_x = (xmin + xmax) / 2
        centro_y = (ymin + ymax) / 2

        ancho = (xmax - xmin) * factor
        alto = (ymax - ymin) * factor

        self.ax.set_xlim(
            centro_x - ancho / 2,
            centro_x + ancho / 2
        )

        self.ax.set_ylim(
            centro_y - alto / 2,
            centro_y + alto / 2
        )

        self._redibujar_viewport_actual()

    def _estilizar_ejes(self):
        """Aplica paleta dark-mode y etiquetas con unidades físicas."""
        ax = self.ax
        ax.set_facecolor(COLORES["fondo"])
        ax.tick_params(colors=COLORES["texto_dim"], labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(COLORES["ejes"])
        ax.grid(True, color=COLORES["grid"], linewidth=0.5, linestyle="--", alpha=0.7)
        ax.set_xlabel("x  [m]", color=COLORES["texto_dim"], fontsize=9, labelpad=4)
        ax.set_ylabel("y  [m]", color=COLORES["texto_dim"], fontsize=9, labelpad=4)
        ax.axhline(0, color=COLORES["ejes"], linewidth=0.8, alpha=0.5)
        ax.axvline(0, color=COLORES["ejes"], linewidth=0.8, alpha=0.5)
        ax.plot(0, 0, "o", color=COLORES["ejes"], markersize=3, zorder=1)

    def _renderizar_vacio(self):
        self.ax.text(
            0.5, 0.5,
            "Agrega cargas al sistema\npara visualizar el campo",
            transform=self.ax.transAxes,
            ha="center", va="center",
            color=COLORES["texto_dim"], fontsize=11, fontstyle="italic"
        )
        self.canvas_widget.draw()

    # ════════════════════════════════════════════
    #  EVENTOS MATPLOTLIB (drag & drop)
    # ════════════════════════════════════════════

    def _conectar_eventos(self):
        self._cid_press   = self.fig.canvas.mpl_connect("button_press_event",   self._on_press)
        self._cid_move    = self.fig.canvas.mpl_connect("motion_notify_event",  self._on_move)
        self._cid_release = self.fig.canvas.mpl_connect("button_release_event", self._on_release)

    def _toolbar_en_uso(self) -> bool:
        """Devuelve True si el usuario activó zoom o pan en la toolbar."""
        if self.toolbar is None:
            return False
        modo = self.toolbar.mode
        return bool(modo)  # modo es string vacío cuando está en reposo

    def _carga_en_pos(self, xd: float, yd: float) -> Carga | None:
        """
        Devuelve la carga más cercana al punto de datos (xd, yd)
        si está dentro del radio de selección, o None.
        """
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()
        rango = max(xmax - xmin, ymax - ymin, 1e-9)
        umbral = RADIO_CLICK * rango

        mejor, dist_mejor = None, float("inf")
        for c in self.sistema.cargas:
            cx = c.posicion[0]
            cy = c.posicion[1] if len(c.posicion) > 1 else 0.0
            d = math.hypot(xd - cx, yd - cy)
            if d < umbral and d < dist_mejor:
                mejor, dist_mejor = c, d
        return mejor

    def _punto_en_pos(self, xd: float, yd: float) -> PuntoPrueba | None:
        """
        Devuelve el punto de prueba más cercano al clic,
        si está dentro del radio de selección.
        """
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()

        rango = max(xmax - xmin, ymax - ymin, 1e-9)
        umbral = RADIO_CLICK * rango

        mejor = None
        dist_mejor = float("inf")

        for p in self.sistema.puntos_prueba:
            px = p.posicion[0]
            py = p.posicion[1] if len(p.posicion) > 1 else 0.0

            d = math.hypot(xd - px, yd - py)

            if d < umbral and d < dist_mejor:
                mejor = p
                dist_mejor = d

        return mejor
    def _on_press(self, event):
        """
        Inicia el arrastre si el clic cae sobre una carga
        o sobre un punto de prueba.
        """
        if event.inaxes != self.ax or self._toolbar_en_uso():
            return

        if event.button != 1:
            return

        if event.xdata is None or event.ydata is None:
            return

        # Primero intentamos seleccionar una carga
        carga = self._carga_en_pos(event.xdata, event.ydata)

        if carga is not None:
            self._drag_carga = carga
            self._drag_punto = None
            self._drag_pos_previa = carga.posicion

            # Seleccionar también en la GUI
            self._carga_seleccionada_id = carga.id_carga
            return

        # Si no fue carga, intentamos seleccionar un punto de prueba
        punto = self._punto_en_pos(event.xdata, event.ydata)

        if punto is not None:
            self._drag_punto = punto
            self._drag_carga = None
            self._drag_pos_previa = punto.posicion
            return

    def _on_move(self, event):
        """
        Durante el arrastre:
        - Si se arrastra una carga, se mueve la carga.
        - Si se arrastra un punto de prueba, se mueve el punto.
        """
        if event.inaxes != self.ax:
            return

        if event.xdata is None or event.ydata is None:
            return

        dim = self.sistema.dimension
        nuevo_x = event.xdata
        nuevo_y = event.ydata if dim == 2 else 0.0

        # Arrastre de carga
        if self._drag_carga is not None:
            if dim == 1:
                self._drag_carga.posicion = (nuevo_x,)
            else:
                self._drag_carga.posicion = (nuevo_x, nuevo_y)

            self._render_drag_ligero()
            return

        # Arrastre de punto de prueba
        if self._drag_punto is not None:
            if dim == 1:
                self._drag_punto.posicion = (nuevo_x,)
            else:
                self._drag_punto.posicion = (nuevo_x, nuevo_y)

            # Si ya había campos calculados, actualizarlos
            self._recalcular_campos_en_puntos(solo_si_ya_existian=True)

            self._render_drag_ligero()
            return

    def _on_release(self, event):
        """
        Al soltar:
        - Finaliza arrastre de cargas.
        - Finaliza arrastre de puntos de prueba.
        - Recalcula campo si era necesario.
        """

        # Si se está usando pan/zoom de Matplotlib, redibujar el campo
        # sobre el nuevo viewport.
        if (
            self._drag_carga is None
            and self._drag_punto is None
            and self._toolbar_en_uso()
        ):
            if hasattr(self, "_redibujar_viewport_actual"):
                self.parent.after(30, self._redibujar_viewport_actual)
            return

        if self._drag_carga is None and self._drag_punto is None:
            return

        dim = self.sistema.dimension

        # ─────────────────────────────────────
        # CASO 1: se arrastró una carga
        # ─────────────────────────────────────
        if self._drag_carga is not None:
            carga_arrastrada = self._drag_carga
            self._drag_carga = None

            if event.xdata is not None and event.ydata is not None:
                nuevo_x = event.xdata
                nuevo_y = event.ydata if dim == 2 else 0.0

                nueva_pos = (nuevo_x,) if dim == 1 else (nuevo_x, nuevo_y)

                conflicto = self.sistema._posicion_ocupada(
                    nueva_pos,
                    excluir_id=carga_arrastrada.id_carga
                )

                if conflicto and self._drag_pos_previa is not None:
                    carga_arrastrada.posicion = self._drag_pos_previa
                else:
                    carga_arrastrada.posicion = nueva_pos

            self._drag_pos_previa = None

            # Invalidar fuerzas; recalcular campos si ya existían
            self._fuerzas_individuales = []
            self._fuerza_neta = None
            self._recalcular_campos_en_puntos(solo_si_ya_existian=True)

            self.actualizar()

            if self.on_drag_released:
                self.on_drag_released(carga_arrastrada.id_carga)

            return

        # ─────────────────────────────────────
        # CASO 2: se arrastró un punto de prueba
        # ─────────────────────────────────────
        if self._drag_punto is not None:
            punto_arrastrado = self._drag_punto
            self._drag_punto = None

            if event.xdata is not None and event.ydata is not None:
                nuevo_x = event.xdata
                nuevo_y = event.ydata if dim == 2 else 0.0

                nueva_pos = (nuevo_x,) if dim == 1 else (nuevo_x, nuevo_y)

                # Evitar que el punto quede exactamente encima de una carga
                conflicto = False
                for c in self.sistema.cargas:
                    if self.sistema._distancia(c.posicion, nueva_pos) < DISTANCIA_MINIMA:
                        conflicto = True
                        break

                if conflicto and self._drag_pos_previa is not None:
                    punto_arrastrado.posicion = self._drag_pos_previa
                else:
                    punto_arrastrado.posicion = nueva_pos

            self._drag_pos_previa = None

            # Recalcular campo en puntos si ya se había calculado antes
            self._recalcular_campos_en_puntos(solo_si_ya_existian=True)

            self.actualizar()

            if self.on_point_drag_released:
                self.on_point_drag_released(punto_arrastrado.id_punto)

            return

    # ════════════════════════════════════════════
    #  API PÚBLICA
    # ════════════════════════════════════════════

    def set_sistema(self, sistema: SistemaElectrostatico):
        """Asocia un nuevo sistema (al cambiar de dimensión)."""
        self.sistema = sistema
        self._carga_seleccionada_id = None
        self._fuerzas_individuales = []
        self._fuerza_neta = None
        self._campos = []
        self._drag_carga = None
        self._drag_punto = None
        self._drag_pos_previa = None

    def set_carga_seleccionada(self, id_carga: int | None):
        self._carga_seleccionada_id = id_carga

    def set_resultados(self, fuerzas, neta, campos):
        self._fuerzas_individuales = fuerzas
        self._fuerza_neta = neta
        self._campos = campos

    # ════════════════════════════════════════════
    #  RENDERIZADO PRINCIPAL
    # ════════════════════════════════════════════

    def actualizar(self):
        """Re-renderiza todo el canvas en el plano principal."""

        self.ax.cla()
        self._estilizar_ejes()

        dim = self.sistema.dimension

        titulo = (
            f"Simulador Electrostático  —  Modo "
            f"{'1D  (eje x)' if dim == 1 else '2D  (plano xy)'}"
        )

        self.ax.set_title(
            titulo,
            color=COLORES["texto"],
            fontsize=10,
            pad=8,
            fontweight="bold"
        )

        if not self.sistema.cargas and not self.sistema.puntos_prueba:
            self._renderizar_vacio()
            return

        limites = self._calcular_limites()

        # Fijar límites ANTES de dibujar el campo
        self.ax.set_xlim(limites["xmin"], limites["xmax"])
        self.ax.set_ylim(limites["ymin"], limites["ymax"])

        # En modo 1D las cargas se quedan en y = 0,
        # pero NO se oculta el eje Y porque queremos ver el campo en todo el plano.
        if dim == 1:
            self.ax.axhline(
                0,
                color=COLORES["ejes"],
                linewidth=1.5,
                alpha=0.8
            )

        # Capas de dibujo
        self._dibujar_quiver(limites)
        self._dibujar_puntos_prueba()
        self._dibujar_vectores_campo()
        self._dibujar_vectores_fuerzas()
        self._dibujar_cargas()
        self._dibujar_leyenda()

        self.fig.subplots_adjust(
            left=0.08,
            right=0.97,
            bottom=0.10,
            top=0.92
        )

        self.canvas_widget.draw()
    
    def _redibujar_viewport_actual(self):
        """
        Redibuja toda la escena usando los límites visibles actuales.
        Sirve para que el campo eléctrico vuelva a cubrir todo el plano
        después de acercar, alejar o mover la vista.
        """
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        self.ax.cla()
        self._estilizar_ejes()

        dim = self.sistema.dimension

        titulo = (
            f"Simulador Electrostático  —  Modo "
            f"{'1D  (eje x)' if dim == 1 else '2D  (plano xy)'}"
        )

        self.ax.set_title(
            titulo,
            color=COLORES["texto"],
            fontsize=10,
            pad=8,
            fontweight="bold"
        )

        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

        if dim == 1:
            self.ax.axhline(
                0,
                color=COLORES["ejes"],
                linewidth=1.5,
                alpha=0.8
            )

        limites = {
            "xmin": xlim[0],
            "xmax": xlim[1],
            "ymin": ylim[0],
            "ymax": ylim[1],
        }

        self._dibujar_quiver(limites)
        self._dibujar_puntos_prueba()
        self._dibujar_vectores_campo()
        self._dibujar_vectores_fuerzas()
        self._dibujar_cargas()
        self._dibujar_leyenda()

        self.fig.subplots_adjust(
            left=0.08,
            right=0.97,
            bottom=0.10,
            top=0.92
        )

        self.canvas_widget.draw_idle()
    def alejar_vista(self, factor: float = 1.25):
        """
        Aleja la vista actual manteniendo el centro.
        Después redibuja el campo para que cubra todo el plano visible.
        """
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()

        centro_x = (xmin + xmax) / 2
        centro_y = (ymin + ymax) / 2

        ancho = (xmax - xmin) * factor
        alto = (ymax - ymin) * factor

        self.ax.set_xlim(
            centro_x - ancho / 2,
            centro_x + ancho / 2
        )

        self.ax.set_ylim(
            centro_y - alto / 2,
            centro_y + alto / 2
        )

        self._redibujar_viewport_actual()
    def _recalcular_campos_en_puntos(self, solo_si_ya_existian=True):
        """
        Recalcula el campo eléctrico en los puntos de prueba
        usando la posición actual de las cargas.
        """
        if solo_si_ya_existian and not self._campos:
            return

        if not self.sistema.cargas or not self.sistema.puntos_prueba:
            self._campos = []
            return

        try:
            self._campos = self.sistema.calcular_todos_los_campos()
        except ValueError:
            self._campos = []
    def _render_drag_ligero(self):
        """
        Render de bajo costo durante el arrastre.
        También actualiza el campo en puntos de prueba si ya había sido calculado.
        """
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        self.ax.cla()
        self._estilizar_ejes()

        dim = self.sistema.dimension

        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

        if dim == 1:
            self.ax.axhline(
                0,
                color=COLORES["ejes"],
                linewidth=1.5,
                alpha=0.8
            )

        limites = {
            "xmin": xlim[0],
            "xmax": xlim[1],
            "ymin": ylim[0],
            "ymax": ylim[1],
        }

        # Recalcular campo en puntos mientras se mueve la carga
        self._recalcular_campos_en_puntos(solo_si_ya_existian=True)

        self._dibujar_quiver(limites)
        self._dibujar_puntos_prueba()
        self._dibujar_vectores_campo()
        self._dibujar_vectores_fuerzas()
        self._dibujar_cargas()

        self.canvas_widget.draw_idle()

    # ════════════════════════════════════════════
    #  QUIVER PLOT — CAMPO ELÉCTRICO EN CUADRÍCULA
    # ════════════════════════════════════════════

    def _dibujar_quiver(self, limites: dict):
        """
        Dibuja el campo eléctrico en todo el plano visible.

        En modo 2D:
            - Las cargas pueden estar en (x, y).
            - El campo se calcula sobre todo el plano visible.

        En modo 1D:
            - Las cargas siguen moviéndose solo sobre el eje x.
            - Pero el campo se visualiza en todo el plano xy,
              tomando y = 0 para la posición de las cargas.
        """
        if not self.sistema.cargas:
            return

        # Usar SIEMPRE los límites visibles actuales del plano
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()

        # Seguridad por si el eje todavía no tiene límites válidos
        if abs(xmax - xmin) < 1e-12:
            xmin, xmax = limites["xmin"], limites["xmax"]

        if abs(ymax - ymin) < 1e-12:
            ymin, ymax = limites.get("ymin", -1.5), limites.get("ymax", 1.5)

        # Cuadrícula en TODO el plano visible, también en modo 1D
        xs = np.linspace(xmin, xmax, QUIVER_GRID)
        ys = np.linspace(ymin, ymax, QUIVER_GRID)

        GX, GY = np.meshgrid(xs, ys)
        puntos = list(zip(GX.ravel(), GY.ravel()))

        Ex_arr = np.zeros(len(puntos))
        Ey_arr = np.zeros(len(puntos))
        mag_arr = np.zeros(len(puntos))

        for i, (px, py) in enumerate(puntos):
            ex, ey = 0.0, 0.0
            singularidad = False

            for c in self.sistema.cargas:
                cx = c.posicion[0]

                # En 1D la carga está sobre el eje x, por tanto y = 0
                cy = c.posicion[1] if len(c.posicion) > 1 else 0.0

                dx = px - cx
                dy = py - cy

                r2 = dx * dx + dy * dy

                if r2 < DISTANCIA_MINIMA ** 2:
                    singularidad = True
                    break

                r = math.sqrt(r2)

                e_mag = K_COULOMB * abs(c.magnitud) / r2
                signo = 1.0 if c.magnitud >= 0 else -1.0

                ex += signo * e_mag * dx / r
                ey += signo * e_mag * dy / r

            if singularidad:
                continue

            Ex_arr[i] = ex
            Ey_arr[i] = ey
            mag_arr[i] = math.sqrt(ex * ex + ey * ey)

        mag_max = np.max(mag_arr)

        if mag_max < 1e-30:
            return

        # Normalizar dirección de las flechas
        with np.errstate(invalid="ignore", divide="ignore"):
            Ux = np.where(mag_arr > 0, Ex_arr / mag_arr, 0.0)
            Uy = np.where(mag_arr > 0, Ey_arr / mag_arr, 0.0)

        # Transparencia según intensidad del campo
        log_mag = np.where(
            mag_arr > 0,
            np.log10(mag_arr / mag_max + 1e-10),
            -10
        )

        log_min = np.min(log_mag[mag_arr > 0]) if np.any(mag_arr > 0) else -10
        rango_log = max(log_min, -8)

        alphas = np.clip(
            0.08 + 0.57 * (log_mag - rango_log) / (-rango_log + 1e-9),
            0.05,
            0.65
        )

        paso_x = abs(xmax - xmin) / QUIVER_GRID
        paso_y = abs(ymax - ymin) / QUIVER_GRID

        longitud = min(paso_x, paso_y) * 0.55

        GX_r = GX.ravel()
        GY_r = GY.ravel()

        # Dibujar por grupos de transparencia
        n_grupos = 6
        bins = np.linspace(0.05, 0.65, n_grupos + 1)

        for k in range(n_grupos):
            if k == n_grupos - 1:
                mask = (
                    (alphas >= bins[k])
                    & (alphas <= bins[k + 1])
                    & (mag_arr > 0)
                )
            else:
                mask = (
                    (alphas >= bins[k])
                    & (alphas < bins[k + 1])
                    & (mag_arr > 0)
                )

            if not np.any(mask):
                continue

            alpha_g = float(np.mean(alphas[mask]))

            self.ax.quiver(
                GX_r[mask],
                GY_r[mask],
                Ux[mask] * longitud,
                Uy[mask] * longitud,
                angles="xy",
                scale_units="xy",
                scale=1,
                color=COLORES["quiver"],
                alpha=alpha_g,
                width=0.003,
                headwidth=4,
                headlength=4,
                headaxislength=3.5,
                zorder=2
            )

    # ════════════════════════════════════════════
    #  CÁLCULO DE LÍMITES
    # ════════════════════════════════════════════

    def _calcular_limites(self) -> dict:
        """Límites automáticos con margen estable para 1D y 2D."""
        posiciones_x, posiciones_y = [], []

        for c in self.sistema.cargas:
            posiciones_x.append(c.posicion[0])
            posiciones_y.append(c.posicion[1] if len(c.posicion) > 1 else 0.0)

        for p in self.sistema.puntos_prueba:
            posiciones_x.append(p.posicion[0])
            posiciones_y.append(p.posicion[1] if len(p.posicion) > 1 else 0.0)

        if not posiciones_x:
            return {
                "xmin": -5,
                "xmax": 5,
                "ymin": -5,
                "ymax": 5,
            }

        xmin = min(posiciones_x)
        xmax = max(posiciones_x)
        ymin = min(posiciones_y)
        ymax = max(posiciones_y)

        rango_x = xmax - xmin
        rango_y = ymax - ymin

        # Si solo hay una carga o los puntos están muy juntos,
        # damos una ventana mínima visible.
        if rango_x < 2.0:
            centro_x = (xmin + xmax) / 2
            xmin = centro_x - 1.5
            xmax = centro_x + 1.5
        else:
            margen_x = rango_x * 0.35
            xmin -= margen_x
            xmax += margen_x

        if self.sistema.dimension == 2:
            if rango_y < 2.0:
                centro_y = (ymin + ymax) / 2
                ymin = centro_y - 1.5
                ymax = centro_y + 1.5
            else:
                margen_y = rango_y * 0.35
                ymin -= margen_y
                ymax += margen_y
        else:
            ymin = -1.2
            ymax = 1.2

        return {
            "xmin": xmin,
            "xmax": xmax,
            "ymin": ymin,
            "ymax": ymax,
        }

    # ════════════════════════════════════════════
    #  RENDERIZADO DE OBJETOS
    # ════════════════════════════════════════════

    def _dibujar_cargas(self):
        """Dibuja cada carga con halo, signo y etiqueta."""
        for carga in self.sistema.cargas:
            pos_x = carga.posicion[0]
            pos_y = carga.posicion[1] if len(carga.posicion) > 1 else 0.0
            es_drag  = (self._drag_carga is not None and
                        self._drag_carga.id_carga == carga.id_carga)
            es_sel   = (carga.id_carga == self._carga_seleccionada_id)
            color    = COLORES["carga_pos"] if carga.es_positiva else COLORES["carga_neg"]
            glow     = COLORES["carga_pos_glow"] if carga.es_positiva else COLORES["carga_neg_glow"]

            # Halo (drag o selección)
            if es_drag:
                self.ax.scatter(pos_x, pos_y, s=TAMANO_CARGA * 4,
                                color=glow, alpha=0.18, zorder=4)
            elif es_sel:
                self.ax.scatter(pos_x, pos_y, s=TAMANO_CARGA * 2.8,
                                color=glow, alpha=0.25, zorder=4)

            # Marcador principal
            self.ax.scatter(pos_x, pos_y, s=TAMANO_CARGA,
                            color=color,
                            edgecolors="#ffffff" if (es_sel or es_drag) else glow,
                            linewidths=2.0 if (es_sel or es_drag) else 0.8,
                            zorder=5)

            # Signo
            self.ax.text(pos_x, pos_y, "+" if carga.es_positiva else "−",
                         ha="center", va="center", fontsize=10,
                         fontweight="bold", color="#ffffff", zorder=6)

            # Etiqueta + magnitud
            mag_str = self._fmt(carga.magnitud)
            self.ax.annotate(
                f"{carga.etiqueta}\n{mag_str} C",
                xy=(pos_x, pos_y), xytext=(12, 12),
                textcoords="offset points",
                color=glow, fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3",
                          fc=COLORES["fondo"], ec=color,
                          alpha=0.85, linewidth=0.8),
                zorder=7
            )

    def _dibujar_puntos_prueba(self):
        for punto in self.sistema.puntos_prueba:
            px = punto.posicion[0]
            py = punto.posicion[1] if len(punto.posicion) > 1 else 0.0
            self.ax.scatter(px, py, s=TAMANO_PUNTO, marker="D",
                            color=COLORES["punto_prueba"],
                            edgecolors="#ffffff", linewidths=0.6,
                            alpha=0.85, zorder=4)
            self.ax.annotate(
                punto.etiqueta, xy=(px, py), xytext=(10, -14),
                textcoords="offset points",
                color=COLORES["punto_prueba"], fontsize=8,
                bbox=dict(boxstyle="round,pad=0.2",
                          fc=COLORES["fondo"], ec=COLORES["punto_prueba"],
                          alpha=0.8, linewidth=0.6),
                zorder=5
            )

    def _dibujar_vectores_fuerzas(self):
        if not self._carga_seleccionada_id:
            return
        objetivo = next((c for c in self.sistema.cargas
                         if c.id_carga == self._carga_seleccionada_id), None)
        if objetivo is None:
            return
        ox = objetivo.posicion[0]
        oy = objetivo.posicion[1] if len(objetivo.posicion) > 1 else 0.0

        todos_v = ([r.vector_fuerza for r in self._fuerzas_individuales]
                   + ([self._fuerza_neta] if self._fuerza_neta else []))
        escala = self._escala_vectores(todos_v)

        for r in self._fuerzas_individuales:
            v = r.vector_fuerza
            self._flecha(ox, oy, v.x*escala, v.y*escala,
                         COLORES["fuerza_ind"], 0.75, 1.5)

        if self._fuerza_neta and self._fuerza_neta.magnitud > 0:
            vn = self._fuerza_neta
            self._flecha(ox, oy, vn.x*escala, vn.y*escala,
                         COLORES["fuerza_neta"], 1.0, 2.5)

    def _dibujar_vectores_campo(self):
        if not self._campos:
            return
        escala = self._escala_vectores([r.vector_campo for r in self._campos])
        for resultado in self._campos:
            px = resultado.posicion[0]
            py = resultado.posicion[1] if len(resultado.posicion) > 1 else 0.0
            v  = resultado.vector_campo
            if v.magnitud < 1e-30:
                continue
            self._flecha(px, py, v.x*escala, v.y*escala,
                         COLORES["campo_e"], 0.9, 2.0)

    def _dibujar_leyenda(self):
        parches = []
        if any(c.es_positiva for c in self.sistema.cargas):
            parches.append(mpatches.Patch(color=COLORES["carga_pos"], label="Carga +"))
        if any(not c.es_positiva for c in self.sistema.cargas):
            parches.append(mpatches.Patch(color=COLORES["carga_neg"], label="Carga −"))
        if self.sistema.cargas:
            parches.append(mpatches.Patch(color=COLORES["quiver"], label="Mapa  E  [quiver]"))
        if self.sistema.puntos_prueba:
            parches.append(mpatches.Patch(color=COLORES["punto_prueba"], label="Punto de prueba"))
        if self._fuerzas_individuales:
            parches.append(mpatches.Patch(color=COLORES["fuerza_ind"], label="Fuerza individual [N]"))
        if self._fuerza_neta and self._fuerza_neta.magnitud > 0:
            parches.append(mpatches.Patch(color=COLORES["fuerza_neta"], label="Fuerza neta [N]"))
        if self._campos:
            parches.append(mpatches.Patch(color=COLORES["campo_e"], label="Campo E en puntos [N/C]"))

        if parches:
            self.ax.legend(
                handles=parches, loc="upper left", fontsize=7.5,
                framealpha=0.75, facecolor=COLORES["fondo_figura"],
                edgecolor=COLORES["ejes"], labelcolor=COLORES["texto"],
            )

    # ════════════════════════════════════════════
    #  UTILIDADES
    # ════════════════════════════════════════════

    def _flecha(self, x, y, dx, dy, color, alpha=1.0, lw=2.0):
        if abs(dx) < 1e-30 and abs(dy) < 1e-30:
            return
        self.ax.annotate(
            "", xy=(x+dx, y+dy), xytext=(x, y),
            arrowprops=dict(arrowstyle="-|>", color=color,
                            lw=lw, mutation_scale=14, alpha=alpha),
            zorder=3
        )

    def _escala_vectores(self, vectores: list) -> float:
        mags = [v.magnitud for v in vectores if v is not None and v.magnitud > 0]
        if not mags:
            return 1.0

        mag_max = max(mags)
        if mag_max < 1e-30:
            return 1.0

        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()

        rango_x = max(abs(xmax - xmin), 1e-9)
        rango_y = max(abs(ymax - ymin), 1e-9)

        if self.sistema.dimension == 1:
            longitud_deseada = rango_x * 0.12
        else:
            longitud_deseada = min(rango_x, rango_y) * 0.12

        return longitud_deseada / mag_max

    @staticmethod
    def _fmt(valor: float) -> str:
        if valor == 0:
            return "0"
        a = abs(valor)
        return f"{valor:.4g}" if 0.01 <= a < 10000 else f"{valor:.3e}"