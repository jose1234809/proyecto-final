# Dólar-Track Pro

## Descripción general
Dólar-Track Pro es una aplicación de escritorio orientada a economía y finanzas. Permite registrar usuarios responsables, administrar tasas diarias de monedas y generar señales de decisión para inversionistas a partir de promedio y volatilidad.

## Problema
Un inversionista necesita analizar el comportamiento de la TRM para decidir si comprar dólares o euros.

## Funcionalidad principal
El sistema permite ingresar una TRM o tasa diaria, calcular el promedio, calcular la volatilidad y generar una alerta automática:

- **COMPRA:** cuando la TRM/tasa está por debajo del promedio de la moneda.
- **VENTA:** cuando la TRM/tasa está por encima del promedio de la moneda.
- **MANTENER:** cuando la TRM/tasa es igual o muy cercana al promedio.

La aplicación no se limita a registrar datos: cada registro se compara contra el promedio histórico de su moneda y se muestra una decisión para el inversionista.

---

## Estructura de archivos

```text
dolar_track_pro/
├── Backend/
│   ├── __init__.py
│   ├── conexion.py          # Conexión SQLite, creación de tablas y datos iniciales
│   ├── datos.py             # Datos semilla: mínimo 5 registros por tabla
│   ├── usuarios.py          # CRUD dimensión usuarios
│   ├── monedas.py           # CRUD dimensión monedas
│   ├── registros_trm.py     # CRUD tabla de hechos y cálculo de alertas
│   ├── analisis.py          # Cálculo/guardado de promedio, volatilidad y decisión
│   ├── script_powerbi.py    # Script para cargar las tablas en Power BI
│   └── dolar_track.db       # Base de datos SQLite creada automáticamente
│
├── Frontend/
│   ├── __init__.py
│   ├── interfaz.py          # Interfaz gráfica Tkinter
│   └── img/
│       ├── logo.png         # Logo de la aplicación
│       ├── finance_hero.png # Imagen decorativa financiera del menú
│       ├── coin_usd.png     # Icono de moneda dólar
│       ├── coin_eur.png     # Icono de moneda euro
│       └── icon_chart.png   # Icono de análisis/gráfica
│
├── main.py                  # Archivo principal que ejecuta la aplicación
├── requirements.txt         # Dependencias de apoyo
├── POWERBI_DAX.md           # Medidas y columna calculada DAX sugeridas
└── README.md                # Documentación
```

---

## Arquitectura usada

El proyecto está dividido en dos capas:

1. **Backend:** contiene la lógica de negocio, clases POO, conexión a SQLite, CRUD y cálculos financieros.
2. **Frontend:** contiene la interfaz gráfica en Tkinter, formularios, tabla, métricas y botones.

El archivo `main.py` queda en la raíz y orquesta la ejecución de la aplicación.

---

## Base de datos SQLite

La base de datos se crea automáticamente en:

```text
Backend/dolar_track.db
```

El modelo tiene 4 tablas relacionadas con claves primarias y foráneas:

| Tabla | Tipo | Descripción |
|---|---|---|
| `usuarios` | Dimensión | Usuarios responsables de registrar o analizar datos. |
| `monedas` | Dimensión | Monedas disponibles: USD, EUR, GBP, MXN y JPY. |
| `registros_trm` | Tabla de hechos | Registros diarios de TRM/tasa por fecha, moneda y usuario. |
| `analisis_trm` | Tabla de hechos/resumen | Historial de análisis con promedio, volatilidad y decisión. |

Relaciones:

```text
usuarios.id_usuario  ──< registros_trm.id_usuario
monedas.id_moneda    ──< registros_trm.id_moneda
usuarios.id_usuario  ──< analisis_trm.id_usuario
monedas.id_moneda    ──< analisis_trm.id_moneda
```

Al inicializar, el sistema inserta automáticamente mínimo 5 registros en cada tabla.

---

## Interfaz gráfica Tkinter profesional

La aplicación inicia con un **centro de control financiero** de estilo profesional, con tarjetas de acceso, indicadores rápidos, logo, elementos financieros y navegación por módulos. Desde ese menú se accede a cinco opciones:

1. **Registrar usuario:** formulario con número de ID, nombre y rol. Los roles disponibles son **Analista** y **Administrador**. Al crear el usuario, la app vuelve al menú principal.
2. **Ver usuarios:** tabla independiente para consultar todos los usuarios registrados, sin tener que entrar al módulo de eliminación.
3. **Eliminar usuario:** tabla con los usuarios registrados y campo para eliminar por ID. Si el usuario tiene registros asociados, el sistema protege la auditoría y no lo elimina.
4. **Análisis inteligente de TRM:** módulo principal del sistema, donde se registran tasas, se calcula promedio, volatilidad y se genera la alerta para el inversionista.
5. **Salir del programa:** cierra la aplicación.

