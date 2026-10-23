
from pathlib import Path
from datetime import date
import sqlite3

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

RAIZ = Path(__file__).resolve().parents[2]
FRONTEND = RAIZ / "frontend" / "gastos"
BASE_DATOS = RAIZ / "database" / "nextrep_gastos.db"

BASE_DATOS.parent.mkdir(parents=True, exist_ok=True)


def conectar():
    db = sqlite3.connect(BASE_DATOS)
    db.row_factory = sqlite3.Row
    return db


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


def validar(datos, recurso):
    campo_tipo = "categoria" if recurso == "gastos" else "tipo"

    descripcion = datos.get("descripcion")
    clasificacion = datos.get(campo_tipo)
    fecha = datos.get("fecha")

    try:
        valor = float(datos.get("valor"))
    except (TypeError, ValueError):
        return None, "El valor debe ser numérico."

    if not isinstance(descripcion, str) or not descripcion.strip():
        return None, "La descripción es obligatoria."

    if not isinstance(clasificacion, str) or not clasificacion.strip():
        return None, "La categoría o tipo es obligatorio."

    if not isinstance(fecha, str):
        return None, "La fecha es obligatoria."

    try:
        fecha_obj = date.fromisoformat(fecha)
        if fecha_obj.isoformat() != fecha:
            raise ValueError
    except ValueError:
        return None, "La fecha debe tener formato AAAA-MM-DD."

    if not 0 < valor < float("inf"):
        return None, "El valor debe ser mayor que cero y finito."

    return {
        "descripcion": descripcion.strip(),
        campo_tipo: clasificacion.strip(),
        "valor": valor,
        "fecha": fecha
    }, None


def registrar_rutas(recurso):
    campo_tipo = "categoria" if recurso == "gastos" else "tipo"

    def listar():
        with conectar() as db:
            filas = db.execute(
                f"SELECT * FROM {recurso} ORDER BY fecha DESC, id DESC"
            ).fetchall()

        return jsonify([dict(fila) for fila in filas])

    def crear():
        datos, error = validar(request.get_json(silent=True) or {}, recurso)

        if error:
            return jsonify({"error": error}), 400

        with conectar() as db:
            cursor = db.execute(
                f"""INSERT INTO {recurso}
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

    def actualizar(registro_id):
        datos, error = validar(request.get_json(silent=True) or {}, recurso)

        if error:
            return jsonify({"error": error}), 400

        with conectar() as db:
            cursor = db.execute(
                f"""UPDATE {recurso}
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

    def eliminar(registro_id):
        with conectar() as db:
            cursor = db.execute(
                f"DELETE FROM {recurso} WHERE id = ?",
                (registro_id,)
            )

            if cursor.rowcount == 0:
                return jsonify({"error": "Registro no encontrado."}), 404

        return jsonify({"mensaje": "Registro eliminado correctamente."})

    # Endpoints con nombres únicos para cada recurso.
    app.add_url_rule(
        f"/api/{recurso}", endpoint=f"{recurso}_listar",
        view_func=listar, methods=["GET"]
    )
    app.add_url_rule(
        f"/api/{recurso}", endpoint=f"{recurso}_crear",
        view_func=crear, methods=["POST"]
    )
    app.add_url_rule(
        f"/api/{recurso}/<int:registro_id>",
        endpoint=f"{recurso}_actualizar",
        view_func=actualizar, methods=["PUT"]
    )
    app.add_url_rule(
        f"/api/{recurso}/<int:registro_id>",
        endpoint=f"{recurso}_eliminar",
        view_func=eliminar, methods=["DELETE"]
    )


registrar_rutas("gastos")
registrar_rutas("costos")


if __name__ == "__main__":
    inicializar_bd()
    app.run(debug=True)
