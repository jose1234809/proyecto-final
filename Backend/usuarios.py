from __future__ import annotations

import sqlite3

from .conexion import BaseDeDatos


class Usuario:
    """CRUD de usuarios responsables del sistema."""

    ROLES_PERMITIDOS = {"Analista", "Administrador"}

    def __init__(self, db: BaseDeDatos):
        self.db = db

    def crear(self, nombre: str, email: str, rol: str) -> int:
        if not nombre.strip() or not email.strip() or not rol.strip():
            raise ValueError("Todos los campos del usuario son obligatorios.")
        if rol.strip() not in self.ROLES_PERMITIDOS:
            raise ValueError("El rol debe ser Analista o Administrador.")
        if "@" not in email:
            raise ValueError("El email debe contener @.")
        return self.db.ejecutar(
            "INSERT INTO usuarios(nombre, email, rol) VALUES (?, ?, ?)",
            (nombre.strip(), email.strip().lower(), rol.strip()),
        )

    def crear_con_id(self, id_usuario: int, nombre: str, rol: str) -> int:
        """Crea un usuario con ID manual, como pide el formulario del reto.

        El email se genera internamente para cumplir la estructura de la base de datos,
        pero la interfaz se concentra en los datos solicitados por el usuario: ID, nombre y rol.
        """
        if id_usuario <= 0:
            raise ValueError("El ID debe ser un número entero mayor que cero.")
        if not nombre.strip():
            raise ValueError("El nombre del usuario es obligatorio.")
        if rol.strip() not in self.ROLES_PERMITIDOS:
            raise ValueError("El rol debe ser Analista o Administrador.")
        if self.obtener(id_usuario):
            raise ValueError("Ya existe un usuario con ese ID.")

        email_generado = f"usuario{id_usuario}@dolartrack.local"
        return self.db.ejecutar(
            "INSERT INTO usuarios(id_usuario, nombre, email, rol) VALUES (?, ?, ?, ?)",
            (id_usuario, nombre.strip(), email_generado, rol.strip()),
        )

    def listar(self) -> list[sqlite3.Row]:
        return self.db.consultar("SELECT * FROM usuarios ORDER BY id_usuario")

    def obtener(self, id_usuario: int) -> sqlite3.Row | None:
        return self.db.consultar_uno("SELECT * FROM usuarios WHERE id_usuario = ?", (id_usuario,))

    def siguiente_id(self) -> int:
        fila = self.db.consultar_uno("SELECT COALESCE(MAX(id_usuario), 0) + 1 AS siguiente FROM usuarios")
        return int(fila["siguiente"]) if fila else 1

    def actualizar(self, id_usuario: int, nombre: str, email: str, rol: str) -> None:
        if not self.obtener(id_usuario):
            raise ValueError("No existe un usuario con ese ID.")
        if not nombre.strip() or not email.strip() or not rol.strip():
            raise ValueError("Todos los campos son obligatorios.")
        if rol.strip() not in self.ROLES_PERMITIDOS:
            raise ValueError("El rol debe ser Analista o Administrador.")
        if "@" not in email:
            raise ValueError("El email debe contener @.")
        self.db.ejecutar(
            "UPDATE usuarios SET nombre = ?, email = ?, rol = ? WHERE id_usuario = ?",
            (nombre.strip(), email.strip().lower(), rol.strip(), id_usuario),
        )

    def eliminar(self, id_usuario: int) -> None:
        if not self.obtener(id_usuario):
            raise ValueError("No existe un usuario con ese ID.")
        self.db.ejecutar("DELETE FROM usuarios WHERE id_usuario = ?", (id_usuario,))
