

from pathlib import Path
from functools import wraps
import os
import sqlite3

from flask import (
    Flask,
    jsonify,
    request,
    send_from_directory,
    session,
    redirect
)

app = Flask(__name__)

# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

app.config["SECRET_KEY"] = os.environ.get(
    "NEXTREP_SECRET_KEY",
    "clave-temporal-solo-desarrollo"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

RAIZ = Path(__file__).resolve().parents[1]
FRONTEND = RAIZ / "frontend" / "Gastos"
BASE_DATOS = RAIZ / "database" / "nextrep_gastos.db"

BASE_DATOS.parent.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# PROTECCIÓN DE LAS API
# --------------------------------------------------

def requiere_sesion(funcion):
    @wraps(funcion)
    def funcion_protegida(*args, **kwargs):
        if not session.get("usuario_id"):
            return jsonify({
                "error": "Debes iniciar sesión para realizar esta acción."
            }), 401

        return funcion(*args, **kwargs)

    return funcion_protegida


# --------------------------------------------------
# CONEXIÓN Y BASE DE DATOS
# --------------------------------------------------

def conectar():
    conexion = sqlite3.connect(BASE_DATOS, timeout=10)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar_bd():
    with conectar() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                categoria TEXT NOT NULL DEFAULT 'General',
                valor REAL NOT NULL CHECK (valor >= 0),
                fecha TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS costos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                tipo TEXT NOT NULL DEFAULT 'General',
                valor REAL NOT NULL CHECK (valor >= 0),
                fecha TEXT NOT NULL
            )
        """)


# --------------------------------------------------
# VALIDACIÓN
# --------------------------------------------------

def validar(datos, tipo):
    campo_tipo = "categoria" if tipo == "gastos" else "tipo"

    descripcion = str(datos.get("descripcion", "")).strip()
    clasificacion = str(
        datos.get(campo_tipo, "General")
    ).strip() or "General"
    fecha = str(datos.get("fecha", "")).strip()

    try:
        valor = float(datos.get("valor", 0))
    except (TypeError, ValueError, OverflowError):
        return None, "El valor debe ser numérico."

    if not descripcion:
        return None, "La descripción es obligatoria."

    if not fecha:
        return None, "La fecha es obligatoria."

    if valor < 0:
        return None, "El valor no puede ser negativo."

    return {
        "descripcion": descripcion,
        campo_tipo: clasificacion,
        "valor": valor,
        "fecha": fecha
    }, None


# --------------------------------------------------
# RUTAS DE GASTOS Y COSTOS
# --------------------------------------------------

def crear_rutas(tipo):
    campo_tipo = "categoria" if tipo == "gastos" else "tipo"

    def listar():
        desde = request.args.get("desde", "").strip()
        hasta = request.args.get("hasta", "").strip()

        consulta = (
            f"SELECT id, descripcion, {campo_tipo}, valor, fecha "
            f"FROM {tipo}"
        )

        condiciones = []
        parametros = []

        if desde:
            condiciones.append("fecha >= ?")
            parametros.append(desde)

        if hasta:
            condiciones.append("fecha <= ?")
            parametros.append(hasta)

        if condiciones:
            consulta += " WHERE " + " AND ".join(condiciones)

        consulta += " ORDER BY fecha DESC, id DESC"

        with conectar() as db:
            filas = db.execute(consulta, parametros).fetchall()

        return jsonify([dict(fila) for fila in filas])

    def crear():
        datos, error = validar(
            request.get_json(silent=True) or {},
            tipo
        )

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

            registro_id = cursor.lastrowid

            fila = db.execute(
                f"""SELECT id, descripcion, {campo_tipo}, valor, fecha
                    FROM {tipo} WHERE id = ?""",
                (registro_id,)
            ).fetchone()

        return jsonify(dict(fila)), 201

    def actualizar(registro_id):
        datos, error = validar(
            request.get_json(silent=True) or {},
            tipo
        )

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
                return jsonify({
                    "error": "Registro no encontrado."
                }), 404

            fila = db.execute(
                f"""SELECT id, descripcion, {campo_tipo}, valor, fecha
                    FROM {tipo} WHERE id = ?""",
                (registro_id,)
            ).fetchone()

        return jsonify(dict(fila))

    def eliminar(registro_id):
        with conectar() as db:
            cursor = db.execute(
                f"DELETE FROM {tipo} WHERE id = ?",
                (registro_id,)
            )

            if cursor.rowcount == 0:
                return jsonify({
                    "error": "Registro no encontrado."
                }), 404

        return jsonify({
            "mensaje": "Registro eliminado correctamente."
        })

    # Cada operación exige una sesión válida.
    app.add_url_rule(
        f"/api/{tipo}",
        endpoint=f"listar_{tipo}",
        view_func=requiere_sesion(listar),
        methods=["GET"]
    )

    app.add_url_rule(
        f"/api/{tipo}",
        endpoint=f"crear_{tipo}",
        view_func=requiere_sesion(crear),
        methods=["POST"]
    )

    app.add_url_rule(
        f"/api/{tipo}/<int:registro_id>",
        endpoint=f"actualizar_{tipo}",
        view_func=requiere_sesion(actualizar),
        methods=["PUT"]
    )

    app.add_url_rule(
        f"/api/{tipo}/<int:registro_id>",
        endpoint=f"eliminar_{tipo}",
        view_func=requiere_sesion(eliminar),
        methods=["DELETE"]
    )


crear_rutas("gastos")
crear_rutas("costos")


# --------------------------------------------------
# ESTADÍSTICAS
# --------------------------------------------------

@app.get("/api/estadisticas")
@requiere_sesion
def obtener_estadisticas():
    resultado = {}

    with conectar() as db:
        for tabla in ("gastos", "costos"):
            fila = db.execute(f"""
                SELECT COUNT(*) AS cantidad,
                       COALESCE(SUM(valor), 0) AS total,
                       COALESCE(AVG(valor), 0) AS promedio
                FROM {tabla}
            """).fetchone()

            resultado[tabla] = {
                "cantidad": fila["cantidad"],
                "total": round(float(fila["total"]), 2),
                "promedio": round(float(fila["promedio"]), 2)
            }

        filas = db.execute("""
            SELECT categoria, SUM(valor) AS total
            FROM gastos
            GROUP BY categoria
            ORDER BY total DESC
        """).fetchall()

        resultado["gastos_por_categoria"] = [
            {
                "categoria": fila["categoria"] or "Sin categoría",
                "total": round(float(fila["total"]), 2)
            }
            for fila in filas
        ]

    return jsonify(resultado)


# --------------------------------------------------
# PÁGINAS DEL FRONTEND
# --------------------------------------------------

@app.get("/")
def inicio():
    if not session.get("usuario_id"):
        return redirect("http://127.0.0.1:5001/login")

    return send_from_directory(FRONTEND, "Gastos.html")


@app.get("/<path:nombre_archivo>")
def archivos_frontend(nombre_archivo):
    if nombre_archivo in {
        "Gastos.html",
        "Gastos.css",
        "Gastos.js",
        "gastos.html",
        "gastos.css",
        "gastos.js"
    }:
        return send_from_directory(FRONTEND, nombre_archivo)

    return jsonify({"error": "Archivo no encontrado."}), 404


# --------------------------------------------------
# INICIAR SERVIDOR
# --------------------------------------------------

if __name__ == "__main__":
    inicializar_bd()
    app.run(port=5000, debug=True)