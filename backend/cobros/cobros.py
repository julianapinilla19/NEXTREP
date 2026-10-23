
from pathlib import Path
import sqlite3

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

RAIZ = Path(__file__).resolve().parents[2]
FRONTEND = RAIZ / "frontend" / "cobros"
BASE_DATOS = RAIZ / "database" / "nextrep_gastos.db"


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


@app.route("/")
def inicio():
    return send_from_directory(FRONTEND, "cobros.html")


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


@app.route("/api/cobros", methods=["GET"])
def listar_cobros():
    with conectar() as db:
        filas = db.execute(
            "SELECT * FROM cobros ORDER BY fecha DESC, id DESC"
        ).fetchall()

    return jsonify([dict(fila) for fila in filas])


@app.route("/api/cobros", methods=["POST"])
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


@app.route("/api/cobros/<int:cobro_id>", methods=["PUT"])
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


@app.route("/api/cobros/<int:cobro_id>", methods=["DELETE"])
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
