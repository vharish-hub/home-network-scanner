from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.models import User, AuditLog
from app.utils.decorators import log_action
from app.utils.helpers import validate_email

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account.

    Expects JSON body:
        - username (str, required): 3-80 characters
        - email (str, required): Valid email format
        - password (str, required): Minimum 6 characters

    Returns:
        201: User created successfully with access and refresh tokens.
        400: Validation error or missing fields.
        409: Username or email already exists.
    """
    data = request.get_json()

    if not data:
        return jsonify({'message': 'Request body is required', 'error': 'bad_request'}), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    # Validate required fields
    errors = []
    if not username:
        errors.append('Username is required')
    elif len(username) < 3 or len(username) > 80:
        errors.append('Username must be between 3 and 80 characters')

    if not email:
        errors.append('Email is required')
    elif not validate_email(email):
        errors.append('Invalid email format')

    if not password:
        errors.append('Password is required')
    elif len(password) < 6:
        errors.append('Password must be at least 6 characters')

    if errors:
        return jsonify({'message': 'Validation failed', 'errors': errors}), 400

    # Check uniqueness
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists', 'error': 'conflict'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered', 'error': 'conflict'}), 409

    # Create user
    user = User(
        username=username,
        email=email,
        role='user',
        is_active=True,
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    # Create audit log
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip_address and ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()

    audit_entry = AuditLog(
        user_id=user.id,
        action='user_registered',
        details=f'New user registered: {username}',
        ip_address=ip_address,
    )
    db.session.add(audit_entry)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully',
        'data': {
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate a user and issue JWT tokens.

    Expects JSON body:
        - username (str, required): Username or email
        - password (str, required): User's password

    Returns:
        200: Login successful with user data and tokens.
        400: Missing credentials.
        401: Invalid credentials or inactive account.
    """
    data = request.get_json()

    if not data:
        return jsonify({'message': 'Request body is required', 'error': 'bad_request'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'message': 'Username and password are required', 'error': 'bad_request'}), 400

    # Look up by username or email
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()

    if user is None or not user.check_password(password):
        return jsonify({'message': 'Invalid username or password', 'error': 'unauthorized'}), 401

    if not user.is_active:
        return jsonify({'message': 'Account is deactivated. Contact an administrator.',
                        'error': 'account_inactive'}), 401

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    # Create audit log
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip_address and ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()

    audit_entry = AuditLog(
        user_id=user.id,
        action='user_login',
        details=f'User {user.username} logged in',
        ip_address=ip_address,
    )
    db.session.add(audit_entry)
    db.session.commit()

    return jsonify({
        'message': 'Login successful',
        'data': {
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
        }
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Log out the current user.

    Creates an audit log entry for the logout event.
    Note: JWT tokens are stateless—client must discard the token.

    Returns:
        200: Logout successful.
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)

    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip_address and ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()

    username = user.username if user else f'user_id:{current_user_id}'
    audit_entry = AuditLog(
        user_id=current_user_id,
        action='user_logout',
        details=f'User {username} logged out',
        ip_address=ip_address,
    )
    db.session.add(audit_entry)
    db.session.commit()

    return jsonify({
        'message': 'Logged out successfully',
        'data': None,
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Issue a new access token using a valid refresh token.

    Returns:
        200: New access token issued.
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)

    if user is None:
        return jsonify({'message': 'User not found', 'error': 'user_not_found'}), 404

    if not user.is_active:
        return jsonify({'message': 'Account is deactivated', 'error': 'account_inactive'}), 401

    access_token = create_access_token(identity=current_user_id)

    return jsonify({
        'message': 'Token refreshed successfully',
        'data': {
            'access_token': access_token,
        }
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Return the current authenticated user's profile.

    Returns:
        200: User profile data.
        404: User not found.
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)

    if user is None:
        return jsonify({'message': 'User not found', 'error': 'user_not_found'}), 404

    return jsonify({
        'message': 'User profile retrieved',
        'data': user.to_dict(),
    }), 200
