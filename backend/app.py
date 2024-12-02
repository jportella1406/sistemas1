from flask import Flask, Blueprint, jsonify, request, session, render_template, redirect, url_for, g
from models import db, Producto, Pedido, ProductoPedido, Usuarios
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from prometheus_flask_exporter import PrometheusMetrics
from cryptography.fernet import Fernet
import base64
import os
import bcrypt
import logging
from logging.handlers import RotatingFileHandler
from models import db


# Crear la aplicación Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'mercadito.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
metrics = PrometheusMetrics(app)
db.init_app(app)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

# Crear el directorio de logs si no existe
log_dir = os.path.join(os.getcwd(), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Nombre de archivo para el log, con fecha
log_filename = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y-%m-%d")}.log')

# Configurar el manejador de logs con rotación
handler = RotatingFileHandler(log_filename, maxBytes=1000000, backupCount=5)
handler.setLevel(logging.INFO)

# Configurar el formato de los logs
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Asegurarse de que el handler se añada al logger de la aplicación después de la inicialización
app.logger.addHandler(handler)

# Configurar el nivel del logger a INFO
app.logger.setLevel(logging.INFO)

# Registrar un mensaje informativo al iniciar la app
app.logger.info("Aplicación iniciada")

# Blueprint para API (endpoints REST)
routes = Blueprint('routes', __name__)

# Generar una clave secreta (haz esto una vez y guárdala en un lugar seguro)
SECRET_KEY = os.getenv('SECRET_KEY') or Fernet.generate_key()
cipher_suite = Fernet(SECRET_KEY)

############################################################################
######################## --- RUTAS API --- #################################
############################################################################

@routes.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = Usuarios.query.filter_by(username=username).first()

    if not user:
        db.session.remove()
        return jsonify({'message': 'Usuario o contraseña incorrectos'}), 401

    # Manejo de contraseñas antiguas (sin hash)
    if user.password == password:
        session['user_id'] = user.user_id
        session['username'] = user.username
        session['role'] = user.rol

        # Liberar la sesión, sin actualizar la contraseña
        db.session.remove()

        return jsonify({
            'message': 'Inicio de sesión exitoso',
            'user_id': user.user_id,
            'username': user.username,
            'role': user.rol
        }), 200

    # Manejo de contraseñas con hash bcrypt
    if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        session['user_id'] = user.user_id
        session['username'] = user.username
        session['role'] = user.rol

        # Liberar la sesión
        db.session.remove()

        return jsonify({
            'message': 'Inicio de sesión exitoso',
            'user_id': user.user_id,
            'username': user.username,
            'role': user.rol
        }), 200

    # Si ninguna coincide, devolver error
    db.session.remove()
    return jsonify({'message': 'Usuario o contraseña incorrectos'}), 401

@routes.route('/api/register', methods=['POST'])
def api_register():
    # Intentar obtener datos como JSON primero
    if request.is_json:
        data = request.json
    else:
        # Si no es JSON, obtenerlos desde form-urlencoded
        data = request.form.to_dict()

    nombre = data.get('nombre')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    rol = data.get('rol', 'usuario')  # Rol por defecto
    direccion = data.get('direccion')  # Campo adicional

    if not all([nombre, username, email, password, direccion]):
        return jsonify({'message': 'Faltan campos obligatorios'}), 400

    # Verificar si el nombre de usuario ya está en uso
    existing_user = Usuarios.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'El nombre de usuario ya está en uso'}), 400

    # Verificar si el email ya está en uso
    existing_email = Usuarios.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({'message': 'La dirección de correo ya está en uso'}), 400

    # Hashear la contraseña antes de guardarla
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Crear un nuevo usuario
    new_user = Usuarios(
        nombre=nombre,
        username=username,
        email=email,
        password=hashed_password.decode('utf-8'),  # Almacenar como string
        rol=rol,
        direccion=direccion
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

    # Update fields only if provided
    if 'nombre' in data:
        usuario.nombre = data['nombre']
    if 'email' in data:
        usuario.email = data['email']
    if 'rol' in data:
        usuario.rol = data['rol']
    if 'direccion' in data:
        usuario.direccion = data['direccion']  # Update only the address if provided

    # Save changes to the database
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


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    # Verificar si el usuario está autenticado
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Por favor, inicia sesión para poder realizar compras. Si aún no tienes una cuenta, ¡Regístrate gratis!'}), 401

    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))

    # Buscar el producto por ID
    product = Producto.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404

    # Obtener el carrito actual de la sesión
    cart = session.get('cart', [])

    # Verificar si el producto ya está en el carrito
    for item in cart:
        if item['id'] == product.id:
            item['quantity'] += quantity
            break
    else:
        # Agregar el producto al carrito
        cart.append({
            'id': product.id,
            'name': product.nombre,
            'price': product.precio,
            'quantity': quantity
        })

    # Guardar el carrito actualizado en la sesión
    session['cart'] = cart
    session.modified = True

    # Calcular el total de artículos en el carrito
    total_items = sum(item['quantity'] for item in cart)

    return jsonify({'success': True, 'message': 'Producto agregado al carrito', 'total_items': total_items}), 200



