"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""

from flask import Flask, request, jsonify, url_for, Blueprint
from api.models import db, User
from api.utils import generate_sitemap, APIException
from flask_cors import CORS

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)

api = Blueprint('api', __name__)

# Allow CORS requests to this API
CORS(api)


# =========================================================
# HELLO
# =========================================================

@api.route('/hello', methods=['GET'])
def handle_hello():

    response_body = {
        "message": "Hello! I'm a message that came from the backend"
    }

    return jsonify(response_body), 200


# =========================================================
# REGISTER
# =========================================================

@api.route('/register', methods=['GET', 'POST'])
def register():

    # SHOW INFO IN BROWSER
    if request.method == "GET":
        return jsonify({
            "endpoint": "/api/register",
            "method": "POST",
            "body": {
                "email": "test@test.com",
                "password": "123456"
            }
        }), 200

    # REGISTER LOGIC
    body = request.get_json() or {}

    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return jsonify({
            "msg": "Email and password are required"
        }), 400

    user = User.query.filter_by(email=email).first()

    if user:
        return jsonify({
            "msg": "User already exists"
        }), 400

    new_user = User(
        email=email,
        password=generate_password_hash(password),
        is_active=True
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "msg": "User registered successfully",
        "user": new_user.serialize()
    }), 201


# =========================================================
# LOGIN
# =========================================================

@api.route('/login', methods=['GET', 'POST'])
def login():

    # SHOW INFO IN BROWSER
    if request.method == "GET":
        return jsonify({
            "endpoint": "/api/login",
            "method": "POST",
            "body": {
                "email": "test@test.com",
                "password": "123456"
            }
        }), 200

    # LOGIN LOGIC
    body = request.get_json() or {}

    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return jsonify({
            "msg": "Email and password are required"
        }), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            "msg": "Invalid email or password"
        }), 401

    if not check_password_hash(user.password, password):
        return jsonify({
            "msg": "Invalid email or password"
        }), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "token": access_token,
        "user": user.serialize()
    }), 200


# =========================================================
# PRIVATE
# =========================================================

@api.route('/private', methods=['GET'])
@jwt_required()
def private():

    user_id = get_jwt_identity()

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "msg": "User not found"
        }), 404

    return jsonify({
        "msg": "Private route accessed",
        "user": user.serialize()
    }), 200