
from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory,
    send_file,
    session
)
import sqlite3
import os
import re
from pathlib import Path
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
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

# Rutas del proyecto
RAIZ = Path(__file__).resolve().parents[2]
FRONTEND = RAIZ / "frontend" / "ventas"
PANEL = RAIZ / "frontend" / "index.html"
BASE_DATOS = RAIZ / "database" / "nextrep_gastos.db"


# --------------------------------------------------
# CONEXIÓN Y BASE DE DATOS
# --------------------------------------------------

def conectar():
    BASE_DATOS.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(BASE_DATOS, timeout=10)
    return db


def crear_tabla():
    with conectar() as db:

        # Tabla de ventas
        db.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                precio REAL NOT NULL,
                total REAL NOT NULL,
                fecha TEXT
            )
        """)

        columnas_ventas = [
            columna[1]
            for columna in db.execute(
                "PRAGMA table_info(ventas)"
            ).fetchall()
        ]

        if "fecha" not in columnas_ventas:
            db.execute(
                "ALTER TABLE ventas ADD COLUMN fecha TEXT"
            )

        # Tabla de usuarios
        db.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL UNIQUE,
                contrasena TEXT NOT NULL,
                fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def obtener_columnas(tabla):
    tablas_permitidas = (
        "ventas",
        "gastos",
        "costos",
        "cobros"
    )

    if tabla not in tablas_permitidas:
        return []

    with conectar() as db:
        existe = db.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
        """, (tabla,)).fetchone()

        if not existe:
            return []

        return [
            columna[1]
            for columna in db.execute(
                f"PRAGMA table_info({tabla})"
            ).fetchall()
        ]


def consultar_total(
    tabla,
    columna_valor="valor",
    condicion=None
):
    """
    Consulta la suma de una columna numérica.
    Si la tabla o columna no existe, devuelve cero.
    """

    tablas_permitidas = ("gastos", "costos", "cobros")

    if tabla not in tablas_permitidas:
        return 0

    columnas = obtener_columnas(tabla)

    if columna_valor not in columnas:
        return 0

    consulta = (
        f"SELECT COALESCE(SUM({columna_valor}), 0) "
        f"FROM {tabla}"
    )

    parametros = []

    if condicion:
        columna_condicion, operador, valor = condicion

        if columna_condicion not in columnas:
            return 0

        if operador not in ("=", "!=", ">", "<", ">=", "<="):
            return 0

        consulta += f" WHERE {columna_condicion} {operador} ?"
        parametros.append(valor)

    with conectar() as db:
        resultado = db.execute(
            consulta,
            parametros
        ).fetchone()

    return resultado[0] or 0


# --------------------------------------------------
# PÁGINAS DEL FRONTEND
# --------------------------------------------------

LOGIN_FRONTEND = RAIZ / "frontend" / "login"
REGISTRO_FRONTEND = RAIZ / "frontend" / "registro"
PERFIL_FRONTEND = RAIZ / "frontend" / "perfil"


@app.route("/login")
def pagina_login():
    return send_from_directory(LOGIN_FRONTEND, "login.html")


@app.route("/registro")
def pagina_registro():
    return send_from_directory(REGISTRO_FRONTEND, "registro.html")


@app.route("/perfil")
def pagina_perfil():
    if not session.get("usuario_id"):
        return __import__("flask").redirect("/login")

    return send_from_directory(PERFIL_FRONTEND, "perfil.html")


@app.route("/panel")
def panel_principal():
    if not session.get("usuario_id"):
        return __import__("flask").redirect("/login")

    if not PANEL.exists():
        return jsonify({
            "error": "No se encontró frontend/index.html."
        }), 404

    return send_file(PANEL)


@app.route("/")
def inicio():
    return send_from_directory(FRONTEND, "ventas.html")


@app.route("/<path:archivo>")
def archivos_frontend(archivo):
    if archivo in ("ventas.css", "ventas.js"):
        return send_from_directory(FRONTEND, archivo)

    return jsonify({
        "error": "Archivo no encontrado."
    }), 404

