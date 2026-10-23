
from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from pathlib import Path

app = Flask(__name__)

# Ubicacion de las carpetas del proyecto
RAIZ = Path(__file__).resolve().parents[2]
FRONTEND = RAIZ / "frontend" / "ventas"
BASE_DATOS = RAIZ / "database" / "nextrep_gastos.db"


def conectar():
    return sqlite3.connect(BASE_DATOS)


def crear_tabla():
    BASE_DATOS.parent.mkdir(parents=True, exist_ok=True)

    with conectar() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                precio REAL NOT NULL,
                total REAL NOT NULL
            )
        """)


@app.route("/")
def inicio():
    return send_from_directory(FRONTEND, "ventas.html")


@app.route("/<path:archivo>")
def archivos_frontend(archivo):
    if archivo in ("ventas.css", "ventas.js"):
        return send_from_directory(FRONTEND, archivo)

    return jsonify({"error": "Archivo no encontrado"}), 404


# Consultar todas las ventas
@app.route("/api/ventas", methods=["GET"])
def listar_ventas():
    with conectar() as db:
        db.row_factory = sqlite3.Row
        filas = db.execute(
            "SELECT * FROM ventas ORDER BY id DESC"
        ).fetchall()

    return jsonify([dict(fila) for fila in filas])


# Registrar una venta
@app.route("/api/ventas", methods=["POST"])
def registrar_venta():
    datos = request.get_json(silent=True) or {}

    producto = str(datos.get("producto", "")).strip()

    try:
        cantidad = int(datos.get("cantidad", 0))
        precio = float(datos.get("precio", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Cantidad o precio inválido"}), 400

    if not producto or cantidad <= 0 or precio <= 0:
        return jsonify({
            "error": "Ingresa producto, cantidad y precio válidos"
        }), 400

    total = cantidad * precio

    with conectar() as db:
        cursor = db.execute(
            """INSERT INTO ventas (producto, cantidad, precio, total)
               VALUES (?, ?, ?, ?)""",
            (producto, cantidad, precio, total)
        )
        venta_id = cursor.lastrowid

    return jsonify({
        "id": venta_id,
        "producto": producto,
        "cantidad": cantidad,
        "precio": precio,
        "total": total
    }), 201


# Editar una venta
@app.route("/api/ventas/<int:venta_id>", methods=["PUT"])
def editar_venta(venta_id):
    datos = request.get_json(silent=True) or {}

    producto = str(datos.get("producto", "")).strip()

    try:
        cantidad = int(datos.get("cantidad", 0))
        precio = float(datos.get("precio", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Cantidad o precio inválido"}), 400

    if not producto or cantidad <= 0 or precio <= 0:
        return jsonify({
            "error": "Ingresa producto, cantidad y precio válidos"
        }), 400

    total = cantidad * precio

    with conectar() as db:
        cursor = db.execute(
            """UPDATE ventas
               SET producto = ?, cantidad = ?, precio = ?, total = ?
               WHERE id = ?""",
            (producto, cantidad, precio, total, venta_id)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Venta no encontrada"}), 404

    return jsonify({"mensaje": "Venta actualizada correctamente"})


# Eliminar una venta
@app.route("/api/ventas/<int:venta_id>", methods=["DELETE"])
def eliminar_venta(venta_id):
    with conectar() as db:
        cursor = db.execute(
            "DELETE FROM ventas WHERE id = ?", (venta_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Venta no encontrada"}), 404

    return jsonify({"mensaje": "Venta eliminada correctamente"})


if __name__ == "__main__":
    crear_tabla()
    app.run(debug=True, port=5001)
