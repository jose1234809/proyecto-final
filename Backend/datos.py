"""Datos iniciales del proyecto Dólar-Track.

La carga semilla cumple el requisito de tener mínimo 5 registros por tabla
al inicializar la aplicación.
"""

USUARIOS_INICIALES = [
    {"nombre": "José Martínez", "email": "jose.martinez@dolartrack.com", "rol": "Administrador"},
    {"nombre": "Laura Gómez", "email": "laura.gomez@dolartrack.com", "rol": "Analista"},
    {"nombre": "Juan Rodríguez", "email": "juan.rodriguez@dolartrack.com", "rol": "Analista"},
    {"nombre": "David Escobar", "email": "david.escobar@dolartrack.com", "rol": "Analista"},
    {"nombre": "César Ramírez", "email": "cesar.ramirez@dolartrack.com", "rol": "Administrador"},
]

MONEDAS_INICIALES = [
    {"nombre": "Dólar estadounidense", "simbolo": "USD", "descripcion": "Moneda principal para seguimiento de TRM."},
    {"nombre": "Euro", "simbolo": "EUR", "descripcion": "Moneda alternativa para inversión."},
    {"nombre": "Libra esterlina", "simbolo": "GBP", "descripcion": "Moneda de referencia europea."},
    {"nombre": "Peso mexicano", "simbolo": "MXN", "descripcion": "Moneda latinoamericana de comparación."},
    {"nombre": "Yen japonés", "simbolo": "JPY", "descripcion": "Moneda asiática de comparación."},
]

# fecha, id_moneda, valor, id_usuario
REGISTROS_TRM_INICIALES = [
    # USD
    ("2026-05-20", 1, 3835.25, 2),
    ("2026-05-21", 1, 3852.10, 2),
    ("2026-05-22", 1, 3820.75, 3),
    ("2026-05-23", 1, 3868.40, 3),
    ("2026-05-24", 1, 3881.90, 4),
    # EUR
    ("2026-05-20", 2, 4420.30, 2),
    ("2026-05-21", 2, 4395.80, 3),
    ("2026-05-22", 2, 4442.15, 3),
    ("2026-05-23", 2, 4460.70, 4),
    ("2026-05-24", 2, 4415.10, 5),
    # GBP
    ("2026-05-20", 3, 5055.20, 2),
    ("2026-05-21", 3, 5088.50, 3),
    ("2026-05-22", 3, 5062.90, 3),
    ("2026-05-23", 3, 5110.40, 4),
    ("2026-05-24", 3, 5095.60, 5),
    # MXN
    ("2026-05-20", 4, 205.30, 2),
    ("2026-05-21", 4, 207.10, 3),
    ("2026-05-22", 4, 204.80, 3),
    ("2026-05-23", 4, 208.25, 4),
    ("2026-05-24", 4, 209.15, 5),
    # JPY
    ("2026-05-20", 5, 26.15, 2),
    ("2026-05-21", 5, 26.35, 3),
    ("2026-05-22", 5, 26.05, 3),
    ("2026-05-23", 5, 26.50, 4),
    ("2026-05-24", 5, 26.58, 5),
]

# id_usuario, id_moneda, fecha_inicio, fecha_fin, promedio, volatilidad,
# minimo, maximo, ultima_tasa, decision, fecha_calculo
ANALISIS_INICIALES = [
    (2, 1, "2026-05-20", "2026-05-24", 3851.68, 22.09, 3820.75, 3881.90, 3881.90, "VENTA", "2026-05-24 18:00:00"),
    (3, 2, "2026-05-20", "2026-05-24", 4426.81, 22.36, 4395.80, 4460.70, 4415.10, "COMPRA", "2026-05-24 18:05:00"),
    (3, 3, "2026-05-20", "2026-05-24", 5082.52, 21.02, 5055.20, 5110.40, 5095.60, "VENTA", "2026-05-24 18:10:00"),
    (4, 4, "2026-05-20", "2026-05-24", 206.92, 1.63, 204.80, 209.15, 209.15, "VENTA", "2026-05-24 18:15:00"),
    (5, 5, "2026-05-20", "2026-05-24", 26.33, 0.20, 26.05, 26.58, 26.58, "VENTA", "2026-05-24 18:20:00"),
]
