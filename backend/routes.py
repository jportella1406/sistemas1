# backend/routes.py
from flask import Blueprint, jsonify, request
from models import db, Producto, Pedido, ProductoPedido

routes = Blueprint('routes', __name__)

# Endpoint para obtener todos los productos
@routes.route('/productos', methods=['GET'])
def get_productos():
    productos = Producto.query.all()
    return jsonify([{
        'id': producto.id,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio': producto.precio,
        'imagen': producto.imagen
    } for producto in productos])

# Endpoint para crear un pedido
@routes.route('/pedidos', methods=['POST'])
def crear_pedido():
    data = request.get_json()
    total = data.get('total')
    productos_data = data.get('productos')  # Lista de productos con sus cantidades

    pedido = Pedido(total=total)
    db.session.add(pedido)
    db.session.flush()  # Guarda el pedido para obtener su ID

    for item in productos_data:
        producto_pedido = ProductoPedido(
            pedido_id=pedido.id,
            producto_id=item['producto_id'],
            cantidad=item['cantidad']
        )
        db.session.add(producto_pedido)

    db.session.commit()
    return jsonify({"message": "Pedido creado con éxito", "pedido_id": pedido.id}), 201

#Endpoint para filtrar productos por categoría
@routes.route('/productos/categoria/<string:categoria>', methods=['GET'])
def get_productos_por_categoria(categoria):
    productos = Producto.query.filter_by(categoria=categoria).all()
    return jsonify([{
        'id': producto.id,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio': producto.precio,
        'imagen': producto.imagen,
        'categoria': producto.categoria
    } for producto in productos])

#Endpoint para obtener todas las categorías
@routes.route('/productos/categorias', methods=['GET'])
def get_categorias():
    categorias = db.session.query(Producto.categoria).distinct().all()
    return jsonify([categoria[0] for categoria in categorias])