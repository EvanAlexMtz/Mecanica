"""
model.py — Motor de Física Electrostática
==========================================
Contiene las clases fundamentales del simulador:
  - Vector:               Representación vectorial en 1D y 2D.
  - Carga:                Partícula cargada con posición y magnitud.
  - PuntosDePrueba:       Punto arbitrario para calcular campo eléctrico.
  - SistemaElectrostatico: Orquesta los cálculos de fuerza y campo.

Autor: Simulador Universitario de Electrostática
Constante de Coulomb: k = 8.99×10⁹ N·m²/C²
"""

import math
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────
#  CONSTANTES FÍSICAS
# ─────────────────────────────────────────────
K_COULOMB = 8.99e9          # N·m²/C²  — constante de Coulomb
DISTANCIA_MINIMA = 1e-12    # m        — umbral para evitar división por cero


# ─────────────────────────────────────────────
#  CLASE: Vector
# ─────────────────────────────────────────────
class Vector:
    """
    Representa un vector en 1D o 2D con sus componentes rectangulares.
    Permite suma, escalar y cálculo de magnitud/ángulo.
    """

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = float(x)
        self.y = float(y)

    # --- Operaciones vectoriales ---

    def __add__(self, otro: "Vector") -> "Vector":
        return Vector(self.x + otro.x, self.y + otro.y)

    def __sub__(self, otro: "Vector") -> "Vector":
        return Vector(self.x - otro.x, self.y - otro.y)

    def __mul__(self, escalar: float) -> "Vector":
        return Vector(self.x * escalar, self.y * escalar)

    def __rmul__(self, escalar: float) -> "Vector":
        return self.__mul__(escalar)

    def __neg__(self) -> "Vector":
        return Vector(-self.x, -self.y)

    def __repr__(self) -> str:
        return f"Vector(x={self.x:.4e}, y={self.y:.4e})"

    # --- Propiedades geométricas ---

    @property
    def magnitud(self) -> float:
        """Módulo del vector: |v| = √(x² + y²)."""
        return math.sqrt(self.x ** 2 + self.y ** 2)

    @property
    def angulo_grados(self) -> float:
        """Ángulo en grados respecto al eje +x (convenio estándar)."""
        return math.degrees(math.atan2(self.y, self.x))

    def unitario(self) -> "Vector":
        """Devuelve el vector unitario; retorna Vector(0,0) si magnitud ≈ 0."""
        mag = self.magnitud
        if mag < DISTANCIA_MINIMA:
            return Vector(0.0, 0.0)
        return Vector(self.x / mag, self.y / mag)

    @staticmethod
    def desde_posiciones(origen: tuple, destino: tuple) -> "Vector":
        """
        Crea un vector de desplazamiento desde 'origen' hasta 'destino'.
        Admite tuplas (x,) para 1D o (x, y) para 2D.
        """
        if len(origen) == 1:
            return Vector(destino[0] - origen[0], 0.0)
        return Vector(destino[0] - origen[0], destino[1] - origen[1])


# ─────────────────────────────────────────────
#  CLASE: Carga
# ─────────────────────────────────────────────
class Carga:
    """
    Representa una partícula cargada puntual en el espacio.

    Atributos:
        id_carga  : Identificador único (int).
        magnitud  : Valor con signo en Coulombs [C].
        posicion  : Tupla de coordenadas (x,) en 1D o (x, y) en 2D  [m].
        etiqueta  : Nombre descriptivo visible en la GUI.
    """

    _contador = 0  # contador global para IDs únicos

    def __init__(self, magnitud: float, posicion: tuple, etiqueta: str = ""):
        Carga._contador += 1
        self.id_carga: int = Carga._contador
        self.magnitud: float = float(magnitud)
        self.posicion: tuple = tuple(float(c) for c in posicion)
        self.etiqueta: str = etiqueta or f"q{self.id_carga}"

    @property
    def es_positiva(self) -> bool:
        return self.magnitud >= 0.0

    @property
    def signo_str(self) -> str:
        return "+" if self.es_positiva else "−"

    def __repr__(self) -> str:
        return (f"Carga(id={self.id_carga}, q={self.magnitud:.3e} C, "
                f"pos={self.posicion}, '{self.etiqueta}')")

    @staticmethod
    def resetear_contador():
        """Resetea el contador global de IDs (usar con cuidado)."""
        Carga._contador = 0


