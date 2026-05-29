# MotoPredict — Sistema de Mantenimiento Predictivo con Machine Learning

> Aplicación web que analiza el estado de los componentes clave de una motocicleta y predice cuáles requieren mantenimiento, usando Regresión Logística entrenada con un dataset propio de 700 registros.

---

## Problema o necesidad que quisimos solucionar

Muchos propietarios de motocicletas no realizan el mantenimiento preventivo a tiempo porque desconocen cuándo exactamente deben hacerlo. Esto genera fallas mecánicas inesperadas, mayores costos de reparación y riesgos de seguridad — especialmente en componentes críticos como los frenos.

**MotoPredict** resuelve esto: el usuario ingresa tres datos básicos (kilometraje actual, km por día y si nota consumo anormal de combustible) y obtiene en segundos un diagnóstico detallado del estado de cada componente, con predicciones de Machine Learning y recomendaciones personalizadas.

---

## Librerías, frameworks y recursos utilizados

| Categoría | Tecnología | Propósito |
|---|---|---|
| Backend | Python 3.9, Flask | Servidor web, rutas HTTP, renderizado de plantillas |
| Machine Learning | scikit-learn | LogisticRegression, StandardScaler, métricas de evaluación |
| Datos | pandas, numpy, openpyxl | Lectura del dataset, manipulación y transformación |
| Frontend | HTML5, CSS3, JavaScript | Interfaz responsive, animaciones, modo claro/oscuro |
| Tipografía | Google Fonts (Plus Jakarta Sans) | Diseño visual de la interfaz |

---

## Cómo construimos el dataset

El dataset fue construido de forma sintética, basado en los intervalos de mantenimiento recomendados por fabricantes de motocicletas de uso urbano (segmento 100–200 cc).

**Proceso de construcción:**

1. Se definieron 5 componentes con sus intervalos estándar de servicio.
2. Para cada componente se generaron 140 registros con distintas combinaciones de:
   - `kilometraje_actual` — km totales del odómetro
   - `km_desde_servicio` — km estimados desde el último servicio (`km_actual % intervalo`)
   - `km_por_dia` — promedio de uso diario del usuario
   - `consumo_anormal` — indicador binario (0 = normal, 1 = hay consumo raro)
3. La variable objetivo `necesita_mantenimiento` se etiquetó como **1** cuando `km_desde_servicio` supera el 85% del intervalo o cuando hay consumo anormal; **0** en caso contrario.
4. Se incluyeron columnas de contexto como `tipo_uso` e `intervalo_mantenimiento_km`.

**Resultado:** 700 registros totales — 140 por componente, que representan escenarios variados de mantenimiento cumplido e incumplido.

---

## Cantidad de entradas para entrenar el modelo

| Dato | Valor |
|---|---|
| Total del dataset | 700 registros |
| Registros por componente | 140 |
| División entrenamiento / prueba | 70% / 30% (`random_state=42`) |
| Registros de entrenamiento por componente | 98 |
| Registros de prueba por componente | 42 |
| Clase 0 (no necesita mantenimiento) | 472 registros |
| Clase 1 (sí necesita mantenimiento) | 228 registros |

Se utilizó `class_weight="balanced"` para compensar el desbalance entre clases.

---

## Modelos de Machine Learning utilizados

Se entrenó un modelo de **Regresión Logística** (`LogisticRegression`) independiente por cada componente — un total de **5 modelos**.

Cada modelo recibe 4 características de entrada:

```
kilometraje_actual, km_desde_servicio, km_por_dia, consumo_anormal
```

Y predice si el componente necesita mantenimiento (`0` o `1`), junto con la probabilidad de mantenimiento (0–100%).

Todos los datos se normalizan con `StandardScaler` (media=0, desviación=1) antes de entrenar y predecir.

---

## Por qué elegimos Regresión Logística

1. **Problema binario directo:** La predicción es ¿necesita mantenimiento sí o no? — exactamente el caso de uso para el que la Regresión Logística está diseñada.
2. **Probabilidades interpretables:** Devuelve una probabilidad continua (no solo 0/1) que se muestra en la interfaz como porcentaje de riesgo, dando información más rica al usuario.
3. **Eficiencia en producción:** Entrena en milisegundos con 140 registros y predice de forma instantánea. Se carga en memoria una sola vez al iniciar el servidor y se reutiliza en todas las solicitudes.
4. **Robustez con datasets pequeños:** Con 140 registros por componente, modelos más complejos (Random Forest, redes neuronales) tienden a sobreajustar. La Regresión Logística generaliza mejor en este escenario.
5. **Transparencia:** Sus coeficientes son interpretables, lo que permite verificar que el modelo está tomando decisiones con sentido técnico.

