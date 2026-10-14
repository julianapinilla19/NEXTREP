function registrarVenta() {

    // Obtener los datos del formulario
    let producto = document.getElementById("producto").value;
    let cantidad = document.getElementById("cantidad").value;
    let precio = document.getElementById("precio").value;

    // Validar que los campos estén completos
    if (producto === "" || cantidad === "" || precio === "") {
        alert("Por favor, complete todos los campos.");
        return;
    }

    // Calcular el total
    let total = cantidad * precio;

    // Crear una nueva fila
    let tabla = document.getElementById("listaVentas");

    let fila = tabla.insertRow();

    fila.insertCell(0).innerHTML = producto;
    fila.insertCell(1).innerHTML = cantidad;
    fila.insertCell(2).innerHTML = precio;
    fila.insertCell(3).innerHTML = total;

    // Limpiar los campos
    document.getElementById("producto").value = "";
    document.getElementById("cantidad").value = "";
    document.getElementById("precio").value = "";
}
