const monedaCOP = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 2 });
const estado = { gastos: [], costos: [], editandoGasto: null, editandoCosto: null };

function moneda(valor) { return monedaCOP.format(Number(valor) || 0); }
function hoyISO() { const ahora = new Date(); const local = new Date(ahora.getTime() - ahora.getTimezoneOffset() * 60000); return local.toISOString().slice(0, 10); }
function valor(id) { return document.getElementById(id).value; }
function mostrarEstado(id, mensaje) { document.getElementById(id).textContent = mensaje; }

async function api(url, opciones = {}) {
  const respuesta = await fetch(url, {
    ...opciones,
    headers: { "Content-Type": "application/json", ...(opciones.headers || {}) }
  });
  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) throw new Error(datos.error || "Ocurrió un error en la solicitud.");
  return datos;
}

function datosFormulario(tipo) {
  const sufijo = tipo === "gastos" ? "Gasto" : "Costo";
  return {
    descripcion: valor(`descripcion${sufijo}`).trim(),
    categoria: valor(`categoria${sufijo}`).trim() || "General",
    monto: Number(valor(`monto${sufijo}`)),
    fecha: valor(`fecha${sufijo}`)
  };
}

function limpiarFormulario(tipo) {
  const sufijo = tipo === "gastos" ? "Gasto" : "Costo";
  document.getElementById(`form${sufijo}`).reset();
  document.getElementById(`fecha${sufijo}`).value = hoyISO();
  estado[tipo === "gastos" ? "editandoGasto" : "editandoCosto"] = null;
  document.getElementById(`guardar${sufijo}`).textContent = `Guardar ${tipo === "gastos" ? "gasto" : "costo"}`;
  document.getElementById(`cancelarEdicion${sufijo}`).classList.add("oculto");
  document.getElementById(`titulo${sufijo}`).textContent = `Registrar ${tipo === "gastos" ? "gasto" : "costo"}`;
}

async function guardar(tipo, evento) {
  evento.preventDefault();
  const sufijo = tipo === "gastos" ? "Gasto" : "Costo";
  const claveEdicion = tipo === "gastos" ? "editandoGasto" : "editandoCosto";
  try {
    const registro = datosFormulario(tipo);
    const id = estado[claveEdicion];
    await api(id ? `/api/${tipo}/${id}` : `/api/${tipo}`, {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(registro)
    });
    limpiarFormulario(tipo);
    await cargarTodo();
    mostrarEstado(tipo === "gastos" ? "estadoGastos" : "estadoCostos", `${tipo === "gastos" ? "Gasto" : "Costo"} ${id ? "actualizado" : "guardado"} correctamente.`);
  } catch (error) {
    alert(error.message);
  }
}

function renderizarTabla(tipo, registros) {
  const idTabla = tipo === "gastos" ? "listaGastos" : "listaCostos";
  const cuerpo = document.getElementById(idTabla);
  cuerpo.replaceChildren();
  if (!registros.length) {
    const fila = document.createElement("tr"); const celda = document.createElement("td");
    celda.colSpan = 5; celda.textContent = "No hay registros para mostrar."; fila.appendChild(celda); cuerpo.appendChild(fila); return;
  }
  registros.forEach(registro => {
    const fila = document.createElement("tr");
    [registro.fecha, registro.descripcion, registro.categoria, moneda(registro.monto)].forEach(texto => {
      const celda = document.createElement("td"); celda.textContent = texto; fila.appendChild(celda);
    });
    const acciones = document.createElement("td");
    const editar = document.createElement("button"); editar.className = "pequeno"; editar.textContent = "Editar"; editar.type = "button";
    editar.addEventListener("click", () => iniciarEdicion(tipo, registro));
    const eliminar = document.createElement("button"); eliminar.className = "pequeno peligro"; eliminar.textContent = "Eliminar"; eliminar.type = "button";
    eliminar.addEventListener("click", () => borrar(tipo, registro.id));
    acciones.append(editar, eliminar); fila.appendChild(acciones); cuerpo.appendChild(fila);
  });
}

function iniciarEdicion(tipo, registro) {
  const sufijo = tipo === "gastos" ? "Gasto" : "Costo";
  const claveEdicion = tipo === "gastos" ? "editandoGasto" : "editandoCosto";
  estado[claveEdicion] = registro.id;
  document.getElementById(`descripcion${sufijo}`).value = registro.descripcion;
  document.getElementById(`categoria${sufijo}`).value = registro.categoria;
  document.getElementById(`monto${sufijo}`).value = registro.monto;
  document.getElementById(`fecha${sufijo}`).value = registro.fecha;
  document.getElementById(`guardar${sufijo}`).textContent = `Actualizar ${tipo === "gastos" ? "gasto" : "costo"}`;
  document.getElementById(`cancelarEdicion${sufijo}`).classList.remove("oculto");
  document.getElementById(`titulo${sufijo}`).textContent = `Editar ${tipo === "gastos" ? "gasto" : "costo"}`;
  document.getElementById(`form${sufijo}`).scrollIntoView({ behavior: "smooth", block: "center" });
}

