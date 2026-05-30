"""
canvas.py — Motor de Visualización Electrostática
===================================================
Gestiona la representación gráfica interactiva usando Matplotlib embebido en Tkinter.

Responsabilidades:
  - Renderizar cargas con diferenciación visual por signo.
  - Dibujar vectores de fuerza individuales y fuerza neta.
  - Mostrar vectores de campo eléctrico en puntos de prueba.
  - Mantener un aspecto científico (dark mode, ejes rotulados con unidades físicas).
  - Adaptarse dinámicamente entre el modo 1D y 2D.

Paleta de colores (dark mode científico):
  Fondo canvas   : #0f1117
  Ejes / grid    : #2a2d3e
  Cargas +       : #e05c5c  (rojo coral)
  Cargas −       : #5c9ee0  (azul acero)
  Fuerza indiv.  : #f0c040  (ámbar)
  Fuerza neta    : #50e896  (verde esmeralda)
  Campo eléctrico: #c97af5  (violeta)
  Puntos prueba  : #78dce8  (cian)
"""

import math
import tkinter as tk
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch
from model import (
    SistemaElectrostatico, Carga, PuntoPrueba,
    ResultadoFuerza, ResultadoCampo, Vector, K_COULOMB
)

# El backend TkAgg se establece en main.py antes de importar pyplot.
# Aquí sólo lo importamos si Tk está disponible.
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    FigureCanvasTkAgg = None

# ─────────────────────────────────────────────
#  PALETA DE COLORES
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
}

TAMANO_CARGA = 180           # puntos² para scatter
TAMANO_PUNTO = 80
ESCALA_FLECHA_AUTO = True    # auto-escalar vectores para visibilidad


