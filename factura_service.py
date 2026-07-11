"""Logica de negocio para construir y validar facturas."""

import pandas as pd

from config import IGV_RATE


def construir_detalle_factura(df_productos, productos_seleccionados, cantidades_por_producto):
    """Construye el DataFrame de detalle de factura desde productos y cantidades."""
    lineas = []

    for producto in productos_seleccionados:
        row = df_productos[df_productos["producto"] == producto].iloc[0]
        precio_unitario = float(row["precio"])
        cantidad = int(cantidades_por_producto[producto])
        total_linea = precio_unitario * cantidad

        lineas.append({
            "Producto": producto,
            "Precio Unitario": precio_unitario,
            "Cantidad": cantidad,
            "Total": total_linea,
        })

    return pd.DataFrame(lineas)


def calcular_totales(df_detalle):
    """Calcula subtotal, IGV y total general."""
    subtotal = float(df_detalle["Total"].sum())
    igv = subtotal * IGV_RATE
    total_general = subtotal + igv
    return subtotal, igv, total_general


def validar_datos_factura(nombre_cliente, ruc_dni, nro_factura, productos_seleccionados):
    """Valida datos minimos antes de registrar una factura."""
    errores = []

    if not nombre_cliente or not nombre_cliente.strip():
        errores.append("Debe ingresar el nombre del cliente o empresa.")

    if not ruc_dni or not ruc_dni.strip():
        errores.append("Debe ingresar RUC, DNI o identificacion.")

    if not nro_factura or not nro_factura.strip():
        errores.append("Debe ingresar el numero de factura.")

    if not productos_seleccionados:
        errores.append("Debe seleccionar al menos un producto.")

    ruc_dni_limpio = ruc_dni.strip() if ruc_dni else ""
    if ruc_dni_limpio and not ruc_dni_limpio.isdigit():
        errores.append("El RUC/DNI debe contener solo numeros.")

    if ruc_dni_limpio and len(ruc_dni_limpio) not in (8, 11):
        errores.append("El DNI suele tener 8 digitos y el RUC 11 digitos.")

    return errores
