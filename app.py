# ============================================================
# MOTOPREDICT — Servidor web con Flask
# Rutas: GET / → formulario  |  POST / → predicción
#        GET /api/referencias/<marca> → JSON para AJAX
# ============================================================

from flask import Flask, render_template, request, jsonify
from modelo import entrenar_y_predecir

app = Flask(__name__)


# ── Datos de referencia ──────────────────────────────────────

# Catálogo de marcas, modelos e imágenes disponibles.
# "referencias" llena el select del formulario;
# "imagenes" determina qué foto mostrar en la vista previa.
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


# ── Ruta principal ───────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def inicio():
    resultado = None
    error     = None

    if request.method == "POST":
        try:
            marca       = request.form.get("marca", "")
            referencia  = request.form.get("referencia", "")
            kilometraje = float(request.form.get("kilometraje", 0))
            km_dia      = float(request.form.get("km_dia", 1))
            consumo     = request.form.get("consumo", "no")

            if kilometraje <= 0:
                error = "El kilometraje debe ser mayor a 0."
            elif km_dia <= 0:
                error = "Los kilómetros por día deben ser mayor a 0."
            else:
                # El modelo espera 1 (consumo anormal) o 0 (normal)
                consumo_anormal = 1 if consumo == "si" else 0

                resultado = entrenar_y_predecir(kilometraje, km_dia, consumo_anormal)

                # Agrega datos de la moto al resultado para mostrarlos en la plantilla
                resultado["marca"]       = marca
                resultado["referencia"]  = referencia
                resultado["kilometraje"] = int(kilometraje)
                resultado["km_dia"]      = km_dia

                # Resuelve la imagen: referencia específica → default de la marca
                info_marca  = MOTOS.get(marca, {})
                imagenes    = info_marca.get("imagenes", {})
                resultado["imagen_moto"] = imagenes.get(referencia, imagenes.get("default", "moto_default.png"))

        except ValueError:
            error = "Por favor, ingresa valores numéricos válidos."
        except Exception as e:
            error = f"Error al procesar la predicción: {str(e)}"

    return render_template("index.html", resultado=resultado, error=error, motos=MOTOS)


# ── API de referencias (AJAX) ────────────────────────────────

# JavaScript llama a este endpoint al cambiar la marca para
# poblar el segundo select sin recargar la página.
@app.route("/api/referencias/<marca>")
def get_referencias(marca):
    info = MOTOS.get(marca, {})
    return jsonify({"referencias": info.get("referencias", [])})


# ── Arranque local ───────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)  # debug=True: recarga automática y errores detallados
