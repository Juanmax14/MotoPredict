# ============================================================
# MOTOPREDICT — Modelo de predicción con Machine Learning
# Entrena un modelo de Regresión Logística por cada componente
# y predice si requiere mantenimiento según los datos del usuario.
# ============================================================

import threading
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


# ── Configuración de componentes ─────────────────────────────

# Intervalo recomendado (en km) para cada componente
componentes = {
    "aceite_motor":        3000,
    "cadena_transmision":  1000,
    "bujia":               3000,
    "filtro_aire":         3000,
    "frenos":              3000
}

# Nombre e icono legibles para mostrar en la interfaz
NOMBRES_COMPONENTES = {
    "aceite_motor":        "Aceite Motor",
    "cadena_transmision":  "Cadena Transmisión",
    "bujia":               "Bujía",
    "filtro_aire":         "Filtro de Aire",
    "frenos":              "Frenos"
}

ICONOS_COMPONENTES = {
    "aceite_motor":        "🛢️",
    "cadena_transmision":  "⛓️",
    "bujia":               "⚡",
    "filtro_aire":         "🌬️",
    "frenos":              "🛑"
}

# Mensajes personalizados por componente y nivel de riesgo
MENSAJES = {
    "aceite_motor": {
        "ALTO":  "El aceite motor superó su vida útil. Rodar así puede causar daño severo al motor por falta de lubricación. Ve al taller hoy mismo.",
        "MEDIO": "El aceite se acerca al final de su ciclo. Planifica el cambio antes de tu próxima salida larga para proteger el motor.",
        "BAJO":  "Aceite en buen estado. Mantén el plan de cambios cada 3 000 km y revisa el nivel regularmente.",
    },
    "cadena_transmision": {
        "ALTO":  "La cadena presenta desgaste crítico: puede estar floja o a punto de romperse en marcha. Revisa tensión y lubricación de inmediato.",
        "MEDIO": "La cadena necesita lubricación y posible ajuste pronto. Evita recorridos largos sin revisarla antes.",
        "BAJO":  "Cadena en buen estado. Lubrica cada 500–1 000 km según el manual para mantenerla en óptimas condiciones.",
    },
    "bujia": {
        "ALTO":  "La bujía puede estar deteriorada o con depósitos de carbón, causando arranque difícil, pérdida de potencia y mayor consumo de combustible.",
        "MEDIO": "La bujía se acerca a su intervalo de reemplazo. Cámbiala pronto para mantener el rendimiento del motor.",
        "BAJO":  "Bujía funcionando correctamente. Inspecciona el electrodo en cada servicio para detectar desgaste temprano.",
    },
    "filtro_aire": {
        "ALTO":  "El filtro de aire está posiblemente obstruido. Un filtro sucio reduce la potencia, aumenta el consumo y puede dañar el motor a largo plazo.",
        "MEDIO": "El filtro empieza a acumular suciedad. Límpialo o reemplázalo pronto para mejorar la respuesta del motor.",
        "BAJO":  "Filtro de aire limpio y con buen flujo. En zonas de mucho polvo aumenta la frecuencia de inspección.",
    },
    "frenos": {
        "ALTO":  "ATENCIÓN: Las pastillas de freno pueden estar al límite. Los frenos son críticos para tu seguridad — no salgas sin revisarlos en un taller.",
        "MEDIO": "Las pastillas muestran desgaste moderado. Programa una revisión pronto; no esperes a notar reducción en la frenada.",
        "BAJO":  "Sistema de frenos en buen estado. Verifica el nivel de líquido de frenos en cada servicio y atiende cualquier chirrido.",
    },
}

# El orden importa: debe coincidir exactamente con el orden
# en que se entrenó el StandardScaler.
COLUMNAS_MODELO = ["kilometraje_actual", "km_desde_servicio", "km_por_dia", "consumo_anormal"]


# ── Caché de modelos entrenados ──────────────────────────────

# Se llena la primera vez que se hace una predicción y se reutiliza
# en todas las solicitudes siguientes.
_modelos_cache = {}
_lock = threading.Lock()  # protege contra condición de carrera en el primer request


# ── Entrenamiento ────────────────────────────────────────────

def _entrenar():
    """Lee el dataset y entrena un modelo por cada componente."""
    dataset = pd.read_excel("dataset_motopredict.xlsx")

    for componente in componentes:
        datos = dataset[dataset["componente"] == componente].copy()

        X = datos[COLUMNAS_MODELO]
        y = datos["necesita_mantenimiento"]

        # 70% entrenamiento / 30% prueba. random_state fija el resultado
        # para que las métricas sean reproducibles entre ejecuciones.
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.30, random_state=42
        )

        # StandardScaler lleva los datos a media=0 y desviación=1.
        # Solo se ajusta (fit) con datos de entrenamiento para no
        # "filtrar" información del conjunto de prueba.
        escalador   = StandardScaler()
        X_train_esc = escalador.fit_transform(X_train)
        X_test_esc  = escalador.transform(X_test)

        # class_weight="balanced" corrige el desbalance de clases
        # (hay más casos "no necesita" que "sí necesita" en el dataset).
        modelo = LogisticRegression(max_iter=1000, class_weight="balanced")
        modelo.fit(X_train_esc, y_train)

        y_pred = modelo.predict(X_test_esc)

        _modelos_cache[componente] = {
            "modelo":    modelo,
            "escalador": escalador,
            "metricas": {
                "accuracy":  round(accuracy_score(y_test, y_pred) * 100, 1),
                "precision": round(precision_score(y_test, y_pred, zero_division=0) * 100, 1),
                "recall":    round(recall_score(y_test, y_pred, zero_division=0) * 100, 1),
                "f1":        round(f1_score(y_test, y_pred, zero_division=0) * 100, 1),
            }
        }


