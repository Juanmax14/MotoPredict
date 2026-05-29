// MOTOPREDICT — SCRIPT PRINCIPAL

const imagenesMotos = {
  "Hero":   { "Hunk 125R": "/static/img/hunk125r.png", "default": "/static/img/moto_default.png" },
  "Bajaj":  { "default": "/static/img/moto_default.png" },
  "Honda":  { "default": "/static/img/moto_default.png" },
  "Yamaha": { "default": "/static/img/moto_default.png" },
  "AKT":    { "default": "/static/img/moto_default.png" }
};

const cacheReferencias = {};

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
const THEME_KEY = "motopredict-theme";

function applyTheme(theme) {
  document.body.classList.toggle("light", theme === "light");
  if (themeToggle) themeToggle.textContent = theme === "light" ? "🌙" : "☀️";
}

applyTheme(localStorage.getItem(THEME_KEY) || "dark");

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const next = document.body.classList.contains("light") ? "dark" : "light";
    localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
  });
}

// ── Referencias ──────────────────────────────────────────────
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
  selectRef.disabled = false;
}

// ── Vista previa de la moto ──────────────────────────────────
function actualizarVistaMoto(marca, referencia) {
  if (!marca || !referencia) { motoPreview.style.display = "none"; return; }
  const imgs  = imagenesMotos[marca] || {};
  const src   = imgs[referencia] || imgs["default"] || "/static/img/moto_default.png";
  motoImg.src             = src;
  motoImg.alt             = `${marca} ${referencia}`;
  motoNombre.textContent  = `${marca} ${referencia}`;
  motoPreview.style.display = "flex";
}

// ── Validación ───────────────────────────────────────────────
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
    if (loadingOverlay) loadingOverlay.classList.add("active");
    if (submitBtn) submitBtn.disabled = true;
  });
}

// ── Inicialización ───────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  if (selectMarca?.value) {
    cargarReferencias(selectMarca.value).then(() => {
      const ref = selectRef.dataset.selected;
      if (ref) { selectRef.value = ref; actualizarVistaMoto(selectMarca.value, ref); }
    });
  }

  animarTarjetas();
  animarBarras();
  animarContadores();

  const secResultados = document.getElementById("resultados");
  if (secResultados) setTimeout(() => secResultados.scrollIntoView({ behavior: "smooth" }), 300);
});

// ── Animaciones ──────────────────────────────────────────────
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

function animarBarras() {
  document.querySelectorAll(".progress-bar").forEach(bar => {
    const target = bar.style.width;
    bar.style.width = "0%";
    setTimeout(() => {
      bar.style.transition = "width .9s cubic-bezier(.4,0,.2,1)";
      bar.style.width      = target;
    }, 200);
  });
}

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