@app.route("/login/<path:archivo>")
def archivos_login(archivo):
    if archivo in ("login.css", "login.js"):
        return send_from_directory(LOGIN_FRONTEND, archivo)

    return jsonify({
        "error": "Archivo no encontrado."
    }), 404
@app.route("/registro/<path:archivo>")
def archivos_registro(archivo):
    if archivo in ("registro.css", "registro.js"):
        return send_from_directory(REGISTRO_FRONTEND, archivo)

    return jsonify({"error": "Archivo no encontrado."
    }), 404
@app.route("/perfil/<path:archivo>")
def archivos_perfil(archivo):
    if archivo in ("perfil.css", "perfil.js"):
        return send_from_directory(PERFIL_FRONTEND, archivo)

    return jsonify({"error": "Archivo no encontrado."}), 404
# REGISTRO DE USUARIOS

@app.route("/api/registro", methods=["POST"])
def registrar_usuario():
    datos = request.get_json(silent=True) or {}

    nombre = str(datos.get("nombre", "")).strip()
    correo = str(datos.get("correo", "")).strip().lower()
    contrasena = str(datos.get("contrasena", ""))

    if not nombre or not correo or not contrasena:
        return jsonify({
            "error": "Todos los campos son obligatorios."
        }), 400

    if len(nombre) > 100:
        return jsonify({
            "error": "El nombre no puede superar 100 caracteres."
        }), 400

    if len(correo) > 254 or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        correo
    ):
        return jsonify({
            "error": "Ingresa un correo válido."
        }), 400

    if len(contrasena) < 8:
        return jsonify({
            "error": "La contraseña debe tener mínimo 8 caracteres."
        }), 400

    hash_contrasena = generate_password_hash(contrasena)

    try:
        with conectar() as db:
            cursor = db.execute("""
                INSERT INTO usuarios (
                    nombre,
                    correo,
                    contrasena
                )
                VALUES (?, ?, ?)
            """, (nombre, correo, hash_contrasena))

            usuario_id = cursor.lastrowid

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Este correo ya está registrado."
        }), 409

    return jsonify({
        "mensaje": "Usuario registrado correctamente.",
        "id": usuario_id
    }), 201


# --------------------------------------------------
# INICIAR SESIÓN
# --------------------------------------------------

@app.route("/api/login", methods=["POST"])
def iniciar_sesion():
    datos = request.get_json(silent=True) or {}

    correo = str(datos.get("correo", "")).strip().lower()
    contrasena = str(datos.get("contrasena", ""))

    if not correo or not contrasena:
        return jsonify({
            "error": "Ingresa tu correo y contraseña."
        }), 400

    with conectar() as db:
        usuario = db.execute("""
            SELECT id, nombre, correo, contrasena
            FROM usuarios
            WHERE correo = ?
        """, (correo,)).fetchone()

    if not usuario or not check_password_hash(
        usuario[3],
        contrasena
    ):
        return jsonify({
            "error": "Correo o contraseña incorrectos."
        }), 401

    session.clear()
    session["usuario_id"] = usuario[0]

    return jsonify({
        "mensaje": "Inicio de sesión correcto.",
        "usuario": {
            "id": usuario[0],
            "nombre": usuario[1],
            "correo": usuario[2]
        },
        "redireccion": "/panel"
    })


# --------------------------------------------------
# CONSULTAR PERFIL
# --------------------------------------------------

@app.route("/api/perfil", methods=["GET"])
def obtener_perfil():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return jsonify({
            "error": "Debes iniciar sesión."
        }), 401

    with conectar() as db:
        usuario = db.execute("""
            SELECT id, nombre, correo, fecha_registro
            FROM usuarios
            WHERE id = ?
        """, (usuario_id,)).fetchone()

    if not usuario:
        session.clear()

        return jsonify({
            "error": "Usuario no encontrado."
        }), 404

    return jsonify({
        "id": usuario[0],
        "nombre": usuario[1],
        "correo": usuario[2],
        "fecha_registro": usuario[3]
    })


