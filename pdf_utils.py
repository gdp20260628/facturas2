"""Generacion de PDF para facturas."""

from fpdf import FPDF

from config import MONEDA


def generar_pdf_factura(
    nro_factura,
    fecha_factura,
    nombre_cliente,
    ruc_dni,
    df_detalle,
    subtotal,
    igv,
    total_general,
):
    """Genera el PDF de la factura y devuelve bytes listos para descargar."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "FACTURA", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Nro. de Factura: {nro_factura}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Fecha de Emision: {fecha_factura.strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Cliente: {nombre_cliente}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"RUC / DNI: {ruc_dni}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    col_widths = [80, 35, 25, 35]
    headers = ["Producto", "Precio Unit.", "Cantidad", "Total"]

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    for width, header in zip(col_widths, headers):
        pdf.cell(width, 8, header, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    for _, fila in df_detalle.iterrows():
        pdf.cell(col_widths[0], 8, str(fila["Producto"]), border=1)
        pdf.cell(col_widths[1], 8, f"{MONEDA} {fila['Precio Unitario']:,.2f}", border=1, align="R")
        pdf.cell(col_widths[2], 8, str(int(fila["Cantidad"])), border=1, align="C")
        pdf.cell(col_widths[3], 8, f"{MONEDA} {fila['Total']:,.2f}", border=1, align="R")
        pdf.ln()

    pdf.ln(4)
    ancho_total = sum(col_widths[:3])

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(ancho_total, 7, "Subtotal:", align="R")
    pdf.cell(col_widths[3], 7, f"{MONEDA} {subtotal:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.cell(ancho_total, 7, "IGV (18%):", align="R")
    pdf.cell(col_widths[3], 7, f"{MONEDA} {igv:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(ancho_total, 9, "TOTAL:", align="R")
    pdf.cell(col_widths[3], 9, f"{MONEDA} {total_general:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
