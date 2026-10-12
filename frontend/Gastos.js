
const API = {
    gastos: "/api/gastos",
    costos: "/api/costos"
};

const formatoCOP = new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 2
});

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
        throw new Error(datos.error || "Ocurrió un error.");
    }

    return datos;
}

function mostrarError(error) {
    alert(error.message || "No se pudo completar la operación.");
}

function configurarModulo(tipo, campos, listaId, cancelarId, botonId) {
    const formulario = document.getElementById(`form${tipo}`);
    const lista = document.getElementById(listaId);
    const cancelar = document.getElementById(cancelarId);
    const boton = document.getElementById(botonId);

    const url = API[tipo.toLowerCase() === "gasto" ? "gastos" : "costos"];
    let idEditando = null;

    function valoresFormulario() {
        return Object.fromEntries(
            Object.entries(campos).map(([campo, id]) => [
                campo,
                document.getElementById(id).value.trim()
            ])
        );
    }

    function limpiarFormulario() {
        formulario.reset();
        idEditando = null;
        boton.textContent = `Registrar ${tipo.toLowerCase()}`;
        cancelar.classList.add("oculto");
    }

    cancelar.addEventListener("click", limpiarFormulario);

    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        const datos = valoresFormulario();
        datos.valor = Number(datos.valor);

        if (!Number.isFinite(datos.valor) || datos.valor <= 0) {
            alert("El valor debe ser mayor que cero.");
            return;
        }

        try {
            const direccion = idEditando ? `${url}/${idEditando}` : url;

            await solicitud(direccion, {
                method: idEditando ? "PUT" : "POST",
                body: JSON.stringify(datos)
            });

            limpiarFormulario();
            await cargarLista();
            alert(`${tipo} ${idEditando ? "actualizado" : "registrado"} correctamente.`);
        } catch (error) {
            mostrarError(error);
        }
    });

    async function cargarLista() {
        try {
            const registros = await solicitud(url);
            lista.replaceChildren();

            if (registros.length === 0) {
                const fila = document.createElement("tr");
                const celda = document.createElement("td");
                celda.colSpan = 5;
                celda.textContent = "No hay registros todavía.";
                fila.appendChild(celda);
                lista.appendChild(fila);
                return;
            }

            registros.forEach((registro) => {
                const fila = document.createElement("tr");

                const valores = [
                    registro.descripcion,
                    registro.categoria || registro.tipo,
                    formatoCOP.format(registro.valor),
                    registro.fecha
                ];

                valores.forEach((valor) => {
                    const celda = document.createElement("td");
                    celda.textContent = valor;
                    fila.appendChild(celda);
                });

                const acciones = document.createElement("td");

                const editar = document.createElement("button");
                editar.textContent = "Editar";
                editar.className = "accion";
                editar.addEventListener("click", () => {
                    idEditando = registro.id;

                    Object.entries(campos).forEach(([campo, id]) => {
                        const valor = campo === "valor"
                            ? registro.valor
                            : registro[campo];

                        document.getElementById(id).value = valor ?? "";
                    });

                    boton.textContent = `Guardar cambios`;
                    cancelar.classList.remove("oculto");
                    formulario.scrollIntoView({ behavior: "smooth" });
                });

                const eliminar = document.createElement("button");
                eliminar.textContent = "Eliminar";
                eliminar.className = "accion eliminar";
                eliminar.addEventListener("click", async () => {
                    if (!confirm(`¿Deseas eliminar este ${tipo.toLowerCase()}?`)) {
                        return;
                    }

                    try {
                        await solicitud(`${url}/${registro.id}`, {
                            method: "DELETE"
                        });

                        if (idEditando === registro.id) {
                            limpiarFormulario();
                        }

                        await cargarLista();
                    } catch (error) {
                        mostrarError(error);
                    }
                });

                acciones.append(editar, eliminar);
                fila.appendChild(acciones);
                lista.appendChild(fila);
            });
        } catch (error) {
            mostrarError(error);
        }
    }

    cargarLista();
}

configurarModulo(
    "Gasto",
    {
        descripcion: "descripcionGasto",
        categoria: "categoriaGasto",
        valor: "valorGasto",
        fecha: "fechaGasto"
    },
    "listaGastos",
    "cancelarGasto",
    "btnGasto"
);

configurarModulo(
    "Costo",
    {
        descripcion: "descripcionCosto",
        tipo: "tipoCosto",
        valor: "valorCosto",
        fecha: "fechaCosto"
    },
    "listaCostos",
    "cancelarCosto",
    "btnCosto"
);
