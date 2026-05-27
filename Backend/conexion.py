from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Optional

from .datos import (
    ANALISIS_INICIALES,
    MONEDAS_INICIALES,
    REGISTROS_TRM_INICIALES,
    USUARIOS_INICIALES,
)


class BaseDeDatos:
    """Gestiona la conexión SQLite, la creación de tablas y la carga inicial."""

    def __init__(self, ruta_db: str | Path):
        self.ruta_db = str(ruta_db)
        Path(self.ruta_db).parent.mkdir(parents=True, exist_ok=True)

    def conectar(self) -> sqlite3.Connection:
        conexion = sqlite3.connect(self.ruta_db)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion

    def ejecutar(self, sql: str, parametros: Iterable = ()) -> int:
        with self.conectar() as conexion:
            cursor = conexion.execute(sql, tuple(parametros))
            conexion.commit()
            return int(cursor.lastrowid)

    def consultar(self, sql: str, parametros: Iterable = ()) -> list[sqlite3.Row]:
        with self.conectar() as conexion:
            cursor = conexion.execute(sql, tuple(parametros))
            return cursor.fetchall()

    def consultar_uno(self, sql: str, parametros: Iterable = ()) -> Optional[sqlite3.Row]:
        filas = self.consultar(sql, parametros)
        return filas[0] if filas else None

    def inicializar(self) -> None:
        self.crear_tablas()
        self.sembrar_datos_minimos()

    def crear_tablas(self) -> None:
        with self.conectar() as conexion:
            conexion.executescript(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    rol TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS monedas (
                    id_moneda INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    simbolo TEXT NOT NULL UNIQUE,
                    descripcion TEXT
                );

                CREATE TABLE IF NOT EXISTS registros_trm (
                    id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    id_moneda INTEGER NOT NULL,
                    valor REAL NOT NULL CHECK(valor > 0),
                    id_usuario INTEGER NOT NULL,
                    FOREIGN KEY (id_moneda) REFERENCES monedas(id_moneda),
                    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
                    UNIQUE(fecha, id_moneda)
                );

                CREATE TABLE IF NOT EXISTS analisis_trm (
                    id_analisis INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_usuario INTEGER NOT NULL,
                    id_moneda INTEGER NOT NULL,
                    fecha_inicio TEXT NOT NULL,
                    fecha_fin TEXT NOT NULL,
                    promedio REAL NOT NULL,
                    volatilidad REAL NOT NULL,
                    minimo REAL NOT NULL,
                    maximo REAL NOT NULL,
                    ultima_tasa REAL NOT NULL,
                    decision TEXT NOT NULL,
                    fecha_calculo TEXT NOT NULL,
                    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
                    FOREIGN KEY (id_moneda) REFERENCES monedas(id_moneda)
                );
                """
            )
            conexion.commit()

    def sembrar_datos_minimos(self) -> None:
        """Inserta datos semilla sin duplicar registros existentes."""
        with self.conectar() as conexion:
            for id_usuario, usuario in enumerate(USUARIOS_INICIALES, start=1):
                conexion.execute(
                    """
                    INSERT INTO usuarios(id_usuario, nombre, email, rol)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(id_usuario) DO UPDATE SET
                        nombre = excluded.nombre,
                        email = excluded.email,
                        rol = excluded.rol
                    """,
                    (id_usuario, usuario["nombre"], usuario["email"], usuario["rol"]),
                )

            for id_moneda, moneda in enumerate(MONEDAS_INICIALES, start=1):
                conexion.execute(
                    """
                    INSERT OR IGNORE INTO monedas(id_moneda, nombre, simbolo, descripcion)
                    VALUES (?, ?, ?, ?)
                    """,
                    (id_moneda, moneda["nombre"], moneda["simbolo"], moneda["descripcion"]),
                )

            for fecha, id_moneda, valor, id_usuario in REGISTROS_TRM_INICIALES:
                conexion.execute(
                    """
                    INSERT OR IGNORE INTO registros_trm(fecha, id_moneda, valor, id_usuario)
                    VALUES (?, ?, ?, ?)
                    """,
                    (fecha, id_moneda, valor, id_usuario),
                )

            total_analisis = conexion.execute("SELECT COUNT(*) AS total FROM analisis_trm").fetchone()["total"]
            if total_analisis < 5:
                conexion.execute("DELETE FROM analisis_trm")
                for fila in ANALISIS_INICIALES:
                    conexion.execute(
                        """
                        INSERT INTO analisis_trm(
                            id_usuario, id_moneda, fecha_inicio, fecha_fin, promedio,
                            volatilidad, minimo, maximo, ultima_tasa, decision, fecha_calculo
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        fila,
                    )

            conexion.commit()
