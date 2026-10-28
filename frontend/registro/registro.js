
const formulario = document.getElementById("formulario-registro");
const mensaje = document.getElementById("mensaje");
const boton = document.getElementById("boton-registro");

formulario.addEventListener("submit", async function (evento) {
    evento.preventDefault();

    mensaje.textContent = "";
    mensaje.classList.remove("exito");

    const nombre = document.getElementById("nombre").value.trim();
    const correo = document.getElementById("correo").value.trim();
    const contrasena = document.getElementById("contrasena").value;
    const confirmar = document.getElementById("confirmar-contrasena").value;

    if (contrasena.length < 8) {
        mensaje.textContent = "La contraseña debe tener al menos 8 caracteres.";
        return;
    }

    if (contrasena !== confirmar) {
        mensaje.textContent = "Las contraseñas no coinciden.";
        return;
    }

    boton.disabled = true;
    boton.textContent = "Creando cuenta...";

    try {
        const respuesta = await fetch("/api/registro", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                nombre: nombre,
                correo: correo,
                contrasena: contrasena
            })
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            mensaje.textContent =
                resultado.error || "No fue posible crear la cuenta.";
            return;
        }

        mensaje.classList.add("exito");
        mensaje.textContent =
            resultado.mensaje || "Cuenta creada correctamente. Redirigiendo...";

        formulario.reset();

        setTimeout(() => {
            window.location.href = "/login";
        }, 1500);

    } catch (error) {
        mensaje.textContent =
            "No se pudo conectar con el servidor. Verifica que Flask esté funcionando.";
    } finally {
        boton.disabled = false;
        boton.textContent = "Crear cuenta";
    }
});