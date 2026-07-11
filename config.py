"""Configuracion general del proyecto."""

DB_NAME = "sistema_facturas.db"
IGV_RATE = 0.18
MONEDA = "S/"

# Configuracion SMTP para envio de facturas por correo.
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

# Nombres de variables de entorno.
# En Windows puedes configurarlas con:
# setx FACTURAS_EMAIL_REMITENTE "tu_correo@gmail.com"
# setx FACTURAS_EMAIL_PASSWORD "tu_password_de_aplicacion"
EMAIL_SENDER_ENV = "FACTURAS_EMAIL_REMITENTE"
EMAIL_PASSWORD_ENV = "FACTURAS_EMAIL_PASSWORD"
