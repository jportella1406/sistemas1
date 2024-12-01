from flask import Flask, Blueprint, jsonify, request, session, render_template, redirect, url_for
from models import db, Producto, Pedido, ProductoPedido, Usuarios
from prometheus_flask_exporter import PrometheusMetrics
##<<<<<<< HEAD
from cryptography.fernet import Fernet
import base64
##=======
##>>>>>>> main
import os
import bcrypt

# Crear la aplicación Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'mercadito.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
metrics = PrometheusMetrics(app)
db.init_app(app)

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
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = Usuarios.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({
                'message': 'Inicio de sesión exitoso',
                'user_id': user.user_id,
                'username': user.username,
                'role': user.rol
            }), 200
        else:
            return jsonify({'message': 'Usuario o contraseña incorrectos'}), 401
    except Exception as e:
        # Captura el error y devuelve un mensaje útil
        return jsonify({'message': 'Error interno en el servidor', 'error': str(e)}), 500


@routes.route('/api/register', methods=['POST'])
def api_register():
    try:
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

        if not all([nombre, username, email, password]):
            return jsonify({'message': 'Faltan campos obligatorios'}), 400

        existing_user = Usuarios.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'message': 'El nombre de usuario ya está en uso'}), 400

        # Hashear la contraseña antes de guardarla
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Crear un nuevo usuario
        new_user = Usuarios(
            nombre=nombre,
            username=username,
            email=email,
            password=hashed_password.decode('utf-8'),  # Almacenar como string
            rol=rol
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'Usuario registrado exitosamente'}), 201
    except Exception as e:
        return jsonify({'message': 'Error interno en el servidor', 'error': str(e)}), 500




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

# Función para cifrar datos
def encrypt_data(data: str) -> str:
    """Cifra un texto en formato base64."""
    encrypted_data = cipher_suite.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted_data).decode()

# Función para descifrar datos
def decrypt_data(encrypted_data: str) -> str:
    """Descifra un texto cifrado en formato base64."""
    try:
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        return cipher_suite.decrypt(decoded_data).decode()
    except Exception:
        return None

# Función para generar un ID único y aleatorio relacionado al producto
def generate_random_id(product_id: int) -> str:
    """Genera un ID aleatorio único basado en el ID del producto."""
    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return f"{product_id}-{random_suffix}"

# Ruta para generar un enlace seguro a un producto
@app.route('/generate_product_url/<int:product_id>')
def generate_product_url(product_id):
    # Generar un ID aleatorio relacionado al producto
    random_id = generate_random_id(product_id)
    encrypted_id = encrypt_data(random_id)  # Cifrar el ID aleatorio
    secure_url = f"http://127.0.0.1:5000/product/{encrypted_id}"
    return jsonify({'secure_url': secure_url})

# Ruta para ver el detalle del producto a través de una URL cifrada
@app.route('/product/<encrypted_id>')
def product_detail(encrypted_id):
    # Descifrar el ID aleatorio
    decrypted_data = decrypt_data(encrypted_id)
    if not decrypted_data:
        return jsonify({'message': 'Invalid or tampered URL'}), 400

    # Extraer el ID del producto desde el dato descifrado
    product_id = decrypted_data.split('-')[0]
    
    # Buscar el producto en la base de datos (esto es un ejemplo, ajusta a tu modelo)
    productos = {
        "1": {"id": 1, "name": "Cerveza Cusqueña", "price": 6.0, "description": "Botella de cerveza 350ml"},
        "2": {"id": 2, "name": "Arroz Costeño", "price": 8.0, "description": "Bolsa de arroz de 5kg"},
    }

    product = productos.get(product_id)
    if not product:
        return jsonify({'message': 'Producto no encontrado'}), 404

    return jsonify(product)

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

# Ruta para agregar un producto al carrito
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))
    
    # Buscar el producto por ID
    product = Producto.query.get(product_id)
    if not product:
        return jsonify({'message': 'Producto no encontrado'}), 404
    
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
    
    return jsonify({'message': 'Producto agregado al carrito', 'total_items': total_items}), 200


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
            session['role'] = user.rol
            return redirect(url_for('dashboard_usuarios'))
        else:
            return "Usuario o contraseña incorrectos", 401

    return render_template('login.html')





############################################################################
####################### --- RUTAS HTML --- #################################
############################################################################

@app.route('/')
def index():
    productos = Producto.query.all()
    return render_template('index.html', productos=productos)

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
    return render_template('registrar.html')

@app.route('/view-cart')
def view_cart():
    cart = session.get('cart', [])
    
    # Manejar el caso de un carrito vacío
    if not cart:
        return render_template('carrito.html', cart=[], subtotal=0, igv=0, total=0)
    
    # Cálculo del subtotal, IGV y total
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    igv = subtotal * 0.18  # Asumiendo IGV del 18%
    total = subtotal + igv

    # Depuración opcional para monitorear el carrito
    print(f"Carrito actual: {cart}")
    print(f"Subtotal: {subtotal}, IGV: {igv}, Total: {total}")

    return render_template('carrito.html', cart=cart, subtotal=subtotal, igv=igv, total=total)

@routes.route('/api/check-login', methods=['GET'])
def check_login():
    if 'user_id' in session:
        return jsonify({'logged_in': True}), 200
    else:
        return jsonify({'logged_in': False}), 200



### --- Registrar el Blueprint después de definir todas las rutas --- ###
app.register_blueprint(routes)

@app.route('/')
def home():
    return "¡El backend Flask está funcionando y exponiendo métricas!"

@app.route('/status')
def status():
    return {"status": "OK"}

if __name__ == "__main__":
    # Corre la aplicación en localhost:5000
    app.run(host="0.0.0.0", port=5000)