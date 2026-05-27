from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.analisis import AnalisisTRM
from Backend.conexion import BaseDeDatos
from Backend.monedas import Moneda
from Backend.registros_trm import RegistroTRM
from Backend.usuarios import Usuario

DB_PATH = PROJECT_ROOT / "Backend" / "dolar_track.db"
PBIX_PATH = PROJECT_ROOT / "informe_powerbi_dolar_track_grupo_7.pbix"
IMG_DIR = Path(__file__).resolve().parent / "img"


class DolarTrackApp:
    """Interfaz gráfica del MVP Dólar-Track.

    La app está organizada como un menú principal con módulos:
    1. Registrar usuario.
    2. Ver usuarios.
    3. Eliminar usuario.
    4. Análisis de TRM/tasas para el inversionista.
    5. Salir.
    """

    COLOR_BG = "#F3F7FB"
    COLOR_CARD = "#FFFFFF"
    COLOR_PANEL = "#F7FAFD"
    COLOR_PRIMARY = "#123B63"
    COLOR_PRIMARY_DARK = "#0B2742"
    COLOR_ACCENT = "#169B62"
    COLOR_DANGER = "#D14343"
    COLOR_WARNING = "#D68A17"
    COLOR_INFO = "#2F6FED"
    COLOR_TEXT = "#1E293B"
    COLOR_MUTED = "#6B7A90"
    COLOR_BORDER = "#D6E2EE"
    COLOR_TABLE_ALT = "#F7FAFD"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('Dólar-Track | Panel financiero')
        self.root.geometry("1220x780")
        self.root.minsize(1080, 680)
        self.root.configure(bg=self.COLOR_BG)

        self.db = BaseDeDatos(DB_PATH)
        self.db.inicializar()
        self.servicio_usuarios = Usuario(self.db)
        self.servicio_monedas = Moneda(self.db)
        self.servicio_registros = RegistroTRM(self.db)
        self.servicio_analisis = AnalisisTRM(self.db)

        self.contenedor: tk.Frame | None = None
        self.imagenes: dict[str, tk.PhotoImage] = {}
        self.metric_labels: dict[str, tk.Label] = {}
        self.id_registro_seleccionado: int | None = None

        self._cargar_imagenes()
        if "app_icon" in self.imagenes:
            self.root.iconphoto(True, self.imagenes["app_icon"])
        self._crear_estilos()
        self.mostrar_menu_principal()

    # ------------------------------------------------------------------
    # Configuración visual general
    # ------------------------------------------------------------------
    def _cargar_imagenes(self) -> None:
        archivos = {
            "logo": "logo.png",
            "hero": "finance_hero.png",
            "usd": "coin_usd.png",
            "eur": "coin_eur.png",
            "chart": "icon_chart.png",
            "app_icon": "app_icon.png",
        }
        for nombre, archivo in archivos.items():
            ruta = IMG_DIR / archivo
            if ruta.exists():
                try:
                    self.imagenes[nombre] = tk.PhotoImage(file=str(ruta))
                except Exception:
                    pass

    def _crear_estilos(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dolar.Treeview",
            background=self.COLOR_CARD,
            fieldbackground=self.COLOR_CARD,
            foreground=self.COLOR_TEXT,
            rowheight=33,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.configure(
            "Dolar.Treeview.Heading",
            background=self.COLOR_PRIMARY,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(8, 8),
            borderwidth=0,
        )
        style.map("Dolar.Treeview.Heading", background=[("active", self.COLOR_PRIMARY_DARK)])
        style.map(
            "Dolar.Treeview",
            background=[("selected", "#CFE8F7")],
            foreground=[("selected", self.COLOR_PRIMARY_DARK)],
        )
        style.configure("Dolar.TCombobox", padding=6, font=("Segoe UI", 10))

    def _limpiar_pantalla(self) -> None:
        if self.contenedor is not None:
            self.contenedor.destroy()
        self.contenedor = tk.Frame(self.root, bg=self.COLOR_BG)
        self.contenedor.pack(fill="both", expand=True)
        self.metric_labels = {}
        self.id_registro_seleccionado = None

    def _shade_color(self, hex_color: str, factor: float = 0.92) -> str:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return f"#{hex_color}" if not hex_color.startswith("#") else hex_color
        r = max(0, min(255, int(int(hex_color[0:2], 16) * factor)))
        g = max(0, min(255, int(int(hex_color[2:4], 16) * factor)))
        b = max(0, min(255, int(int(hex_color[4:6], 16) * factor)))
        return f"#{r:02X}{g:02X}{b:02X}"

    def _aplicar_hover_boton(self, boton: tk.Button, bg: str, fg: str) -> None:
        hover = self._shade_color(bg, 0.90)
        boton.bind("<Enter>", lambda _e: boton.configure(bg=hover, fg=fg, activebackground=hover))
        boton.bind("<Leave>", lambda _e: boton.configure(bg=bg, fg=fg, activebackground=bg))

    def _crear_boton(
        self,
        parent: tk.Widget,
        texto: str,
        comando,
        bg: str,
        fg: str = "white",
        pady: int = 11,
        ancho: int | None = None,
    ) -> tk.Button:
        boton = tk.Button(
            parent,
            text=texto,
            command=comando,
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            font=("Segoe UI", 10, "bold"),
            bd=0,
            cursor="hand2",
            pady=pady,
            padx=14,
            height=1,
            relief="flat",
        )
        self._aplicar_hover_boton(boton, bg, fg)
        if ancho:
            boton.configure(width=ancho)
        return boton

    def _crear_card(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(parent, bg=self.COLOR_CARD, highlightbackground=self.COLOR_BORDER, highlightthickness=1, bd=0)

    def _crear_header_modulo(self, parent: tk.Widget, titulo: str, subtitulo: str) -> None:
        header = tk.Frame(parent, bg=self.COLOR_PRIMARY, height=122)
        header.pack(fill="x")
        header.pack_propagate(False)

        fila = tk.Frame(header, bg=self.COLOR_PRIMARY)
        fila.pack(fill="both", expand=True, padx=28, pady=14)

        if "logo" in self.imagenes:
            tk.Label(fila, image=self.imagenes["logo"], bg=self.COLOR_PRIMARY).pack(side="left", padx=(0, 18))

        textos = tk.Frame(fila, bg=self.COLOR_PRIMARY)
        textos.pack(side="left", fill="both", expand=True)
        tk.Label(textos, text=titulo, bg=self.COLOR_PRIMARY, fg="white", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(
            textos,
            text=subtitulo,
            bg=self.COLOR_PRIMARY,
            fg="#EAF6FC",
            justify="left",
            font=("Segoe UI", 10, "bold"),
            wraplength=950,
        ).pack(anchor="w", pady=(4, 0))

        self._crear_boton(fila, "Volver al menú", self.mostrar_menu_principal, "#FFFFFF", self.COLOR_PRIMARY, pady=9).pack(side="right")

    # ------------------------------------------------------------------
    # Menú principal
    # ------------------------------------------------------------------
    def mostrar_menu_principal(self) -> None:
        self._limpiar_pantalla()
        assert self.contenedor is not None

        self.contenedor.grid_columnconfigure(0, weight=1)
        self.contenedor.grid_columnconfigure(1, weight=1)
        self.contenedor.grid_rowconfigure(0, weight=1)

        lado_izquierdo = tk.Frame(self.contenedor, bg=self.COLOR_PRIMARY)
        lado_izquierdo.grid(row=0, column=0, sticky="nsew")
        lado_izquierdo.grid_rowconfigure(0, weight=1)
        lado_izquierdo.grid_rowconfigure(1, weight=0)
        lado_izquierdo.grid_rowconfigure(2, weight=1)
        lado_izquierdo.grid_columnconfigure(0, weight=1)

        centro = tk.Frame(lado_izquierdo, bg=self.COLOR_PRIMARY)
        centro.grid(row=1, column=0, padx=34, pady=28, sticky="nw")
        if "logo" in self.imagenes:
            tk.Label(centro, image=self.imagenes["logo"], bg=self.COLOR_PRIMARY).pack(anchor="w", pady=(0, 18))

        tk.Label(
            centro,
            text="Dólar-Track Pro",
            bg=self.COLOR_PRIMARY,
            fg="white",
            font=("Segoe UI", 32, "bold"),
        ).pack(anchor="w")
        bloque_texto = tk.Frame(centro, bg=self.COLOR_PRIMARY)
        bloque_texto.pack(anchor="w", fill="x", pady=(12, 22))
        tk.Label(
            bloque_texto,
            text=(
                "Centro de control cambiario para registrar responsables, auditar tasas y convertir "
                "datos diarios de TRM en señales claras de compra, venta o espera."
            ),
            bg=self.COLOR_PRIMARY,
            fg="#DDECF6",
            justify="left",
            anchor="w",
            wraplength=430,
            font=("Segoe UI", 11),
        ).pack(anchor="w")

        chips = tk.Frame(centro, bg=self.COLOR_PRIMARY)
        chips.pack(anchor="w", fill="x")
        for texto in ["Economía y Finanzas", "SQLite", "Tkinter", "Power BI"]:
            tk.Label(
                chips,
                text=texto,
                bg="#123F61",
                fg="#EAF6FC",
                font=("Segoe UI", 10, "bold"),
                padx=12,
                pady=7,
            ).pack(side="left", padx=(0, 8), pady=(0, 8))

        tk.Label(
            centro,
            text="Diseñado para equipos financieros que necesitan decisiones rápidas, trazables y visuales.",
            bg=self.COLOR_PRIMARY,
            fg="#BFD5E6",
            font=("Segoe UI", 9, "italic"),
        ).pack(anchor="w", pady=(6, 6))

        if "hero" in self.imagenes:
            tk.Label(centro, image=self.imagenes["hero"], bg=self.COLOR_PRIMARY).pack(anchor="w", pady=(18, 0))

        lado_derecho = tk.Frame(self.contenedor, bg=self.COLOR_BG)
        lado_derecho.grid(row=0, column=1, sticky="nsew", padx=34, pady=34)
        lado_derecho.grid_columnconfigure(0, weight=1)

        tk.Label(
            lado_derecho,
            text='Centro de control financiero',
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("Segoe UI", 24, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        tk.Label(
            lado_derecho,
            text="Gestiona usuarios, registra tasas y revisa alertas desde un solo panel.",
            bg=self.COLOR_BG,
            fg=self.COLOR_MUTED,
            font=("Segoe UI", 11),
        ).grid(row=1, column=0, sticky="w", pady=(0, 14))

        fila_kpis = tk.Frame(lado_derecho, bg=self.COLOR_BG)
        fila_kpis.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        for col in range(3):
            fila_kpis.grid_columnconfigure(col, weight=1)
        self._crear_kpi_menu(fila_kpis, 0, "Usuarios", str(len(self.servicio_usuarios.listar())), self.COLOR_PRIMARY)
        self._crear_kpi_menu(fila_kpis, 1, "Monedas", str(len(self.servicio_monedas.listar())), self.COLOR_INFO)
        self._crear_kpi_menu(fila_kpis, 2, "Tasas", str(len(self.servicio_registros.listar())), self.COLOR_ACCENT)

        opciones = [
            ("Registrar usuario", "Crear responsable con ID, nombre y rol.", "👤", self.mostrar_registrar_usuario, self.COLOR_ACCENT),
            ("Ver usuarios", "Consultar la lista completa de usuarios registrados.", "📋", self.mostrar_ver_usuarios, self.COLOR_PRIMARY),
            ("Eliminar usuario", "Eliminar por ID solo si no afecta la auditoría.", "🗑", self.mostrar_eliminar_usuario, self.COLOR_DANGER),
            ("Análisis inteligente de TRM", "Registra tasas, mide volatilidad y genera señales accionables.", "📈", self.mostrar_analisis_trm, self.COLOR_INFO),
            ("Salir del programa", "Cerrar la aplicación de forma segura.", "⏻", self.root.destroy, self.COLOR_PRIMARY_DARK),
        ]
        for indice, (titulo, descripcion, icono, comando, color) in enumerate(opciones, start=3):
            self._crear_tarjeta_menu(lado_derecho, indice, titulo, descripcion, icono, comando, color)

        tk.Label(
            lado_derecho,
            text=f"Versión profesional · SQLite local · Tkinter · Power BI · {datetime.now().strftime('%Y-%m-%d')}",
            bg=self.COLOR_BG,
            fg=self.COLOR_MUTED,
            font=("Segoe UI", 9),
        ).grid(row=len(opciones) + 3, column=0, sticky="w", pady=(12, 0))

    def _crear_kpi_menu(self, parent: tk.Widget, columna: int, titulo: str, valor: str, color: str) -> None:
        card = self._crear_card(parent)
        card.grid(row=0, column=columna, sticky="ew", padx=(0 if columna == 0 else 8, 0))
        tk.Label(card, text=titulo, bg=self.COLOR_CARD, fg=self.COLOR_MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(10, 0))
        tk.Label(card, text=valor, bg=self.COLOR_CARD, fg=color, font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=14, pady=(0, 8))

    def _crear_tarjeta_menu(self, parent: tk.Widget, fila: int, titulo: str, descripcion: str, icono: str, comando, color: str) -> None:
        card = self._crear_card(parent)
        card.grid(row=fila, column=0, sticky="ew", pady=8)
        card.grid_columnconfigure(2, weight=1)

        tk.Frame(card, bg=color, width=6).grid(row=0, column=0, rowspan=2, sticky="nsw")
        icon_card = tk.Frame(card, bg="#F7FAFD", width=54, height=54, highlightbackground=self.COLOR_BORDER, highlightthickness=1)
        icon_card.grid(row=0, column=1, rowspan=2, padx=(18, 14), pady=18)
        icon_card.grid_propagate(False)
        tk.Label(icon_card, text=icono, bg="#F7FAFD", fg=color, font=("Segoe UI Emoji", 24)).place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text=titulo, bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 15, "bold")).grid(row=0, column=2, sticky="w", pady=(18, 2))
        tk.Label(card, text=descripcion, bg=self.COLOR_CARD, fg=self.COLOR_MUTED, font=("Segoe UI", 10), wraplength=360, justify="left").grid(row=1, column=2, sticky="w", pady=(0, 18))
        self._crear_boton(card, "Abrir módulo", comando, color, pady=9, ancho=13).grid(row=0, column=3, rowspan=2, padx=18, pady=18)

    # ------------------------------------------------------------------
    # Módulo de registrar usuario
    # ------------------------------------------------------------------
    def mostrar_registrar_usuario(self) -> None:
        self._limpiar_pantalla()
        assert self.contenedor is not None
        self._crear_header_modulo(
            self.contenedor,
            "Registrar usuario",
            "Crea el responsable que podrá registrar TRM/tasas o ejecutar análisis. Campos solicitados: ID, nombre y rol.",
        )

        cuerpo = tk.Frame(self.contenedor, bg=self.COLOR_BG)
        cuerpo.pack(fill="both", expand=True, padx=34, pady=28)
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        card = self._crear_card(cuerpo)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        card.grid_columnconfigure(0, weight=1)

        tk.Label(card, text="Nuevo usuario", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=24, pady=(24, 4))
        tk.Label(
            card,
            text="Después de crear el usuario, la app vuelve automáticamente al menú principal.",
            bg=self.COLOR_CARD,
            fg=self.COLOR_MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=24, pady=(0, 18))

        form = tk.Frame(card, bg=self.COLOR_CARD)
        form.pack(fill="x", padx=24)

        self.entry_user_id = self._crear_input(form, "Número de ID", "Ejemplo: 6")
        self.entry_user_id.insert(0, str(self.servicio_usuarios.siguiente_id()))
        self.entry_user_nombre = self._crear_input(form, "Nombre del usuario", "Ejemplo: Ana Gómez")
        self.combo_user_rol = self._crear_combo(form, "Rol del usuario")
        self.combo_user_rol["values"] = ["Analista", "Administrador"]
        self.combo_user_rol.current(0)

        botones = tk.Frame(card, bg=self.COLOR_CARD)
        botones.pack(fill="x", padx=24, pady=(24, 0))
        self._crear_boton(botones, "Crear usuario", self.crear_usuario, self.COLOR_ACCENT).pack(fill="x", pady=(0, 8))
        self._crear_boton(botones, "Cancelar y volver al menú", self.mostrar_menu_principal, "#E8F1F8", self.COLOR_PRIMARY).pack(fill="x")

        info = self._crear_card(cuerpo)
        info.grid(row=0, column=1, sticky="nsew")
        if "usd" in self.imagenes:
            tk.Label(info, image=self.imagenes["usd"], bg=self.COLOR_CARD).pack(pady=(42, 8))
        tk.Label(info, text="Roles disponibles", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 20, "bold")).pack()
        tk.Label(
            info,
            text=(
                "Analista: registra TRM/tasas y genera análisis.\n\n"
                "Administrador: puede gestionar usuarios y usar los módulos del sistema.\n\n"
                "El ID queda guardado en la base SQLite para mantener auditoría."
            ),
            bg=self.COLOR_CARD,
            fg=self.COLOR_MUTED,
            justify="left",
            wraplength=430,
            font=("Segoe UI", 11),
        ).pack(padx=34, pady=18)

    def crear_usuario(self) -> None:
        try:
            id_usuario = int(self.entry_user_id.get().strip())
            nombre = self.entry_user_nombre.get().strip()
            rol = self.combo_user_rol.get().strip()
            self.servicio_usuarios.crear_con_id(id_usuario, nombre, rol)
            messagebox.showinfo("Usuario creado", f"Usuario ID {id_usuario} creado correctamente.")
            self.mostrar_menu_principal()
        except ValueError as error:
            messagebox.showerror("Error de validación", str(error))
        except sqlite3.IntegrityError as error:
            messagebox.showerror("Error de base de datos", f"No se pudo crear el usuario. Revisa si el ID ya existe.\n{error}")
        except Exception as error:
            messagebox.showerror("Error inesperado", f"No se pudo crear el usuario:\n{error}")

    # ------------------------------------------------------------------
    # Módulo de ver usuarios
    # ------------------------------------------------------------------
    def mostrar_ver_usuarios(self) -> None:
        self._limpiar_pantalla()
        assert self.contenedor is not None
        self._crear_header_modulo(
            self.contenedor,
            "Ver usuarios",
            "Consulta los usuarios registrados con su ID real, nombre y rol dentro del sistema.",
        )

        cuerpo = tk.Frame(self.contenedor, bg=self.COLOR_BG)
        cuerpo.pack(fill="both", expand=True, padx=34, pady=28)
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla_card = self._crear_card(cuerpo)
        tabla_card.grid(row=0, column=0, sticky="nsew")
        tabla_card.grid_columnconfigure(0, weight=1)
        tabla_card.grid_rowconfigure(2, weight=1)

        tk.Label(
            tabla_card,
            text="Usuarios registrados",
            bg=self.COLOR_CARD,
            fg=self.COLOR_TEXT,
            font=("Segoe UI", 22, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(22, 4))
        tk.Label(
            tabla_card,
            text="Estos ID son los mismos que aparecen como responsables en el análisis de TRM.",
            bg=self.COLOR_CARD,
            fg=self.COLOR_MUTED,
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 14))

        columnas = ("id", "nombre", "rol")
        self.tabla_usuarios = ttk.Treeview(tabla_card, columns=columnas, show="headings", style="Dolar.Treeview")
        for col, titulo, ancho in [("id", "ID Usuario", 120), ("nombre", "Nombre", 360), ("rol", "Rol", 220)]:
            self.tabla_usuarios.heading(col, text=titulo)
            self.tabla_usuarios.column(col, width=ancho, anchor="center" if col != "nombre" else "w")
        scroll = ttk.Scrollbar(tabla_card, orient="vertical", command=self.tabla_usuarios.yview)
        self.tabla_usuarios.configure(yscrollcommand=scroll.set)
        self.tabla_usuarios.grid(row=2, column=0, sticky="nsew", padx=(22, 0), pady=(0, 18))
        scroll.grid(row=2, column=1, sticky="ns", pady=(0, 18), padx=(0, 22))

        botones = tk.Frame(tabla_card, bg=self.COLOR_CARD)
        botones.grid(row=3, column=0, columnspan=2, sticky="ew", padx=22, pady=(0, 22))
        self._crear_boton(botones, "Registrar nuevo usuario", self.mostrar_registrar_usuario, self.COLOR_ACCENT).pack(side="left", padx=(0, 10))
        self._crear_boton(botones, "Eliminar usuario", self.mostrar_eliminar_usuario, self.COLOR_DANGER).pack(side="left", padx=(0, 10))
        self._crear_boton(botones, "Volver al menú", self.mostrar_menu_principal, "#E8F1F8", self.COLOR_PRIMARY).pack(side="right")

        self._cargar_tabla_usuarios()

    # ------------------------------------------------------------------
    # Módulo de eliminar usuario
    # ------------------------------------------------------------------
    def mostrar_eliminar_usuario(self) -> None:
        self._limpiar_pantalla()
        assert self.contenedor is not None
        self._crear_header_modulo(
            self.contenedor,
            "Eliminar usuario",
            "Consulta los usuarios registrados y elimina por número de ID. Si un usuario tiene registros asociados, se protege la auditoría.",
        )

        cuerpo = tk.Frame(self.contenedor, bg=self.COLOR_BG)
        cuerpo.pack(fill="both", expand=True, padx=34, pady=28)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla_card = self._crear_card(cuerpo)
        tabla_card.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        tabla_card.grid_columnconfigure(0, weight=1)
        tabla_card.grid_rowconfigure(1, weight=1)
        tk.Label(tabla_card, text="Usuarios registrados", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 19, "bold")).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 8))

        columnas = ("id", "nombre", "rol")
        self.tabla_usuarios = ttk.Treeview(tabla_card, columns=columnas, show="headings", style="Dolar.Treeview")
        for col, titulo, ancho in [("id", "ID Usuario", 100), ("nombre", "Nombre", 280), ("rol", "Rol", 170)]:
            self.tabla_usuarios.heading(col, text=titulo)
            self.tabla_usuarios.column(col, width=ancho, anchor="center" if col != "nombre" else "w")
        self.tabla_usuarios.bind("<<TreeviewSelect>>", self._seleccionar_usuario_para_eliminar)
        scroll = ttk.Scrollbar(tabla_card, orient="vertical", command=self.tabla_usuarios.yview)
        self.tabla_usuarios.configure(yscrollcommand=scroll.set)
        self.tabla_usuarios.grid(row=1, column=0, sticky="nsew", padx=(18, 0), pady=(0, 18))
        scroll.grid(row=1, column=1, sticky="ns", pady=(0, 18), padx=(0, 18))

        panel = self._crear_card(cuerpo)
        panel.grid(row=0, column=1, sticky="nsew")
        if "chart" in self.imagenes:
            tk.Label(panel, image=self.imagenes["chart"], bg=self.COLOR_CARD).pack(pady=(28, 0))
        tk.Label(panel, text="Eliminar por ID", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=22, pady=(18, 4))
        tk.Label(
            panel,
            text="Puedes seleccionar un usuario en la tabla o escribir directamente el ID.",
            bg=self.COLOR_CARD,
            fg=self.COLOR_MUTED,
            wraplength=260,
            justify="left",
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=22, pady=(0, 12))
        self.entry_delete_id = self._crear_input(panel, "ID del usuario", "Ejemplo: 6")
        self._crear_boton(panel, "Eliminar usuario", self.eliminar_usuario, self.COLOR_DANGER).pack(fill="x", padx=22, pady=(22, 8))
        self._crear_boton(panel, "Volver al menú", self.mostrar_menu_principal, "#E8F1F8", self.COLOR_PRIMARY).pack(fill="x", padx=22)

        self._cargar_tabla_usuarios()

    def _cargar_tabla_usuarios(self) -> None:
        try:
            for item in self.tabla_usuarios.get_children():
                self.tabla_usuarios.delete(item)
            for indice, fila in enumerate(self.servicio_usuarios.listar()):
                self.tabla_usuarios.insert(
                    "",
                    "end",
                    values=(fila["id_usuario"], fila["nombre"], fila["rol"]),
                    tags=("par" if indice % 2 == 0 else "impar",),
                )
            self.tabla_usuarios.tag_configure("par", background=self.COLOR_CARD)
            self.tabla_usuarios.tag_configure("impar", background=self.COLOR_TABLE_ALT)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo cargar la tabla de usuarios:\n{error}")

    def _seleccionar_usuario_para_eliminar(self, _event=None) -> None:
        seleccion = self.tabla_usuarios.selection()
        if not seleccion:
            return
        valores = self.tabla_usuarios.item(seleccion[0], "values")
        self.entry_delete_id.delete(0, tk.END)
        self.entry_delete_id.insert(0, valores[0])

    def eliminar_usuario(self) -> None:
        try:
            id_usuario = int(self.entry_delete_id.get().strip())
            usuario = self.servicio_usuarios.obtener(id_usuario)
            if not usuario:
                raise ValueError("No existe un usuario con ese ID.")
            confirmar = messagebox.askyesno("Confirmar eliminación", f"¿Eliminar al usuario {usuario['nombre']} con ID {id_usuario}?")
            if not confirmar:
                return
            self.servicio_usuarios.eliminar(id_usuario)
            self._cargar_tabla_usuarios()
            self.entry_delete_id.delete(0, tk.END)
            messagebox.showinfo("Usuario eliminado", "El usuario fue eliminado correctamente.")
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "No se puede eliminar",
                "Este usuario tiene registros o análisis asociados. Para mantener la auditoría del proyecto, no se elimina.",
            )
        except ValueError as error:
            messagebox.showerror("Error de validación", str(error))
        except Exception as error:
            messagebox.showerror("Error inesperado", f"No se pudo eliminar el usuario:\n{error}")

    # ------------------------------------------------------------------
    # Módulo de análisis TRM
    # ------------------------------------------------------------------
    def mostrar_analisis_trm(self) -> None:
        self._limpiar_pantalla()
        assert self.contenedor is not None
        self._crear_header_modulo(
            self.contenedor,
            "Mesa de análisis TRM",
            "Registra tasas, revisa promedio y volatilidad, y genera una señal final para el inversionista.",
        )

        contenido = tk.Frame(self.contenedor, bg=self.COLOR_BG)
        contenido.pack(fill="both", expand=True, padx=20, pady=16)
        contenido.grid_columnconfigure(0, weight=0)
        contenido.grid_columnconfigure(1, weight=1)
        contenido.grid_rowconfigure(0, weight=1)

        self._crear_panel_formulario_trm(contenido)
        self._crear_panel_dashboard_trm(contenido)
        self._cargar_opciones_trm()
        self._cargar_tabla_registros()
        self._cargar_historial_analisis()
        self._actualizar_resumen_moneda()

    def _crear_panel_formulario_trm(self, parent: tk.Frame) -> None:
        card = self._crear_card(parent)
        card.grid(row=0, column=0, sticky="ns", padx=(0, 18))
        card.configure(width=305)
        card.grid_propagate(False)

        tk.Label(card, text="Operación diaria", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 19, "bold")).pack(anchor="w", padx=22, pady=(22, 0))
        self.label_modo = tk.Label(card, text="Modo: registrar nueva tasa", bg=self.COLOR_CARD, fg=self.COLOR_MUTED, font=("Segoe UI", 10))
        self.label_modo.pack(anchor="w", padx=22, pady=(2, 14))

        form = tk.Frame(card, bg=self.COLOR_CARD)
        form.pack(fill="x", padx=22)
        self.entry_fecha = self._crear_input(form, "Fecha", "Formato: AAAA-MM-DD")
        self.entry_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.combo_moneda = self._crear_combo(form, "Moneda a analizar")
        self.combo_moneda.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_resumen_moneda())
        self.entry_valor = self._crear_input(form, "Valor TRM / tasa", "Ejemplo: 3850.75")
        self.combo_usuario = self._crear_combo(form, "Usuario responsable")

        botones = tk.Frame(card, bg=self.COLOR_CARD)
        botones.pack(fill="x", padx=22, pady=(18, 8))
        botones.grid_columnconfigure(0, weight=1)
        acciones = [
            ("Registrar tasa", self.registrar_trm, self.COLOR_ACCENT),
            ("Actualizar tasa", self.actualizar_registro, self.COLOR_INFO),
            ("Eliminar tasa", self.eliminar_registro, self.COLOR_DANGER),
            ("Generar señal", self.analizar_decision, self.COLOR_WARNING),
            ("Abrir Power BI", self.abrir_powerbi, "#7C3AED"),
            ("Limpiar campos", self.limpiar_formulario_trm, "#E8F1F8", self.COLOR_PRIMARY),
        ]
        for fila, datos in enumerate(acciones):
            if len(datos) == 3:
                texto, comando, color = datos
                fg = "white"
            else:
                texto, comando, color, fg = datos
            self._crear_boton(botones, texto, comando, color, fg, pady=11).grid(row=fila, column=0, sticky="ew", pady=(0, 7))

        regla = tk.Frame(card, bg=self.COLOR_PANEL, highlightbackground=self.COLOR_BORDER, highlightthickness=1)
        regla.pack(fill="x", padx=22, pady=(8, 0))
        tk.Label(regla, text="Regla del negocio", bg=self.COLOR_PANEL, fg=self.COLOR_PRIMARY, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(
            regla,
            text="• TRM < promedio: COMPRA\n• TRM > promedio: VENTA\n• TRM = promedio: MANTENER\n• Volatilidad: variación de los registros",
            bg=self.COLOR_PANEL,
            fg=self.COLOR_MUTED,
            justify="left",
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=12, pady=(0, 12))

    def _crear_panel_dashboard_trm(self, parent: tk.Frame) -> None:
        panel = tk.Frame(parent, bg=self.COLOR_BG)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=3)
        panel.grid_rowconfigure(2, weight=1)

        metricas = tk.Frame(panel, bg=self.COLOR_BG)
        metricas.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        for col in range(4):
            metricas.grid_columnconfigure(col, weight=1)
        self._crear_tarjeta_metrica(metricas, 0, "Última tasa", "$ 0.00", "Último registro")
        self._crear_tarjeta_metrica(metricas, 1, "Promedio", "$ 0.00", "Promedio de moneda")
        self._crear_tarjeta_metrica(metricas, 2, "Volatilidad", "0.00", "Desviación estándar")
        self._crear_tarjeta_metrica(metricas, 3, "Alerta", "--", "Compra / venta")

        self._crear_tabla_registros(panel)
        self._crear_panel_resultado_analisis(panel)

    def _crear_tarjeta_metrica(self, parent: tk.Frame, columna: int, titulo: str, valor: str, descripcion: str) -> None:
        card = self._crear_card(parent)
        card.grid(row=0, column=columna, sticky="ew", padx=0 if columna == 0 else 8)
        tk.Label(card, text=titulo, bg=self.COLOR_CARD, fg=self.COLOR_MUTED, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(12, 0))
        label = tk.Label(card, text=valor, bg=self.COLOR_CARD, fg=self.COLOR_PRIMARY, font=("Segoe UI", 20, "bold"))
        label.pack(anchor="w", padx=14, pady=(2, 0))
        tk.Label(card, text=descripcion, bg=self.COLOR_CARD, fg=self.COLOR_MUTED, font=("Segoe UI", 8)).pack(anchor="w", padx=14, pady=(0, 12))
        self.metric_labels[titulo] = label

    def _crear_tabla_registros(self, parent: tk.Frame) -> None:
        card = self._crear_card(parent)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        encabezado = tk.Frame(card, bg=self.COLOR_CARD)
        encabezado.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        encabezado.grid_columnconfigure(0, weight=1)
        tk.Label(encabezado, text="Historial operativo de tasas", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 17, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(encabezado, text="Cada registro queda asociado a un usuario responsable y a una señal calculada.", bg=self.COLOR_CARD, fg=self.COLOR_MUTED, font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=(2, 0))

        wrapper = tk.Frame(card, bg=self.COLOR_CARD)
        wrapper.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(0, weight=1)

        columnas = ("id_usuario", "fecha", "moneda", "valor", "promedio", "diferencia", "alerta", "usuario")
        self.tabla = ttk.Treeview(wrapper, columns=columnas, show="headings", style="Dolar.Treeview")
        config = {
            "id_usuario": ("ID Usuario", 82),
            "fecha": ("Fecha", 92),
            "moneda": ("Moneda", 72),
            "valor": ("TRM / tasa", 108),
            "promedio": ("Promedio", 108),
            "diferencia": ("Dif.", 78),
            "alerta": ("Alerta", 82),
            "usuario": ("Responsable", 160),
        }
        for col, (titulo, ancho) in config.items():
            self.tabla.heading(col, text=titulo)
            self.tabla.column(col, width=ancho, anchor="center" if col != "usuario" else "w")
        self.tabla.tag_configure("par", background=self.COLOR_CARD)
        self.tabla.tag_configure("impar", background=self.COLOR_TABLE_ALT)
        self.tabla.tag_configure("COMPRA", foreground=self.COLOR_ACCENT)
        self.tabla.tag_configure("VENTA", foreground=self.COLOR_DANGER)
        self.tabla.tag_configure("MANTENER", foreground=self.COLOR_WARNING)
        self.tabla.bind("<<TreeviewSelect>>", self._seleccionar_fila_registro)

        scroll_y = ttk.Scrollbar(wrapper, orient="vertical", command=self.tabla.yview)
        scroll_x = ttk.Scrollbar(wrapper, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

    def _crear_panel_resultado_analisis(self, parent: tk.Frame) -> None:
        abajo = tk.Frame(parent, bg=self.COLOR_BG)
        abajo.grid(row=2, column=0, sticky="nsew", pady=(14, 0))
        abajo.grid_columnconfigure(0, weight=1)
        abajo.grid_columnconfigure(1, weight=1)
        abajo.grid_rowconfigure(0, weight=1)

        resultado = self._crear_card(abajo)
        resultado.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        resultado.grid_columnconfigure(0, weight=1)
        resultado.grid_rowconfigure(1, weight=1)
        tk.Label(
            resultado,
            text="Señal para el inversionista",
            bg=self.COLOR_CARD,
            fg=self.COLOR_TEXT,
            font=("Segoe UI", 15, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        self.text_resultado = tk.Text(
            resultado,
            height=10,
            wrap="word",
            bg="#FBFCFE",
            fg=self.COLOR_TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
            padx=10,
            pady=6,
        )
        self.text_resultado.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        self._set_texto_resultado("Selecciona una moneda y presiona 'Generar señal'.")

        historial = self._crear_card(abajo)
        historial.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        historial.grid_columnconfigure(0, weight=1)
        historial.grid_rowconfigure(1, weight=1)
        tk.Label(historial, text="Bitácora de señales guardadas", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 15, "bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        columnas = ("fecha", "moneda", "promedio", "vol", "ultima", "decision")
        self.tabla_analisis = ttk.Treeview(historial, columns=columnas, show="headings", height=5, style="Dolar.Treeview")
        config = {
            "fecha": ("Fecha cálculo", 145),
            "moneda": ("Moneda", 70),
            "promedio": ("Prom.", 95),
            "vol": ("Vol.", 75),
            "ultima": ("Última", 95),
            "decision": ("Decisión", 90),
        }
        for col, (titulo, ancho) in config.items():
            self.tabla_analisis.heading(col, text=titulo)
            self.tabla_analisis.column(col, width=ancho, anchor="center")
        self.tabla_analisis.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))

    # ------------------------------------------------------------------
    # Inputs, combos y carga de datos
    # ------------------------------------------------------------------
    def _crear_input(self, parent: tk.Widget, etiqueta: str, ayuda: str) -> tk.Entry:
        tk.Label(parent, text=etiqueta, bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 4), padx=0 if isinstance(parent, tk.Frame) else 22)
        entry = tk.Entry(parent, font=("Segoe UI", 11), bg="#F9FBFD", fg=self.COLOR_TEXT, relief="solid", bd=1, insertbackground=self.COLOR_PRIMARY)
        entry.pack(fill="x", ipady=8, padx=0 if isinstance(parent, tk.Frame) else 22)
        tk.Label(parent, text=ayuda, bg=self.COLOR_CARD, fg=self.COLOR_MUTED, font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0), padx=0 if isinstance(parent, tk.Frame) else 22)
        return entry

    def _crear_combo(self, parent: tk.Widget, etiqueta: str) -> ttk.Combobox:
        tk.Label(parent, text=etiqueta, bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 4))
        combo = ttk.Combobox(parent, state="readonly", style="Dolar.TCombobox", font=("Segoe UI", 10))
        combo.pack(fill="x", ipady=4)
        return combo

    def _cargar_opciones_trm(self) -> None:
        monedas = self.servicio_monedas.listar()
        usuarios = self.servicio_usuarios.listar()
        self.combo_moneda["values"] = [f"{m['id_moneda']} - {m['simbolo']} · {m['nombre']}" for m in monedas]
        self.combo_usuario["values"] = [f"{u['id_usuario']} - {u['nombre']} · {u['rol']}" for u in usuarios]
        if monedas:
            self.combo_moneda.current(0)
        if usuarios:
            self.combo_usuario.current(0)

    def _cargar_tabla_registros(self) -> None:
        try:
            for item in self.tabla.get_children():
                self.tabla.delete(item)
            registros = list(self.servicio_registros.listar())
            promedios = self._promedios_por_moneda(registros)
            for indice, fila in enumerate(reversed(registros)):
                promedio = promedios.get(int(fila["id_moneda"]), float(fila["valor"]))
                valor = float(fila["valor"])
                alerta = self._decision(valor, promedio)
                diferencia = valor - promedio
                self.tabla.insert(
                    "",
                    "end",
                    iid=str(fila["id_registro"]),
                    values=(
                        fila["id_usuario"],
                        fila["fecha"],
                        fila["moneda"],
                        self._formato_moneda(valor),
                        self._formato_moneda(promedio),
                        self._formato_numero(diferencia),
                        alerta,
                        fila["usuario"],
                    ),
                    tags=("par" if indice % 2 == 0 else "impar", alerta),
                )
            self._actualizar_resumen_moneda()
        except Exception as error:
            messagebox.showerror("Error al leer", f"No se pudo cargar la tabla:\n{error}")

    def _cargar_historial_analisis(self) -> None:
        try:
            for item in self.tabla_analisis.get_children():
                self.tabla_analisis.delete(item)
            for fila in self.servicio_analisis.listar():
                self.tabla_analisis.insert(
                    "",
                    "end",
                    values=(
                        fila["fecha_calculo"],
                        fila["moneda"],
                        self._formato_moneda(float(fila["promedio"])),
                        self._formato_numero(float(fila["volatilidad"])),
                        self._formato_moneda(float(fila["ultima_tasa"])),
                        fila["decision"],
                    ),
                )
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo cargar el historial de análisis:\n{error}")

    # ------------------------------------------------------------------
    # Acciones del análisis TRM
    # ------------------------------------------------------------------
    def registrar_trm(self) -> None:
        try:
            fecha, id_moneda, valor, id_usuario = self._obtener_datos_formulario_trm()
            nuevo_id = self.servicio_registros.crear(fecha, id_moneda, valor, id_usuario)
            self._cargar_tabla_registros()
            resultado = self.servicio_registros.analizar_moneda(id_moneda)
            self._mostrar_resultado(resultado, guardar=False)
            messagebox.showinfo(
                "Registro exitoso",
                f"La TRM/tasa fue guardada correctamente.\nID generado: {nuevo_id}\nAlerta actual: {resultado['decision']}",
            )
            self.limpiar_formulario_trm(mantener_fecha=True)
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicado", "Ya existe un registro para esa fecha y esa moneda.")
        except ValueError as error:
            messagebox.showerror("Error de validación", str(error))
        except Exception as error:
            messagebox.showerror("Error inesperado", f"No se pudo registrar:\n{error}")

    def actualizar_registro(self) -> None:
        try:
            if self.id_registro_seleccionado is None:
                raise ValueError("Selecciona una fila de la tabla antes de actualizar.")
            fecha, id_moneda, valor, id_usuario = self._obtener_datos_formulario_trm()
            self.servicio_registros.actualizar(self.id_registro_seleccionado, fecha, id_moneda, valor, id_usuario)
            self._cargar_tabla_registros()
            self.limpiar_formulario_trm(mantener_fecha=True)
            messagebox.showinfo("Actualización exitosa", "El registro fue actualizado y las alertas se recalcularon.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicado", "Ya existe otro registro con esa fecha y moneda.")
        except ValueError as error:
            messagebox.showerror("Error de validación", str(error))
        except Exception as error:
            messagebox.showerror("Error inesperado", f"No se pudo actualizar:\n{error}")

    def eliminar_registro(self) -> None:
        try:
            if self.id_registro_seleccionado is None:
                raise ValueError("Selecciona una fila de la tabla antes de eliminar.")
            confirmar = messagebox.askyesno("Confirmar eliminación", f"¿Eliminar el registro ID {self.id_registro_seleccionado}?")
            if not confirmar:
                return
            self.servicio_registros.eliminar(self.id_registro_seleccionado)
            self._cargar_tabla_registros()
            self.limpiar_formulario_trm()
            messagebox.showinfo("Eliminación exitosa", "El registro fue eliminado y las alertas se recalcularon.")
        except ValueError as error:
            messagebox.showerror("Error de validación", str(error))
        except Exception as error:
            messagebox.showerror("Error inesperado", f"No se pudo eliminar:\n{error}")

    def analizar_decision(self) -> None:
        try:
            id_moneda = self._obtener_id_combo(self.combo_moneda.get(), "una moneda")
            id_usuario = self._obtener_id_combo(self.combo_usuario.get(), "un usuario")
            resultado = self.servicio_analisis.calcular(id_usuario, id_moneda)
            self.servicio_analisis.guardar(resultado)
            self._mostrar_resultado(resultado, guardar=True)
            self._cargar_historial_analisis()
            self._actualizar_resumen_moneda()
            messagebox.showinfo(
                "Análisis generado",
                f"Promedio: {self._formato_moneda(resultado['promedio'])}\n"
                f"Volatilidad: {self._formato_numero(resultado['volatilidad'])}\n"
                f"Decisión: {resultado['decision']}",
            )
        except ValueError as error:
            messagebox.showerror("Error de análisis", str(error))
        except Exception as error:
            messagebox.showerror("Error inesperado", f"No se pudo calcular el análisis:\n{error}")

    def abrir_powerbi(self) -> None:
        try:
            if not PBIX_PATH.exists():
                raise FileNotFoundError(
                    "No se encontró el archivo .pbix. Cuando lo crees en Power BI Desktop, "
                    f"guárdalo en la raíz del proyecto con este nombre: {PBIX_PATH.name}"
                )
            if sys.platform.startswith("win"):
                os.startfile(PBIX_PATH)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(PBIX_PATH)])
            else:
                subprocess.Popen(["xdg-open", str(PBIX_PATH)])
        except Exception as error:
            messagebox.showerror("No se pudo abrir Power BI", str(error))

    def limpiar_formulario_trm(self, mantener_fecha: bool = False) -> None:
        fecha = self.entry_fecha.get().strip() if mantener_fecha else datetime.now().strftime("%Y-%m-%d")
        self.entry_fecha.delete(0, tk.END)
        self.entry_fecha.insert(0, fecha)
        self.entry_valor.delete(0, tk.END)
        if self.combo_moneda["values"]:
            self.combo_moneda.current(0)
        if self.combo_usuario["values"]:
            self.combo_usuario.current(0)
        self.id_registro_seleccionado = None
        try:
            self.tabla.selection_remove(self.tabla.selection())
        except Exception:
            pass
        self.label_modo.configure(text="Modo: registrar nueva tasa")
        self.entry_valor.focus_set()
        self._actualizar_resumen_moneda()

    # ------------------------------------------------------------------
    # Cálculos y utilidades
    # ------------------------------------------------------------------
    def _promedios_por_moneda(self, registros: list[sqlite3.Row]) -> dict[int, float]:
        acumulados: dict[int, list[float]] = {}
        for fila in registros:
            acumulados.setdefault(int(fila["id_moneda"]), []).append(float(fila["valor"]))
        return {id_moneda: sum(valores) / len(valores) for id_moneda, valores in acumulados.items()}

    def _actualizar_resumen_moneda(self) -> None:
        try:
            id_moneda = self._obtener_id_combo(self.combo_moneda.get(), "una moneda")
            resultado = self.servicio_registros.analizar_moneda(id_moneda)
            self.metric_labels["Última tasa"].configure(text=self._formato_moneda(resultado["ultima_tasa"]), fg=self.COLOR_PRIMARY)
            self.metric_labels["Promedio"].configure(text=self._formato_moneda(resultado["promedio"]), fg=self.COLOR_PRIMARY)
            self.metric_labels["Volatilidad"].configure(text=self._formato_numero(resultado["volatilidad"]), fg=self.COLOR_PRIMARY)
            color_alerta = self.COLOR_WARNING
            if resultado["decision"] == "COMPRA":
                color_alerta = self.COLOR_ACCENT
            elif resultado["decision"] == "VENTA":
                color_alerta = self.COLOR_DANGER
            self.metric_labels["Alerta"].configure(text=resultado["decision"], fg=color_alerta)
            self._mostrar_resultado(resultado, guardar=False)
        except Exception:
            if self.metric_labels:
                self.metric_labels["Última tasa"].configure(text="$ 0.00", fg=self.COLOR_PRIMARY)
                self.metric_labels["Promedio"].configure(text="$ 0.00", fg=self.COLOR_PRIMARY)
                self.metric_labels["Volatilidad"].configure(text="0.00", fg=self.COLOR_PRIMARY)
                self.metric_labels["Alerta"].configure(text="--", fg=self.COLOR_WARNING)
            self._set_texto_resultado("No hay suficientes registros para calcular el análisis de esta moneda.")

    def _mostrar_resultado(self, resultado: dict, guardar: bool) -> None:
        prefijo = "Análisis guardado en historial" if guardar else "Análisis actual de la moneda seleccionada"
        texto = (
            f"{prefijo}\n"
            f"Rango: {resultado['fecha_inicio']} a {resultado['fecha_fin']}\n"
            f"Registros usados: {resultado['cantidad_registros']}\n"
            f"Promedio: {self._formato_moneda(resultado['promedio'])}\n"
            f"Volatilidad: {self._formato_numero(resultado['volatilidad'])}\n"
            f"Mínimo / máximo: {self._formato_moneda(resultado['minimo'])} / {self._formato_moneda(resultado['maximo'])}\n"
            f"Última tasa: {self._formato_moneda(resultado['ultima_tasa'])}\n"
            f"Diferencia contra promedio: {self._formato_numero(resultado['diferencia'])}\n"
            f"Decisión: {resultado['decision']}\n"
            f"Interpretación: {resultado['explicacion']}"
        )
        self._set_texto_resultado(texto)

    def _set_texto_resultado(self, texto: str) -> None:
        if not hasattr(self, "text_resultado"):
            return
        self.text_resultado.configure(state="normal")
        self.text_resultado.delete("1.0", tk.END)
        self.text_resultado.insert("1.0", texto)
        self.text_resultado.configure(state="disabled")

    def _decision(self, valor: float, promedio: float) -> str:
        if abs(valor - promedio) < 0.01:
            return "MANTENER"
        return "COMPRA" if valor < promedio else "VENTA"

    def _obtener_id_combo(self, texto_combo: str, nombre_campo: str) -> int:
        if not texto_combo:
            raise ValueError(f"Debes seleccionar {nombre_campo}.")
        return int(texto_combo.split(" - ")[0])

    def _seleccionar_combo_por_id(self, combo: ttk.Combobox, id_buscado: int) -> None:
        for indice, valor in enumerate(combo["values"]):
            if valor.startswith(f"{id_buscado} - "):
                combo.current(indice)
                return

    def _obtener_datos_formulario_trm(self) -> tuple[str, int, float, int]:
        fecha = self.entry_fecha.get().strip()
        valor_texto = self.entry_valor.get().strip().replace(",", ".")
        id_moneda = self._obtener_id_combo(self.combo_moneda.get(), "una moneda")
        id_usuario = self._obtener_id_combo(self.combo_usuario.get(), "un usuario")
        if not fecha or not valor_texto:
            raise ValueError("La fecha, moneda, valor y usuario son obligatorios.")
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("La fecha debe tener formato AAAA-MM-DD. Ejemplo: 2026-05-25") from exc
        try:
            valor = float(valor_texto)
        except ValueError as exc:
            raise ValueError("El valor debe ser numérico. Ejemplo: 3850.75") from exc
        if valor <= 0:
            raise ValueError("La TRM/tasa debe ser mayor que cero.")
        return fecha, id_moneda, valor, id_usuario

    def _seleccionar_fila_registro(self, _event=None) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        try:
            id_registro = int(seleccion[0])
            registro = self.servicio_registros.obtener(id_registro)
            if not registro:
                raise ValueError("El registro seleccionado ya no existe.")
            self.id_registro_seleccionado = id_registro
            self.entry_fecha.delete(0, tk.END)
            self.entry_fecha.insert(0, registro["fecha"])
            self.entry_valor.delete(0, tk.END)
            self.entry_valor.insert(0, str(registro["valor"]))
            self._seleccionar_combo_por_id(self.combo_moneda, int(registro["id_moneda"]))
            self._seleccionar_combo_por_id(self.combo_usuario, int(registro["id_usuario"]))
            self.label_modo.configure(text=f"Modo: editando registro ID {id_registro}")
            self._actualizar_resumen_moneda()
        except Exception as error:
            messagebox.showerror("Error de selección", str(error))

    def _formato_moneda(self, valor: float) -> str:
        return f"$ {valor:,.2f}"

    def _formato_numero(self, valor: float) -> str:
        return f"{valor:,.2f}"


def iniciar_app() -> None:
    root = tk.Tk()
    DolarTrackApp(root)
    root.mainloop()


if __name__ == "__main__":
    iniciar_app()
