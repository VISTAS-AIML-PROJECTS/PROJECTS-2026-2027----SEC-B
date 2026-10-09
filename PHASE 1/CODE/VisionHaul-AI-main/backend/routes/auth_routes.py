import random
import jwt
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify
from backend.config import Config
from backend.database.db import SessionLocal
from backend.database.models import User

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Create / Register a new Officer Profile (Admin or Manager).
    """
    data = request.json or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    role = data.get('role', 'Manager').strip().capitalize() # 'Admin' or 'Manager'
    department = data.get('department', '').strip()
    phone = data.get('phone', '').strip()

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required.'}), 400

    if role not in ['Admin', 'Manager']:
        role = 'Manager'

    db = SessionLocal()
    try:
        # Check if email is already registered
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({'error': 'This email address is already registered to an officer profile.'}), 400

        # Generate custom badge ID
        prefix = 'SEC-CMD' if role == 'Admin' else 'LOG-MGR'
        badge_id = data.get('badge_id', '').strip() or f"{prefix}-{random.randint(10, 99)}"
        
        # Set Clearance level
        clearance = 'Level 5 (Full Command & Calibration)' if role == 'Admin' else 'Level 3 (Surveillance & Logistics)'
        
        if not department:
            department = 'National Heavy Transport Security Command' if role == 'Admin' else 'Port & Highway Logistics Operations'

        new_user = User(
            name=name,
            email=email,
            password=password,
            role=role,
            badge_id=badge_id,
            department=department,
            clearance=clearance,
            phone=phone,
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_user)
        db.commit()

        # Generate JWT Token
        token_payload = {
            'user_id': new_user.id,
            'email': new_user.email,
            'role': new_user.role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=12)
        }
        token = jwt.encode(token_payload, Config.SECRET_KEY, algorithm='HS256')

        return jsonify({
            'success': True,
            'message': f'{role} profile created successfully',
            'token': token,
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Failed to create profile: {str(e)}'}), 500
    finally:
        db.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Role-based authentication endpoint for Admin and Manager.
    """
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or user.password != password:
            return jsonify({'error': 'Invalid security credentials or unrecognized email address.'}), 401

        token_payload = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=12)
        }
        token = jwt.encode(token_payload, Config.SECRET_KEY, algorithm='HS256')

        return jsonify({
            'success': True,
            'token': token,
            'user': user.to_dict()
        })
    finally:
        db.close()


@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """
    Verify officer JWT token.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing authorization token'}), 401

    token = auth_header.split(' ')[1]
    db = SessionLocal()
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        user = db.query(User).filter(User.id == payload.get('user_id')).first()
        if not user:
            return jsonify({'error': 'Officer profile not found'}), 404
        return jsonify({'valid': True, 'user': user.to_dict()})
    except Exception:
        return jsonify({'error': 'Expired or invalid token'}), 401
    finally:
        db.close()
