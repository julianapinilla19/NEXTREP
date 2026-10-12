from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def inicio():
    return jsonify({
        "mensaje": "Backend de gastos de NEXTREP funcionando"
    })


@app.route("/gastos", methods=["POST"])
def registrar_gasto():

    datos = request.get_json()

    descripcion = datos.get("descripcion")
    categoria = datos.get("categoria")
    valor = datos.get("valor")
    fecha = datos.get("fecha")

    if not descripcion or not categoria or not valor or not fecha:
        return jsonify({
            "error": "Todos los campos son obligatorios"
        }), 400

    gasto = {
        "descripcion": descripcion,
        "categoria": categoria,
        "valor": valor,
        "fecha": fecha
    }

    return jsonify({
        "mensaje": "Gasto recibido correctamente",
        "gasto": gasto
    }), 201


@app.route("/costos", methods=["POST"])
def registrar_costo():

    datos = request.get_json()

    descripcion = datos.get("descripcion")
    tipo = datos.get("tipo")
    valor = datos.get("valor")
    fecha = datos.get("fecha")

    if not descripcion or not tipo or not valor or not fecha:
        return jsonify({
            "error": "Todos los campos son obligatorios"
        }), 400

    costo = {
        "descripcion": descripcion,
        "tipo": tipo,
        "valor": valor,
        "fecha": fecha
    }

    return jsonify({
        "mensaje": "Costo recibido correctamente",
        "costo": costo
    }), 201


if __name__ == "__main__":
    app.run(debug=True)
