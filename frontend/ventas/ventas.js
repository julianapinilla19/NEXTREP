
const API = "/api/ventas";

async function cargarVentas() {
    const tabla = document.getElementById("listaVentas");

    try {
        const respuesta = await fetch(API);
        const ventas = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error("No se pudieron consultar las ventas.");
        }

        tabla.replaceChildren();

        if (ventas.length === 0) {
            const fila = tabla.insertRow();
            const celda = fila.insertCell();

            celda.colSpan = 6;
            celda.textContent = "Todavia no hay ventas registradas.";
            return;
        }

        ventas.forEach(venta => {
            const fila = tabla.insertRow();

            [
                venta.id,
                venta.producto,
                venta.cantidad,
                formatoPesos(venta.precio),
                formatoPesos(venta.total)
            ].forEach(valor => {
                const celda = fila.insertCell();
                celda.textContent = valor;
            });

            const acciones = fila.insertCell();

            const botonEditar = document.createElement("button");
            botonEditar.textContent = "Editar";
            botonEditar.type = "button";
            botonEditar.addEventListener("click", () => {
                editarVenta(venta);
            });

            const botonEliminar = document.createElement("button");
            botonEliminar.textContent = "Eliminar";
            botonEliminar.type = "button";
            botonEliminar.addEventListener("click", () => {
                eliminarVenta(venta.id);
            });

            acciones.append(botonEditar, botonEliminar);
        });

    } catch (error) {
        alert("No se pudieron cargar las ventas. Revisa el servidor.");
        console.error(error);
    }
}

function formatoPesos(valor) {
    return Number(valor).toLocaleString("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 2
    });
}

// Registrar una venta nueva
async function registrarVenta() {
    const producto = document.getElementById("producto").value.trim();
    const cantidadTexto = document.getElementById("cantidad").value;
    const precioTexto = document.getElementById("precio").value;

    if (!producto || !cantidadTexto || !precioTexto) {
        alert("Completa todos los campos.");
        return;
    }

    const cantidad = Number(cantidadTexto);
    const precio = Number(precioTexto);

    if (!Number.isInteger(cantidad) || cantidad <= 0 ||
        !Number.isFinite(precio) || precio <= 0) {
        alert("La cantidad y el precio deben ser mayores que cero.");
        return;
    }

    try {
        const respuesta = await fetch(API, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                producto,
                cantidad,
                precio
            })
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || "Error al registrar.");
        }

        document.getElementById("producto").value = "";
        document.getElementById("cantidad").value = "";
        document.getElementById("precio").value = "";

        await cargarVentas();
        alert("Venta registrada correctamente.");

    } catch (error) {
        alert(error.message || "No se pudo conectar con el servidor.");
    }
}

// Editar una venta existente
async function editarVenta(venta) {
    const producto = prompt("Nombre del producto:", venta.producto);
    if (producto === null) return;

    const cantidadTexto = prompt("Cantidad:", venta.cantidad);
    if (cantidadTexto === null) return;

    const precioTexto = prompt("Precio por unidad:", venta.precio);
    if (precioTexto === null) return;

    const cantidad = Number(cantidadTexto);
    const precio = Number(precioTexto);

    if (!producto.trim() || !Number.isInteger(cantidad) ||
        cantidad <= 0 || !Number.isFinite(precio) || precio <= 0) {
        alert("Verifica el producto, la cantidad y el precio.");
        return;
    }

    try {
        const respuesta = await fetch(`${API}/${venta.id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                producto: producto.trim(),
                cantidad,
                precio
            })
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || "No se pudo editar.");
        }

        await cargarVentas();
        alert("Venta actualizada correctamente.");

    } catch (error) {
        alert(error.message || "Error al editar la venta.");
    }
}

// Eliminar una venta
async function eliminarVenta(id) {
    if (!confirm("¿Seguro que deseas eliminar esta venta?")) {
        return;
    }

    try {
        const respuesta = await fetch(`${API}/${id}`, {
            method: "DELETE"
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || "No se pudo eliminar.");
        }

        await cargarVentas();
        alert("Venta eliminada correctamente.");

    } catch (error) {
        alert(error.message || "Error al eliminar la venta.");
    }
}

// Consultar las ventas al abrir la pantalla
document.addEventListener("DOMContentLoaded", cargarVentas);