Dentro del módulo de análisis se mantienen las acciones principales del CRUD:

- **Registrar tasa**
- **Actualizar tasa**
- **Eliminar tasa**

La lectura se muestra de forma permanente en la tabla de historial, por eso se quitó el botón repetido de **Ver tabla / Leer**.

También incluye:

- Botón **Generar señal** para calcular promedio, volatilidad y alerta.
- Botón **Abrir Power BI** para abrir el `.pbix` desde Python cuando exista.
- Tabla con historial de registros y alerta automática por fila.
- Tarjetas con última tasa, promedio, volatilidad y alerta.
- Historial de análisis guardados.
- Uso de `try-except` y `messagebox` para errores, confirmaciones y validaciones.

---

## Cómo ejecutar

Abre la carpeta del proyecto en Visual Studio Code y ejecuta en la terminal:

```bash
python -m pip install -r requirements.txt
python main.py
```

Si `python` no funciona en tu computador, prueba:

```bash
py main.py
```

---

## Cómo usar la aplicación

### Registrar usuario

1. En el menú principal, entra a **Registrar usuario**.
2. Escribe el número de ID.
3. Escribe el nombre del usuario.
4. Selecciona el rol: **Analista** o **Administrador**.
5. Presiona **Crear usuario**.
6. El sistema muestra confirmación y vuelve al menú principal.

### Ver usuarios

1. En el menú principal, entra a **Ver usuarios**.
2. Revisa la tabla con ID, nombre y rol.
3. Desde ese módulo también puedes ir a registrar o eliminar usuarios.

### Eliminar usuario

1. En el menú principal, entra a **Eliminar usuario**.
2. Revisa la tabla de usuarios registrados.
3. Selecciona un usuario o escribe el ID manualmente.
4. Presiona **Eliminar usuario**.
5. Confirma la eliminación. Si el usuario tiene registros TRM o análisis asociados, el sistema no lo elimina para conservar la auditoría.

### Analizar TRM

1. En el menú principal, entra a **Análisis inteligente de TRM**.
2. Selecciona una moneda, por ejemplo USD o EUR.
3. Ingresa la fecha en formato `AAAA-MM-DD`.
4. Ingresa la TRM/tasa del día.
5. Selecciona el usuario responsable.
6. Presiona **Registrar tasa**.
7. La tabla se actualiza y muestra la alerta automática. La primera columna muestra el **ID del usuario responsable**, no un ID aleatorio de registro.
8. Presiona **Generar señal** para guardar el análisis en la tabla `analisis_trm`.

Para actualizar o eliminar registros TRM:

1. Selecciona una fila en la tabla.
2. Modifica los datos en el formulario y presiona **Actualizar tasa**, o presiona **Eliminar tasa**.
3. El sistema recalcula las alertas después del cambio.

---

## Power BI

No se incluye un `.pbix` falso porque Power BI Desktop rechaza archivos generados manualmente fuera de la aplicación. Para cumplir esa parte, crea el informe directamente en Power BI Desktop y guárdalo en la raíz del proyecto con este nombre:

```text
informe_powerbi_dolar_track_grupo_7.pbix
```

La app ya tiene el botón **Abrir Power BI** preparado para abrir ese archivo cuando exista.

Para conectar Power BI con SQLite puedes usar el script:

```text
Backend/script_powerbi.py
```

Medidas y columna calculada sugeridas están en:

```text
POWERBI_DAX.md
```

---

## Requisitos cubiertos

| Requisito | Estado |
|---|---|
| Carpeta `Backend/` con lógica, POO y base de datos | Cumplido |
| Carpeta `Frontend/` con interfaz gráfica y logo | Cumplido |
| `main.py` en la raíz | Cumplido |
| `README.md` detallado | Cumplido |
| Base de datos SQLite `.db` | Cumplido |
| Modelo con PK/FK tipo estrella | Cumplido |
| Mínimo 5 registros por tabla al inicializar | Cumplido |
| Centro de control principal Tkinter | Cumplido |
| 4 botones CRUD | Cumplido |
| Botón para abrir Power BI | Cumplido |
| `try-except` y `messagebox` | Cumplido |
| Promedio, volatilidad y alertas de compra/venta | Cumplido |
