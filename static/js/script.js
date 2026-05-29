// ============================================================
// MOTOPREDICT — Lógica del frontend
// Responsabilidades: tema, referencias AJAX, vista previa,
// validación, overlay de carga y animaciones.
// ============================================================

// Imágenes por marca y referencia. "default" se usa cuando no
// existe una foto específica para esa referencia.
const imagenesMotos = {
  "Hero":   { "Hunk 125R": "/static/img/hunk125r.png", "default": "/static/img/moto_default.png" },
  "Bajaj":  { "default": "/static/img/moto_default.png" },
  "Honda":  { "default": "/static/img/moto_default.png" },
  "Yamaha": { "default": "/static/img/moto_default.png" },
  "AKT":    { "default": "/static/img/moto_default.png" }
};

// Caché local para no repetir la llamada al servidor por la
// misma marca si el usuario cambia de opinión y vuelve.
const cacheReferencias = {};

// Referencias a elementos del DOM usados en varios lugares
const selectMarca    = document.getElementById("marca");
const selectRef      = document.getElementById("referencia");
const motoPreview    = document.getElementById("motoPreview");
const motoImg        = document.getElementById("motoImg");
const motoNombre     = document.getElementById("motoNombre");
const submitBtn      = document.getElementById("submitBtn");
const mainForm       = document.getElementById("mainForm");
const loadingOverlay = document.getElementById("loadingOverlay");
const themeToggle    = document.getElementById("themeToggle");


// ── Tema claro / oscuro ──────────────────────────────────────

const THEME_KEY = "motopredict-theme"; // clave en localStorage

function applyTheme(theme) {
  document.body.classList.toggle("light", theme === "light");
  if (themeToggle) themeToggle.textContent = theme === "light" ? "🌙" : "☀️";
}

// Aplica el tema guardado antes del primer render para evitar
// un parpadeo de colores al cargar la página
applyTheme(localStorage.getItem(THEME_KEY) || "dark");

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const next = document.body.classList.contains("light") ? "dark" : "light";
    localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
  });
}


// ── Carga dinámica de referencias (AJAX) ────────────────────

// Consulta GET /api/referencias/<marca> y llena el segundo select.
// Si ya se consultó esa marca antes, usa el resultado guardado en caché.
async function cargarReferencias(marca) {
  if (!marca) return;
  if (cacheReferencias[marca]) { llenarSelectReferencias(cacheReferencias[marca]); return; }
  try {
    const res  = await fetch(`/api/referencias/${encodeURIComponent(marca)}`);
    const data = await res.json();
    cacheReferencias[marca] = data.referencias;
    llenarSelectReferencias(data.referencias);
  } catch (err) {
    console.error("Error al cargar referencias:", err);
  }
}

function llenarSelectReferencias(referencias) {
  selectRef.innerHTML = '<option value="" disabled selected>Selecciona una referencia…</option>';
  referencias.forEach(ref => {
    const opt = document.createElement("option");
    opt.value = opt.textContent = ref;
    selectRef.appendChild(opt);
  });
  selectRef.disabled = false; // se mantiene bloqueado hasta recibir opciones
}


// ── Vista previa de la moto ──────────────────────────────────

function actualizarVistaMoto(marca, referencia) {
  if (!marca || !referencia) { motoPreview.style.display = "none"; return; }
  const imgs = imagenesMotos[marca] || {};
  // Busca imagen específica → imagen por defecto de la marca → fallback global
  const src  = imgs[referencia] || imgs["default"] || "/static/img/moto_default.png";
  motoImg.src            = src;
  motoImg.alt            = `${marca} ${referencia}`;
  motoNombre.textContent = `${marca} ${referencia}`;
  motoPreview.style.display = "flex";
}


// ── Validación del formulario ────────────────────────────────

// Segunda capa de validación (el servidor también valida).
// Detiene el envío antes de mostrar el overlay si los datos son inválidos.
function validarFormulario() {
  const km    = parseFloat(document.getElementById("kilometraje")?.value || 0);
  const kmDia = parseFloat(document.getElementById("km_dia")?.value || 0);
  if (km <= 0)    { alert("El kilometraje debe ser mayor a 0."); return false; }
  if (kmDia <= 0) { alert("Los kilómetros por día deben ser mayor a 0."); return false; }
  return true;
}


// ── Eventos ──────────────────────────────────────────────────

if (selectMarca) {
  selectMarca.addEventListener("change", () => {
    // Bloquea referencias y oculta preview mientras llega la respuesta
    selectRef.innerHTML = '<option value="" disabled selected>Cargando referencias…</option>';
    selectRef.disabled  = true;
    motoPreview.style.display = "none";
    cargarReferencias(selectMarca.value);
  });
}

if (selectRef) {
  selectRef.addEventListener("change", () => {
    actualizarVistaMoto(selectMarca.value, selectRef.value);
  });
}

if (mainForm) {
  mainForm.addEventListener("submit", (e) => {
    if (!validarFormulario()) { e.preventDefault(); return; }
    if (loadingOverlay) loadingOverlay.classList.add("active"); // muestra overlay de carga
    if (submitBtn) submitBtn.disabled = true; // evita doble envío
  });
}


// ── Inicialización al cargar la página ───────────────────────

document.addEventListener("DOMContentLoaded", () => {

  // Si la página carga con resultados (POST), restaura el estado
  // del formulario para que el usuario vea qué moto se analizó.
  if (selectMarca?.value) {
    cargarReferencias(selectMarca.value).then(() => {
      const ref = selectRef.dataset.selected;
      if (ref) { selectRef.value = ref; actualizarVistaMoto(selectMarca.value, ref); }
    });
  }

  animarTarjetas();
  animarBarras();
  animarContadores();

  // Desplaza automáticamente a los resultados cuando existen
  const secResultados = document.getElementById("resultados");
  if (secResultados) setTimeout(() => secResultados.scrollIntoView({ behavior: "smooth" }), 300);
});


// ── Animaciones ──────────────────────────────────────────────

// Usa IntersectionObserver para animar solo cuando el elemento
// es visible en pantalla, evitando trabajo innecesario.
function animarTarjetas() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.opacity   = "1";
        e.target.style.transform = "translateY(0)";
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll(".component-card, .summary-card, .metric-chip")
    .forEach(el => observer.observe(el));
}

// Resetea el ancho a 0 y lo anima al valor real para que la
// barra se "llene" visualmente al entrar a la sección.
function animarBarras() {
  document.querySelectorAll(".progress-bar").forEach(bar => {
    const target = bar.style.width;
    bar.style.width = "0%";
    setTimeout(() => {
      bar.style.transition = "width .9s cubic-bezier(.4,0,.2,1)";
      bar.style.width      = target;
    }, 200); // delay mínimo para que el navegador registre el estado inicial
  });
}

// Anima números desde 0 hasta su valor final con ease-out cúbico
// (la fórmula 1 - (1-t)³ hace que acelere al inicio y frene al final).
function animarContadores() {
  document.querySelectorAll(".count-up[data-target]").forEach(el => {
    const target   = parseFloat(el.dataset.target);
    const suffix   = el.classList.contains("prob-num") ? "%" : "";
    const duration = 900;
    const t0       = performance.now();
    el.textContent = "0" + suffix;

    (function tick(now) {
      const p = Math.min((now - t0) / duration, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3))) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    })(t0);
  });
}
