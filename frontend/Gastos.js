
const API = {
    gastos: "/api/gastos",
    costos: "/api/costos"
};

const dinero = new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 2
});

let gastosActuales = [];
let costosActuales = [];

async function solicitud(url, opciones = {}) {
    const respuesta = await fetch(url, {
        ...opciones,
        headers: {
            "Content-Type": "application/json",
            ...opciones.headers
        }
    });

    const datos = await respuesta.json();

    if (!respuesta.ok) {
        throw new Error(datos.error || "Error en la solicitud.");
    }

    return datos;
}

function mostrarError(error) {
    alert(error.message || "No se pudo completar la operación.");
}

function celda(fila, valor) {
    const td = document.createElement("td");
    td.textContent = valor ?? "";
    fila.appendChild(td);
    return td;
}

function crearBoton(texto, clase, accion) {
    const boton = document.createElement("button");
    boton.textContent = texto;
    boton.className = clase;
    boton.type = "button";
    boton.addEventListener("click", accion);
    return boton;
}

function configurarFormulario(tipo, campos, actualizarLista) {
    const formulario = document.getElementById(`form${tipo}`);
    const boton = document.getElementById(`btn${tipo}`);
    const cancelar = document.getElementById(`cancelar${tipo}`);

    const recurso = tipo === "Gasto" ? "gastos" : "costos";
    let idEditando = null;

    function limpiar() {
        formulario.reset();
        idEditando = null;
        boton.textContent = `Registrar ${tipo.toLowerCase()}`;
        cancelar.classList.add("oculto");
    }

    cancelar.addEventListener("click", limpiar);

    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        const datos = {};

        for (const [campo, id] of Object.entries(campos)) {
            datos[campo] = document.getElementById(id).value.trim();
        }

        datos.valor = Number(datos.valor);

        if (!Number.isFinite(datos.valor) || datos.valor <= 0) {
            alert("El valor debe ser mayor que cero.");
            return;
        }

        const estabaEditando = idEditando !== null;

        try {
            const url = idEditando
                ? `${API[recurso]}/${idEditando}`
                : API[recurso];

            await solicitud(url, {
                method: estabaEditando ? "PUT" : "POST",
                body: JSON.stringify(datos)
            });

            limpiar();
            await actualizarLista();

            alert(estabaEditando
                ? `${tipo} actualizado correctamente.`
                : `${tipo} registrado correctamente.`);
        } catch (error) {
            mostrarError(error);
        }
    });

    return {
        editar(registro) {
            idEditando = registro.id;

            for (const [campo, id] of Object.entries(campos)) {
                document.getElementById(id).value =
                    registro[campo] ?? "";
            }

            boton.textContent = "Guardar cambios";
            cancelar.classList.remove("oculto");
            formulario.scrollIntoView({ behavior: "smooth" });
        },
        obtenerId: () => idEditando,
        limpiar
    };
}

function renderizarTabla(registros, elemento, campoTipo, formulario, recurso) {
    const tbody = document.getElementById(elemento);
    tbody.replaceChildren();

    if (registros.length === 0) {
        const fila = document.createElement("tr");
        const td = celda(fila, "No hay registros para mostrar.");
        td.colSpan = 5;
        tbody.appendChild(fila);
        return;
    }

    registros.forEach((registro) => {
        const fila = document.createElement("tr");

        celda(fila, registro.descripcion);
        celda(fila, registro[campoTipo]);
        celda(fila, dinero.format(registro.valor));
        celda(fila, registro.fecha);

        const acciones = celda(fila, "");

        acciones.appendChild(crearBoton("Editar", "accion", () => {
            formulario.editar(registro);
        }));

        acciones.appendChild(crearBoton(
            "Eliminar",
            "accion eliminar",
            async () => {
                if (!confirm("¿Seguro que deseas eliminar este registro?")) {
                    return;
                }

                try {
                    await solicitud(`${API[recurso]}/${registro.id}`, {
                        method: "DELETE"
                    });

                    if (formulario.obtenerId() === registro.id) {
                        formulario.limpiar();
                    }

                    await cargarDatos();
                } catch (error) {
                    mostrarError(error);
                }
            }
        ));

        tbody.appendChild(fila);
    });
}

function aplicarFiltros() {
    const inicio = document.getElementById("fechaInicio").value;
    const fin = document.getElementById("fechaFin").value;

    if (inicio && fin && inicio > fin) {
        alert("La fecha inicial no puede ser posterior a la fecha final.");
        return;
    }

    const filtrados = gastosActuales.filter((gasto) => {
        return (!inicio || gasto.fecha >= inicio) &&
               (!fin || gasto.fecha <= fin);
    });

    renderizarTabla(
        filtrados, "listaGastos", "categoria", formularioGasto, "gastos"
    );

    document.getElementById("mensajeHistorial").textContent =
        `Se encontraron ${filtrados.length} gastos.`;

    generarReporte(filtrados);
}

function generarReporte(registros) {
    const total = registros.reduce(
        (suma, registro) => suma + Number(registro.valor), 0
    );

    document.getElementById("totalGastos").textContent =
        dinero.format(total);

    document.getElementById("cantidadGastos").textContent =
        registros.length;

    document.getElementById("promedioGastos").textContent =
        dinero.format(registros.length ? total / registros.length : 0);

    const categorias = {};

    registros.forEach((registro) => {
        const nombre = registro.categoria;

        if (!categorias[nombre]) {
            categorias[nombre] = { cantidad: 0, total: 0 };
        }

        categorias[nombre].cantidad += 1;
        categorias[nombre].total += Number(registro.valor);
    });

    const tbody = document.getElementById("reporteCategorias");
    tbody.replaceChildren();

    const nombres = Object.keys(categorias).sort();

    if (nombres.length === 0) {
        const fila = document.createElement("tr");
        const td = celda(fila, "No hay datos para el reporte.");
        td.colSpan = 3;
        tbody.appendChild(fila);
        return;
    }

    nombres.forEach((nombre) => {
        const fila = document.createElement("tr");

        celda(fila, nombre);
        celda(fila, categorias[nombre].cantidad);
        celda(fila, dinero.format(categorias[nombre].total));

        tbody.appendChild(fila);
    });
}

async function cargarDatos() {
    try {
        const [gastos, costos] = await Promise.all([
            solicitud(API.gastos),
            solicitud(API.costos)
        ]);

        gastosActuales = gastos;
        costosActuales = costos;

        aplicarFiltros();

        renderizarTabla(
            costosActuales, "listaCostos", "tipo", formularioCosto, "costos"
        );
    } catch (error) {
        mostrarError(error);
    }
}

const formularioGasto = configurarFormulario(
    "Gasto",
    {
        descripcion: "descripcionGasto",
        categoria: "categoriaGasto",
        valor: "valorGasto",
        fecha: "fechaGasto"
    },
    cargarDatos
);

const formularioCosto = configurarFormulario(
    "Costo",
    {
        descripcion: "descripcionCosto",
        tipo: "tipoCosto",
        valor: "valorCosto",
        fecha: "fechaCosto"
    },
    cargarDatos
);

document.getElementById("btnFiltrar").addEventListener("click", aplicarFiltros);

document.getElementById("btnLimpiar").addEventListener("click", () => {
    document.getElementById("fechaInicio").value = "";
    document.getElementById("fechaFin").value = "";
    aplicarFiltros();
});

cargarDatos();
