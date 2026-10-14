from flask import Flask, request, jsonify

app = Flask(__name__)

# Lista temporal para guardar las ventas
ventas = []


@app.route("/ventas", methods=["POST"])
def registrar_venta():

    datos = request.json

    producto = datos["producto"]
    cantidad = datos["cantidad"]
    precio = datos["precio"]

    total = cantidad * precio

    venta = {
        "producto": producto,
        "cantidad": cantidad,
        "precio": precio,
        "total": total
    }

    ventas.append(venta)

    return jsonify({
        "mensaje": "Venta registrada correctamente",
        "venta": venta
    })


@app.route("/ventas", methods=["GET"])
def consultar_ventas():

    return jsonify(ventas)


if __name__ == "__main__":
    app.run(debug=True)
