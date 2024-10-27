# app.py
from flask import Flask, request, session, redirect, url_for, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mercadito.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)  # Clave secreta para firmar las sesiones
db = SQLAlchemy(app)

# Definición del modelo de Usuario
class User(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)

# Ruta de registro
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'comprador')  # Rol por defecto

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'El usuario ya existe'}), 400

    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Usuario registrado exitosamente'}), 201

# Ruta de inicio de sesión
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return jsonify({'message': 'Usuario o contraseña incorrectos'}), 401

    # Almacenar los datos del usuario en la sesión
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    return jsonify({'message': 'Inicio de sesión exitoso'}), 200

# Ruta de cierre de sesión
@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return jsonify({'message': 'Sesión cerrada exitosamente'}), 200

# Ruta protegida para verificar si el usuario está logeado
@app.route('/protected', methods=['GET'])
def protected():
    if 'user_id' in session:
        return jsonify({'message': f'Bienvenido, {session["username"]}', 'role': session['role']}), 200
    else:
        return jsonify({'message': 'No autenticado'}), 401

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)

