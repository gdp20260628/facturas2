"""Funciones relacionadas con PostgreSQL.

Este módulo permite:

- Consultar el catálogo de productos.
- Guardar facturas.
- Guardar los detalles de las facturas.
- Consultar el historial.
- Obtener el siguiente número sugerido de factura.

Las tablas utilizadas tienen el prefijo st_.
"""

from datetime import date, datetime

import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


# ============================================================
# CONEXIÓN DEL USUARIO LIMITADO
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("POSTGRES_USER")
pwd = os.getenv("POSTGRES_PASSWORD")

if not user or not pwd:
    raise ValueError(
        "No se encontraron POSTGRES_USER y POSTGRES_PASSWORD."
    )

host = (
    "dpg-d29qb6ripnbc73b70q00-a."
    "oregon-postgres.render.com"
)

database = "centrocapacitacion"


DATABASE_DSN = URL.create(
    drivername="postgresql+psycopg2",
    username=user,
    password=pwd,
    host=host,
    port=5432,
    database=database,
    query={
        "sslmode": "require",
    },
)


engine = create_engine(
    DATABASE_DSN,
    pool_pre_ping=True,
    pool_recycle=300,
)


# ============================================================
# TABLAS REQUERIDAS
# ============================================================

TABLAS_REQUERIDAS = {
    "st_productos",
    "st_pedidos",
    "st_detalle_pedidos",
}


def conectar_db():
    """Abre una conexión PostgreSQL."""

    return engine.connect()