async function borrar(tipo, id) {
  if (!confirm(`¿Seguro que deseas eliminar este registro de ${tipo === "gastos" ? "gastos" : "costos"}?`)) return;
  try {
    await api(`/api/${tipo}/${id}`, { method: "DELETE" });
    await cargarTodo();
    mostrarEstado(tipo === "gastos" ? "estadoGastos" : "estadoCostos", "Registro eliminado correctamente.");
  } catch (error) { alert(error.message); }
}

async function cargarGastos() {
  const parametros = new URLSearchParams();
  if (valor("desde")) parametros.set("desde", valor("desde"));
  if (valor("hasta")) parametros.set("hasta", valor("hasta"));
  const query = parametros.toString();
  estado.gastos = await api(`/api/gastos${query ? `?${query}` : ""}`);
  renderizarTabla("gastos", estado.gastos);
  const total = estado.gastos.reduce((suma, item) => suma + Number(item.monto), 0);
  document.getElementById("reporteTotal").textContent = moneda(total);
  document.getElementById("reporteCantidad").textContent = String(estado.gastos.length);
  document.getElementById("reportePromedio").textContent = moneda(estado.gastos.length ? total / estado.gastos.length : 0);
}

async function cargarCostos() {
  estado.costos = await api("/api/costos");
  renderizarTabla("costos", estado.costos);
}

async function cargarEstadisticas() {
  const datos = await api("/api/estadisticas");
  document.getElementById("estadisticaTotalGastos").textContent = moneda(datos.gastos.total);
  document.getElementById("estadisticaCantidadGastos").textContent = `${datos.gastos.cantidad} registros`;
  document.getElementById("estadisticaPromedioGastos").textContent = moneda(datos.gastos.promedio);
  document.getElementById("estadisticaTotalCostos").textContent = moneda(datos.costos.total);
  document.getElementById("estadisticaCantidadCostos").textContent = `${datos.costos.cantidad} registros`;
  document.getElementById("estadisticaPromedioCostos").textContent = moneda(datos.costos.promedio);
  const tabla = document.getElementById("tablaEstadisticasCategorias");
  tabla.replaceChildren();
  if (!datos.gastos_por_categoria.length) {
    const fila = document.createElement("tr"); const celda = document.createElement("td");
    celda.colSpan = 2; celda.textContent = "Todavía no hay gastos registrados."; fila.appendChild(celda); tabla.appendChild(fila); return;
  }
  datos.gastos_por_categoria.forEach(item => {
    const fila = document.createElement("tr"); const categoria = document.createElement("td"); const total = document.createElement("td");
    categoria.textContent = item.categoria; total.textContent = moneda(item.total); fila.append(categoria, total); tabla.appendChild(fila);
  });
}

async function cargarTodo() {
  try {
    await Promise.all([cargarGastos(), cargarCostos(), cargarEstadisticas()]);
  } catch (error) {
    console.error(error);
    mostrarEstado("estadoGastos", `Error al cargar datos: ${error.message}`);
    mostrarEstado("estadoCostos", `Error al cargar datos: ${error.message}`);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("fechaGasto").value = hoyISO();
  document.getElementById("fechaCosto").value = hoyISO();
  document.getElementById("formGasto").addEventListener("submit", evento => guardar("gastos", evento));
  document.getElementById("formCosto").addEventListener("submit", evento => guardar("costos", evento));
  document.getElementById("cancelarEdicionGasto").addEventListener("click", () => limpiarFormulario("gastos"));
  document.getElementById("cancelarEdicionCosto").addEventListener("click", () => limpiarFormulario("costos"));
  document.getElementById("filtrarGastos").addEventListener("click", async () => {
    if (valor("desde") && valor("hasta") && valor("desde") > valor("hasta")) { alert("La fecha inicial no puede ser posterior a la fecha final."); return; }
    try { await cargarGastos(); } catch (error) { alert(error.message); }
  });
  document.getElementById("limpiarFiltros").addEventListener("click", async () => {
    document.getElementById("desde").value = ""; document.getElementById("hasta").value = "";
    try { await cargarGastos(); } catch (error) { alert(error.message); }
  });
  document.getElementById("actualizarEstadisticas").addEventListener("click", async () => {
    try { await cargarEstadisticas(); } catch (error) { alert(error.message); }
  });
  cargarTodo();
});



cargarDatos();
