
from pathlib import Path
import sqlite3

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

# Ruta principal del proyecto NEXTREP
RAIZ = Path(__file__).resolve().parents[2]

# Frontend del modulo de ventas
FRONTEND = RAIZ / "frontend" / "ventas"

# Usar la misma base de datos del modulo de gastos
BASE_DATOS = RAIZ / "database" / "nextrep_gastos.db"

# Crear la carpeta database si no existe
BASE_DATOS.parent.mkdir(parents=True, exist_ok=True)


def conectar():
    conexion = sqlite3.connect(BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    return conexion


# Crear la tabla de ventas sin modificar las otras tablas
def inicializar_bd():
    with conectar() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto TEXT NOT NULL,
                cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                precio REAL NOT NULL CHECK(precio > 0),
                total REAL NOT NULL CHECK(total > 0)
            )
        """)


# Abrir la pantalla principal
@app.route("/")
def inicio():
    return send_from_directory(FRONTEND, "ventas.html")


# Cargar CSS y JavaScript
@app.route("/<path:archivo>")
def archivos_frontend(archivo):
    if archivo not in {"ventas.css", "ventas.js"}:
        return jsonify({"error": "Archivo no encontrado"}), 404

    return send_from_directory(FRONTEND, archivo)


# Validar la informacion recibida
def validar_venta(datos):
    producto = datos.get("producto")

    if not isinstance(producto, str) or not producto.strip():
        return None, "El nombre del producto es obligatorio."

    try:
        cantidad = int(datos.get("cantidad"))
        precio = float(datos.get("precio"))
    except (ValueError, TypeError, OverflowError):
        return None, "Cantidad y precio deben ser numericos."

    if cantidad <= 0 or precio <= 0:
        return None, "Cantidad y precio deben ser mayores que cero."

    total = cantidad * precio

    return {
        "producto": producto.strip(),
        "cantidad": cantidad,
        "precio": precio,
        "total": total
    }, None


# CONSULTAR ventas
@app.route("/api/ventas", methods=["GET"])
def consultar_ventas():
    with conectar() as db:
        filas = db.execute(
            "SELECT * FROM ventas ORDER BY id DESC"
        ).fetchall()

    return jsonify([dict(fila) for fila in filas])


# REGISTRAR una venta
@app.route("/api/ventas", methods=["POST"])
def registrar_venta():
    datos, error = validar_venta(
        request.get_json(silent=True) or {}
    )

    if error:
        return jsonify({"error": error}), 400

    with conectar() as db:
        cursor = db.execute("""
            INSERT INTO ventas
            (producto, cantidad, precio, total)
            VALUES (?, ?, ?, ?)
        """, (
            datos["producto"],
            datos["cantidad"],
            datos["precio"],
            datos["total"]
        ))

        nuevo_id = cursor.lastrowid

    return jsonify({
        "mensaje": "Venta registrada correctamente.",
        "id": nuevo_id
    }), 201


# EDITAR una venta
@app.route("/api/ventas/<int:venta_id>", methods=["PUT"])
def editar_venta(venta_id):
    datos, error = validar_venta(
        request.get_json(silent=True) or {}
    )

    if error:
        return jsonify({"error": error}), 400

    with conectar() as db:
        cursor = db.execute("""
            UPDATE ventas
            SET producto = ?, cantidad = ?, precio = ?, total = ?
            WHERE id = ?
        """, (
            datos["producto"],
            datos["cantidad"],
            datos["precio"],
            datos["total"],
            venta_id
        ))

        if cursor.rowcount == 0:
            return jsonify({
                "error": "La venta no existe."
            }), 404

    return jsonify({
        "mensaje": "Venta actualizada correctamente."
    })


# ELIMINAR una venta
@app.route("/api/ventas/<int:venta_id>", methods=["DELETE"])
def eliminar_venta(venta_id):
    with conectar() as db:
        cursor = db.execute(
            "DELETE FROM ventas WHERE id = ?",
            (venta_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({
                "error": "La venta no existe."
            }), 404

    return jsonify({
        "mensaje": "Venta eliminada correctamente."
    })


if __name__ == "__main__":
    inicializar_bd()

    # Puerto distinto al de Gastos.py
    app.run(debug=True, port=5001)
