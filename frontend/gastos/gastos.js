
// ======================================================
// NEXTREP - Gestión financiera
// Archivo: frontend/gastos/gastos.js
// ======================================================

const API_BASE = "/api";

// ======================================================
// FUNCIONES GENERALES
// ======================================================

async function api(ruta, opciones = {}) {
    const respuesta = await fetch(`${API_BASE}${ruta}`, {
        ...opciones,
        headers: {
            "Content-Type": "application/json",
            ...(opciones.headers || {})
        }
    });

    if (!respuesta.ok) {
        let mensaje = `Error ${respuesta.status}`;

        try {
            const datos = await respuesta.json();
            mensaje = datos.error || datos.mensaje || mensaje;
        } catch (_) {}

        throw new Error(mensaje);
    }

    if (respuesta.status === 204) return null;

    return respuesta.json();
}

function moneda(valor) {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 2
    }).format(Number(valor) || 0);
}

function escaparHTML(valor) {
    return String(valor ?? "").replace(/[&<>"']/g, caracter => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[caracter]);
}

function elemento(id) {
    return document.getElementById(id);
}

function establecerTexto(id, valor) {
    const campo = elemento(id);
    if (campo) campo.textContent = valor;
}

function establecerValor(id, valor) {
    const campo = elemento(id);
    if (campo) campo.value = valor ?? "";
}

function mostrarError(error) {
    console.error(error);
    alert(error.message || "Ocurrió un error al procesar la solicitud.");
}

// ======================================================
// GASTOS: CONSULTAR Y FILTRAR
// ======================================================

async function cargarGastos() {
    const desde = elemento("filtroFechaInicio")?.value || "";
    const hasta = elemento("filtroFechaFin")?.value || "";
    const categoria = elemento("filtroCategoria")?.value || "";

    const parametros = new URLSearchParams();

    if (desde) parametros.set("desde", desde);
    if (hasta) parametros.set("hasta", hasta);

    const consulta = parametros.toString()
        ? `?${parametros.toString()}`
        : "";

    let gastos = await api(`/gastos${consulta}`);

    if (!Array.isArray(gastos)) {
        gastos = gastos.gastos || [];
    }

    // El backend no filtra por categoría, así que se hace aquí.
    if (categoria) {
        gastos = gastos.filter(
            gasto => gasto.categoria === categoria
        );
    }

    const tabla = elemento("listaGastos");
    if (!tabla) return;

    if (gastos.length === 0) {
        tabla.innerHTML = `
            <tr>
                <td colspan="6">No hay gastos registrados.</td>
            </tr>
        `;
        return;
    }

    tabla.innerHTML = gastos.map(gasto => `
        <tr>
            <td>${escaparHTML(gasto.descripcion)}</td>
            <td>${escaparHTML(gasto.categoria)}</td>
            <td>${moneda(gasto.monto)}</td>
            <td>${escaparHTML(gasto.fecha)}</td>
            <td>
                <button type="button"
                    data-editar-gasto="${gasto.id}">
                    Editar
                </button>
                <button type="button"
                    data-eliminar-gasto="${gasto.id}">
                    Eliminar
                </button>
            </td>
        </tr>
    `).join("");

    tabla.querySelectorAll("[data-editar-gasto]").forEach(boton => {
        boton.addEventListener("click", () => {
            const gasto = gastos.find(
                registro => registro.id === Number(boton.dataset.editarGasto)
            );

            if (gasto) editarGasto(gasto);
        });
    });

    tabla.querySelectorAll("[data-eliminar-gasto]").forEach(boton => {
        boton.addEventListener("click", async () => {
            try {
                await eliminarRegistro(
                    "gastos",
                    boton.dataset.eliminarGasto
                );
            } catch (error) {
                mostrarError(error);
            }
        });
    });
}

// ======================================================
// GASTOS: REGISTRAR Y EDITAR
// ======================================================

function editarGasto(gasto) {
    establecerValor("gastoId", gasto.id);
    establecerValor("descripcionGasto", gasto.descripcion);
    establecerValor("categoriaGasto", gasto.categoria);
    establecerValor("montoGasto", gasto.monto);
    establecerValor("fechaGasto", gasto.fecha);

    elemento("formGasto")?.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

async function guardarGasto(evento) {
    evento.preventDefault();

    const id = elemento("gastoId")?.value;

    const datos = {
        descripcion: elemento("descripcionGasto").value.trim(),
        categoria: elemento("categoriaGasto").value,
        monto: Number(elemento("montoGasto").value),
        fecha: elemento("fechaGasto").value
    };

    if (
        !datos.descripcion ||
        !datos.categoria ||
        !datos.fecha ||
        !Number.isFinite(datos.monto) ||
        datos.monto < 0
    ) {
        alert("Verifica la descripción, categoría, monto y fecha del gasto.");
        return;
    }

    try {
        await api(
            id ? `/gastos/${encodeURIComponent(id)}` : "/gastos",
            {
                method: id ? "PUT" : "POST",
                body: JSON.stringify(datos)
            }
        );

        alert(id ? "Gasto actualizado correctamente." :
            "Gasto registrado correctamente.");

        limpiarFormulario("gastos");

        await Promise.all([
            cargarGastos(),
            cargarReporte(),
            cargarEstadisticas()
        ]);
    } catch (error) {
        mostrarError(error);
    }
}

// ======================================================
// COSTOS: CONSULTAR
// ======================================================

async function cargarCostos() {
    let costos = await api("/costos");

    if (!Array.isArray(costos)) {
        costos = costos.costos || [];
    }

    const tabla = elemento("listaCostos");
    if (!tabla) return;

    if (costos.length === 0) {
        tabla.innerHTML = `
            <tr>
                <td colspan="6">No hay costos registrados.</td>
            </tr>
        `;
        return;
    }

    tabla.innerHTML = costos.map(costo => `
        <tr>
            <td>${escaparHTML(costo.descripcion)}</td>
            <td>${escaparHTML(costo.categoria)}</td>
            <td>${moneda(costo.monto)}</td>
            <td>${escaparHTML(costo.fecha)}</td>
            <td>
                <button type="button"
                    data-editar-costo="${costo.id}">
                    Editar
                </button>
                <button type="button"
                    data-eliminar-costo="${costo.id}">
                    Eliminar
                </button>
            </td>
        </tr>
    `).join("");

    tabla.querySelectorAll("[data-editar-costo]").forEach(boton => {
        boton.addEventListener("click", () => {
            const costo = costos.find(
                registro => registro.id === Number(boton.dataset.editarCosto)
            );

            if (costo) editarCosto(costo);
        });
    });

    tabla.querySelectorAll("[data-eliminar-costo]").forEach(boton => {
        boton.addEventListener("click", async () => {
            try {
                await eliminarRegistro(
                    "costos",
                    boton.dataset.eliminarCosto
                );
            } catch (error) {
                mostrarError(error);
            }
        });
    });
}

// ======================================================
// COSTOS: REGISTRAR Y EDITAR
// ======================================================

function editarCosto(costo) {
    establecerValor("costoId", costo.id);
    establecerValor("descripcionCosto", costo.descripcion);
    establecerValor("categoriaCosto", costo.categoria);
    establecerValor("montoCosto", costo.monto);
    establecerValor("fechaCosto", costo.fecha);

    elemento("formCosto")?.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

async function guardarCosto(evento) {
    evento.preventDefault();

    const id = elemento("costoId")?.value;

    const datos = {
        descripcion: elemento("descripcionCosto").value.trim(),
        categoria: elemento("categoriaCosto").value,
        monto: Number(elemento("montoCosto").value),
        fecha: elemento("fechaCosto").value
    };

    if (
        !datos.descripcion ||
        !datos.categoria ||
        !datos.fecha ||
        !Number.isFinite(datos.monto) ||
        datos.monto < 0
    ) {
        alert("Verifica la descripción, categoría, monto y fecha del costo.");
        return;
    }

    try {
        await api(
            id ? `/costos/${encodeURIComponent(id)}` : "/costos",
            {
                method: id ? "PUT" : "POST",
                body: JSON.stringify(datos)
            }
        );

        alert(id ? "Costo actualizado correctamente." :
            "Costo registrado correctamente.");

        limpiarFormulario("costos");

        await Promise.all([
            cargarCostos(),
            cargarEstadisticas()
        ]);
    } catch (error) {
        mostrarError(error);
    }
}

// ======================================================
// LIMPIAR FORMULARIOS
// ======================================================

function limpiarFormulario(tipo) {
    if (tipo === "gastos") {
        elemento("formGasto")?.reset();
        establecerValor("gastoId", "");
    }

    if (tipo === "costos") {
        elemento("formCosto")?.reset();
        establecerValor("costoId", "");
    }
}

// ======================================================
// ELIMINAR REGISTROS
// ======================================================

async function eliminarRegistro(tipo, id) {
    if (!confirm(`¿Deseas eliminar este registro de ${tipo}?`)) {
        return;
    }

    await api(`/${tipo}/${encodeURIComponent(id)}`, {
        method: "DELETE"
    });

    alert("Registro eliminado correctamente.");

    if (tipo === "gastos") {
        await Promise.all([
            cargarGastos(),
            cargarReporte()
        ]);
    } else {
        await cargarCostos();
    }

    await cargarEstadisticas();
}

// ======================================================
// REPORTE DE GASTOS
// ======================================================

async function cargarReporte() {
    let gastos = await api("/gastos");

    if (!Array.isArray(gastos)) {
        gastos = gastos.gastos || [];
    }

    const total = gastos.reduce(
        (suma, gasto) => suma + Number(gasto.monto || 0),
        0
    );

    establecerTexto("totalGastos", moneda(total));
    establecerTexto("cantidadGastos", gastos.length);
    establecerTexto(
        "promedioGastos",
        moneda(gastos.length ? total / gastos.length : 0)
    );

    const grupos = {};

    gastos.forEach(gasto => {
        const categoria = gasto.categoria || "Sin categoría";

        if (!grupos[categoria]) {
            grupos[categoria] = {
                cantidad: 0,
                total: 0
            };
        }

        grupos[categoria].cantidad++;
        grupos[categoria].total += Number(gasto.monto || 0);
    });

    const tabla = elemento("tablaReporteCategorias");
    if (!tabla) return;

    const categorias = Object.entries(grupos);

    tabla.innerHTML = categorias.length
        ? categorias.map(([categoria, datos]) => `
            <tr>
                <td>${escaparHTML(categoria)}</td>
                <td>${datos.cantidad}</td>
                <td>${moneda(datos.total)}</td>
            </tr>
        `).join("")
        : `<tr><td colspan="3">No hay datos disponibles.</td></tr>`;
}

// ======================================================
// ESTADÍSTICAS: GASTOS Y COSTOS
// ======================================================

async function cargarEstadisticas() {
    const datos = await api("/estadisticas");

    const gastos = datos.gastos || {};
    const costos = datos.costos || {};

    establecerTexto(
        "estadisticaTotalGastos",
        moneda(gastos.total)
    );

    establecerTexto(
        "estadisticaCantidadGastos",
        `${Number(gastos.cantidad || 0)} registros`
    );

    establecerTexto(
        "estadisticaPromedioGastos",
        moneda(gastos.promedio)
    );

    establecerTexto(
        "estadisticaTotalCostos",
        moneda(costos.total)
    );

    establecerTexto(
        "estadisticaCantidadCostos",
        `${Number(costos.cantidad || 0)} registros`
    );

    establecerTexto(
        "estadisticaPromedioCostos",
        moneda(costos.promedio)
    );

    const tabla = elemento("tablaEstadisticasCategorias");
    if (!tabla) return;

    const categorias = datos.gastos_por_categoria || [];

    if (categorias.length === 0) {
        tabla.innerHTML = `
            <tr>
                <td colspan="2">Todavía no hay gastos registrados.</td>
            </tr>
        `;
        return;
    }

    tabla.innerHTML = categorias.map(item => `
        <tr>
            <td>${escaparHTML(item.categoria)}</td>
            <td>${moneda(item.total)}</td>
        </tr>
    `).join("");
}

// ======================================================
// INICIALIZACIÓN Y EVENTOS
// ======================================================

document.addEventListener("DOMContentLoaded", () => {
    elemento("formGasto")?.addEventListener(
        "submit",
        guardarGasto
    );

    elemento("formCosto")?.addEventListener(
        "submit",
        guardarCosto
    );

    elemento("btnCancelarGasto")?.addEventListener(
        "click",
        () => limpiarFormulario("gastos")
    );

    elemento("btnCancelarCosto")?.addEventListener(
        "click",
        () => limpiarFormulario("costos")
    );

    // Aplicar filtros de gastos.
    elemento("btnFiltrar")?.addEventListener("click", async () => {
        const desde = elemento("filtroFechaInicio")?.value || "";
        const hasta = elemento("filtroFechaFin")?.value || "";

        if (desde && hasta && desde > hasta) {
            alert("La fecha inicial no puede ser posterior a la fecha final.");
            return;
        }

        try {
            await cargarGastos();
        } catch (error) {
            mostrarError(error);
        }
    });

    // Limpiar filtros.
    elemento("btnLimpiarFiltros")?.addEventListener(
        "click",
        async () => {
            establecerValor("filtroFechaInicio", "");
            establecerValor("filtroFechaFin", "");
            establecerValor("filtroCategoria", "");

            try {
                await cargarGastos();
            } catch (error) {
                mostrarError(error);
            }
        }
    );

    // Identificador correcto del botón en gastos.html.
    elemento("btnActualizarEstadisticas")?.addEventListener(
        "click",
        async () => {
            try {
                await cargarEstadisticas();
            } catch (error) {
                mostrarError(error);
            }
        }
    );

    // Cargar información al abrir la página.
    Promise.allSettled([
        cargarGastos(),
        cargarCostos(),
        cargarReporte(),
        cargarEstadisticas()
    ]).then(resultados => {
        resultados.forEach(resultado => {
            if (resultado.status === "rejected") {
                console.error(
                    "No se pudo cargar una sección:",
                    resultado.reason
                );
            }
        });
    });
});
```


cargarDatos();
