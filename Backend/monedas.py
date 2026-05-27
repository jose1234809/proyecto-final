from __future__ import annotations

import sqlite3

from .conexion import BaseDeDatos


class Moneda:
    """CRUD de monedas disponibles para el análisis de tasas."""

    def __init__(self, db: BaseDeDatos):
        self.db = db

    def crear(self, nombre: str, simbolo: str, descripcion: str = "") -> int:
        if not nombre.strip() or not simbolo.strip():
            raise ValueError("El nombre y el símbolo son obligatorios.")
        return self.db.ejecutar(
            "INSERT INTO monedas(nombre, simbolo, descripcion) VALUES (?, ?, ?)",
            (nombre.strip(), simbolo.strip().upper(), descripcion.strip()),
        )

    def listar(self) -> list[sqlite3.Row]:
        return self.db.consultar("SELECT * FROM monedas ORDER BY id_moneda")

    def obtener(self, id_moneda: int) -> sqlite3.Row | None:
        return self.db.consultar_uno("SELECT * FROM monedas WHERE id_moneda = ?", (id_moneda,))

    def actualizar(self, id_moneda: int, nombre: str, simbolo: str, descripcion: str = "") -> None:
        if not self.obtener(id_moneda):
            raise ValueError("No existe una moneda con ese ID.")
        if not nombre.strip() or not simbolo.strip():
            raise ValueError("El nombre y el símbolo son obligatorios.")
        self.db.ejecutar(
            "UPDATE monedas SET nombre = ?, simbolo = ?, descripcion = ? WHERE id_moneda = ?",
            (nombre.strip(), simbolo.strip().upper(), descripcion.strip(), id_moneda),
        )

    def eliminar(self, id_moneda: int) -> None:
        if not self.obtener(id_moneda):
            raise ValueError("No existe una moneda con ese ID.")
        self.db.ejecutar("DELETE FROM monedas WHERE id_moneda = ?", (id_moneda,))
