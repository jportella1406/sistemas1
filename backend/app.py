from flask import Flask, Blueprint, jsonify, request, session, render_template, redirect, url_for
from models import db, Producto, Pedido, ProductoPedido, Usuarios
import os

# Crear la aplicación Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'mercadito.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db.init_app(app)


# Blueprint para API (endpoints REST)
routes = Blueprint('routes', __name__)

### --- Definir todas las rutas del Blueprint antes de registrarlo --- ###

# Endpoint para obtener todos los productos
@routes.route('/api/productos', methods=['GET'])
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
@routes.route('/api/pedidos', methods=['POST'])
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
@routes.route('/api/productos/categoria/<string:categoria>', methods=['GET'])
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
@routes.route('/api/productos/categorias', methods=['GET'])
def get_categorias():
    categorias = db.session.query(Producto.categoria).distinct().all()
    return jsonify([categoria[0] for categoria in categorias])

# Ruta de registro
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json  # Asegúrate de recibir datos en formato JSON
    nombre = data.get('nombre')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    rol = data.get('rol', 'usuario')  # Valor por defecto: 'usuario'

    # Validar que no falten datos
    if not all([nombre, username, email, password]):
        return jsonify({'message': 'Faltan campos obligatorios'}), 400

    # Verificar si el usuario ya existe
    existing_user = Usuarios.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'El nombre de usuario ya está en uso'}), 400

    # Crear un nuevo usuario
    new_user = Usuarios(
        nombre=nombre,
        username=username,
        email=email,
        password=password,
        rol=rol
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Usuario registrado exitosamente'}), 201


# Dashboard para ver los usuarios desde admin

@app.route('/dashboard')
def dashboard():
    # Consulta a la base de datos para obtener todos los usuarios
    usuarios = Usuarios.query.all()
    return render_template('dashboard.html', usuarios=usuarios)



# Ruta de inicio de sesión
@routes.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Verificar usuario en la tabla Usuarios
    user = Usuarios.query.filter_by(username=username).first()

    if user and user.password == password:
        # Almacenar los datos del usuario en la sesión
        session['user_id'] = user.user_id
        session['username'] = user.username
        session['role'] = user.rol
        return jsonify({'message': 'Inicio de sesión exitoso'}), 200
    else:
        return jsonify({'message': 'Usuario o contraseña incorrectos'}), 401

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = Usuarios.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return redirect('/dashboard')
    return "Usuario no encontrado", 404


@app.route('/api/usuarios/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    usuario = Usuarios.query.get(user_id)

    if not usuario:
        return jsonify({'message': 'Usuario no encontrado'}), 404

    usuario.nombre = data.get('nombre', usuario.nombre)
    usuario.email = data.get('email', usuario.email)
    usuario.rol = data.get('rol', usuario.rol)

    db.session.commit()
    return jsonify({'message': 'Usuario actualizado con éxito'}), 200

### --- Rutas para Páginas HTML --- ###

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/carrito')
def carrito():
    return render_template('carrito.html')

@app.route('/registrar')
def registrar():
    return render_template('registrar.html')

@app.route('/productos')
def productos():
    return render_template('productos.html')

### --- Registrar el Blueprint después de definir todas las rutas --- ###
app.register_blueprint(routes)

# Iniciar la aplicación Flask
if __name__ == '__main__':
    app.run(debug=True)
