
const API = "/api/ventas";

function formatoCOP(valor) {
    return Number(valor).toLocaleString("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 2
    });
}

async function cargarVentas() {
    try {
        const respuesta = await fetch(API);

        if (!respuesta.ok) {
            throw new Error("No se pudieron consultar las ventas");
        }

        const ventas = await respuesta.json();
        const tabla = document.getElementById("listaVentas");
        tabla.innerHTML = "";

        ventas.forEach(venta => {
            const fila = document.createElement("tr");

            [
                venta.id,
                venta.producto,
                venta.cantidad,
                formatoCOP(venta.precio),
                formatoCOP(venta.total)
            ].forEach(valor => {
                const celda = document.createElement("td");
                celda.textContent = valor;
                fila.appendChild(celda);
            });

            const acciones = document.createElement("td");

            const botonEditar = document.createElement("button");
            botonEditar.textContent = "Editar";
            botonEditar.onclick = () => editarVenta(venta);

            const botonEliminar = document.createElement("button");
            botonEliminar.textContent = "Eliminar";
            botonEliminar.onclick = () => eliminarVenta(venta.id);

            acciones.append(botonEditar, " ", botonEliminar);
            fila.appendChild(acciones);
            tabla.appendChild(fila);
        });
    } catch (error) {
        console.error(error);
        alert("No se pudieron cargar las ventas. Revisa el backend.");
    }
}

async function registrarVenta() {
    const producto = document.getElementById("producto").value.trim();
    const cantidad = Number(document.getElementById("cantidad").value);
    const precio = Number(document.getElementById("precio").value);

    if (!producto || !Number.isInteger(cantidad) ||
        cantidad <= 0 || !Number.isFinite(precio) || precio <= 0) {
        alert("Ingresa un producto, una cantidad entera y un precio válido.");
        return;
    }

    try {
        const respuesta = await fetch(API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ producto, cantidad, precio })
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || "No se pudo registrar la venta");
        }

        document.getElementById("producto").value = "";
        document.getElementById("cantidad").value = "";
        document.getElementById("precio").value = "";

        await cargarVentas();
        alert("Venta registrada correctamente.");
    } catch (error) {
        alert(error.message);
    }
}

async function editarVenta(venta) {
    const producto = prompt("Nombre del producto:", venta.producto);
    if (producto === null) return;

    const cantidadTexto = prompt("Cantidad:", venta.cantidad);
    if (cantidadTexto === null) return;

    const precioTexto = prompt("Precio unitario:", venta.precio);
    if (precioTexto === null) return;

    const cantidad = Number(cantidadTexto);
    const precio = Number(precioTexto);

    if (!producto.trim() || !Number.isInteger(cantidad) ||
        cantidad <= 0 || !Number.isFinite(precio) || precio <= 0) {
        alert("Los datos ingresados no son válidos.");
        return;
    }

    try {
        const respuesta = await fetch(`${API}/${venta.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ producto, cantidad, precio })
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || "No se pudo editar la venta");
        }

        await cargarVentas();
        alert("Venta actualizada correctamente.");
    } catch (error) {
        alert(error.message);
    }
}

async function eliminarVenta(id) {
    if (!confirm("¿Seguro que deseas eliminar esta venta?")) return;

    try {
        const respuesta = await fetch(`${API}/${id}`, {
            method: "DELETE"
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || "No se pudo eliminar la venta");
        }

        await cargarVentas();
        alert("Venta eliminada correctamente.");
    } catch (error) {
        alert(error.message);
    }
}

document.addEventListener("DOMContentLoaded", cargarVentas);
