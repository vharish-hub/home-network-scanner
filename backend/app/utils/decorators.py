import json
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models import User, AuditLog
from app.extensions import db


def admin_required(fn):
    """Decorator that restricts access to admin users only.

    Verifies the JWT token, looks up the user, and checks that their
    role is 'admin'. Returns 403 Forbidden if the user is not an admin.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)

        if user is None:
            return jsonify({'message': 'User not found', 'error': 'user_not_found'}), 404

        if not user.is_active:
            return jsonify({'message': 'Account is deactivated', 'error': 'account_inactive'}), 403

        if user.role != 'admin':
            return jsonify({'message': 'Admin privileges required', 'error': 'forbidden'}), 403

        return fn(*args, **kwargs)

    return wrapper


def log_action(action_name):
    """Decorator that creates an AuditLog entry after the route executes.

    Logs the action name, user ID, request IP address, and response details.

    Args:
        action_name: A string describing the action (e.g., 'user_login', 'scan_started').
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            response = fn(*args, **kwargs)

            try:
                verify_jwt_in_request(optional=True)
                current_user_id = get_jwt_identity()
            except Exception:
                current_user_id = None

            if current_user_id is not None:
                # Extract details from the response for logging
                details_data = {
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'url': request.url,
                }

                # If there are request arguments or JSON body, include relevant info
                if request.args:
                    details_data['query_params'] = dict(request.args)

                if request.is_json and request.get_json(silent=True):
                    body = request.get_json(silent=True)
                    # Exclude sensitive fields from logging
                    safe_body = {k: v for k, v in body.items()
                                 if k not in ('password', 'current_password', 'new_password',
                                              'password_hash', 'token')}
                    if safe_body:
                        details_data['request_body'] = safe_body

                # Determine the status code from the response
                if isinstance(response, tuple):
                    status_code = response[1] if len(response) > 1 else 200
                else:
                    status_code = getattr(response, 'status_code', 200)

                details_data['status_code'] = status_code

                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                if ip_address and ',' in ip_address:
                    ip_address = ip_address.split(',')[0].strip()

                audit_entry = AuditLog(
                    user_id=current_user_id,
                    action=action_name,
                    details=json.dumps(details_data),
                    ip_address=ip_address,
                )
                db.session.add(audit_entry)
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()

            return response

        return wrapper
    return decorator