---

## Nivel de efectividad — Métricas obtenidas por modelo

Métricas calculadas sobre el 30% de datos reservados para prueba (42 registros por componente, nunca vistos durante el entrenamiento):

| Componente | Accuracy | Precisión | Recall | F1-Score |
|---|---|---|---|---|
| 🛢️ Aceite Motor | 90.5% | 91.7% | 78.6% | 84.6% |
| ⛓️ Cadena Transmisión | 90.5% | 91.7% | 78.6% | 84.6% |
| ⚡ Bujía | 85.7% | 53.8% | 100.0% | 70.0% |
| 🌬️ Filtro de Aire | 83.3% | 50.0% | 42.9% | 46.2% |
| 🛑 Frenos | 90.5% | 77.8% | 100.0% | 87.5% |
| **Promedio global** | **88.1%** | **73.0%** | **80.0%** | **74.6%** |

> Los frenos tienen Recall del 100%: el modelo nunca omite un caso real de mantenimiento en ese componente, lo cual es prioritario por razones de seguridad.
> El Filtro de Aire tiene las métricas más bajas; esto se compensa con la regla preventiva de umbral al 85% del ciclo.

---

## Predicciones generadas por el sistema

Para cada uno de los 5 componentes, el sistema genera:

- **Predicción binaria (0/1):** si el modelo considera que el componente necesita mantenimiento ahora.
- **Probabilidad de mantenimiento (%):** qué tan seguro está el modelo, expresado como porcentaje.
- **Porcentaje del ciclo de mantenimiento usado:** calculado como `(km_desde_servicio / intervalo) × 100`.
- **Km restantes** hasta el próximo servicio estimado.
- **Días aproximados** restantes según el uso diario declarado.
- **Nivel de riesgo** (ALTO / MEDIO / BAJO): clasificación derivada del porcentaje usado y el consumo anormal.
- **Mensaje de recomendación** único por componente y nivel de riesgo (15 mensajes distintos en total).

---

## Cómo las predicciones se usaron para construir la solución de cara al usuario

Las predicciones del modelo se combinaron con reglas preventivas de dominio para generar una solución más segura y accionable:

| Fuente | Comportamiento generado |
|---|---|
| Predicción ML = 1 | Activa "Requiere mantenimiento" |
| Ciclo de uso ≥ 85% | Activa alerta aunque el modelo prediga 0 |
| Consumo anormal = 1 | Eleva riesgo a ALTO en todos los componentes |
| Probabilidad ML alta | Determina nivel ALTO / MEDIO / BAJO |
| Nivel de riesgo | Selecciona mensaje personalizado por componente |
| Mayor probabilidad global | Identifica y destaca el componente más urgente |
| Km y días restantes | Permite al usuario planificar el mantenimiento con antelación |

El resultado visible para el usuario es una **tarjeta por componente** con color semántico (🔴 rojo = cambio urgente, 🟡 amarillo = próximo, 🟢 verde = normal), datos numéricos clave, y una recomendación escrita en lenguaje natural.

---

## Cómo llevamos la solución a la web

La aplicación fue desarrollada como una **web app local** con Flask:

1. El usuario accede al navegador en `http://localhost:5000`.
2. Flask maneja dos rutas: `GET /` muestra el formulario; `POST /` recibe los datos, ejecuta los 5 modelos ML y devuelve la página con resultados.
3. Las plantillas HTML se renderizan con **Jinja2**, que inyecta los resultados del modelo directamente en el HTML.
4. Una API REST adicional (`GET /api/referencias/<marca>`) sirve JSON para actualizar el selector de modelos de moto sin recargar la página.
5. Los modelos entrenados se mantienen en **memoria del proceso** con lazy init thread-safe (double-checked locking), para que no se reentrenen en cada solicitud.

**Para ejecutar el proyecto:**

```bash
git clone <url-del-repositorio>
cd motopredict
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
# Abrir http://127.0.0.1:5000
```

---

## Explicación general del frontend y backend

### Backend

**`app.py`** — Servidor Flask:
- Define las rutas HTTP (`/` y `/api/referencias/<marca>`).
- Captura y valida los datos del formulario.
- Llama al módulo de predicción y pasa los resultados a la plantilla Jinja2.
- Gestiona el diccionario de marcas y modelos disponibles.

