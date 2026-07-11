# Generador de Facturas con Streamlit

Proyecto modular para registrar facturas, generar PDF y enviar la factura por correo usando Gmail SMTP.

## Estructura

```text
streamlit_facturas_modular/
├── app.py
├── config.py
├── database.py
├── factura_service.py
├── pdf_utils.py
├── email_service.py
├── requirements.txt
└── README.md
```

## Instalacion

```bash
pip install -r requirements.txt
```

## Configurar correo Gmail con variables de entorno

No coloques el correo ni la contraseña dentro del codigo.

En Windows CMD:

```bash
setx FACTURAS_EMAIL_REMITENTE "tu_correo@gmail.com"
setx FACTURAS_EMAIL_PASSWORD "tu_password_de_aplicacion"
```

Cierra y vuelve a abrir la terminal despues de ejecutar `setx`.

## Ejecutar

```bash
streamlit run app.py
```

## Flujo

1. Selecciona productos.
2. Registra la factura.
3. Descarga el PDF.
4. Ingresa un correo de destino.
5. Envia la factura adjunta por correo.
