
from pathlib import Path
import sqlite3

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

# Raíz del repositorio NEXTREP
RAIZ = Path(__file__).resolve().parents[2]
FRONTEND = RAIZ / "frontend" / "gastos"
BASE_DATOS = RAIZ / "database" / "nextrep_gastos.db"

BASE_DATOS.parent.mkdir(parents=True, exist_ok=True)


def conectar():
    conexion = sqlite3.connect(BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_bd():
    with conectar() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                categoria TEXT NOT NULL,
                valor REAL NOT NULL CHECK(valor > 0),
                fecha TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS costos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                tipo TEXT NOT NULL,
                valor REAL NOT NULL CHECK(valor > 0),
                fecha TEXT NOT NULL
            )
        """)


@app.route("/")
def inicio():
    return send_from_directory(FRONTEND, "gastos.html")


@app.route("/<path:archivo>")
def archivos_frontend(archivo):
    if archivo not in {"gastos.css", "gastos.js"}:
        return jsonify({"error": "Archivo no encontrado"}), 404

    return send_from_directory(FRONTEND, archivo)


def validar(datos, tipo):
    campo_tipo = "categoria" if tipo == "gastos" else "tipo"

    descripcion = datos.get("descripcion")
    clasificacion = datos.get(campo_tipo)
    fecha = datos.get("fecha")

    try:
        valor = float(datos.get("valor"))
    except (TypeError, ValueError):
        valor = 0

    if not all([descripcion, clasificacion, fecha]):
        return None, "Todos los campos son obligatorios."

    if valor <= 0:
        return None, "El valor debe ser mayor que cero."

    campos = {
        "descripcion": str(descripcion).strip(),
        campo_tipo: str(clasificacion).strip(),
        "valor": valor,
        "fecha": str(fecha)
    }

    if not campos["descripcion"] or not campos[campo_tipo]:
        return None, "La descripción y el tipo son obligatorios."

    return campos, None


def crear_rutas(tipo):
    campo_tipo = "categoria" if tipo == "gastos" else "tipo"

    @app.route(f"/api/{tipo}", methods=["GET"])
    def listar():
        with conectar() as db:
            filas = db.execute(
                f"SELECT * FROM {tipo} ORDER BY fecha DESC, id DESC"
            ).fetchall()

        return jsonify([dict(fila) for fila in filas])

    @app.route(f"/api/{tipo}", methods=["POST"])
    def crear():
        datos, error = validar(request.get_json(silent=True) or {}, tipo)

        if error:
            return jsonify({"error": error}), 400

        with conectar() as db:
            cursor = db.execute(
                f"""INSERT INTO {tipo}
                    (descripcion, {campo_tipo}, valor, fecha)
                    VALUES (?, ?, ?, ?)""",
                (
                    datos["descripcion"],
                    datos[campo_tipo],
                    datos["valor"],
                    datos["fecha"]
                )
            )
            nuevo_id = cursor.lastrowid

        return jsonify({
            "mensaje": "Registro creado correctamente.",
            "id": nuevo_id
        }), 201

    @app.route(f"/api/{tipo}/<int:registro_id>", methods=["PUT"])
    def actualizar(registro_id):
        datos, error = validar(request.get_json(silent=True) or {}, tipo)

        if error:
            return jsonify({"error": error}), 400

        with conectar() as db:
            cursor = db.execute(
                f"""UPDATE {tipo}
                    SET descripcion = ?, {campo_tipo} = ?,
                        valor = ?, fecha = ?
                    WHERE id = ?""",
                (
                    datos["descripcion"],
                    datos[campo_tipo],
                    datos["valor"],
                    datos["fecha"],
                    registro_id
                )
            )

            if cursor.rowcount == 0:
                return jsonify({"error": "Registro no encontrado."}), 404

        return jsonify({"mensaje": "Registro actualizado correctamente."})

    @app.route(f"/api/{tipo}/<int:registro_id>", methods=["DELETE"])
    def eliminar(registro_id):
        with conectar() as db:
            cursor = db.execute(
                f"DELETE FROM {tipo} WHERE id = ?",
                (registro_id,)
            )

            if cursor.rowcount == 0:
                return jsonify({"error": "Registro no encontrado."}), 404

        return jsonify({"mensaje": "Registro eliminado correctamente."})


crear_rutas("gastos")
crear_rutas("costos")

if __name__ == "__main__":
    inicializar_bd()
    app.run(debug=True)
