"""Servicio para enviar facturas PDF por correo usando Gmail SMTP.

Las credenciales se leen desde variables de entorno. No coloques usuario ni
password directamente en el codigo fuente.
"""

import os
import re
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

from config import (
    EMAIL_PASSWORD_ENV,
    EMAIL_SENDER_ENV,
    SMTP_HOST,
    SMTP_PORT,
)


EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validar_correo_destino(correo_destino: str) -> tuple[bool, str]:
    """Valida formato basico del correo destino."""
    if not correo_destino or not correo_destino.strip():
        return False, "Debe ingresar un correo de destino."

    correo_limpio = correo_destino.strip()
    if not EMAIL_REGEX.match(correo_limpio):
        return False, "El correo de destino no tiene un formato valido."

    return True, "Correo valido."


def obtener_credenciales_correo() -> tuple[str | None, str | None]:
    """Obtiene usuario y password desde variables de entorno."""
    correo = os.getenv(EMAIL_SENDER_ENV)
    password = os.getenv(EMAIL_PASSWORD_ENV)
    return correo, password


def enviar_factura_pdf(
    correo_destino: str,
    pdf_bytes: bytes,
    nombre_pdf: str,
    nro_factura: str,
    nombre_cliente: str,
) -> tuple[bool, str]:
    """Envia la factura PDF adjunta por Gmail SMTP.

    Retorna:
        (True, mensaje) si se envio correctamente.
        (False, mensaje) si hubo error.
    """
    valido, mensaje_validacion = validar_correo_destino(correo_destino)
    if not valido:
        return False, mensaje_validacion

    correo_remitente, password = obtener_credenciales_correo()
    if not correo_remitente or not password:
        return (
            False,
            "Faltan variables de entorno para el correo remitente. "
            f"Configura {EMAIL_SENDER_ENV} y {EMAIL_PASSWORD_ENV}.",
        )

    if not pdf_bytes:
        return False, "No se encontro ningun PDF para enviar. Primero registra la factura."

    correo_destino = correo_destino.strip()

    asunto = f"Factura {nro_factura}"
    cuerpo = f"""Estimado/a,

Adjunto encontrará la factura {nro_factura} correspondiente a {nombre_cliente}.

Saludos.
"""

    mensaje = EmailMessage()
    mensaje["From"] = correo_remitente
    mensaje["To"] = correo_destino
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    mensaje.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=nombre_pdf,
    )

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(correo_remitente, password)
            smtp.send_message(mensaje)

        return True, f"Factura enviada correctamente a {correo_destino}."

    except smtplib.SMTPAuthenticationError:
        return (
            False,
            "No se pudo autenticar con Gmail. Verifica que uses una contraseña de aplicacion y que las variables de entorno esten bien configuradas.",
        )

    except Exception as exc:
        return False, f"Error al enviar el correo: {exc}"
