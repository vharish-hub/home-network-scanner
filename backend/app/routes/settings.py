from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User, ScanConfig
from app.utils.decorators import log_action
from app.utils.helpers import validate_ip_range, validate_email

settings_bp = Blueprint('settings', __name__)


# ──────────────────────────────────────────────────────────────
# Scan Configuration Endpoints
# ──────────────────────────────────────────────────────────────

@settings_bp.route('/scan-configs', methods=['GET'])
@jwt_required()
def list_scan_configs():
    """List all saved scan configurations for the current user.

    Returns:
        200: List of scan configuration objects.
    """
    current_user_id = get_jwt_identity()

    configs = (
        ScanConfig.query
        .filter_by(user_id=current_user_id)
        .order_by(ScanConfig.created_at.desc())
        .all()
    )

    return jsonify({
        'message': 'Scan configurations retrieved',
        'data': [c.to_dict() for c in configs],
    }), 200


@settings_bp.route('/scan-configs', methods=['POST'])
@jwt_required()
@log_action('scan_config_created')
def create_scan_config():
    """Create a new scan configuration.

    Expects JSON body:
        - name (str, required): Configuration name.
        - target_range (str, required): IP range in CIDR notation.
        - scan_type (str, optional): 'quick', 'full', or 'custom'. Defaults to 'quick'.
        - ports (str, optional): Custom port specification (e.g., '22,80,443' or '1-1024').
        - is_scheduled (bool, optional): Whether to schedule recurring scans. Defaults to False.
        - schedule_cron (str, optional): Cron expression for scheduling.
        - email_notify (bool, optional): Whether to send email notifications. Defaults to False.

    Returns:
        201: Scan configuration created.
        400: Validation error.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'message': 'Request body is required', 'error': 'bad_request'}), 400

    name = data.get('name', '').strip()
    target_range = data.get('target_range', '').strip()
    scan_type = data.get('scan_type', 'quick').strip().lower()

    # Validate required fields
    errors = []
    if not name:
        errors.append('Name is required')
    elif len(name) > 100:
        errors.append('Name must be 100 characters or less')

    if not target_range:
        errors.append('Target range is required')
    elif not validate_ip_range(target_range):
        errors.append('Invalid target range format')

    valid_scan_types = ('quick', 'full', 'custom')
    if scan_type not in valid_scan_types:
        errors.append(f'Scan type must be one of: {", ".join(valid_scan_types)}')

    if errors:
        return jsonify({'message': 'Validation failed', 'errors': errors}), 400

    # Check for duplicate name
    existing = ScanConfig.query.filter_by(user_id=current_user_id, name=name).first()
    if existing:
        return jsonify({
            'message': 'A configuration with this name already exists',
            'error': 'conflict',
        }), 409

    config = ScanConfig(
        user_id=current_user_id,
        name=name,
        target_range=target_range,
        scan_type=scan_type,
        ports=data.get('ports', '').strip() or None,
        is_scheduled=data.get('is_scheduled', False),
        schedule_cron=data.get('schedule_cron', '').strip() or None,
        email_notify=data.get('email_notify', False),
    )

    db.session.add(config)
    db.session.commit()

    return jsonify({
        'message': 'Scan configuration created',
        'data': config.to_dict(),
    }), 201


@settings_bp.route('/scan-configs/<int:config_id>', methods=['PUT'])
@jwt_required()
@log_action('scan_config_updated')
def update_scan_config(config_id):
    """Update an existing scan configuration.

    Args:
        config_id: The ID of the configuration to update.

    Expects JSON body with any of the configuration fields.

    Returns:
        200: Configuration updated.
        400: Validation error.
        404: Configuration not found.
    """
    current_user_id = get_jwt_identity()

    config = ScanConfig.query.filter_by(id=config_id, user_id=current_user_id).first()
    if config is None:
        return jsonify({'message': 'Scan configuration not found', 'error': 'not_found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'message': 'Request body is required', 'error': 'bad_request'}), 400

    errors = []

    # Update name
    if 'name' in data:
        name = data['name'].strip()
        if not name:
            errors.append('Name cannot be empty')
        elif len(name) > 100:
            errors.append('Name must be 100 characters or less')
        else:
            # Check for duplicate name (excluding current config)
            existing = ScanConfig.query.filter(
                ScanConfig.user_id == current_user_id,
                ScanConfig.name == name,
                ScanConfig.id != config_id,
            ).first()
            if existing:
                errors.append('A configuration with this name already exists')
            else:
                config.name = name

    # Update target range
    if 'target_range' in data:
        target_range = data['target_range'].strip()
        if not target_range:
            errors.append('Target range cannot be empty')
        elif not validate_ip_range(target_range):
            errors.append('Invalid target range format')
        else:
            config.target_range = target_range

    # Update scan type
    if 'scan_type' in data:
        scan_type = data['scan_type'].strip().lower()
        valid_scan_types = ('quick', 'full', 'custom')
        if scan_type not in valid_scan_types:
            errors.append(f'Scan type must be one of: {", ".join(valid_scan_types)}')
        else:
            config.scan_type = scan_type

    if errors:
        return jsonify({'message': 'Validation failed', 'errors': errors}), 400

    # Update optional fields
    if 'ports' in data:
        config.ports = data['ports'].strip() if data['ports'] else None

    if 'is_scheduled' in data:
        config.is_scheduled = bool(data['is_scheduled'])

    if 'schedule_cron' in data:
        config.schedule_cron = data['schedule_cron'].strip() if data['schedule_cron'] else None

    if 'email_notify' in data:
        config.email_notify = bool(data['email_notify'])

    db.session.commit()

    return jsonify({
        'message': 'Scan configuration updated',
        'data': config.to_dict(),
    }), 200


@settings_bp.route('/scan-configs/<int:config_id>', methods=['DELETE'])
@jwt_required()
@log_action('scan_config_deleted')
def delete_scan_config(config_id):
    """Delete a scan configuration.

    Args:
        config_id: The ID of the configuration to delete.

    Returns:
        200: Configuration deleted.
        404: Configuration not found.
    """
    current_user_id = get_jwt_identity()

    config = ScanConfig.query.filter_by(id=config_id, user_id=current_user_id).first()
    if config is None:
        return jsonify({'message': 'Scan configuration not found', 'error': 'not_found'}), 404

    db.session.delete(config)
    db.session.commit()

    return jsonify({
        'message': 'Scan configuration deleted',
        'data': None,
    }), 200


# ──────────────────────────────────────────────────────────────
# User Profile Endpoints
# ──────────────────────────────────────────────────────────────

@settings_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get the current user's profile.

    Returns:
        200: User profile data.
        404: User not found.
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)

    if user is None:
        return jsonify({'message': 'User not found', 'error': 'not_found'}), 404

    return jsonify({
        'message': 'Profile retrieved',
        'data': user.to_dict(),
    }), 200


@settings_bp.route('/profile', methods=['PUT'])
@jwt_required()
@log_action('profile_updated')
def update_profile():
    """Update the current user's profile (username, email).

    Expects JSON body with any of:
        - username (str): New username (3-80 characters).
        - email (str): New email address.

    Returns:
        200: Profile updated.
        400: Validation error.
        409: Username or email already taken.
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)

    if user is None:
        return jsonify({'message': 'User not found', 'error': 'not_found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'message': 'Request body is required', 'error': 'bad_request'}), 400

    errors = []

    if 'username' in data:
        username = data['username'].strip()
        if not username:
            errors.append('Username cannot be empty')
        elif len(username) < 3 or len(username) > 80:
            errors.append('Username must be between 3 and 80 characters')
        else:
            existing = User.query.filter(
                User.username == username,
                User.id != current_user_id,
            ).first()
            if existing:
                return jsonify({
                    'message': 'Username already taken',
                    'error': 'conflict',
                }), 409
            user.username = username

    if 'email' in data:
        email = data['email'].strip()
        if not email:
            errors.append('Email cannot be empty')
        elif not validate_email(email):
            errors.append('Invalid email format')
        else:
            existing = User.query.filter(
                User.email == email,
                User.id != current_user_id,
            ).first()
            if existing:
                return jsonify({
                    'message': 'Email already registered',
                    'error': 'conflict',
                }), 409
            user.email = email

    if errors:
        return jsonify({'message': 'Validation failed', 'errors': errors}), 400

    db.session.commit()

    return jsonify({
        'message': 'Profile updated successfully',
        'data': user.to_dict(),
    }), 200


@settings_bp.route('/password', methods=['PUT'])
@jwt_required()
@log_action('password_changed')
def change_password():
    """Change the current user's password.

    Expects JSON body:
        - current_password (str, required): The user's current password.
        - new_password (str, required): The new password (minimum 6 characters).

    Returns:
        200: Password changed successfully.
        400: Validation error or incorrect current password.
    """
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)

    if user is None:
        return jsonify({'message': 'User not found', 'error': 'not_found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'message': 'Request body is required', 'error': 'bad_request'}), 400

    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')

    if not current_password:
        return jsonify({
            'message': 'Current password is required',
            'error': 'validation_error',
        }), 400

    if not new_password:
        return jsonify({
            'message': 'New password is required',
            'error': 'validation_error',
        }), 400

    if len(new_password) < 6:
        return jsonify({
            'message': 'New password must be at least 6 characters',
            'error': 'validation_error',
        }), 400

    if not user.check_password(current_password):
        return jsonify({
            'message': 'Current password is incorrect',
            'error': 'invalid_password',
        }), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({
        'message': 'Password changed successfully',
        'data': None,
    }), 200
