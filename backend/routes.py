# backend/routes.py
from flask import Blueprint, jsonify, request
from models import db, Producto, Pedido, ProductoPedido, User, Usuario

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

@routes.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    rol = data.get('rol', 'comprador')  # Asigna rol por defecto si no se especifica (puede ser 'comprador', 'vendedor', etc.)

    # Verifica si el usuario ya existe
    if Usuario.query.filter_by(username=username).first():
        return jsonify({'message': 'El usuario ya existe'}), 400

    # Crea un nuevo usuario y guarda el hash de la contraseña
    new_user = Usuario(username=username, rol=rol)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Usuario registrado exitosamente'}), 201

@routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Busca el usuario por nombre de usuario
    user = Usuario.query.filter_by(username=username).first()

    # Verifica si el usuario existe y la contraseña es correcta
    if user and user.check_password(password):
        return jsonify({'message': 'Inicio de sesión exitoso'}), 200
    else:
        return jsonify({'message': 'Usuario o contraseña incorrectos'}), 401