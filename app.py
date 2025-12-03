from flask import Flask, render_template, request, url_for, redirect, session
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage  # para incrustar la imagen del afiche

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-despues"  # necesaria para manejar sesión

# Lista de ciudadanos registrados:
# cada elemento será: {"nombre": ..., "email": ..., "municipio": ...}
registered_users = []


# ------------------ FUNCIÓN PARA ENVIAR CORREOS ------------------ #

def enviar_correo(destinatario, asunto, cuerpo_html, imagen_path=None):
    """
    Envía un correo en HTML (con versión de texto plano por compatibilidad)
    y opcionalmente incrusta una imagen (afiche).

    Usa SMTP con STARTTLS en el puerto 587, que es lo que suele funcionar
    mejor (como en RecuperAndes).
    """

    remitente = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")

    print("DEBUG EMAIL_USER:", remitente)  # Para verificar que sí se cargó

    if not remitente or not password:
        print("ERROR: No se encontraron EMAIL_USER o EMAIL_PASS en las variables de entorno.")
        return

    # Correo multipart/related: HTML + imagen inline
    msg = MIMEMultipart("related")
    msg["From"] = remitente
    msg["To"] = destinatario
    msg["Subject"] = asunto

    # Parte alternativa: texto plano + HTML
    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)

    # Texto plano mínimo
    texto_plano = "Este mensaje contiene información en formato HTML. Si no lo ves bien, revisa tu cliente de correo."
    msg_alternative.attach(MIMEText(texto_plano, "plain", "utf-8"))

    # Versión HTML
    msg_alternative.attach(MIMEText(cuerpo_html, "html", "utf-8"))

    # Adjuntar imagen incrustada si se pasa la ruta
    if imagen_path:
        try:
            # Asegurarnos de que la ruta es relativa al archivo actual
            base_dir = os.path.dirname(os.path.abspath(__file__))
            ruta_imagen = os.path.join(base_dir, imagen_path)

            with open(ruta_imagen, "rb") as img_file:
                img = MIMEImage(img_file.read())
                img.add_header("Content-ID", "<afiche>")
                img.add_header("Content-Disposition", "inline", filename="afiche_aguaguardian.png")
                msg.attach(img)
            print("DEBUG: Imagen del afiche cargada correctamente.")
        except Exception as e:
            print("Error cargando la imagen del afiche:", repr(e))

    # -------- Enviar usando SMTP con STARTTLS (puerto 587) -------- #
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(remitente, password)
            server.send_message(msg)

        print(f"Correo enviado correctamente a {destinatario}")
    except Exception as e:
        print("ERROR enviando correo:", repr(e))


# ------------------ RUTAS PRINCIPALES ------------------ #

# ---------- RUTA PRINCIPAL ----------
@app.route("/")
def index():
    # Podemos pasar el email del usuario logueado (si existe)
    user_email = session.get("user_email")
    return render_template("index.html", user_email=user_email)


# ---------- INTERFAZ ESTADO DEL AGUA ----------
@app.route("/estado")
def estado():
    return render_template("interfaz_principal.html")


# ---------- MAPA ----------
@app.route("/mapa")
def mapa():
    return render_template("map.html")


# ---------- ALERTAS (pantalla visual) ----------
@app.route("/alertas")
def alertas_new():
    return render_template("alertas_new.html")


# ---------- LOGIN / REGISTRO CIUDADANO ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    mensaje = None
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        municipio = request.form.get("municipio")  # viene del <select name="municipio">

        if not email or not municipio:
            mensaje = "Por favor ingresa tu correo y selecciona tu municipio."
        else:
            email = email.strip().lower()

            # Buscar si ya estaba registrado para actualizar
            encontrado = False
            for u in registered_users:
                if u["email"] == email:
                    u["nombre"] = nombre
                    u["municipio"] = municipio
                    encontrado = True
                    break

            if not encontrado:
                registered_users.append({
                    "nombre": nombre,
                    "email": email,
                    "municipio": municipio
                })

            session["user_email"] = email

            # --------- Correo automático de confirmación (con afiche) ---------
            asunto = "Registro exitoso – Red de Alertas Santurbán"
            cuerpo_html = f"""
            <html>
            <body style="font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
              <p>Hola <strong>{nombre}</strong>,</p>

              <p>
                Te has registrado correctamente en <strong>AquaGuardian</strong>, la red ciudadana que monitorea
                la calidad del agua que llega a tu municipio desde el Páramo de Santurbán.
              </p>

              <p>
                <strong>Municipio registrado:</strong> {municipio}.
              </p>

              <p>
                A partir de ahora, solo recibirás correos cuando se reporte un incidente
                que afecte directamente a <strong>{municipio}</strong>. No enviaremos alertas de otros pueblos
                para evitar ruido y desinformación.
              </p>

              <p>
                Cuando te llegue una alerta, verás palabras como <strong>pH</strong>, <strong>turbidez</strong> o
                <strong>metales</strong>. Si no las conoces, no te preocupes:
                en este afiche las explicamos con dibujos y ejemplos sencillos:
              </p>

              <div style="margin: 18px 0; text-align: center;">
                <img src="cid:afiche" alt="Afiche explicativo sobre la calidad del agua"
                     style="max-width: 600px; width: 100%; border-radius: 12px;">
              </div>

              <p>
                Gracias por ser parte de esta red que cuida el agua 💧
              </p>

              <p style="font-size: 0.85rem; color: #666;">
                AquaGuardian – Páramo de Santurbán
              </p>
            </body>
            </html>
            """

            enviar_correo(
                email,
                asunto,
                cuerpo_html,
                imagen_path="static/img/afiche_aguaguardian.png"
            )

            # Redirigimos a la página principal después de login
            return redirect(url_for("index"))

    return render_template("login.html", mensaje=mensaje)


