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

### --- RUTAS API --- ###

@routes.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()  # Obtener datos enviados como JSON
    username = data.get('username')
    password = data.get('password')

    # Verificar si el usuario existe
    user = Usuarios.query.filter_by(username=username).first()

    if user and user.password == password:
        # Iniciar sesión (sin sesión para API, solo devolver datos)
        return jsonify({
            'message': 'Inicio de sesión exitoso',
            'user_id': user.user_id,
            'username': user.username,
            'role': user.rol
        }), 200
    else:
        return jsonify({'message': 'Usuario o contraseña incorrectos'}), 401

@routes.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    nombre = data.get('nombre')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    rol = data.get('rol', 'usuario')  # Rol por defecto

    if not all([nombre, username, email, password]):
        return jsonify({'message': 'Faltan campos obligatorios'}), 400

    existing_user = Usuarios.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'El nombre de usuario ya está en uso'}), 400

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


# Obtener todos los productos
@routes.route('/api/productos', methods=['GET'])
def get_productos():
    productos = Producto.query.all()
    return jsonify([{
        'id': producto.id,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio': producto.precio,
        'imagen': producto.imagen,
        'categoria': producto.categoria
    } for producto in productos])

# Crear un nuevo producto
@routes.route('/api/productos', methods=['POST'])
def create_producto():
    data = request.get_json()
    nuevo_producto = Producto(
        nombre=data['nombre'],
        descripcion=data['descripcion'],
        precio=data['precio'],
        imagen=data['imagen'],
        categoria=data['categoria']
    )
    db.session.add(nuevo_producto)
    db.session.commit()
    return jsonify({'message': 'Producto creado exitosamente'}), 201

# Actualizar un producto existente
@routes.route('/api/productos/<int:producto_id>', methods=['PUT'])
def update_producto(producto_id):
    data = request.get_json()
    producto = Producto.query.get(producto_id)

    if not producto:
        return jsonify({'message': 'Producto no encontrado'}), 404

    producto.nombre = data.get('nombre', producto.nombre)
    producto.descripcion = data.get('descripcion', producto.descripcion)
    producto.precio = data.get('precio', producto.precio)
    producto.imagen = data.get('imagen', producto.imagen)
    producto.categoria = data.get('categoria', producto.categoria)

    db.session.commit()
    return jsonify({'message': 'Producto actualizado exitosamente'}), 200

# Eliminar un producto
@routes.route('/api/productos/<int:producto_id>', methods=['DELETE'])
def delete_producto(producto_id):
    producto = Producto.query.get(producto_id)

    if not producto:
        return jsonify({'message': 'Producto no encontrado'}), 404

    db.session.delete(producto)
    db.session.commit()
    return jsonify({'message': 'Producto eliminado exitosamente'}), 200

# Actualizar un usuario
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

# Eliminar un usuario
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = Usuarios.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('dashboard_usuarios'))  # Esto está correcto
    return "Usuario no encontrado", 404


# Agregar un producto al carrito

@routes.route('/api/carrito', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    if not product_id or not quantity:
        return jsonify({'message': 'Faltan datos'}), 400

    # Aquí puedes guardar el producto en una tabla de carrito (en sesión o base de datos)
    carrito_item = Carrito(product_id=product_id, quantity=quantity)
    db.session.add(carrito_item)
    db.session.commit()

    return jsonify({'message': 'Producto agregado al carrito'}), 201




### --- RUTAS HTML --- ###

@app.route('/')
def index():
    productos = Producto.query.all()  # Obtiene todos los productos de la base de datos
    return render_template('index.html', productos=productos)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Verificar usuario y contraseña
        user = Usuarios.query.filter_by(username=username).first()

        if user and user.password == password:
            # Configurar sesión para el usuario
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['role'] = user.rol
            return redirect(url_for('dashboard_usuarios'))
        else:
            return "Usuario o contraseña incorrectos", 401

    return render_template('login.html')

@app.route('/dashboard/usuarios')
def dashboard_usuarios():
    usuarios = Usuarios.query.all()
    return render_template('dash-usuarios.html', usuarios=usuarios)

@app.route('/dashboard/productos')
def dashboard_productos():
    productos = Producto.query.all()
    return render_template('dash-productos.html', productos=productos)

@app.route('/dashboard')
def dashboard():
    return redirect(url_for('dashboard_usuarios'))

@app.route('/registrar')
def registrar():
    return redirect(url_for('registrar.html'))

### --- Registrar el Blueprint después de definir todas las rutas --- ###
app.register_blueprint(routes)

# Iniciar la aplicación Flask
if __name__ == '__main__':
    app.run(debug=True)
