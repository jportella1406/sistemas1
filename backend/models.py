from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(100), nullable=True)  # URL de la imagen
    categoria = db.Column(db.String(50), nullable=False)  # Columna de categoría

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(50), default="pendiente")
    productos = db.relationship('ProductoPedido', backref='pedido', lazy=True)

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
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)  # Cambiar "username" si corresponde a "usuario"
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50), nullable=False)

    def __init__(self, username, password, rol, nombre=None, email=None):
        self.username = username
        self.password = password
        self.rol = rol
        self.nombre = nombre
        self.email = email

