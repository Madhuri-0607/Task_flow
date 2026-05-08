from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
import re
import logging
from backend.models import db, User

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}

    # Validate required fields
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not email:
        return jsonify({"error": "Email is required"}), 400
    if not password:
        return jsonify({"error": "Password is required"}), 400

    # Validate field lengths
    if len(name) > 120:
        return jsonify({"error": "Name must be less than 120 characters"}), 400
    
    # Validate email format
    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    # Validate password length
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if len(password) > 255:
        return jsonify({"error": "Password must be less than 255 characters"}), 400

    # Check duplicate email
    if User.query.filter_by(email=email).first():
        logger.warning(f"Signup attempt with existing email: {email}")
        return jsonify({"error": "Email already registered"}), 409

    # Create new user (always as member)
    hashed_pw = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    user = User(name=name, email=email, password=hashed_pw, role="member")
    
    try:
        db.session.add(user)
        db.session.commit()
        logger.info(f"New user registered: {email} (ID: {user.id})")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error for {email}: {str(e)}")
        return jsonify({"error": "Registration failed. Please try again"}), 500

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "email": user.email}
    )

    return jsonify({
        "message": "Account created successfully",
        "token": token,
        "user": user.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        logger.warning(f"Failed login attempt for email: {email}")
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "email": user.email}
    )

    logger.info(f"User logged in: {email} (ID: {user.id})")
    
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.to_dict(),
    }), 200