def inicializar_db():
    """Verifica que las tablas st_ existan.

    La aplicación no crea las tablas porque utiliza un usuario
    con permisos restringidos.
    """

    consulta = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name IN (
              'st_productos',
              'st_pedidos',
              'st_detalle_pedidos'
          )
    """)

    with engine.connect() as conn:
        resultado = conn.execute(consulta)

        tablas_encontradas = {
            fila[0]
            for fila in resultado.fetchall()
        }

    tablas_faltantes = (
        TABLAS_REQUERIDAS
        - tablas_encontradas
    )

    if tablas_faltantes:
        nombres = ", ".join(
            sorted(tablas_faltantes)
        )

        raise RuntimeError(
            "No se encontraron las siguientes tablas: "
            f"{nombres}. "
            "Ejecuta primero crear_tablas_postgresql.py."
        )

    return True


def cargar_productos_db():
    """Devuelve el catálogo de productos como DataFrame."""

    consulta = text("""
        SELECT
            id,
            producto,
            precio::DOUBLE PRECISION AS precio
        FROM public.st_productos
        ORDER BY producto
    """)

    with engine.connect() as conn:
        return pd.read_sql_query(
            consulta,
            conn,
        )


def guardar_factura_en_db(
    nro_factura,
    fecha_factura,
    nombre_cliente,
    ruc_dni,
    df_detalle,
    subtotal,
    igv,
    total_general,
):
    """Guarda una factura y sus líneas de detalle.

    Retorna:
        tuple: (éxito: bool, mensaje: str)
    """

    nro_factura = str(
        nro_factura
    ).strip()

    nombre_cliente = str(
        nombre_cliente
    ).strip()

    ruc_dni = str(
        ruc_dni
    ).strip()

    if isinstance(fecha_factura, datetime):
        fecha_factura = fecha_factura.date()

    if not isinstance(fecha_factura, date):
        return (
            False,
            "La fecha de la factura no es válida.",
        )

    if not nro_factura:
        return (
            False,
            "El número de factura es obligatorio.",
        )

    if not nombre_cliente:
        return (
            False,
            "El nombre del cliente es obligatorio.",
        )

    if not ruc_dni:
        return (
            False,
            "El RUC o DNI es obligatorio.",
        )

    if df_detalle is None or df_detalle.empty:
        return (
            False,
            "La factura debe tener al menos un producto.",
        )

    insertar_pedido = text("""
        INSERT INTO public.st_pedidos (
            nro_factura,
            fecha,
            cliente,
            ruc_dni,
            subtotal,
            iva,
            total
        )
        VALUES (
            :nro_factura,
            :fecha,
            :cliente,
            :ruc_dni,
            :subtotal,
            :iva,
            :total
        )
    """)

    insertar_detalle = text("""
        INSERT INTO public.st_detalle_pedidos (
            nro_factura,
            producto,
            precio_unitario,
            cantidad,
            total
        )
        VALUES (
            :nro_factura,
            :producto,
            :precio_unitario,
            :cantidad,
            :total
        )
    """)

    datos_pedido = {
        "nro_factura": nro_factura,
        "fecha": fecha_factura,
        "cliente": nombre_cliente,
        "ruc_dni": ruc_dni,
        "subtotal": float(subtotal),
        "iva": float(igv),
        "total": float(total_general),
    }

    datos_detalle = []

    for _, fila in df_detalle.iterrows():
        datos_detalle.append({
            "nro_factura": nro_factura,
            "producto": str(
                fila["Producto"]
            ).strip(),
            "precio_unitario": float(
                fila["Precio Unitario"]
            ),
            "cantidad": int(
                fila["Cantidad"]
            ),
            "total": float(
                fila["Total"]
            ),
        })

    try:
        # La cabecera y los detalles se guardan
        # dentro de una sola transacción.
        with engine.begin() as conn:
            conn.execute(
                insertar_pedido,
                datos_pedido,
            )

            conn.execute(
                insertar_detalle,
                datos_detalle,
            )

        return (
            True,
            f"Factura {nro_factura} registrada correctamente.",
        )

    except IntegrityError as exc:
        codigo_postgresql = getattr(
            exc.orig,
            "pgcode",
            None,
        )

        if codigo_postgresql == "23505":
            return (
                False,
                "El número de factura "
                f"'{nro_factura}' ya se encuentra registrado.",
            )

        if codigo_postgresql == "23503":
            return (
                False,
                "No se pudo registrar el detalle porque "
                "la factura asociada no existe.",
            )

        if codigo_postgresql == "23514":
            return (
                False,
                "Uno de los valores no cumple las reglas "
                "de validación de la base de datos.",
            )

        return (
            False,
            "No se pudo registrar la factura debido a "
            "una restricción de integridad.",
        )

    except SQLAlchemyError as exc:
        return (
            False,
            "Error de base de datos al guardar "
            f"la factura: {exc}",
        )

    except Exception as exc:
        return (
            False,
            f"Error inesperado al guardar la factura: {exc}",
        )


def cargar_historial():
    """Devuelve el historial de facturas registradas."""

    consulta = text("""
        SELECT
            nro_factura,
            fecha,
            cliente,
            ruc_dni,
            subtotal::DOUBLE PRECISION AS subtotal,
            iva::DOUBLE PRECISION AS iva,
            total::DOUBLE PRECISION AS total,
            fecha_registro
        FROM public.st_pedidos
        ORDER BY fecha_registro DESC
    """)

    with engine.connect() as conn:
        return pd.read_sql_query(
            consulta,
            conn,
        )


def obtener_siguiente_factura():
    """Genera un número sugerido FAC-0001, FAC-0002, etc."""

    consulta = text("""
        SELECT nro_factura
        FROM public.st_pedidos
        WHERE nro_factura LIKE 'FAC-%'
        ORDER BY
            CAST(
                REPLACE(nro_factura, 'FAC-', '')
                AS INTEGER
            ) DESC
        LIMIT 1
    """)

    try:
        with engine.connect() as conn:
            ultima_factura = conn.execute(
                consulta
            ).scalar_one_or_none()

    except SQLAlchemyError:
        # Respaldo por si existe alguna factura con un formato
        # distinto de FAC-0001.
        consulta_respaldo = text("""
            SELECT nro_factura
            FROM public.st_pedidos
            WHERE nro_factura LIKE 'FAC-%'
            ORDER BY fecha_registro DESC
            LIMIT 1
        """)

        with engine.connect() as conn:
            ultima_factura = conn.execute(
                consulta_respaldo
            ).scalar_one_or_none()

    if ultima_factura is None:
        return "FAC-0001"

    try:
        ultimo_numero = int(
            str(ultima_factura).replace(
                "FAC-",
                "",
            )
        )

        return (
            f"FAC-{ultimo_numero + 1:04d}"
        )

    except ValueError:
        return "FAC-0001"


# ============================================================
# ALIAS DE COMPATIBILIDAD
# ============================================================

def cargar_historial_facturas():
    """Alias de compatibilidad con versiones anteriores."""

    return cargar_historial()


def obtener_siguiente_numero_factura():
    """Alias de compatibilidad con versiones anteriores."""

    return obtener_siguiente_factura()