@app.route("/logout")
def logout():
    session.pop("user_email", None)
    return redirect(url_for("index"))


# ---------- REPORTAR (SOLO ENTIDADES OFICIALES) ----------
@app.route("/reportar", methods=["GET", "POST"])
def report_new():
    mensaje = None
    tipo = None  # "ok" o "error"

    if request.method == "POST":
        org = request.form.get("org")
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        codigo = request.form.get("codigo")
        incidente = request.form.get("incidente")
        nivel = request.form.get("nivel")
        descripcion = request.form.get("descripcion")
        municipio_alerta = request.form.get("municipio_alerta")  # municipio afectado

        # Pasamos el correo a minúsculas para evitar problemas de mayúsculas/minúsculas
        email = (email or "").lower()

        # Dominios permitidos (simulación de entidades oficiales)
        dominios_oficiales = [
            "@danna1.gov.co",
            "@loewens2.gov.co",
            "@tein3.gov.co",
            "@cbu4.gov.co",
            "@resolviendoretos.com.co"
        ]

        autorizado_por_dominio = any(email.endswith(d) for d in dominios_oficiales)

        # Códigos por cada entidad oficial
        codigos_org = {
            "Danna1": "1Danna",
            "Loewens2": "loewenstein",
            "Tein3": "Millan",
            "CBU4": "uniandes",
            "ResolviendoRetos": "ProyectoFinal"
        }

        codigo_correcto = codigos_org.get(org) == codigo

        # Validación simulada
        if autorizado_por_dominio and codigo_correcto:
            print("INCIDENTE REGISTRADO POR ENTIDAD OFICIAL:")
            print(nombre, email, org, incidente, nivel, descripcion, "Municipio:", municipio_alerta)

            # Filtrar solo ciudadanos del municipio afectado
            destinatarios = [u for u in registered_users if u["municipio"] == municipio_alerta]

            print(f"Se enviaría alerta SOLO a ciudadanos del municipio {municipio_alerta}:")
            for u in destinatarios:
                print("  -", u["email"])

                # --------- Correo automático de alerta (con afiche) ---------
                asunto = f"ALERTA DE AGUA – {municipio_alerta} – Nivel {nivel}"
                cuerpo_html = f"""
                <html>
                <body style="font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
                  <p>Hola <strong>{u['nombre']}</strong>,</p>

                  <p>
                    Una entidad ambiental oficial (<strong>{org}</strong>) ha reportado un incidente
                    de calidad del agua que afecta al municipio de <strong>{municipio_alerta}</strong>.
                  </p>

                  <p><strong>Resumen del incidente:</strong></p>
                  <ul>
                    <li><strong>Tipo de incidente:</strong> {incidente}</li>
                    <li><strong>Nivel de alerta:</strong> {nivel}</li>
                  </ul>

                  <p>
                    Descripción técnica (para las autoridades y equipos técnicos):
                  </p>
                  <p style="background:#f5f8fa; padding:10px; border-radius:8px;">
                    {descripcion}
                  </p>

                  <p>
                    ¿Qué significa esto para ti? La entidad detectó cambios en indicadores como
                    pH, turbidez o metales. Esto puede indicar que el agua está un poco diferente a lo normal.
                  </p>

                  <p>
                    <strong>Recomendación principal:</strong><br>
                    Revisa las indicaciones de tu acueducto local y, si es necesario,
                    hierve el agua antes de consumirla.
                  </p>

                  <p>
                    Si quieres entender mejor qué significan estos términos técnicos,
                    revisa este afiche explicativo con lenguaje sencillo:
                  </p>

                  <div style="margin: 18px 0; text-align: center;">
                    <img src="cid:afiche" alt="Afiche explicativo sobre la calidad del agua"
                         style="max-width: 600px; width: 100%; border-radius: 12px;">
                  </div>

                  <p>
                    Esta alerta se envía solo a personas registradas en <strong>{municipio_alerta}</strong>
                    para no generar pánico en otros municipios a los que no afecta el incidente.
                  </p>

                  <p style="font-size: 0.85rem; color: #666;">
                    Red de Alertas Santurbán · AquaGuardian 💧
                  </p>
                </body>
                </html>
                """

                enviar_correo(
                    u["email"],
                    asunto,
                    cuerpo_html,
                    imagen_path="static/img/afiche_aguaguardian.png"
                )

            mensaje = (
                f"El incidente ha sido registrado correctamente. "
                f"{len(destinatarios)} ciudadanos de {municipio_alerta} han recibido una alerta por correo."
            )
            tipo = "ok"
        else:
            mensaje = (
                "Error: Solo entidades ambientales oficiales con credenciales válidas pueden reportar incidentes."
            )
            tipo = "error"

    # Lista de municipios para el <select> del formulario de entidades
    municipios_disponibles = sorted({u["municipio"] for u in registered_users}) or [
        "Bucaramanga", "Floridablanca", "Girón", "Piedecuesta",
        "California", "Vetas", "Suratá", "Tona", "Charta", "Matanza"
    ]

    return render_template("report_new.html",
                           mensaje=mensaje,
                           tipo=tipo,
                           municipios_disponibles=municipios_disponibles)


if __name__ == "__main__":
    # Replit normalmente respeta este host y puerto
    app.run(host="0.0.0.0", port=5000, debug=True)