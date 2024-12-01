from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()

class Pedido(db.Model):
    __tablename__ = 'pedidos'

    pedidoId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.user_id'), nullable=False)
    direccion = db.Column(db.String(255), nullable=True)
    producto = db.Column(db.String(255), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='pendiente')

    usuario = db.relationship('Usuarios', backref=db.backref('pedidos', lazy=True))

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(100), nullable=True)  # URL de la imagen
    categoria = db.Column(db.String(50), nullable=False)  # Columna de categoría

class ProductoPedido(db.Model):  # Relación de muchos a muchos entre Pedido y Producto
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Usuarios(db.Model):
    __tablename__ = 'usuarios'
    
    user_id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(10), nullable=False, default='usuario')
    direccion = db.Column(db.String(255), nullable=True) 

    def __init__(self, fecha, user_id, direccion, producto, precio, estado='pendiente'):
        self.fecha = fecha
        self.user_id = user_id
        self.direccion = direccion
        self.producto = producto
        self.precio = precio
        self.estado = estado