# --------------------------------------------------
# CERRAR SESIÓN
# --------------------------------------------------

@app.route("/api/logout", methods=["POST"])
def cerrar_sesion():
    session.clear()

    return jsonify({
        "mensaje": "Sesión cerrada correctamente."
    })


# --------------------------------------------------
# REGISTRAR VENTAS
# --------------------------------------------------

@app.route("/api/ventas", methods=["POST"])
def registrar_venta():
    datos = request.get_json(silent=True) or {}

    producto = str(datos.get("producto", "")).strip()

    try:
        cantidad = int(datos.get("cantidad", 0))
        precio = float(datos.get("precio", 0))
    except (ValueError, TypeError):
        return jsonify({
            "error": "La cantidad y el precio deben ser números válidos."
        }), 400

    if not producto:
        return jsonify({
            "error": "Ingresa el nombre del producto."
        }), 400

    if cantidad <= 0 or precio <= 0:
        return jsonify({
            "error": "La cantidad y el precio deben ser mayores que cero."
        }), 400

    total = cantidad * precio

    with conectar() as db:
        cursor = db.execute("""
            INSERT INTO ventas (
                producto,
                cantidad,
                precio,
                total,
                fecha
            )
            VALUES (?, ?, ?, ?, date('now', 'localtime'))
        """, (producto, cantidad, precio, total))

        venta_id = cursor.lastrowid

    return jsonify({
        "mensaje": "Venta registrada correctamente.",
        "id": venta_id,
        "producto": producto,
        "cantidad": cantidad,
        "precio": precio,
        "total": total
    }), 201


# --------------------------------------------------
# CONSULTAR VENTAS
# --------------------------------------------------

@app.route("/api/ventas", methods=["GET"])
def listar_ventas():
    with conectar() as db:
        ventas = db.execute("""
            SELECT id, producto, cantidad, precio, total, fecha
            FROM ventas
            ORDER BY id DESC
        """).fetchall()

    return jsonify([
        {
            "id": fila[0],
            "producto": fila[1],
            "cantidad": fila[2],
            "precio": fila[3],
            "total": fila[4],
            "fecha": fila[5]
        }
        for fila in ventas
    ])


# --------------------------------------------------
# HISTORIAL Y FILTROS DE VENTAS
# --------------------------------------------------

@app.route("/api/ventas/historial", methods=["GET"])
def historial_ventas():
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    consulta = """
        SELECT id, producto, cantidad, precio, total, fecha
        FROM ventas
        WHERE 1 = 1
    """

    parametros = []

    if desde:
        consulta += " AND fecha >= ?"
        parametros.append(desde)

    if hasta:
        consulta += " AND fecha <= ?"
        parametros.append(hasta)

    consulta += " ORDER BY id DESC"

    with conectar() as db:
        ventas = db.execute(
            consulta,
            parametros
        ).fetchall()

    return jsonify([
        {
            "id": fila[0],
            "producto": fila[1],
            "cantidad": fila[2],
            "precio": fila[3],
            "total": fila[4],
            "fecha": fila[5]
        }
        for fila in ventas
    ])


# --------------------------------------------------
# TOTAL DE VENTAS
# --------------------------------------------------

