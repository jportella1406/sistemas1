# backend/routes.py
from flask import Flask, Blueprint, jsonify, request, session, current_app as app
from models import db, Producto, Pedido, ProductoPedido, Usuarios
routes = Blueprint('routes', __name__)
import os
import datetime
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mercadito.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db.init_app(app)

# Registrar el Blueprint
app.register_blueprint(routes)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

def format_producto(producto):
    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio': producto.precio,
        'imagen': producto.imagen,
        'categoria': producto.categoria.nombre
    }

@routes.route('/productos', methods=['GET'])
def get_productos():
    productos = Producto.query.all()
    return jsonify([format_producto(producto) for producto in productos])

@routes.route('/pedidos', methods=['POST'])
def crear_pedido():

    data = request.get_json()
    productos = data.get('productos', [])

    nuevo_pedido = Pedido(fecha=datetime.datetime.utcnow(), total=0, estado='Pendiente')
    db.session.add(nuevo_pedido)
    db.session.flush()

    total = 0
    for item in productos:
        producto_id = item['producto_id']
        cantidad = item['cantidad']
        producto = Producto.query.get(producto_id)
        
        if producto:
            total += producto.precio * cantidad
            producto_pedido = ProductoPedido(pedido_id=nuevo_pedido.id, producto_id=producto.id, cantidad=cantidad)
            db.session.add(producto_pedido)

    nuevo_pedido.total = total
    db.session.commit()

    return jsonify({'message': 'Pedido creado exitosamente', 'pedido_id': nuevo_pedido.id}), 201

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

    print(f"Username recibido: {username}, Password recibido: {password}")  # Mensaje de depuración

    # Verificar usuario en la tabla Usuarios
    user = Usuarios.query.filter_by(username=username).first()

    if user:
        print(f"Usuario encontrado: {user.username}, Password esperado: {user.password}")  # Debug
    else:
        print("Usuario no encontrado")

    if user and user.password == password:
        # Almacenar los datos del usuario en la sesión
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        print("Inicio de sesión exitoso")  # Mensaje de depuración
        return jsonify({'message': 'Inicio de sesión exitoso'}), 200
    else:
        print("Usuario o contraseña incorrectos")  # Mensaje de depuración
        return jsonify({'message': 'Usuario o contraseña incorrectos'}), 401