**`modelo.py`** — Motor de Machine Learning:
- Carga el dataset desde Excel y entrena 5 modelos Logistic Regression (uno por componente).
- Escala los datos con `StandardScaler`.
- Calcula métricas de evaluación (accuracy, precisión, recall, F1).
- Genera predicciones, probabilidades, niveles de riesgo y recomendaciones para los datos del usuario.
- Implementa thread-safety con `threading.Lock` para entornos multi-hilo.

### Frontend

**`templates/index.html`** — Plantilla Jinja2 única con tres secciones:
- Hero con llamado a la acción.
- Formulario de entrada de datos con selector dinámico de moto.
- Sección de resultados (solo visible cuando hay predicción): banner personalizado, resumen ejecutivo, tarjetas por componente y tabla de métricas.

**`static/css/style.css`** — Diseño:
- Variables CSS para theming (dark/light).
- Sistema de colores semántico (rojo / amarillo / verde) aplicado a bordes de tarjetas, barras de progreso y textos de recomendación.
- Diseño responsive para móvil y escritorio.

**`static/js/script.js`** — Comportamiento:
- Carga dinámica de modelos de moto por marca (AJAX sin recarga).
- Vista previa de imagen de la moto seleccionada.
- Overlay de carga al enviar el formulario.
- Animaciones: contadores numéricos, barras de progreso y entrada de tarjetas.
- Toggle modo claro/oscuro con persistencia en `localStorage`.
- Validación del formulario en el cliente.

---

## Cómo se aprovecharon las predicciones para generar nuevas reglas o comportamientos

El sistema no se limita a mostrar los valores del modelo — los transforma en comportamientos concretos de la interfaz:

- **Color de la tarjeta:** El nivel de riesgo calculado (ML + regla de umbral) determina el color del borde y fondo de cada tarjeta de componente (rojo / amarillo / verde).
- **Texto de la recomendación:** 15 mensajes únicos (3 por componente × 5 componentes) redactados específicamente para cada situación — no son plantillas genéricas.
- **Decisión final combinada:** `mantenimiento = predicción_ML OR ciclo ≥ 85% OR consumo_anormal` — más conservador que el modelo solo, garantizando seguridad.
- **Componente urgente destacado:** El componente con mayor probabilidad se muestra en el resumen ejecutivo con badge de porcentaje.
- **Proyección temporal:** A partir de los km restantes y el uso diario, el sistema calcula y muestra los días aproximados hasta el próximo servicio — convirtiendo una métrica técnica en información accionable.
- **Scroll automático a resultados:** Al recibir el diagnóstico, la página desplaza automáticamente al usuario a los resultados, reduciendo fricción.

---

## Cómo funciona la interfaz y cuál es su objetivo

**Objetivo:** Permitir que cualquier propietario de motocicleta, sin conocimientos técnicos, obtenga un diagnóstico claro y accionable en menos de 30 segundos.

**Flujo de uso:**

1. **Selección de moto** → el usuario elige marca y referencia; aparece la foto de la moto como confirmación visual.
2. **Ingreso de datos** → kilometraje actual, km por día y si nota consumo anormal.
3. **Análisis** → un overlay de carga confirma que el modelo está procesando; el servidor ejecuta los 5 modelos y genera el diagnóstico.
4. **Resultados** → la página hace scroll automático a:
   - **Banner personalizado** con foto de la moto, marca, referencia y datos de uso.
   - **Resumen ejecutivo** con el componente más crítico, cuántos requieren atención y precisión del modelo.
   - **5 tarjetas** (una por componente) con código de color, probabilidad animada, barra de ciclo de vida, estadísticas de km y días, decisión y recomendación específica.
   - **Tabla de métricas** del modelo para transparencia técnica.
5. **Modo claro/oscuro** → toggle en el header, preferencia guardada entre sesiones.

---

## Estructura del repositorio

```
motopredict/
├── app.py                        # Servidor Flask y rutas
├── modelo.py                     # Modelos ML, entrenamiento y predicción
├── dataset_motopredict.xlsx      # Dataset de 700 registros
├── requirements.txt              # Dependencias Python
├── README.md                     # Este archivo
├── templates/
│   └── index.html                # Plantilla HTML (Jinja2)
└── static/
    ├── css/style.css             # Estilos con soporte dark/light
    ├── js/script.js              # Lógica del frontend
    └── img/                      # Imágenes de motos y favicon
```

---

*Proyecto académico — Machine Learning aplicado al mantenimiento preventivo de motocicletas.*
