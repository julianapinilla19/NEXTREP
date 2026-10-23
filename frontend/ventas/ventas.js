
const API = "/api/ventas";
const API_HISTORIAL = "/api/ventas/historial";
const API_TOTAL = "/api/ventas/total";

function formatoCOP(valor) {
    return Number(valor).toLocaleString("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 2
    });
}

// Consultar y mostrar las ventas
async function cargarVentas(url = API) {
    try {
        const respuesta = await fetch(url);

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
                formatoCOP(venta.total),
                venta.fecha || "Sin fecha"
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

// Registrar una venta
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

        await consultarHistorial();
        alert("Venta registrada correctamente.");

    } catch (error) {
        alert(error.message);
    }
}

// Editar una venta
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

        await consultarHistorial();
        alert("Venta actualizada correctamente.");

    } catch (error) {
        alert(error.message);
    }
}

// Eliminar una venta
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

        await consultarHistorial();
        alert("Venta eliminada correctamente.");

    } catch (error) {
        alert(error.message);
    }
}

// Consultar el historial por fechas
async function consultarHistorial() {
    const desde = document.getElementById("fechaDesde").value;
    const hasta = document.getElementById("fechaHasta").value;

    if (desde && hasta && desde > hasta) {
        alert("La fecha inicial no puede ser posterior a la fecha final.");
        return;
    }

    const parametros = new URLSearchParams();

    if (desde) parametros.set("desde", desde);
    if (hasta) parametros.set("hasta", hasta);

    const sufijo = parametros.toString();
    const urlHistorial = sufijo
        ? `${API_HISTORIAL}?${sufijo}`
        : API_HISTORIAL;

    try {
        const respuesta = await fetch(urlHistorial);

        if (!respuesta.ok) {
            throw new Error("No se pudo consultar el historial");
        }

        const ventas = await respuesta.json();

        // Mostrar el historial en la tabla
        await cargarVentasDesdeLista(ventas);

        // Consultar el total del mismo período
        const urlTotal = sufijo
            ? `${API_TOTAL}?${sufijo}`
            : API_TOTAL;

        const respuestaTotal = await fetch(urlTotal);

        if (!respuestaTotal.ok) {
            throw new Error("No se pudo consultar el total");
        }

        const resultadoTotal = await respuestaTotal.json();

        document.getElementById("totalVentas").textContent =
            formatoCOP(resultadoTotal.total_ventas);

    } catch (error) {
        console.error(error);
        alert("No se pudo consultar el historial o el total de ventas.");
    }
}

// Mostrar en la tabla una lista de ventas recibida
async function cargarVentasDesdeLista(ventas) {
    const tabla = document.getElementById("listaVentas");
    tabla.innerHTML = "";

    ventas.forEach(venta => {
        const fila = document.createElement("tr");

        [
            venta.id,
            venta.producto,
            venta.cantidad,
            formatoCOP(venta.precio),
            formatoCOP(venta.total),
            venta.fecha || "Sin fecha"
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
}

// Quitar el filtro y mostrar todas las ventas
async function limpiarFiltro() {
    document.getElementById("fechaDesde").value = "";
    document.getElementById("fechaHasta").value = "";

    await consultarHistorial();
}

document.addEventListener("DOMContentLoaded", consultarHistorial);