# Ruta para eliminar un producto del carrito
@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    product_id = data.get('productId')

    if not product_id:
        return jsonify({'success': False, 'error': 'Producto no especificado'}), 400

    # Obtener el carrito actual desde la sesión
    cart = session.get('cart', [])
    # Filtrar los productos para eliminar el especificado
    cart = [item for item in cart if item['id'] != product_id]
    session['cart'] = cart
    session.modified = True

    # Recalcular subtotal, IGV y total
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    igv = subtotal * 0.18
    total = subtotal + igv

    return jsonify({
        'success': True,
        'subtotal': subtotal,
        'igv': igv,
        'total': total
    })



@app.route('/update-cart', methods=['POST'])
def update_cart():
    try:
        data = request.get_json()  # Verifica que los datos lleguen correctamente
        print(data)  # Depuración: verifica los datos recibidos

        product_id = data.get('productId')
        new_quantity = data.get('newQuantity')

        if not product_id or not isinstance(new_quantity, int) or new_quantity <= 0:
            return jsonify({"success": False, "error": "Datos inválidos"}), 400

        # Obtener el carrito desde la sesión
        cart = session.get('cart', [])
        found = False

        # Actualizar la cantidad del producto en el carrito
        for item in cart:
            if item['id'] == product_id:
                item['quantity'] = new_quantity
                found = True
                break

        if not found:
            return jsonify({"success": False, "error": "Producto no encontrado en el carrito"}), 404

        # Guardar el carrito actualizado en la sesión
        session['cart'] = cart
        session.modified = True

        # Calcular subtotal, IGV y total
        subtotal = sum(item['price'] * item['quantity'] for item in cart)
        igv = subtotal * 0.18
        total = subtotal + igv

        return jsonify({
            "success": True,
            "subtotal": subtotal,
            "igv": igv,
            "total": total
        }), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "error": "Error del servidor"}), 500


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
            session['role'] = user.rol  # Guardar el rol en la sesión para usarlo en otras rutas

            # Depuración: Verificar si el rol se asigna correctamente
            print(f"Usuario logeado: {user.username}, Rol: {user.rol}")

            # Redirigir según el rol del usuario
            if session['role'] == 'admin':  # Cambia 'admin' al valor exacto de tu base de datos
                return redirect(url_for('dashboard_usuarios'))
            else:
                return redirect(url_for('index'))
        else:
            return "Usuario o contraseña incorrectos", 401

    return render_template('login.html')


@app.route('/logout')
def logout():
    # Limpia la sesión del usuario
    session.clear()
    return redirect(url_for('index'))


@app.route('/api/usuarios/<int:user_id>', methods=['GET'])
def get_user(user_id):
    usuario = Usuarios.query.get(user_id)

    if not usuario:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

    return jsonify({
        'success': True,
        'usuario': {
            'nombre': usuario.nombre,
            'username': usuario.username,
            'email': usuario.email,
            'direccion': usuario.direccion
        }
    }), 200



