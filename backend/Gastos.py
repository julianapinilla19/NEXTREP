from pathlib import Path
import sqlite3
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend" / "gastos"
DB_PATH = BASE_DIR / "database" / "nextrep_gastos.db"


def conectar_bd():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar_bd():
    with conectar_bd() as conexion:
        for tabla in ("gastos", "costos"):
            conexion.execute(f"""
                CREATE TABLE IF NOT EXISTS {tabla} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descripcion TEXT NOT NULL,
                    categoria TEXT NOT NULL DEFAULT 'General',
                    monto REAL NOT NULL CHECK (monto >= 0),
                    fecha TEXT NOT NULL
                )
            """)


def validar_registro(datos):
    descripcion = str(datos.get("descripcion", "")).strip()
    categoria = str(datos.get("categoria", "General")).strip() or "General"
    fecha = str(datos.get("fecha", "")).strip()
    try:
        monto = float(datos.get("monto", 0))
    except (TypeError, ValueError):
        raise ValueError("El monto debe ser numérico.")
    if not descripcion:
        raise ValueError("La descripción es obligatoria.")
    if not fecha:
        raise ValueError("La fecha es obligatoria.")
    if monto < 0:
        raise ValueError("El monto no puede ser negativo.")
    return descripcion, categoria, monto, fecha


def registrar_rutas(tabla):
    # El nombre de tabla proviene únicamente de las llamadas internas al final del archivo.
    endpoint = tabla

    def listar():
        fecha_inicio = request.args.get("desde", "").strip()
        fecha_fin = request.args.get("hasta", "").strip()
        consulta = f"SELECT id, descripcion, categoria, monto, fecha FROM {tabla}"
        condiciones, parametros = [], []
        if fecha_inicio:
            condiciones.append("fecha >= ?")
            parametros.append(fecha_inicio)
        if fecha_fin:
            condiciones.append("fecha <= ?")
            parametros.append(fecha_fin)
        if condiciones:
            consulta += " WHERE " + " AND ".join(condiciones)
        consulta += " ORDER BY fecha DESC, id DESC"
        with conectar_bd() as conexion:
            filas = conexion.execute(consulta, parametros).fetchall()
        return jsonify([dict(fila) for fila in filas])

    def crear():
        try:
            descripcion, categoria, monto, fecha = validar_registro(request.get_json(silent=True) or {})
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        with conectar_bd() as conexion:
            cursor = conexion.execute(
                f"INSERT INTO {tabla} (descripcion, categoria, monto, fecha) VALUES (?, ?, ?, ?)",
                (descripcion, categoria, monto, fecha),
            )
            registro_id = cursor.lastrowid
            fila = conexion.execute(
                f"SELECT id, descripcion, categoria, monto, fecha FROM {tabla} WHERE id = ?",
                (registro_id,),
            ).fetchone()
        return jsonify(dict(fila)), 201

    def editar(registro_id):
        try:
            descripcion, categoria, monto, fecha = validar_registro(request.get_json(silent=True) or {})
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        with conectar_bd() as conexion:
            cursor = conexion.execute(
                f"UPDATE {tabla} SET descripcion = ?, categoria = ?, monto = ?, fecha = ? WHERE id = ?",
                (descripcion, categoria, monto, fecha, registro_id),
            )
            if cursor.rowcount == 0:
                return jsonify({"error": "Registro no encontrado."}), 404
            fila = conexion.execute(
                f"SELECT id, descripcion, categoria, monto, fecha FROM {tabla} WHERE id = ?",
                (registro_id,),
            ).fetchone()
        return jsonify(dict(fila))

    def eliminar(registro_id):
        with conectar_bd() as conexion:
            cursor = conexion.execute(f"DELETE FROM {tabla} WHERE id = ?", (registro_id,))
            if cursor.rowcount == 0:
                return jsonify({"error": "Registro no encontrado."}), 404
        return jsonify({"mensaje": "Registro eliminado correctamente."})

    app.add_url_rule(f"/api/{tabla}", endpoint=f"listar_{endpoint}", view_func=listar, methods=["GET"])
    app.add_url_rule(f"/api/{tabla}", endpoint=f"crear_{endpoint}", view_func=crear, methods=["POST"])
    app.add_url_rule(f"/api/{tabla}/<int:registro_id>", endpoint=f"editar_{endpoint}", view_func=editar, methods=["PUT"])
    app.add_url_rule(f"/api/{tabla}/<int:registro_id>", endpoint=f"eliminar_{endpoint}", view_func=eliminar, methods=["DELETE"])


registrar_rutas("gastos")
registrar_rutas("costos")


@app.get("/api/estadisticas")
def obtener_estadisticas():
    resultado = {}
    with conectar_bd() as conexion:
        for tabla in ("gastos", "costos"):
            fila = conexion.execute(f"""
                SELECT COUNT(*) AS cantidad,
                       COALESCE(SUM(monto), 0) AS total,
                       COALESCE(AVG(monto), 0) AS promedio
                FROM {tabla}
            """).fetchone()
            resultado[tabla] = {
                "cantidad": fila["cantidad"],
                "total": round(float(fila["total"]), 2),
                "promedio": round(float(fila["promedio"]), 2),
            }
        filas = conexion.execute("""
            SELECT categoria, SUM(monto) AS total
            FROM gastos
            GROUP BY categoria
            ORDER BY total DESC
        """).fetchall()
        resultado["gastos_por_categoria"] = [
            {"categoria": fila["categoria"] or "Sin categoría", "total": round(float(fila["total"]), 2)}
            for fila in filas
        ]
    return jsonify(resultado)


@app.get("/")
def inicio():
    return send_from_directory(FRONTEND_DIR, "gastos.html")


@app.get("/<path:nombre_archivo>")
def archivos_frontend(nombre_archivo):
    if nombre_archivo in {"gastos.html", "gastos.css", "gastos.js"}:
        return send_from_directory(FRONTEND_DIR, nombre_archivo)
    return jsonify({"error": "Archivo no encontrado."}), 404


if __name__ == "__main__":
    inicializar_bd()
    app.run(debug=True)

