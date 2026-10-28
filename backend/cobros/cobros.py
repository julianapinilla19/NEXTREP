
from pathlib import Path
import sqlite3
import os
from functools import wraps

from flask import (
    Flask, jsonify, request, send_from_directory,
    session, redirect
)

app = Flask(__name__)

# Configuración de sesión: debe coincidir con Ventas y Gastos
app.config["SECRET_KEY"] = os.environ.get(
    "NEXTREP_SECRET_KEY",
    "clave-temporal-solo-desarrollo"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

RAIZ = Path(__file__).resolve().parents[2]
FRONTEND = RAIZ / "frontend" / "cobros"
BASE_DATOS = RAIZ / "database" / "nextrep_gastos.db"


# Verificar que el usuario haya iniciado sesión
def requiere_sesion(funcion):
    @wraps(funcion)
    def funcion_protegida(*args, **kwargs):
        if not session.get("usuario_id"):
            return jsonify({
                "error": "Debes iniciar sesión para realizar esta acción."
            }), 401

        return funcion(*args, **kwargs)

    return funcion_protegida


def conectar():
    conexion = sqlite3.connect(BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_bd():
    BASE_DATOS.parent.mkdir(parents=True, exist_ok=True)

    with conectar() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS cobros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                valor REAL NOT NULL CHECK(valor > 0),
                fecha TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'Pendiente'
            )
        """)


# Página principal de Cobros
@app.route("/")
def inicio():
    if not session.get("usuario_id"):
        return redirect("http://127.0.0.1:5001/login")

    return send_from_directory(FRONTEND, "cobros.html")


# Archivos de diseño y funcionamiento
@app.route("/<path:archivo>")
def archivos_frontend(archivo):
    if archivo not in {"cobros.css", "cobros.js"}:
        return jsonify({"error": "Archivo no encontrado"}), 404

    return send_from_directory(FRONTEND, archivo)


def validar(datos):
    cliente = str(datos.get("cliente", "")).strip()
    descripcion = str(datos.get("descripcion", "")).strip()
    fecha = str(datos.get("fecha", "")).strip()
    estado = str(datos.get("estado", "Pendiente")).strip()

    try:
        valor = float(datos.get("valor", 0))
    except (TypeError, ValueError):
        return None, "El valor debe ser numérico."

    if not cliente or not descripcion or not fecha:
        return None, "Completa todos los campos obligatorios."

    if valor <= 0:
        return None, "El valor debe ser mayor que cero."

    if estado not in {"Pendiente", "Pagado"}:
        return None, "El estado seleccionado no es válido."

    return {
        "cliente": cliente,
        "descripcion": descripcion,
        "valor": valor,
        "fecha": fecha,
        "estado": estado
    }, None


# Listar cobros
@app.route("/api/cobros", methods=["GET"])
@requiere_sesion
def listar_cobros():
    with conectar() as db:
        filas = db.execute(
            "SELECT * FROM cobros ORDER BY fecha DESC, id DESC"
        ).fetchall()

    return jsonify([dict(fila) for fila in filas])


# Registrar un cobro
@app.route("/api/cobros", methods=["POST"])
@requiere_sesion
def registrar_cobro():
    datos, error = validar(request.get_json(silent=True) or {})

    if error:
        return jsonify({"error": error}), 400

    with conectar() as db:
        cursor = db.execute("""
            INSERT INTO cobros
                (cliente, descripcion, valor, fecha, estado)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datos["cliente"],
            datos["descripcion"],
            datos["valor"],
            datos["fecha"],
            datos["estado"]
        ))

        nuevo_id = cursor.lastrowid

    return jsonify({
        "mensaje": "Cobro registrado correctamente.",
        "id": nuevo_id
    }), 201


# Editar un cobro
@app.route("/api/cobros/<int:cobro_id>", methods=["PUT"])
@requiere_sesion
def editar_cobro(cobro_id):
    datos, error = validar(request.get_json(silent=True) or {})

    if error:
        return jsonify({"error": error}), 400

    with conectar() as db:
        cursor = db.execute("""
            UPDATE cobros
            SET cliente = ?, descripcion = ?, valor = ?,
                fecha = ?, estado = ?
            WHERE id = ?
        """, (
            datos["cliente"],
            datos["descripcion"],
            datos["valor"],
            datos["fecha"],
            datos["estado"],
            cobro_id
        ))

        if cursor.rowcount == 0:
            return jsonify({"error": "Cobro no encontrado."}), 404

    return jsonify({"mensaje": "Cobro actualizado correctamente."})


# Eliminar un cobro
@app.route("/api/cobros/<int:cobro_id>", methods=["DELETE"])
@requiere_sesion
def eliminar_cobro(cobro_id):
    with conectar() as db:
        cursor = db.execute(
            "DELETE FROM cobros WHERE id = ?", (cobro_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Cobro no encontrado."}), 404

    return jsonify({"mensaje": "Cobro eliminado correctamente."})


if __name__ == "__main__":
    inicializar_bd()
    app.run(debug=True, port=5002)