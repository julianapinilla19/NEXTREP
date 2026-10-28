

const formulario = document.getElementById("formulario-login");
const mensaje = document.getElementById("mensaje");
const boton = document.getElementById("boton-login");

formulario.addEventListener("submit", async function (evento) {
    evento.preventDefault();

    mensaje.textContent = "";
    boton.disabled = true;
    boton.textContent = "Ingresando...";

    const datos = {
        correo: document.getElementById("correo").value.trim(),
        contrasena: document.getElementById("contrasena").value
    };

    try {
        const respuesta = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(datos)
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            mensaje.textContent =
                resultado.error || "No fue posible iniciar sesión.";
            return;
        }

        window.location.href = "/panel";

    } catch (error) {
        mensaje.textContent =
            "No se pudo conectar con el servidor. Verifica que Flask esté funcionando.";
    } finally {
        boton.disabled = false;
        boton.textContent = "Iniciar sesión";
    }
});
