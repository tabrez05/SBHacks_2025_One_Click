from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user = User(username=data['username'], email=data['email'])
    return jsonify({'message': 'User created successfully'})

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    return jsonify({'message': 'Login successful'})
