from flask import Flask, render_template, request, url_for, redirect, session

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-despues"  # necesaria para manejar sesión

# Lista (en memoria) de ciudadanos registrados que recibirían correos
registered_users = set()  # guardaremos solo los correos


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

        if not email:
            mensaje = "Por favor ingresa un correo electrónico."
        else:
            # Registramos al usuario en la lista de ciudadanos
            registered_users.add(email.strip().lower())
            session["user_email"] = email.strip().lower()
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
            # Aquí simulamos el envío de correos a todos los ciudadanos registrados
            num_destinatarios = len(registered_users)
            print("INCIDENTE REGISTRADO POR ENTIDAD OFICIAL:")
            print(nombre, email, org, incidente, nivel, descripcion)
            print("Se enviaría alerta a estos correos ciudadanos:")
            for u in registered_users:
                print("  -", u)

            mensaje = (
                f"El incidente ha sido registrado correctamente. "
                f"{num_destinatarios} ciudadanos registrados recibirían una alerta por correo."
            )
            tipo = "ok"
        else:
            mensaje = (
                "Error: Solo entidades ambientales oficiales con credenciales válidas pueden reportar incidentes."
            )
            tipo = "error"

    return render_template("report_new.html", mensaje=mensaje, tipo=tipo)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
