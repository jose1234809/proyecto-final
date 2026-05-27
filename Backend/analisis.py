from __future__ import annotations

from datetime import datetime

from .conexion import BaseDeDatos
from .registros_trm import RegistroTRM


class AnalisisTRM:
    """Calcula y guarda análisis de promedio, volatilidad y decisión."""

    def __init__(self, db: BaseDeDatos):
        self.db = db
        self.registros = RegistroTRM(db)

    def calcular(self, id_usuario: int, id_moneda: int) -> dict:
        resultado = self.registros.analizar_moneda(id_moneda)
        resultado["id_usuario"] = id_usuario
        resultado["fecha_calculo"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return resultado

    def guardar(self, resultado: dict) -> int:
        return self.db.ejecutar(
            """
            INSERT INTO analisis_trm(
                id_usuario, id_moneda, fecha_inicio, fecha_fin, promedio,
                volatilidad, minimo, maximo, ultima_tasa, decision, fecha_calculo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resultado["id_usuario"],
                resultado["id_moneda"],
                resultado["fecha_inicio"],
                resultado["fecha_fin"],
                resultado["promedio"],
                resultado["volatilidad"],
                resultado["minimo"],
                resultado["maximo"],
                resultado["ultima_tasa"],
                resultado["decision"],
                resultado["fecha_calculo"],
            ),
        )

    def listar(self):
        return self.db.consultar(
            """
            SELECT
                a.id_analisis,
                a.fecha_calculo,
                u.nombre AS usuario,
                m.simbolo AS moneda,
                a.fecha_inicio,
                a.fecha_fin,
                a.promedio,
                a.volatilidad,
                a.ultima_tasa,
                a.decision
            FROM analisis_trm a
            JOIN usuarios u ON u.id_usuario = a.id_usuario
            JOIN monedas m ON m.id_moneda = a.id_moneda
            ORDER BY a.id_analisis DESC
            """
        )
