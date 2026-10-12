// Formulario de gastos
const formGasto = document.getElementById("formGasto");

formGasto.addEventListener("submit", function(event) {

    event.preventDefault();

    const descripcion = document.getElementById("descripcionGasto").value;
    const categoria = document.getElementById("categoriaGasto").value;
    const valor = document.getElementById("valorGasto").value;
    const fecha = document.getElementById("fechaGasto").value;

    console.log("Gasto registrado:");
    console.log("Descripción:", descripcion);
    console.log("Categoría:", categoria);
    console.log("Valor:", valor);
    console.log("Fecha:", fecha);

    alert("Gasto registrado correctamente.");

    formGasto.reset();
});


// Formulario de costos
const formCosto = document.getElementById("formCosto");

formCosto.addEventListener("submit", function(event) {

    event.preventDefault();

    const descripcion = document.getElementById("descripcionCosto").value;
    const tipo = document.getElementById("tipoCosto").value;
    const valor = document.getElementById("valorCosto").value;
    const fecha = document.getElementById("fechaCosto").value;

    console.log("Costo registrado:");
    console.log("Descripción:", descripcion);
    console.log("Tipo:", tipo);
    console.log("Valor:", valor);
    console.log("Fecha:", fecha);

    alert("Costo registrado correctamente.");

    formCosto.reset();
});