# ─────────────────────────────────────────────
#  CLASE: PuntoPrueba
# ─────────────────────────────────────────────
class PuntoPrueba:
    """
    Punto arbitrario en el espacio donde se evalúa el campo eléctrico.

    Atributos:
        id_punto : Identificador único.
        posicion : Coordenadas del punto [m].
        etiqueta : Nombre descriptivo.
    """

    _contador = 0

    def __init__(self, posicion: tuple, etiqueta: str = ""):
        PuntoPrueba._contador += 1
        self.id_punto: int = PuntoPrueba._contador
        self.posicion: tuple = tuple(float(c) for c in posicion)
        self.etiqueta: str = etiqueta or f"P{self.id_punto}"

    def __repr__(self) -> str:
        return f"PuntoPrueba(id={self.id_punto}, pos={self.posicion}, '{self.etiqueta}')"

    @staticmethod
    def resetear_contador():
        PuntoPrueba._contador = 0


# ─────────────────────────────────────────────
#  CLASE: ResultadoFuerza
# ─────────────────────────────────────────────
@dataclass
class ResultadoFuerza:
    """Encapsula el resultado de una fuerza entre dos cargas."""
    carga_fuente_id: int
    carga_objetivo_id: int
    vector_fuerza: Vector
    distancia: float

    @property
    def magnitud(self) -> float:
        return self.vector_fuerza.magnitud


# ─────────────────────────────────────────────
#  CLASE: ResultadoCampo
# ─────────────────────────────────────────────
@dataclass
class ResultadoCampo:
    """Encapsula el resultado del campo eléctrico en un punto de prueba."""
    punto_id: int
    posicion: tuple
    vector_campo: Vector
    contribuciones: list = field(default_factory=list)  # lista de (id_carga, Vector)

    @property
    def magnitud(self) -> float:
        return self.vector_campo.magnitud


