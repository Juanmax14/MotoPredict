
# MOTOPREDICT — SERVIDOR WEB CON FLASK

# Flask es un microframework de Python que permite crear
# aplicaciones web de forma sencilla.
#
# ¿Cómo funciona Flask aquí?
#   1. El usuario abre el navegador en http://127.0.0.1:5000
#   2. Flask recibe la petición HTTP (GET o POST)
#   3. Si es GET → muestra el formulario vacío
#   4. Si es POST → lee los datos del formulario, llama al modelo,
#      y devuelve la página con los resultados


from flask import Flask, render_template, request, jsonify
from modelo import entrenar_y_predecir

# Crea la instancia de la aplicación Flask
# __name__ le dice a Flask dónde buscar plantillas y archivos estáticos
app = Flask(__name__)



# DATOS DE REFERENCIA — MARCAS Y MODELOS

#
# Diccionario con las marcas disponibles y sus referencias.
# Se usa para llenar el formulario desplegable de forma dinámica.
# La imagen asociada se usa para la vista previa de la moto.


MOTOS = {
    "Hero": {
        "referencias": ["Hunk 125R", "Splendor+", "Passion Pro", "Glamour"],
        "imagenes": {
            "Hunk 125R": "hunk125r.png",
            "default":   "moto_default.png"
        }
    },
    "Bajaj": {
        "referencias": ["Pulsar NS200", "Pulsar 150", "Discover 125", "Platina 110"],
        "imagenes": {"default": "moto_default.png"}
    },
    "Honda": {
        "referencias": ["CB190R", "CB125F", "XR150L", "Wave 110"],
        "imagenes": {"default": "moto_default.png"}
    },
    "Yamaha": {
        "referencias": ["FZ-S FI", "MT-03", "SZ-RR", "YBR 125"],
        "imagenes": {"default": "moto_default.png"}
    },
    "AKT": {
        "referencias": ["TTX 125", "Dynamic R", "NKD 125", "RTX 150"],
        "imagenes": {"default": "moto_default.png"}
    }

}



# RUTA PRINCIPAL

@app.route("/", methods=["GET", "POST"])
def inicio():
    """
    Ruta raíz de la aplicación.

    GET:  Renderiza la página con el formulario vacío.
    POST: Recibe los datos del formulario, ejecuta el modelo
          y renderiza la página con los resultados.
    """

    resultado = None   # Sin predicción hasta que el usuario envíe el formulario
    error     = None   # Mensaje de error si algo falla

    if request.method == "POST":
        try:
            # ── Captura de datos del formulario ───────────────
            marca       = request.form.get("marca", "")
            referencia  = request.form.get("referencia", "")
            kilometraje = float(request.form.get("kilometraje", 0))
            km_dia      = float(request.form.get("km_dia", 1))
            consumo     = request.form.get("consumo", "no")

            # Validación básica
            if kilometraje <= 0:
                error = "El kilometraje debe ser mayor a 0."
            elif km_dia <= 0:
                error = "Los kilómetros por día deben ser mayor a 0."
            else:
                # Convierte la respuesta de consumo a valor numérico
                # El modelo espera 1 (sí hay problema) o 0 (todo normal)
                consumo_anormal = 1 if consumo == "si" else 0

                # ── Llamada al modelo ──────────────────────────
                # Aquí se entrena el modelo y se genera la predicción
                resultado = entrenar_y_predecir(
                    kilometraje,
                    km_dia,
                    consumo_anormal
                )

                # Agrega datos de la moto al resultado para mostrarlos
                resultado["marca"]      = marca
                resultado["referencia"] = referencia
                resultado["kilometraje"] = int(kilometraje)
                resultado["km_dia"]     = km_dia

                # Determina la imagen de la moto según selección
                info_marca = MOTOS.get(marca, {})
                imagenes   = info_marca.get("imagenes", {})
                imagen_moto = imagenes.get(referencia, imagenes.get("default", "moto_default.png"))
                resultado["imagen_moto"] = imagen_moto

        except ValueError:
            error = "Por favor, ingresa valores numéricos válidos."
        except Exception as e:
            error = f"Error al procesar la predicción: {str(e)}"

    # Renderiza la plantilla HTML y pasa los datos
    return render_template(
        "index.html",
        resultado=resultado,
        error=error,
        motos=MOTOS
    )



# RUTA API — OBTENER REFERENCIAS POR MARCA (AJAX)


@app.route("/api/referencias/<marca>")
def get_referencias(marca):
    """
    Endpoint JSON que devuelve las referencias disponibles
    para una marca específica.

    Usado por JavaScript para actualizar el segundo desplegable
    de forma dinámica sin recargar la página (AJAX).

    Ejemplo: GET /api/referencias/Hero
    Respuesta: {"referencias": ["Hunk 125R", "Splendor+", ...]}
    """
    info = MOTOS.get(marca, {})
    referencias = info.get("referencias", [])
    return jsonify({"referencias": referencias})



# EJECUCIÓN LOCAL


if __name__ == "__main__":
    # debug=True activa el modo desarrollo:
    #   - Muestra errores detallados en el navegador
    #   - Recarga automáticamente cuando cambias el código
    # IMPORTANTE: nunca usar debug=True en producción
    app.run(debug=True)