@app.route("/api/ventas/total", methods=["GET"])
def total_ventas():
    with conectar() as db:
        resultado = db.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM ventas
        """).fetchone()[0]

    return jsonify({
        "total": resultado or 0
    })


# --------------------------------------------------
# EDITAR VENTAS
# --------------------------------------------------

@app.route("/api/ventas/<int:venta_id>", methods=["PUT"])
def editar_venta(venta_id):
    datos = request.get_json(silent=True) or {}

    producto = str(datos.get("producto", "")).strip()

    try:
        cantidad = int(datos.get("cantidad", 0))
        precio = float(datos.get("precio", 0))
    except (ValueError, TypeError):
        return jsonify({
            "error": "La cantidad y el precio deben ser números válidos."
        }), 400

    if not producto:
        return jsonify({
            "error": "Ingresa el nombre del producto."
        }), 400

    if cantidad <= 0 or precio <= 0:
        return jsonify({
            "error": "La cantidad y el precio deben ser mayores que cero."
        }), 400

    total = cantidad * precio

    with conectar() as db:
        existe = db.execute(
            "SELECT id FROM ventas WHERE id = ?",
            (venta_id,)
        ).fetchone()

        if not existe:
            return jsonify({
                "error": "La venta no existe."
            }), 404

        db.execute("""
            UPDATE ventas
            SET producto = ?,
                cantidad = ?,
                precio = ?,
                total = ?
            WHERE id = ?
        """, (producto, cantidad, precio, total, venta_id))

    return jsonify({
        "mensaje": "Venta actualizada correctamente.",
        "id": venta_id,
        "producto": producto,
        "cantidad": cantidad,
        "precio": precio,
        "total": total
    })


# --------------------------------------------------
# ELIMINAR VENTAS
# --------------------------------------------------

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


# --------------------------------------------------
# RESUMEN FINANCIERO
# --------------------------------------------------

@app.route("/api/resumen", methods=["GET"])
def resumen_financiero():
    with conectar() as db:
        total_ventas = db.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM ventas
        """).fetchone()[0] or 0

    # Solo sumar cobros pagados si existen las columnas.
    columnas_cobros = obtener_columnas("cobros")

    if (
        "estado" in columnas_cobros
        and "valor" in columnas_cobros
    ):
        total_cobros = consultar_total(
            "cobros",
            "valor",
            ("estado", "=", "Pagado")
        )
    else:
        total_cobros = 0

    total_gastos = consultar_total("gastos")
    total_costos = consultar_total("costos")

    balance = total_ventas - total_gastos - total_costos

    if total_ventas > 0:
        rentabilidad = (balance / total_ventas) * 100
    else:
        rentabilidad = 0

    return jsonify({
        "ventas": total_ventas,
        "cobros_pagados": total_cobros,
        "gastos": total_gastos,
        "costos": total_costos,
        "balance": balance,
        "rentabilidad": round(rentabilidad, 2)
    })


# --------------------------------------------------
# ANÁLISIS INTELIGENTE DEL NEGOCIO
# --------------------------------------------------

@app.route("/api/analisis-inteligente", methods=["GET"])
def analisis_inteligente():
    with conectar() as db:
        ventas = db.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM ventas
        """).fetchone()[0] or 0

    gastos = consultar_total("gastos")
    costos = consultar_total("costos")

    egresos = gastos + costos
    balance = ventas - egresos

    if ventas == 0 and egresos == 0:
        estado = "Sin datos"
        recomendacion = (
            "Registra tus primeras ventas, gastos y costos "
            "para obtener un análisis de tu negocio."
        )

    elif ventas == 0:
        estado = "Atención"
        recomendacion = (
            "Hay gastos o costos registrados, pero no hay ventas. "
            "Revisa los egresos y registra tus ingresos."
        )

    elif egresos > ventas:
        estado = "Riesgo"
        recomendacion = (
            "Tus gastos y costos superan las ventas. "
            "Revisa los egresos y busca formas de reducirlos."
        )

    elif (egresos / ventas) >= 0.70:
        estado = "Precaución"
        recomendacion = (
            "Los gastos y costos representan una parte alta "
            "de tus ventas. Revisa tus costos para mejorar "
            "la rentabilidad."
        )

    else:
        estado = "Favorable"
        recomendacion = (
            "Tu balance es positivo y los egresos están "
            "controlados respecto a las ventas registradas."
        )

    rentabilidad = (
        (balance / ventas) * 100
        if ventas > 0
        else 0
    )

    return jsonify({
        "ventas": ventas,
        "gastos": gastos,
        "costos": costos,
        "egresos": egresos,
        "balance": balance,
        "rentabilidad": round(rentabilidad, 2),
        "estado": estado,
        "recomendacion": recomendacion
    })


# --------------------------------------------------
# INICIAR SERVIDOR
# --------------------------------------------------

if __name__ == "__main__":
    crear_tabla()
    app.run(debug=True, port=5001)