# ─────────────────────────────────────────────
#  CLASE PRINCIPAL: SistemaElectrostatico
# ─────────────────────────────────────────────
class SistemaElectrostatico:
    """
    Motor de cálculo electrostático.

    Gestiona colecciones de cargas y puntos de prueba para una dimensión dada,
    implementando la Ley de Coulomb y el Principio de Superposición.

    Dimensiones soportadas: 1 (eje x) y 2 (plano xy).
    """

    def __init__(self, dimension: int = 2):
        self._validar_dimension(dimension)
        self.dimension: int = dimension
        self.cargas: list[Carga] = []
        self.puntos_prueba: list[PuntoPrueba] = []

    # ── Validaciones ──────────────────────────

    @staticmethod
    def _validar_dimension(d: int):
        if d not in (1, 2):
            raise ValueError(f"Dimensión '{d}' no soportada. Use 1 o 2.")

    def _validar_posicion(self, posicion: tuple):
        """Verifica que la posición tenga las coordenadas correctas."""
        n = len(posicion)
        if self.dimension == 1 and n != 1:
            raise ValueError("En 1D la posición debe tener exactamente 1 coordenada (x).")
        if self.dimension == 2 and n != 2:
            raise ValueError("En 2D la posición debe tener exactamente 2 coordenadas (x, y).")

    def _posicion_ocupada(self, posicion: tuple,
                          excluir_id: Optional[int] = None) -> Optional[Carga]:
        """
        Verifica si ya existe una carga en la posición dada (dentro de DISTANCIA_MINIMA).
        Devuelve la carga en conflicto o None.
        """
        for c in self.cargas:
            if c.id_carga == excluir_id:
                continue
            d = self._distancia(c.posicion, posicion)
            if d < DISTANCIA_MINIMA:
                return c
        return None

    @staticmethod
    def _distancia(pos_a: tuple, pos_b: tuple) -> float:
        """Distancia euclidiana entre dos posiciones."""
        return math.sqrt(sum((b - a) ** 2 for a, b in zip(pos_a, pos_b)))

    # ── Gestión de cargas ─────────────────────

    def agregar_carga(self, magnitud: float, posicion: tuple,
                      etiqueta: str = "") -> Carga:
        """
        Agrega una nueva carga al sistema.
        Lanza ValueError si la posición está ocupada o la posición es inválida.
        """
        self._validar_posicion(posicion)
        conflicto = self._posicion_ocupada(posicion)
        if conflicto:
            raise ValueError(
                f"Ya existe '{conflicto.etiqueta}' en la posición {posicion}. "
                "Dos cargas no pueden coincidir en el mismo punto."
            )
        carga = Carga(magnitud, posicion, etiqueta)
        self.cargas.append(carga)
        return carga

    def eliminar_carga(self, id_carga: int) -> bool:
        """Elimina una carga por su ID. Retorna True si fue encontrada."""
        antes = len(self.cargas)
        self.cargas = [c for c in self.cargas if c.id_carga != id_carga]
        return len(self.cargas) < antes

    # ── Gestión de puntos de prueba ───────────

    def agregar_punto_prueba(self, posicion: tuple, etiqueta: str = "") -> PuntoPrueba:
        """
        Agrega un punto de prueba al sistema.
        Lanza ValueError si coincide exactamente con una carga (evita indeterminación).
        """
        self._validar_posicion(posicion)
        for c in self.cargas:
            if self._distancia(c.posicion, posicion) < DISTANCIA_MINIMA:
                raise ValueError(
                    f"El punto de prueba coincide con la carga '{c.etiqueta}' "
                    f"en la posición {posicion}. El campo eléctrico diverge en ese punto."
                )
        punto = PuntoPrueba(posicion, etiqueta)
        self.puntos_prueba.append(punto)
        return punto

    def eliminar_punto_prueba(self, id_punto: int) -> bool:
        """Elimina un punto de prueba por su ID."""
        antes = len(self.puntos_prueba)
        self.puntos_prueba = [p for p in self.puntos_prueba if p.id_punto != id_punto]
        return len(self.puntos_prueba) < antes

    # ── Cálculos físicos ──────────────────────

    def calcular_fuerza_entre(self, carga_a: Carga,
                              carga_b: Carga) -> ResultadoFuerza:
        """
        Calcula la fuerza ejercida por 'carga_a' SOBRE 'carga_b' (Ley de Coulomb).

        F = k · q_a · q_b / r² · r̂_{a→b}

        Lanza ValueError si las cargas son la misma o están en el mismo punto.
        """
        if carga_a.id_carga == carga_b.id_carga:
            raise ValueError(
                "No se puede calcular la fuerza de una carga sobre sí misma."
            )
        r_vec = Vector.desde_posiciones(carga_a.posicion, carga_b.posicion)
        r = r_vec.magnitud

        if r < DISTANCIA_MINIMA:
            raise ValueError(
                f"Las cargas '{carga_a.etiqueta}' y '{carga_b.etiqueta}' "
                "están en el mismo punto. Distancia cero genera indeterminación."
            )

        magnitud_f = K_COULOMB * abs(carga_a.magnitud) * abs(carga_b.magnitud) / r ** 2
        # Signo: si mismo signo → repulsión (sentido a→b), opuesto → atracción (sentido b→a)
        signo = 1.0 if (carga_a.magnitud * carga_b.magnitud) > 0 else -1.0
        # La fuerza sobre b apunta en la dirección r̂_{a→b} si se repelen
        vector_f = r_vec.unitario() * (magnitud_f * signo)

        return ResultadoFuerza(
            carga_fuente_id=carga_a.id_carga,
            carga_objetivo_id=carga_b.id_carga,
            vector_fuerza=vector_f,
            distancia=r
        )

    def calcular_fuerza_neta(self, id_carga_objetivo: int
                             ) -> tuple[list[ResultadoFuerza], Vector]:
        """
        Calcula la fuerza neta sobre una carga usando el Principio de Superposición.

        Retorna (lista_de_fuerzas_individuales, vector_fuerza_neta).
        Lanza ValueError si la carga objetivo no existe o el sistema tiene < 2 cargas.
        """
        objetivo = next((c for c in self.cargas if c.id_carga == id_carga_objetivo), None)
        if objetivo is None:
            raise ValueError(f"No existe carga con id={id_carga_objetivo}.")
        if len(self.cargas) < 2:
            raise ValueError(
                "Se necesitan al menos 2 cargas para calcular una fuerza."
            )

        fuerzas = []
        neta = Vector(0.0, 0.0)

        for fuente in self.cargas:
            if fuente.id_carga == objetivo.id_carga:
                continue
            resultado = self.calcular_fuerza_entre(fuente, objetivo)
            fuerzas.append(resultado)
            neta = neta + resultado.vector_fuerza

        return fuerzas, neta

    def calcular_campo_en_punto(self, punto: PuntoPrueba) -> ResultadoCampo:
        """
        Calcula el campo eléctrico total en un punto de prueba (Superposición).

        E = Σ k · q_i / r_i² · r̂_i

        Lanza ValueError si el punto coincide con alguna carga.
        """
        if not self.cargas:
            raise ValueError("No hay cargas en el sistema para calcular el campo.")

        contribuciones = []
        campo_total = Vector(0.0, 0.0)

        for carga in self.cargas:
            r_vec = Vector.desde_posiciones(carga.posicion, punto.posicion)
            r = r_vec.magnitud

            if r < DISTANCIA_MINIMA:
                raise ValueError(
                    f"El punto '{punto.etiqueta}' coincide con la carga "
                    f"'{carga.etiqueta}'. El campo eléctrico diverge en ese punto."
                )

            # E apunta en r̂ si carga positiva, opuesto si negativa
            magnitud_e = K_COULOMB * abs(carga.magnitud) / r ** 2
            signo_e = 1.0 if carga.magnitud >= 0 else -1.0
            vector_e = r_vec.unitario() * (magnitud_e * signo_e)

            contribuciones.append((carga.id_carga, vector_e))
            campo_total = campo_total + vector_e

        return ResultadoCampo(
            punto_id=punto.id_punto,
            posicion=punto.posicion,
            vector_campo=campo_total,
            contribuciones=contribuciones
        )

    def calcular_todos_los_campos(self) -> list[ResultadoCampo]:
        """Calcula el campo eléctrico en todos los puntos de prueba registrados."""
        resultados = []
        for punto in self.puntos_prueba:
            try:
                resultados.append(self.calcular_campo_en_punto(punto))
            except ValueError:
                continue  # Puntos conflictivos se omiten silenciosamente en bulk
        return resultados

    # ── Estado del sistema ────────────────────

    def limpiar(self):
        """Elimina todas las cargas y puntos de prueba del sistema."""
        self.cargas.clear()
        self.puntos_prueba.clear()

    def resumen(self) -> str:
        """Devuelve un resumen legible del estado actual del sistema."""
        lineas = [f"=== Sistema {self.dimension}D ===",
                  f"Cargas ({len(self.cargas)}):"]
        for c in self.cargas:
            lineas.append(f"  {c.etiqueta}: q={c.magnitud:.3e} C  pos={c.posicion} m")
        lineas.append(f"Puntos de prueba ({len(self.puntos_prueba)}):")
        for p in self.puntos_prueba:
            lineas.append(f"  {p.etiqueta}: pos={p.posicion} m")
        return "\n".join(lineas)


# ─────────────────────────────────────────────
#  CLASE: EstadoSimulador  (para persistencia entre dimensiones)
# ─────────────────────────────────────────────
class EstadoSimulador:
    """
    Mantiene en memoria el estado independiente de cada dimensión (1D y 2D).
    Permite conmutar sin perder datos.
    """

    def __init__(self):
        # Un SistemaElectrostatico por dimensión
        self._sistemas: dict[int, SistemaElectrostatico] = {
            1: SistemaElectrostatico(dimension=1),
            2: SistemaElectrostatico(dimension=2),
        }
        self._dimension_activa: int = 2

    @property
    def dimension_activa(self) -> int:
        return self._dimension_activa

    @property
    def sistema_activo(self) -> SistemaElectrostatico:
        return self._sistemas[self._dimension_activa]

    def cambiar_dimension(self, nueva_dimension: int):
        """Cambia la dimensión activa conservando el estado de ambas."""
        if nueva_dimension not in (1, 2):
            raise ValueError(f"Dimensión inválida: {nueva_dimension}.")
        self._dimension_activa = nueva_dimension

    def sistema(self, dimension: int) -> SistemaElectrostatico:
        return self._sistemas[dimension]