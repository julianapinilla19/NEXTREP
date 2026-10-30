

const formulario = document.getElementById("formCobros");
const tabla = document.getElementById("tablaCobros");
const mensaje = document.getElementById("mensaje");
const botonGuardar = document.getElementById("btnGuardar");
const botonCancelar = document.getElementById("btnCancelar");

let cobros = [];

async function cargarCobros() {
    try {
        const respuesta = await fetch("/api/cobros");

        if (!respuesta.ok) {
            throw new Error("No se pudieron consultar los cobros.");
        }

        cobros = await respuesta.json();
        mostrarCobros();
    } catch (error) {
        mensaje.textContent = "Error al cargar los cobros. Revisa el servidor.";
        console.error(error);
    }
}

function mostrarCobros() {
    tabla.innerHTML = "";

    cobros.forEach(function(cobro) {
        const fila = document.createElement("tr");

        const datos = [
            cobro.cliente,
            cobro.descripcion,
            "$ " + Number(cobro.valor).toLocaleString("es-CO"),
            cobro.fecha,
            cobro.estado
        ];

        datos.forEach(function(dato) {
            const celda = document.createElement("td");
            celda.textContent = dato;
            fila.appendChild(celda);
        });

        const acciones = document.createElement("td");

        const botonEditar = document.createElement("button");
        botonEditar.textContent = "Editar";
        botonEditar.type = "button";
        botonEditar.addEventListener("click", function() {
            editarCobro(cobro);
        });

        const botonEliminar = document.createElement("button");
        botonEliminar.textContent = "Eliminar";
        botonEliminar.type = "button";
        botonEliminar.addEventListener("click", function() {
            eliminarCobro(cobro.id);
        });

        acciones.appendChild(botonEditar);
        acciones.appendChild(botonEliminar);
        fila.appendChild(acciones);

        tabla.appendChild(fila);
    });
}

formulario.addEventListener("submit", async function(evento) {
    evento.preventDefault();

    const id = document.getElementById("cobroId").value;

    const datos = {
        cliente: document.getElementById("cliente").value.trim(),
        descripcion: document.getElementById("descripcion").value.trim(),
        valor: Number(document.getElementById("valor").value),
        fecha: document.getElementById("fecha").value,
        estado: document.getElementById("estado").value
    };

    try {
        botonGuardar.disabled = true;

        const respuesta = await fetch(
            id ? "/api/cobros/" + id : "/api/cobros",
            {
                method: id ? "PUT" : "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(datos)
            }
        );

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || "No se pudo guardar el cobro.");
        }

        mensaje.textContent = resultado.mensaje;
        formulario.reset();
        document.getElementById("cobroId").value = "";
        botonGuardar.textContent = "Registrar cobro";

        await cargarCobros();

    } catch (error) {
        mensaje.textContent = error.message;
        console.error(error);
    } finally {
        botonGuardar.disabled = false;
    }
});

function editarCobro(cobro) {
    document.getElementById("cobroId").value = cobro.id;
    document.getElementById("cliente").value = cobro.cliente;
    document.getElementById("descripcion").value = cobro.descripcion;
    document.getElementById("valor").value = cobro.valor;
    document.getElementById("fecha").value = cobro.fecha;
    document.getElementById("estado").value = cobro.estado;

    botonGuardar.textContent = "Guardar cambios";
    mensaje.textContent = "Editando el cobro #" + cobro.id;

    formulario.scrollIntoView({ behavior: "smooth" });
}

async function eliminarCobro(id) {
    if (!confirm("¿Seguro que deseas eliminar este cobro?")) {
        return;
    }

    try {
        const respuesta = await fetch("/api/cobros/" + id, {
            method: "DELETE"
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || "No se pudo eliminar el cobro.");
        }

        mensaje.textContent = resultado.mensaje;
        await cargarCobros();

    } catch (error) {
        mensaje.textContent = error.message;
        console.error(error);
    }
}

botonCancelar.addEventListener("click", function() {
    formulario.reset();
    document.getElementById("cobroId").value = "";
    botonGuardar.textContent = "Registrar cobro";
    mensaje.textContent = "";
});

cargarCobros();
