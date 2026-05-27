"""Script de apoyo para cargar datos en Power BI desde SQLite.

En Power BI Desktop: Inicio > Obtener datos > Más > Script de Python.
Pega este script y cambia RUTA_DB por la ruta real de tu computador si hace falta.
"""

import sqlite3
from pathlib import Path

import pandas as pd

RUTA_DB = Path(__file__).resolve().parent / "dolar_track.db"
conexion = sqlite3.connect(RUTA_DB)

usuarios = pd.read_sql_query("SELECT * FROM usuarios", conexion)
monedas = pd.read_sql_query("SELECT * FROM monedas", conexion)
registros_trm = pd.read_sql_query("SELECT * FROM registros_trm", conexion)
analisis_trm = pd.read_sql_query("SELECT * FROM analisis_trm", conexion)

conexion.close()
