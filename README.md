# ⚡ Simulador Computacional de Electrostática
## Cargas, Fuerzas y Campos Eléctricos

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.6%2B-11557C?style=for-the-badge)
![NumPy](https://img.shields.io/badge/NumPy-1.23%2B-013243?style=for-the-badge&logo=numpy&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-4a7cdc?style=for-the-badge)
![License](https://img.shields.io/badge/Licencia-MIT-50e896?style=for-the-badge)

</div>

---

## 👥 Información del Equipo

| Campo | Detalle |
|---|---|
| **Asignatura** | Mecánica y Electromagnetismo |
| **Carrera** | Ingeniería en Sistemas Computacionales |
| **Institución** | Intituto Politéctico Nacional ESCOM |
| **Periodo** | 2026 Semestre II. |

### Integrantes del Equipo

| # | Nombre Completo | Boleta |
|---|---|---|
| 1 | Martínez Maciel Evan Alexander | 2026630112 |
| 2 | Delgado Andrade Cristian Antonio | 2026630229 |
| 3 | Hernandez Elizalde Yael | 2026630088 |

---

## 📋 Descripción del Simulador

Este proyecto es una **aplicación de escritorio interactiva** construida en Python que permite simular y visualizar en tiempo real los fenómenos electrostáticos fundamentales: la fuerza entre cargas puntuales (Ley de Coulomb) y el campo eléctrico generado por distribuciones de carga arbitrarias, tanto en **entornos 1D como 2D**.

### ✨ Características Principales

- **Simulación dual 1D / 2D** — Cambia entre una dimensión (eje x) y dos dimensiones (plano xy) en cualquier momento sin perder ningún dato. La clase `EstadoSimulador` mantiene un `SistemaElectrostatico` independiente por cada dimensión, permitiendo conmutar con total persistencia de estado.

- **Mapa dinámico de vectores de campo (Quiver Plot)** — Al agregar cargas, el lienzo genera automáticamente un mapa de flechas sobre una cuadrícula de 18×18 puntos (configurable vía `QUIVER_GRID`) que muestra la dirección e intensidad del campo eléctrico en todo el plano visible. La intensidad de cada flecha se atenúa en función de la distancia a las cargas para mayor claridad visual.

- **Sistema interactivo Drag & Drop** — Las cargas y los puntos de prueba pueden arrastrarse directamente con el mouse sobre el lienzo. La actualización de los cálculos de fuerza y campo es **diferida al evento Mouse Release** (`on_drag_released` / `on_point_drag_released`), evitando cálculos costosos durante el movimiento continuo y optimizando el rendimiento de renderizado.

- **Interfaz oscura profesional** — Diseño visual dark-mode coherente en todos los componentes, implementado mediante una paleta de colores centralizada (`COLORES` en `canvas.py`, `PALETA` en `gui.py`) y configuración global de Matplotlib en `main.py`.

- **Validaciones físicas robustas** — El motor previene automáticamente la división por cero, el solapamiento de cargas en la misma coordenada, y la evaluación del campo en el punto exacto de una carga (donde diverge), lanzando excepciones descriptivas con umbral `DISTANCIA_MINIMA = 1e-12 m`.

---

## 🛠️ Tecnologías y Librerías Utilizadas

| Tecnología | Versión Mínima | Rol en el Proyecto |
|---|---|---|
| **Python** | 3.11+ | Lenguaje base; se aprovechan anotaciones de tipos modernas (`list[T]`, `int \| None`) y `dataclasses` |
| **tkinter / ttk** | stdlib | Construcción de la GUI principal: ventana, paneles, formularios, `Listbox`, `Scrollbar`, barra de estado y sistema de botones con efectos hover |
| **matplotlib** | 3.6+ | Motor de renderizado del lienzo físico interactivo embebido con `FigureCanvasTkAgg`; flechas vectoriales (`annotate`), scatter plots de cargas, quiver plots del campo y toolbar de navegación personalizada |
| **numpy** | 1.23+ | Generación eficiente de la rejilla de puntos (`np.linspace`, `np.meshgrid`) para el mapa de campo eléctrico y normalización vectorial de las flechas del quiver |
| **math** | stdlib | Cálculos escalares de magnitud (`sqrt`), ángulo director (`atan2`, `degrees`) y operaciones geométricas en la clase `Vector` |

---

## 📦 Instalación y Ejecución

### Prerequisitos

Asegúrate de tener **Python 3.11 o superior** instalado. Puedes verificarlo con:

```bash
python --version
```

### Paso 1 — Clonar o descargar el repositorio

```bash
git clone https://github.com/tu-usuario/simulador-electrostatica.git
cd simulador-electrostatica
```

O bien, si descargaste el ZIP, extrae los archivos y abre una terminal en la carpeta del proyecto.

### Paso 2 — Crear y activar un entorno virtual *(recomendado)*

```bash
# Crear el entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en macOS / Linux
source venv/bin/activate
```

### Paso 3 — Instalar las dependencias

```bash
pip install matplotlib numpy
```

> **Nota para Linux:** Si `tkinter` no está disponible, instálalo con:
> ```bash
> sudo apt-get install python3-tk
> ```

### Paso 4 — Ejecutar la aplicación

```bash
python main.py
```

El programa verificará automáticamente todas las dependencias al inicio y mostrará un mensaje descriptivo si falta alguna.

---

## 🧮 Fundamentos Físicos y Cálculos Implementados

El motor de física se encuentra íntegramente en `model.py` y trabaja con la siguiente constante de Coulomb:

$$k = 8.99 \times 10^9 \ \text{N} \cdot \text{m}^2 / \text{C}^2$$

### 1. Ley de Coulomb — Fuerza entre dos cargas

La magnitud de la fuerza electrostática entre dos cargas puntuales $q_a$ y $q_b$ separadas una distancia $r$ es:

$$F = k \cdot \frac{|q_a \cdot q_b|}{r^2}$$

Vectorialmente, la fuerza ejercida por $q_a$ **sobre** $q_b$ se calcula preservando el signo del producto de cargas (positivo → repulsión, negativo → atracción):

$$\vec{F}_{ab} = k \cdot \frac{q_a \cdot q_b}{r^2} \cdot \hat{r}_{ab}$$

donde $\hat{r}_{ab}$ es el vector unitario que apunta desde $q_a$ hacia $q_b$, implementado en `Vector.unitario()`.

### 2. Descomposición Vectorial y Ángulos Directores

Cada fuerza o campo se descompone en componentes rectangulares para operar con la clase `Vector`:

$$F_x = F \cdot \cos(\theta), \qquad F_y = F \cdot \sin(\theta)$$

El ángulo director respecto al eje $+x$ se obtiene con la función `angulo_grados`:

$$\theta = \arctan\!\left(\frac{F_y}{F_x}\right) \quad \text{[implementado con } \texttt{math.atan2}\text{]}$$

La magnitud del vector resultante es:

$$|\vec{F}| = \sqrt{F_x^2 + F_y^2}$$

### 3. Principio de Superposición — Fuerza Neta

La fuerza neta sobre una carga objetivo $q_j$ debida a $n-1$ cargas fuente es la suma vectorial de todas las fuerzas individuales (método `calcular_fuerza_neta`):

$$\vec{F}_{\text{neta}} = \sum_{\substack{i=1 \\ i \neq j}}^{n} \vec{F}_{ij} = \sum_{\substack{i=1 \\ i \neq j}}^{n} k \cdot \frac{q_i \cdot q_j}{r_{ij}^2} \cdot \hat{r}_{ij}$$

### 4. Campo Eléctrico Total — Superposición en Puntos de Prueba

El campo eléctrico total en un punto de prueba $P$ generado por $n$ cargas es (método `calcular_campo_en_punto`):

$$\vec{E}_{\text{total}}(P) = \sum_{i=1}^{n} \vec{E}_i = \sum_{i=1}^{n} k \cdot \frac{q_i}{r_i^2} \cdot \hat{r}_i$$

donde $r_i$ es la distancia desde la carga $q_i$ hasta el punto $P$, y $\hat{r}_i$ apunta desde $q_i$ hacia $P$. El signo de $q_i$ determina automáticamente la dirección: campo saliente para cargas positivas, entrante para negativas.

### 5. Protección contra Singularidades

Para evitar la división por cero cuando dos entidades coinciden en el mismo punto, el sistema aplica el umbral:

$$r_{\min} = 10^{-12} \ \text{m}$$

Si $r < r_{\min}$, se lanza una excepción `ValueError` con un mensaje descriptivo antes de ejecutar cualquier cálculo.

---

## 🗂️ Arquitectura Modular del Proyecto

El proyecto sigue el patrón de diseño **MVC (Modelo–Vista–Controlador)** con separación clara de responsabilidades, implementado en cuatro módulos con Programación Orientada a Objetos (POO):

```
simulador-electrostatica/
│
├── main.py        ← Orquestador y punto de entrada
├── model.py       ← Motor de física (Modelo)
├── canvas.py      ← Lienzo gráfico interactivo (Vista)
├── gui.py         ← Interfaz y controlador de eventos (Vista + Controlador)
└── README.md
```

### `model.py` — Motor de Física

Contiene el núcleo matemático y de datos del simulador. No depende de ninguna librería gráfica.

| Clase | Responsabilidad |
|---|---|
| `Vector` | Aritmética vectorial 1D/2D: suma, escala, magnitud, ángulo director, vector unitario |
| `Carga` | Partícula cargada con ID único, magnitud con signo [C], posición [m] y etiqueta descriptiva |
| `PuntoPrueba` | Punto arbitrario en el espacio para evaluación del campo eléctrico |
| `ResultadoFuerza` | Dataclass que encapsula la fuerza entre un par de cargas y la distancia entre ellas |
| `ResultadoCampo` | Dataclass que encapsula el campo total en un punto y las contribuciones individuales por carga |
| `SistemaElectrostatico` | Motor principal: gestiona colecciones de cargas/puntos, valida posiciones y ejecuta los cálculos de Coulomb y superposición |
| `EstadoSimulador` | Mantiene instancias independientes de `SistemaElectrostatico` para 1D y 2D, habilitando la persistencia al cambiar de dimensión |

### `canvas.py` — Lienzo Gráfico Interactivo

Gestiona toda la visualización mediante Matplotlib embebido en el frame de Tkinter.

- **`CanvasElectrostatico`**: Widget principal que contiene la figura, los ejes estilizados y la toolbar de navegación personalizada (`NavigationToolbarSinZoom`).
- Gestión de eventos del mouse: clic para seleccionar (`_drag_carga`, `_drag_punto`), movimiento continuo para arrastrar y liberación (`on_drag_released`, `on_point_drag_released`) para recalcular con actualización diferida.
- Renderizado de cargas con halos de glow, puntos de prueba con marcador diamante, vectores de fuerza individuales (amarillo) y fuerza neta (verde), vectores de campo eléctrico en puntos de prueba (violeta) y quiver automático del campo sobre toda la vista.
- Funciones de zoom: `acercar_vista()` y `alejar_vista()` con recálculo del quiver tras el reencuadre.

### `gui.py` — Interfaz de Usuario y Controlador

Implementa la ventana principal `VentanaPrincipal` y sus subpaneles.

- **`PanelControl`**: Formularios de entrada con validación numérica para agregar cargas (etiqueta, magnitud, posición x/y) y puntos de prueba; listas con scrollbar que muestran posiciones en tiempo real tras el arrastre.
- **`PanelResultados`**: Tablas de resultados numéricos para fuerzas individuales, fuerza neta (magnitud, componentes, ángulo) y campo eléctrico por punto de prueba.
- **`BarraEstado`**: Indicador visual con tres niveles: `exito()` (verde), `alerta()` (amarillo) y `error()` (rojo).
- **`VentanaPrincipal`**: Controlador central; inyecta los callbacks `on_drag_released` / `on_point_drag_released` en `CanvasElectrostatico` y orquesta las acciones del usuario: `agregar_carga()`, `eliminar_carga()`, `calcular_fuerzas()`, `calcular_campos()`, `cambiar_dimension()` y `limpiar_sistema()`.

### `main.py` — Orquestador y Punto de Entrada

Ejecuta tres pasos secuenciales antes de lanzar la GUI:

1. `verificar_dependencias()` — Comprueba Python ≥ 3.11, tkinter, matplotlib y numpy, terminando con mensaje descriptivo si falta algo.
2. `configurar_matplotlib()` — Aplica el tema dark-mode global (`plt.rcParams`) y fija el backend `TkAgg` antes de cualquier importación de pyplot.
3. Importación tardía de `VentanaPrincipal` y centrado automático de la ventana en pantalla.

---

## 🖼️ Ejemplos de Uso y Visualizaciones

### Vista 1 — Modo 1D: Dos cargas en el eje x

Al iniciar la aplicación en modo 1D, el usuario verá el eje horizontal con dos cargas representadas como círculos (rojo = positiva, azul = negativa). Las flechas amarillas muestran las fuerzas individuales que actúa cada carga sobre la seleccionada, y la flecha verde más gruesa indica la fuerza neta resultante. La tabla de resultados a la derecha desglosa $F_x$, $|F|$ y el ángulo $\theta$.

```
📸 [Captura: simulador_1D_dos_cargas.png]
   Descripción: carga q1 (+2μC) en x=0 m y q2 (−1μC) en x=3 m,
   con vector de fuerza neta verde apuntando hacia q2.
```

### Vista 2 — Modo 2D: Múltiples cargas con mapa de campo

En modo 2D con tres o más cargas, el lienzo muestra el **quiver plot** automático: una cuadrícula de flechas violetas que cubre todo el plano visible e ilustra la dirección y magnitud relativa del campo eléctrico total en cada punto. Al soltar una carga arrastrada, el mapa se recalcula instantáneamente y las tablas de la derecha se actualizan.

```
📸 [Captura: simulador_2D_quiver.png]
   Descripción: tres cargas dispuestas en triángulo con el mapa de
   vectores de campo E visible en el plano, y un punto de prueba P1
   con su vector de campo en violeta brillante.
```

### Vista 3 — Drag & Drop y actualización en vivo

Al arrastrar una carga con el mouse, ésta se mueve visualmente con un halo ampliado (glow) mientras el quiver permanece estático para mantener fluidez. Al soltar el botón del mouse, el sistema ejecuta `on_drag_released(id_carga)`, recalcula todas las fuerzas y campos, y actualiza simultáneamente el lienzo y las tablas de resultados.

```
📸 [Captura: simulador_drag_drop.png]
   Descripción: carga q2 siendo arrastrada a nueva posición,
   mostrando halo de selección blanco y posición actualizada
   en la lista de cargas del panel de control.
```

---

## 🔬 Flujo de Trabajo Típico

```
1. Seleccionar dimensión (1D / 2D) con el selector de la GUI
         ↓
2. Agregar cargas: etiqueta + magnitud [C] + posición [m]
         ↓
3. (Opcional) Arrastrar cargas con el mouse para reposicionarlas
         ↓
4. Seleccionar una carga en la lista → clic en "Calcular fuerzas"
         ↓   ← Fuerza neta + componentes + ángulo en la tabla
5. Agregar puntos de prueba → clic en "Calcular campos"
         ↓   ← Campo E en cada punto + mapa quiver actualizado
6. Cambiar a la otra dimensión (el estado de esta queda guardado)
```

---

## 📐 Constantes y Parámetros de Configuración

| Parámetro | Valor | Archivo | Descripción |
|---|---|---|---|
| `K_COULOMB` | $8.99 \times 10^9$ N·m²/C² | `model.py` | Constante de Coulomb |
| `DISTANCIA_MINIMA` | $10^{-12}$ m | `model.py` | Umbral anti-singularidad |
| `QUIVER_GRID` | 18 | `canvas.py` | Resolución NxN del mapa de campo |
| `RADIO_CLICK` | 0.08 | `canvas.py` | Fracción del rango visible para seleccionar con clic |
| `TAMANO_CARGA` | 180 | `canvas.py` | Tamaño del marcador de carga en scatter |
| `TAMANO_PUNTO` | 80 | `canvas.py` | Tamaño del marcador de punto de prueba |

---

<div align="center">

**Simulador Universitario de Electrostática · v2.0.0**  
_Desarrollado con Python, Matplotlib y NumPy_

</div>
