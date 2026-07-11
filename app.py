"""Aplicacion principal de Streamlit.

Este archivo solo contiene interfaz y coordinacion general.
Las funcionalidades estan separadas en database.py, factura_service.py y pdf_utils.py.
"""

from datetime import datetime

import streamlit as st

from config import MONEDA
from database import (
    cargar_historial,
    cargar_productos_db,
    guardar_factura_en_db,
    inicializar_db,
    obtener_siguiente_factura,
)
from factura_service import (
    calcular_totales,
    construir_detalle_factura,
    validar_datos_factura,
)
from pdf_utils import generar_pdf_factura
from email_service import enviar_factura_pdf


st.set_page_config(
    page_title="Generador de Facturas",
    page_icon="📄",
    layout="centered",
)


@st.cache_data(ttl=60)
def cargar_productos_cache():
    """Carga productos con cache de Streamlit."""
    return cargar_productos_db()


def mostrar_vista_previa(nro_factura, fecha_factura, nombre_cliente, ruc_dni, df_detalle, subtotal, igv, total_general):
    """Muestra la vista previa de la factura en pantalla."""
    st.subheader("📝 Vista Previa de la Factura")

    factura_box = st.container(border=True)
    with factura_box:
        st.markdown(f"### **FACTURA: {nro_factura}**")
        st.write(f"**Fecha:** {fecha_factura.strftime('%d/%m/%Y')}")
        st.write(f"**Cliente:** {nombre_cliente} | **ID/RUC:** {ruc_dni}")
        st.markdown("---")

        st.dataframe(
            df_detalle.set_index("Producto"),
            use_container_width=True,
        )

        st.markdown("---")
        _, col_totales = st.columns([3, 1])
        with col_totales:
            st.write(f"**Subtotal:** {MONEDA} {subtotal:,.2f}")
            st.write(f"**IGV (18%):** {MONEDA} {igv:,.2f}")
            st.markdown(f"### **Total: {MONEDA} {total_general:,.2f}**")


def mostrar_historial():
    """Muestra el historial de facturas guardadas."""
    st.markdown("---")
    st.subheader("📚 Historial de Pedidos Registrados")

    try:
        df_historial = cargar_historial()

        if not df_historial.empty:
            df_historial = df_historial.rename(columns={
                "nro_factura": "Factura",
                "fecha": "Fecha",
                "cliente": "Cliente",
                "ruc_dni": "RUC/DNI",
                "subtotal": "Subtotal",
                "iva": "IGV",
                "total": "Total",
                "fecha_registro": "Fecha de registro",
            })
            st.dataframe(df_historial, use_container_width=True)
        else:
            st.caption("Aun no se ha registrado ningun pedido.")

    except Exception as exc:
        st.error(f"Error al cargar historial: {exc}")


def main():
    """Punto de entrada de la app."""
    inicializar_db()

    st.title("📄 Generador Automático de Facturas")
    st.write("Selecciona los productos y cantidades para generar la factura.")

    df_productos = cargar_productos_cache()

    st.subheader("👤 Datos de Facturación")
    col_cliente, col_factura = st.columns(2)

    with col_cliente:
        nombre_cliente = st.text_input("Nombre del Cliente / Empresa", "Juan Perez")
        ruc_dni = st.text_input("RUC / DNI / Identificacion", "12345678901")

    with col_factura:
        fecha_factura = st.date_input("Fecha de Emision", datetime.now())
        nro_sugerido = obtener_siguiente_factura()
        nro_factura = st.text_input("Numero de Factura", nro_sugerido)

    st.markdown("---")
    st.subheader("🛒 Selección de Productos")

    productos_seleccionados = st.multiselect(
        "Elige los productos a incluir en la factura:",
        options=df_productos["producto"].sort_values().tolist(),
    )

    cantidades_por_producto = {}

    if productos_seleccionados:
        st.write("Define las cantidades:")

        for producto in productos_seleccionados:
            row = df_productos[df_productos["producto"] == producto].iloc[0]
            precio_unitario = float(row["precio"])

            col_producto, col_cantidad, col_total = st.columns([2, 1, 1])

            with col_producto:
                st.text(f"{producto} ({MONEDA} {precio_unitario:,.2f} c/u)")

            with col_cantidad:
                cantidad = st.number_input(
                    f"Cantidad para {producto}",
                    min_value=1,
                    value=1,
                    step=1,
                    key=f"cant_{producto}",
                )

            with col_total:
                st.text(f"Total: {MONEDA} {precio_unitario * cantidad:,.2f}")

            cantidades_por_producto[producto] = cantidad

        df_detalle = construir_detalle_factura(
            df_productos,
            productos_seleccionados,
            cantidades_por_producto,
        )
        subtotal, igv, total_general = calcular_totales(df_detalle)

        st.markdown("---")
        mostrar_vista_previa(
            nro_factura,
            fecha_factura,
            nombre_cliente,
            ruc_dni,
            df_detalle,
            subtotal,
            igv,
            total_general,
        )

        if st.button("💾 Procesar y Registrar Factura", type="primary"):
            errores = validar_datos_factura(
                nombre_cliente,
                ruc_dni,
                nro_factura,
                productos_seleccionados,
            )

            if errores:
                for error in errores:
                    st.error(error)
            else:
                exito, mensaje = guardar_factura_en_db(
                    nro_factura,
                    fecha_factura,
                    nombre_cliente,
                    ruc_dni,
                    df_detalle,
                    subtotal,
                    igv,
                    total_general,
                )

                if exito:
                    pdf_bytes = generar_pdf_factura(
                        nro_factura,
                        fecha_factura,
                        nombre_cliente,
                        ruc_dni,
                        df_detalle,
                        subtotal,
                        igv,
                        total_general,
                    )
                    st.session_state["ultima_factura_pdf"] = pdf_bytes
                    st.session_state["ultima_factura_nombre"] = f"{nro_factura}.pdf"
                    st.success(mensaje)
                    st.cache_data.clear()
                else:
                    st.error(mensaje)

        if "ultima_factura_pdf" in st.session_state:
            st.download_button(
                label="⬇️ Descargar Factura en PDF",
                data=st.session_state["ultima_factura_pdf"],
                file_name=st.session_state["ultima_factura_nombre"],
                mime="application/pdf",
            )

            st.markdown("---")
            st.subheader("📧 Enviar factura por correo")
            correo_destino = st.text_input(
                "Correo del destinatario",
                placeholder="cliente@empresa.com",
                key="correo_destino_factura",
            )

            if st.button("📨 Enviar factura por correo"):
                exito_correo, mensaje_correo = enviar_factura_pdf(
                    correo_destino=correo_destino,
                    pdf_bytes=st.session_state["ultima_factura_pdf"],
                    nombre_pdf=st.session_state["ultima_factura_nombre"],
                    nro_factura=nro_factura,
                    nombre_cliente=nombre_cliente,
                )

                if exito_correo:
                    st.success(mensaje_correo)
                else:
                    st.error(mensaje_correo)

    else:
        st.info("Por favor, selecciona al menos un producto arriba para empezar a estructurar la factura.")

    mostrar_historial()


if __name__ == "__main__":
    main()
