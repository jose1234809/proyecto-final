from __future__ import annotations

import sqlite3
from statistics import mean, pstdev

from .conexion import BaseDeDatos


class RegistroTRM:
    """CRUD y lógica de negocio para registros diarios de TRM/tasa."""

    def __init__(self, db: BaseDeDatos):
        self.db = db

    def crear(self, fecha: str, id_moneda: int, valor: float, id_usuario: int) -> int:
        if valor <= 0:
            raise ValueError("La TRM/tasa debe ser mayor que cero.")
        return self.db.ejecutar(
            """
            INSERT INTO registros_trm(fecha, id_moneda, valor, id_usuario)
            VALUES (?, ?, ?, ?)
            """,
            (fecha, id_moneda, valor, id_usuario),
        )

    def listar(self) -> list[sqlite3.Row]:
        return self.db.consultar(
            """
            SELECT
                r.id_registro,
                r.fecha,
                r.id_moneda,
                m.simbolo AS moneda,
                m.nombre AS nombre_moneda,
                r.valor,
                r.id_usuario,
                u.nombre AS usuario,
                u.rol AS rol_usuario
            FROM registros_trm r
            JOIN monedas m ON m.id_moneda = r.id_moneda
            JOIN usuarios u ON u.id_usuario = r.id_usuario
            ORDER BY r.fecha ASC, r.id_registro ASC
            """
        )

    def listar_por_moneda(self, id_moneda: int) -> list[sqlite3.Row]:
        return self.db.consultar(
            """
            SELECT *
            FROM registros_trm
            WHERE id_moneda = ?
            ORDER BY fecha ASC, id_registro ASC
            """,
            (id_moneda,),
        )

    def obtener(self, id_registro: int) -> sqlite3.Row | None:
        return self.db.consultar_uno("SELECT * FROM registros_trm WHERE id_registro = ?", (id_registro,))

    def actualizar(self, id_registro: int, fecha: str, id_moneda: int, valor: float, id_usuario: int) -> None:
        if not self.obtener(id_registro):
            raise ValueError("No existe un registro con ese ID.")
        if valor <= 0:
            raise ValueError("La TRM/tasa debe ser mayor que cero.")
        self.db.ejecutar(
            """
            UPDATE registros_trm
            SET fecha = ?, id_moneda = ?, valor = ?, id_usuario = ?
            WHERE id_registro = ?
            """,
            (fecha, id_moneda, valor, id_usuario, id_registro),
        )

    def eliminar(self, id_registro: int) -> None:
        if not self.obtener(id_registro):
            raise ValueError("No existe un registro con ese ID.")
        self.db.ejecutar("DELETE FROM registros_trm WHERE id_registro = ?", (id_registro,))

    def analizar_moneda(self, id_moneda: int) -> dict:
        """Calcula promedio, volatilidad y alerta para la moneda seleccionada.

        Regla del negocio:
        - Si última tasa < promedio: COMPRA.
        - Si última tasa > promedio: VENTA.
        - Si última tasa = promedio: MANTENER.
        """
        registros = self.listar_por_moneda(id_moneda)
        if len(registros) < 2:
            raise ValueError("Se necesitan al menos 2 registros de la moneda para calcular volatilidad.")

        valores = [float(r["valor"]) for r in registros]
        promedio = mean(valores)
        volatilidad = pstdev(valores)
        ultimo = registros[-1]
        ultima_tasa = float(ultimo["valor"])
        diferencia = ultima_tasa - promedio

        if abs(diferencia) < 0.01:
            decision = "MANTENER"
            explicacion = "La tasa está muy cerca del promedio histórico registrado."
        elif ultima_tasa < promedio:
            decision = "COMPRA"
            explicacion = "La tasa está por debajo del promedio; el inversionista podría comprar."
        else:
            decision = "VENTA"
            explicacion = "La tasa está por encima del promedio; el inversionista podría vender o esperar para comprar."

        return {
            "id_moneda": id_moneda,
            "fecha_inicio": registros[0]["fecha"],
            "fecha_fin": registros[-1]["fecha"],
            "cantidad_registros": len(registros),
            "promedio": round(promedio, 2),
            "volatilidad": round(volatilidad, 2),
            "minimo": round(min(valores), 2),
            "maximo": round(max(valores), 2),
            "ultima_tasa": round(ultima_tasa, 2),
            "diferencia": round(diferencia, 2),
            "decision": decision,
            "explicacion": explicacion,
        }
