
# MOTOPREDICT — MODELO DE PREDICCIÓN CON MACHINE LEARNING

import threading
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


componentes = {
    "aceite_motor":        3000,
    "cadena_transmision":  1000,
    "bujia":               3000,
    "filtro_aire":         3000,
    "frenos":              3000
}

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

# Orden de columnas que espera el escalador (debe coincidir con el entrenamiento)
COLUMNAS_MODELO = ["kilometraje_actual", "km_desde_servicio", "km_por_dia", "consumo_anormal"]

_modelos_cache = {}
_lock = threading.Lock()


def _entrenar():
    dataset = pd.read_excel("dataset_motopredict.xlsx")

    for componente in componentes:
        datos = dataset[dataset["componente"] == componente].copy()

        X = datos[COLUMNAS_MODELO]
        y = datos["necesita_mantenimiento"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.30, random_state=42
        )

        escalador    = StandardScaler()
        X_train_esc  = escalador.fit_transform(X_train)
        X_test_esc   = escalador.transform(X_test)

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


def estimar_km_desde_servicio(kilometraje_actual, intervalo):
    return kilometraje_actual % intervalo


def entrenar_y_predecir(kilometraje_actual, km_por_dia, consumo_anormal):
    # Double-checked locking: thread-safe lazy init
    if not _modelos_cache:
        with _lock:
            if not _modelos_cache:
                _entrenar()

    resultados         = []
    mayor_probabilidad = 0
    componente_urgente = nombre_urgente = icono_urgente = ""
    metricas_por_comp  = []

    # Fila base reutilizable: [km_actual, km_desde_servicio, km_dia, consumo]
    # km_desde_servicio (índice 1) varía por componente; el resto es constante
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

        km_desde_servicio = estimar_km_desde_servicio(kilometraje_actual, intervalo)
        porcentaje_usado  = (km_desde_servicio / intervalo) * 100
        km_restantes      = intervalo - km_desde_servicio
        dias_restantes    = km_restantes / km_por_dia if km_por_dia > 0 else 999

        fila_base[0, 1] = float(km_desde_servicio)
        datos_esc        = escalador.transform(fila_base)
        prediccion       = modelo.predict(datos_esc)[0]
        probabilidad     = modelo.predict_proba(datos_esc)[0][1] * 100

        if porcentaje_usado >= 90 or consumo_anormal == 1:
            riesgo = "ALTO"
        elif porcentaje_usado >= 75:
            riesgo = "MEDIO"
        else:
            riesgo = "BAJO"

        if prediccion == 1 or porcentaje_usado >= 85 or consumo_anormal == 1:
            decision, decision_ok = "Requiere mantenimiento", False
        else:
            decision, decision_ok = "Estado aceptable", True

        nombre        = NOMBRES_COMPONENTES[componente]
        recomendacion = MENSAJES[componente][riesgo]

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
