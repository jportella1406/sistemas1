# backend/routes.py
from flask import Blueprint, jsonify, request, session, current_app as app
from models import db, Producto, Pedido, ProductoPedido, Usuarios

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

# Endpoint para filtrar productos por categoría
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

# Endpoint para obtener todas las categorías
@routes.route('/productos/categorias', methods=['GET'])
def get_categorias():
    categorias = db.session.query(Producto.categoria).distinct().all()
    return jsonify([categoria[0] for categoria in categorias])

# Ruta de registro
@routes.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    rol = data.get('rol', 'comprador')  # Asigna rol por defecto si no se especifica

    # Verifica si el usuario ya existe
    if Usuarios.query.filter_by(username=username).first():
        return jsonify({'message': 'El usuario ya existe'}), 400

    # Crea un nuevo usuario y guarda la contraseña
    new_user = Usuarios(username=username, password=password, role=rol)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Usuario registrado exitosamente'}), 201

# Ruta de inicio de sesión
@routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Verificar usuario en la tabla Usuarios
    user = Usuarios.query.filter_by(username=username).first()

    if user:
        # Comparar contraseña recibida con la almacenada
        if user.password == password:
            # Almacenar los datos del usuario en la sesión
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return jsonify({'message': 'Inicio de sesión exitoso'}), 200
        else:
            return jsonify({'message': 'Usuario o contraseña incorrectos'}), 401
    else:
        return jsonify({'message': 'Usuario no encontrado'}), 404