class CanvasElectrostatico:
    """
    Widget de visualización. Se embebe dentro de un Frame de Tkinter.

    Expone métodos para:
      - actualizar(): Re-renderiza todo según el estado del sistema.
      - set_carga_seleccionada(): Resalta una carga específica.
    """

    def __init__(self, parent_frame: tk.Frame, sistema: SistemaElectrostatico):
        self.parent = parent_frame
        self.sistema = sistema

        # Carga cuyas fuerzas se visualizan actualmente
        self._carga_seleccionada_id: int | None = None
        # Resultados de último cálculo (para redibujar sin recalcular)
        self._fuerzas_individuales: list[ResultadoFuerza] = []
        self._fuerza_neta: Vector | None = None
        self._campos: list[ResultadoCampo] = []

        self._construir_figura()

    # ── Construcción de figura ────────────────

    def _construir_figura(self):
        """Inicializa la figura Matplotlib con estilo dark-mode científico."""
        self.fig = Figure(figsize=(7, 6), dpi=100, facecolor=COLORES["fondo_figura"])
        self.ax = self.fig.add_subplot(111, facecolor=COLORES["fondo"])
        self._estilizar_ejes()

        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.fig.tight_layout(pad=1.5)
        self._renderizar_vacio()

    def _estilizar_ejes(self):
        """Aplica la paleta dark-mode y etiquetas con unidades físicas."""
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
        # Marca el origen
        ax.plot(0, 0, "o", color=COLORES["ejes"], markersize=3, zorder=1)

    def _renderizar_vacio(self):
        """Muestra pantalla vacía con mensaje orientativo."""
        self.ax.text(
            0.5, 0.5,
            "Agrega cargas al sistema\npara visualizar el campo",
            transform=self.ax.transAxes,
            ha="center", va="center",
            color=COLORES["texto_dim"], fontsize=11,
            fontstyle="italic"
        )
        self.canvas_widget.draw()

    # ── API pública ───────────────────────────

    def set_sistema(self, sistema: SistemaElectrostatico):
        """Asocia un nuevo sistema (p.ej. al cambiar de dimensión)."""
        self.sistema = sistema
        self._carga_seleccionada_id = None
        self._fuerzas_individuales = []
        self._fuerza_neta = None
        self._campos = []

    def set_carga_seleccionada(self, id_carga: int | None):
        """Define la carga que se resaltará y cuyos vectores se mostrarán."""
        self._carga_seleccionada_id = id_carga

    def set_resultados(self, fuerzas: list[ResultadoFuerza],
                       neta: Vector | None,
                       campos: list[ResultadoCampo]):
        """Almacena los resultados de cálculo para el próximo render."""
        self._fuerzas_individuales = fuerzas
        self._fuerza_neta = neta
        self._campos = campos

    def actualizar(self):
        """Re-renderiza todo el canvas con el estado actual del sistema."""
        self.ax.cla()
        self._estilizar_ejes()

        dim = self.sistema.dimension

        # Ajustar título según dimensión
        titulo = f"Simulador Electrostático  —  Modo {'1D  (eje x)' if dim == 1 else '2D  (plano xy)'}"
        self.ax.set_title(titulo, color=COLORES["texto"], fontsize=10, pad=8,
                          fontweight="bold")

        if not self.sistema.cargas and not self.sistema.puntos_prueba:
            self._renderizar_vacio()
            return

        # Calcular límites del plot dinámicamente
        limites = self._calcular_limites()

        # Renderizar en orden (capas)
        self._dibujar_puntos_prueba()
        self._dibujar_vectores_campo()
        self._dibujar_vectores_fuerzas()
        self._dibujar_cargas()
        self._dibujar_leyenda()

        # Aplicar límites
        self.ax.set_xlim(limites["xmin"], limites["xmax"])
        if dim == 2:
            self.ax.set_ylim(limites["ymin"], limites["ymax"])
        else:
            # En 1D comprimimos el eje y
            self.ax.set_ylim(-1.2, 1.2)
            self.ax.set_ylabel("")
            self.ax.set_yticks([])
            self.ax.axhline(0, color=COLORES["ejes"], linewidth=1.5)

        self.fig.tight_layout(pad=1.5)
        self.canvas_widget.draw()

    # ── Cálculo de límites ────────────────────

    def _calcular_limites(self) -> dict:
        """Calcula límites automáticos con margen para no recortar vectores."""
        posiciones_x = []
        posiciones_y = []

        for c in self.sistema.cargas:
            posiciones_x.append(c.posicion[0])
            posiciones_y.append(c.posicion[1] if len(c.posicion) > 1 else 0.0)
        for p in self.sistema.puntos_prueba:
            posiciones_x.append(p.posicion[0])
            posiciones_y.append(p.posicion[1] if len(p.posicion) > 1 else 0.0)

        if not posiciones_x:
            return {"xmin": -5, "xmax": 5, "ymin": -5, "ymax": 5}

        cx, cy = min(posiciones_x), min(posiciones_y)
        mx, my = max(posiciones_x), max(posiciones_y)

        rango_x = max(mx - cx, 1.0)
        rango_y = max(my - cy, 1.0)
        margen_x = rango_x * 0.45
        margen_y = rango_y * 0.45

        return {
            "xmin": cx - margen_x,
            "xmax": mx + margen_x,
            "ymin": cy - margen_y,
            "ymax": my + margen_y,
        }

    # ── Renderizado de cargas ──────────────────

    def _dibujar_cargas(self):
        """Dibuja cada carga como un círculo con su signo y etiqueta."""
        for carga in self.sistema.cargas:
            pos_x = carga.posicion[0]
            pos_y = carga.posicion[1] if len(carga.posicion) > 1 else 0.0

            color_base = COLORES["carga_pos"] if carga.es_positiva else COLORES["carga_neg"]
            color_glow = COLORES["carga_pos_glow"] if carga.es_positiva else COLORES["carga_neg_glow"]
            es_sel = (carga.id_carga == self._carga_seleccionada_id)

            # Halo de selección
            if es_sel:
                self.ax.scatter(pos_x, pos_y,
                                s=TAMANO_CARGA * 2.8,
                                color=color_glow, alpha=0.25, zorder=4)

            # Círculo principal
            self.ax.scatter(pos_x, pos_y,
                            s=TAMANO_CARGA,
                            color=color_base,
                            edgecolors="#ffffff" if es_sel else color_glow,
                            linewidths=2.0 if es_sel else 0.8,
                            zorder=5)

            # Signo de la carga (+ o −)
            signo = "+" if carga.es_positiva else "−"
            self.ax.text(pos_x, pos_y, signo,
                         ha="center", va="center",
                         fontsize=10, fontweight="bold",
                         color="#ffffff", zorder=6)

            # Etiqueta con magnitud
            mag_str = self._formato_magnitud(carga.magnitud)
            self.ax.annotate(
                f"{carga.etiqueta}\n{mag_str} C",
                xy=(pos_x, pos_y), xytext=(12, 12),
                textcoords="offset points",
                color=color_glow, fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3",
                          fc=COLORES["fondo"], ec=color_base,
                          alpha=0.85, linewidth=0.8),
                zorder=7
            )

    # ── Renderizado de puntos de prueba ───────

    def _dibujar_puntos_prueba(self):
        """Dibuja los puntos de prueba como marcadores distintos."""
        for punto in self.sistema.puntos_prueba:
            pos_x = punto.posicion[0]
            pos_y = punto.posicion[1] if len(punto.posicion) > 1 else 0.0

            self.ax.scatter(pos_x, pos_y,
                            s=TAMANO_PUNTO,
                            marker="D",
                            color=COLORES["punto_prueba"],
                            edgecolors="#ffffff",
                            linewidths=0.6,
                            alpha=0.85, zorder=4)

            self.ax.annotate(
                punto.etiqueta,
                xy=(pos_x, pos_y), xytext=(10, -14),
                textcoords="offset points",
                color=COLORES["punto_prueba"], fontsize=8,
                bbox=dict(boxstyle="round,pad=0.2",
                          fc=COLORES["fondo"],
                          ec=COLORES["punto_prueba"],
                          alpha=0.8, linewidth=0.6),
                zorder=5
            )

    # ── Renderizado de vectores de fuerza ─────

    def _dibujar_vectores_fuerzas(self):
        """Dibuja flechas de fuerzas individuales y la fuerza neta."""
        if not self._carga_seleccionada_id:
            return

        objetivo = next((c for c in self.sistema.cargas
                         if c.id_carga == self._carga_seleccionada_id), None)
        if objetivo is None:
            return

        ox = objetivo.posicion[0]
        oy = objetivo.posicion[1] if len(objetivo.posicion) > 1 else 0.0

        # Escala adaptativa para las flechas
        escala = self._calcular_escala_vectores(
            [r.vector_fuerza for r in self._fuerzas_individuales]
            + ([self._fuerza_neta] if self._fuerza_neta else [])
        )

        # Fuerzas individuales
        for resultado in self._fuerzas_individuales:
            v = resultado.vector_fuerza
            self._dibujar_flecha(
                ox, oy,
                v.x * escala, v.y * escala,
                color=COLORES["fuerza_ind"],
                alpha=0.75,
                linewidth=1.5,
                label="_fuerza_ind"
            )

        # Fuerza neta
        if self._fuerza_neta and self._fuerza_neta.magnitud > 0:
            vn = self._fuerza_neta
            self._dibujar_flecha(
                ox, oy,
                vn.x * escala, vn.y * escala,
                color=COLORES["fuerza_neta"],
                alpha=1.0,
                linewidth=2.5,
                label="_fuerza_neta"
            )

    # ── Renderizado de campo eléctrico ────────

    def _dibujar_vectores_campo(self):
        """Dibuja vectores del campo eléctrico en los puntos de prueba."""
        if not self._campos:
            return

        escala = self._calcular_escala_vectores(
            [r.vector_campo for r in self._campos]
        )

        for resultado in self._campos:
            pos_x = resultado.posicion[0]
            pos_y = resultado.posicion[1] if len(resultado.posicion) > 1 else 0.0
            v = resultado.vector_campo
            if v.magnitud < 1e-30:
                continue
            self._dibujar_flecha(
                pos_x, pos_y,
                v.x * escala, v.y * escala,
                color=COLORES["campo_e"],
                alpha=0.9,
                linewidth=2.0,
                label="_campo"
            )

    # ── Utilidades de dibujo ──────────────────

    def _dibujar_flecha(self, x, y, dx, dy,
                        color, alpha=1.0, linewidth=2.0, label=""):
        """Dibuja una flecha estilizada desde (x,y) en dirección (dx,dy)."""
        if abs(dx) < 1e-30 and abs(dy) < 1e-30:
            return
        self.ax.annotate(
            "", xy=(x + dx, y + dy), xytext=(x, y),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=linewidth,
                mutation_scale=14,
                alpha=alpha,
            ),
            zorder=3,
            label=label
        )

    def _calcular_escala_vectores(self, vectores: list[Vector]) -> float:
        """
        Calcula un factor de escala para que las flechas sean visibles
        pero no dominen el plot. Basado en el rango espacial del sistema.
        """
        if not vectores:
            return 1.0

        mags = [v.magnitud for v in vectores if v.magnitud > 0]
        if not mags:
            return 1.0

        mag_max = max(mags)
        if mag_max < 1e-30:
            return 1.0

        # Rango espacial del sistema
        posiciones_x = [c.posicion[0] for c in self.sistema.cargas]
        rango_x = max(posiciones_x) - min(posiciones_x) if len(posiciones_x) > 1 else 1.0
        rango_x = max(rango_x, 1.0)

        # Queremos que la flecha más larga mida ~20% del rango espacial
        return (rango_x * 0.20) / mag_max

    # ── Leyenda ───────────────────────────────

    def _dibujar_leyenda(self):
        """Añade una leyenda compacta al canvas."""
        parches = []
        if any(c.es_positiva for c in self.sistema.cargas):
            parches.append(mpatches.Patch(color=COLORES["carga_pos"], label="Carga +"))
        if any(not c.es_positiva for c in self.sistema.cargas):
            parches.append(mpatches.Patch(color=COLORES["carga_neg"], label="Carga −"))
        if self.sistema.puntos_prueba:
            parches.append(mpatches.Patch(color=COLORES["punto_prueba"], label="Punto de prueba"))
        if self._fuerzas_individuales:
            parches.append(mpatches.Patch(color=COLORES["fuerza_ind"], label="Fuerza individual  [N]"))
        if self._fuerza_neta and self._fuerza_neta.magnitud > 0:
            parches.append(mpatches.Patch(color=COLORES["fuerza_neta"], label="Fuerza neta  [N]"))
        if self._campos:
            parches.append(mpatches.Patch(color=COLORES["campo_e"], label="Campo eléctrico  [N/C]"))

        if parches:
            leg = self.ax.legend(
                handles=parches,
                loc="upper left",
                fontsize=7.5,
                framealpha=0.75,
                facecolor=COLORES["fondo_figura"],
                edgecolor=COLORES["ejes"],
                labelcolor=COLORES["texto"],
            )

    # ── Utilidades de formato ──────────────────

    @staticmethod
    def _formato_magnitud(valor: float) -> str:
        """Formatea un número con notación científica si es muy grande/pequeño."""
        if valor == 0:
            return "0"
        abs_v = abs(valor)
        if 0.01 <= abs_v < 10000:
            return f"{valor:.4g}"
        return f"{valor:.3e}"