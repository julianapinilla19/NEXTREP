const nombreElemento = document.getElementById("nombre");
const correoElemento = document.getElementById("correo");
const avatar = document.getElementById("avatar");
const mensaje = document.getElementById("mensaje");
const botonCerrar = document.getElementById("boton-cerrar");

async function cargarPerfil() {
    try {
        const respuesta = await fetch("/api/perfil");

        if (respuesta.status === 401 || respuesta.status === 403) {
            window.location.href = "/login";
            return;
        }

        const usuario = await respuesta.json();

        if (!respuesta.ok) {
            mensaje.textContent =
                usuario.error || "No se pudo cargar el perfil.";
            return;
        }

        nombreElemento.textContent = usuario.nombre;
        correoElemento.textContent = usuario.correo;
        avatar.textContent = usuario.nombre.trim().charAt(0).toUpperCase();

    } catch (error) {
        mensaje.textContent =
            "No se pudo conectar con el servidor.";
    }
}

botonCerrar.addEventListener("click", async function () {
    botonCerrar.disabled = true;
    botonCerrar.textContent = "Cerrando sesión...";
    mensaje.textContent = "";

    try {
        const respuesta = await fetch("/api/logout", {
            method: "POST"
        });

        if (!respuesta.ok) {
            mensaje.textContent = "No se pudo cerrar la sesión.";
            return;
        }

        window.location.href = "/login";

    } catch (error) {
        mensaje.textContent =
            "No se pudo conectar con el servidor.";
    } finally {
        botonCerrar.disabled = false;
        botonCerrar.textContent = "Cerrar sesión";
    }
});

cargarPerfil();