@app.route('/procesar-pago', methods=['POST'])
def procesar_pago():
    if 'cart' not in session or not session['cart']:
        return jsonify({'success': False, 'message': 'El carrito está vacío'}), 400

    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Debe iniciar sesión para realizar un pedido'}), 401

    # Obtener datos del usuario y del carrito
    user_id = session['user_id']
    usuario = db.session.get(Usuarios, user_id)  # Utiliza Session.get()
    if not usuario:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

    direccion = usuario.direccion  # Obtener la dirección del usuario
    cart = session['cart']

    # Crear un ID único para el pedido
    fecha_actual = datetime.now()

    try:
        # Insertar cada producto del carrito en la tabla pedidos
        for item in cart:
            nuevo_pedido = Pedido(
                fecha=fecha_actual,
                user_id=user_id,
                direccion=direccion,
                producto=item['name'],
                precio=item['price'] * item['quantity'],
                estado='pendiente'
            )
            db.session.add(nuevo_pedido)

        db.session.commit()
        session.pop('cart', None)  # Vaciar el carrito
        return jsonify({'success': True, 'message': 'Pedido procesado correctamente'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al procesar el pedido: {str(e)}'}), 500


@app.route('/pedido', methods=['GET'])
def gestion_pedidos():
    pedidos = Pedido.query.all()  # Consulta todos los pedidos en la base de datos

    # Verifica si se encontraron pedidos
    if not pedidos:
        return render_template('dash-pedido.html', message="No hay pedidos disponibles.")

    # Serializa los pedidos para pasarlos al template
    pedidos_data = [{
        'pedidoId': pedido.pedidoId,
        'fecha': pedido.fecha,
        'usuario': Usuarios.query.get(pedido.user_id).username,  # Obtener el nombre del usuario
        'direccion': pedido.direccion,
        'producto': pedido.producto,
        'precio': pedido.precio,
        'estado': pedido.estado
    } for pedido in pedidos]

    # Renderiza la plantilla con los datos de pedidos
    return render_template('dash-pedido.html', pedidos=pedidos_data)

############################################################################
####################### --- RUTAS HTML --- #################################
############################################################################

@app.route('/')
def index():
    print(f"Usuario logeado: {session.get('username')}, {session.get('role')}")
    productos = Producto.query.all()
    return render_template('index.html', productos=productos)

@app.route('/dashboard/usuarios')
def dashboard_usuarios():
    # Verifica si el usuario es administrador
    if session.get('role') != 'admin':
        return redirect(url_for('index'))  # Redirige a index si no es admin

    usuarios = Usuarios.query.all()  # Aquí obtendrás todos los usuarios
    return render_template('dash-usuarios.html', usuarios=usuarios)


@app.route('/dashboard/productos')
def dashboard_productos():
    # Verifica si el usuario está logueado y tiene rol de admin
    if session.get('role') != 'admin':
        return redirect(url_for('index'))  # Redirige al índice si no es admin
    
    # Carga los productos si el usuario es admin
    productos = Producto.query.all()
    return render_template('dash-productos.html', productos=productos)


@app.route('/dashboard')
def dashboard():
    # Verifica si el usuario es un administrador
    if session.get('role') != 'admin':
        return redirect(url_for('index'))  # Redirige a index si no es admin
    return render_template('dash-usuarios.html')  # Renderiza el dashboard


@app.route('/registrar')
def registrar():
    return render_template('registrar.html')

@app.route('/carritoDeCompras')
def view_cart():
    cart = session.get('cart', [])
    
    # Manejar el caso de un carrito vacío
    if not cart:
        return render_template('carrito.html', cart=[], subtotal=0, igv=0, total=0)
    
    # Cálculo del subtotal, IGV y total
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    igv = subtotal * 0.18  # Asumiendo IGV del 18%
    total = subtotal + igv

    return render_template('carrito.html', cart=cart, subtotal=subtotal, igv=igv, total=total)

@app.route('/payment')
def payment_page():
    # Verifica si el usuario tiene productos en el carrito
    cart = session.get('cart', [])
    if not cart:
        return redirect(url_for('view_cart'))  # Si no hay productos, redirige al carrito

    # Calcula el total del carrito
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    igv = subtotal * 0.18  # IGV del 18%
    total = subtotal + igv

    return render_template('pago.html', cart=cart, subtotal=subtotal, igv=igv, total=total)


@app.route('/api/pedidos/<int:pedido_id>', methods=['PUT'])
def actualizar_estado_pedido(pedido_id):
    data = request.get_json()
    nuevo_estado = data.get('estado')

    if not nuevo_estado:
        return jsonify({'message': 'Estado no proporcionado'}), 400

    pedido = Pedido.query.get(pedido_id)
    if not pedido:
        return jsonify({'message': 'Pedido no encontrado'}), 404

    pedido.estado = nuevo_estado
    db.session.commit()

    return jsonify({'message': 'Estado del pedido actualizado con éxito'}), 200



### --- Registrar el Blueprint después de definir todas las rutas --- ###
app.register_blueprint(routes)

# Iniciar la aplicación Flask
if __name__ == '__main__':
    app.run(debug=True)