# ── Predicción ───────────────────────────────────────────────

def estimar_km_desde_servicio(kilometraje_actual, intervalo):
    # El módulo (%) calcula cuántos km lleva dentro del ciclo actual.
    # Ejemplo: 8900 km con intervalo 3000 → 8900 % 3000 = 2900 km usados.
    return kilometraje_actual % intervalo


def entrenar_y_predecir(kilometraje_actual, km_por_dia, consumo_anormal):
    # Double-checked locking: si dos requests llegan al mismo tiempo
    # antes de entrenar, solo uno ejecuta _entrenar(). El segundo
    # espera y luego encuentra el caché ya lleno.
    if not _modelos_cache:
        with _lock:
            if not _modelos_cache:
                _entrenar()

    resultados         = []
    mayor_probabilidad = 0
    componente_urgente = nombre_urgente = icono_urgente = ""
    metricas_por_comp  = []

    # Array reutilizable para los 5 componentes. Solo cambia
    # km_desde_servicio (índice 1) en cada iteración.
    fila_base = np.array([[float(kilometraje_actual), 0.0, float(km_por_dia), float(consumo_anormal)]])

    for componente, intervalo in componentes.items():
        cache     = _modelos_cache[componente]
        modelo    = cache["modelo"]
        escalador = cache["escalador"]
        met       = cache["metricas"]

        metricas_por_comp.append({
            "componente": NOMBRES_COMPONENTES[componente],
            "icono":      ICONOS_COMPONENTES[componente],
            **met,
        })

        # Cálculos preventivos basados en el ciclo de mantenimiento
        km_desde_servicio = estimar_km_desde_servicio(kilometraje_actual, intervalo)
        porcentaje_usado  = (km_desde_servicio / intervalo) * 100
        km_restantes      = intervalo - km_desde_servicio
        dias_restantes    = km_restantes / km_por_dia if km_por_dia > 0 else 999

        # Predicción del modelo para este componente
        fila_base[0, 1] = float(km_desde_servicio)
        datos_esc        = escalador.transform(fila_base)
        prediccion       = modelo.predict(datos_esc)[0]
        probabilidad     = modelo.predict_proba(datos_esc)[0][1] * 100  # probabilidad de clase 1

        # Nivel de riesgo combinando uso del ciclo y consumo anormal
        if porcentaje_usado >= 90 or consumo_anormal == 1:
            riesgo = "ALTO"
        elif porcentaje_usado >= 75:
            riesgo = "MEDIO"
        else:
            riesgo = "BAJO"

        # Decisión final: ML + regla preventiva al 85% del ciclo
        # Más conservador que el modelo solo — prioriza la seguridad.
        if prediccion == 1 or porcentaje_usado >= 85 or consumo_anormal == 1:
            decision, decision_ok = "Requiere mantenimiento", False
        else:
            decision, decision_ok = "Estado aceptable", True

        nombre        = NOMBRES_COMPONENTES[componente]
        recomendacion = MENSAJES[componente][riesgo]

        # Identifica el componente con mayor probabilidad para el resumen ejecutivo
        if probabilidad > mayor_probabilidad:
            mayor_probabilidad = probabilidad
            componente_urgente = componente
            nombre_urgente     = nombre
            icono_urgente      = ICONOS_COMPONENTES[componente]

        resultados.append({
            "componente":       componente,
            "nombre":           nombre,
            "icono":            ICONOS_COMPONENTES[componente],
            "probabilidad":     round(probabilidad, 1),
            "riesgo":           riesgo,
            "porcentaje_usado": round(porcentaje_usado, 1),
            "km_restantes":     round(km_restantes, 0),
            "dias_restantes":   round(dias_restantes, 1),
            "decision":         decision,
            "decision_ok":      decision_ok,
            "recomendacion":    recomendacion,
            "intervalo_km":     intervalo,
        })

    # Promedio de métricas globales calculado directamente del caché
    metricas_resumen = {
        k: round(sum(c["metricas"][k] for c in _modelos_cache.values()) / len(_modelos_cache), 1)
        for k in ("accuracy", "precision", "recall", "f1")
    }
    metricas_resumen["por_componente"] = metricas_por_comp

    return {
        "componente_urgente": componente_urgente,
        "nombre_urgente":     nombre_urgente,
        "icono_urgente":      icono_urgente,
        "mayor_probabilidad": round(mayor_probabilidad, 1),
        "requieren_atencion": sum(1 for r in resultados if not r["decision_ok"]),
        "resultados":         resultados,
        "metricas":           metricas_resumen,
    }
