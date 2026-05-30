"""
main.py — Punto de Entrada del Simulador de Electrostática
============================================================
Orquesta el arranque de la aplicación:
  1. Verifica dependencias mínimas (Python ≥ 3.11, tkinter, matplotlib, numpy).
  2. Aplica configuración global de Matplotlib para el estilo dark-mode.
  3. Lanza la ventana principal (VentanaPrincipal).

Uso:
    python main.py

Dependencias:
    - Python  >= 3.11
    - tkinter  (incluido en la stdlib; en Linux: python3-tk)
    - matplotlib >= 3.6
    - numpy   >= 1.23

Autor  : Simulador Universitario de Electrostática
Versión: 1.0.0
"""

import sys
import os

# ─────────────────────────────────────────────
#  VERIFICACIÓN DE DEPENDENCIAS
# ─────────────────────────────────────────────

def verificar_dependencias() -> None:
    """
    Comprueba que el entorno de ejecución sea compatible.
    Termina con un mensaje descriptivo si falta algo.
    """
    # Python 3.11+
    if sys.version_info < (3, 11):
        print(
            "ERROR: Este simulador requiere Python 3.11 o superior.\n"
            f"       Versión actual: {sys.version}\n"
            "       Actualiza Python en https://www.python.org/downloads/"
        )
        sys.exit(1)

    # tkinter
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print(
            "ERROR: tkinter no está disponible.\n"
            "       En Ubuntu/Debian: sudo apt-get install python3-tk\n"
            "       En Windows/macOS: viene incluido con Python oficial."
        )
        sys.exit(1)

    # matplotlib
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        print(
            "ERROR: matplotlib no está instalado.\n"
            "       Instala con: pip install matplotlib"
        )
        sys.exit(1)

    # numpy
    try:
        import numpy  # noqa: F401
    except ImportError:
        print(
            "ERROR: numpy no está instalado.\n"
            "       Instala con: pip install numpy"
        )
        sys.exit(1)


# ─────────────────────────────────────────────
#  CONFIGURACIÓN GLOBAL DE MATPLOTLIB
# ─────────────────────────────────────────────

def configurar_matplotlib() -> None:
    """
    Aplica el tema visual dark-mode a Matplotlib antes de crear cualquier figura.
    Esto asegura coherencia con la paleta de la GUI.
    """
    import matplotlib
    import matplotlib.pyplot as plt

    # Backend Tkinter (debe establecerse antes de importar pyplot)
    matplotlib.use("TkAgg")

    # Parámetros globales de estilo
    plt.rcParams.update({
        # Fuentes
        "font.family":          "DejaVu Sans",
        "font.size":            9,
        "axes.titlesize":       10,
        "axes.labelsize":       9,
        "xtick.labelsize":      8,
        "ytick.labelsize":      8,
        "legend.fontsize":      8,

        # Colores base
        "figure.facecolor":     "#141720",
        "axes.facecolor":       "#0f1117",
        "text.color":           "#c8cde4",
        "axes.labelcolor":      "#6b7194",
        "xtick.color":          "#6b7194",
        "ytick.color":          "#6b7194",
        "axes.edgecolor":       "#2a3050",
        "grid.color":           "#1e2230",
        "grid.linestyle":       "--",
        "grid.linewidth":       0.5,
        "grid.alpha":           0.7,

        # Líneas
        "axes.linewidth":       0.8,
        "lines.linewidth":      1.5,

        # Layout
        "figure.autolayout":    False,
        "axes.grid":            True,
    })


# ─────────────────────────────────────────────
#  FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────

def main() -> None:
    """Función de entrada principal."""

    # 1. Verificar dependencias
    verificar_dependencias()

    # 2. Configurar Matplotlib (antes de importar la GUI)
    configurar_matplotlib()

    # 3. Importar módulos de la aplicación
    #    (importación tardía para que matplotlib.use() ya esté activo)
    from gui import VentanaPrincipal

    # 4. Crear y lanzar la ventana principal
    app = VentanaPrincipal()

    # Centrar ventana en la pantalla
    app.update_idletasks()
    ancho = app.winfo_width()
    alto = app.winfo_height()
    ancho_pantalla = app.winfo_screenwidth()
    alto_pantalla = app.winfo_screenheight()
    x = (ancho_pantalla - ancho) // 2
    y = (alto_pantalla - alto) // 2
    app.geometry(f"{ancho}x{alto}+{x}+{y}")

    # 5. Iniciar el bucle de eventos de Tkinter
    app.mainloop()


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────

if __name__ == "__main__":
    main()