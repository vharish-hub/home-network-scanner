import os
from flask import Flask, jsonify, request as flask_request
from flask_jwt_extended import get_jwt_identity
from app.config import config_by_name
from app.extensions import db, jwt, cors, migrate, bcrypt


def create_app(config_name=None):
    """Application factory for creating the Flask app."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Ensure instance and reports folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config.get('REPORTS_FOLDER', 'reports'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {
        "origins": "*",
        "allow_headers": ["Content-Type", "Authorization", "Accept", "X-Requested-With"],
        "expose_headers": ["Content-Type", "Authorization"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": False
    }})
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # JWT identity loader — ensure identity is always a string
    @jwt.user_identity_loader
    def user_identity_lookup(user_id):
        return str(user_id)

    # Import models so they are registered with SQLAlchemy
    from app.models import User, Scan, Device, Vulnerability, AuditLog, ScanConfig  # noqa: F401

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.scan import scan_bp
    from app.routes.devices import devices_bp
    from app.routes.vulnerabilities import vulnerabilities_bp
    from app.routes.reports import reports_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(scan_bp, url_prefix='/api/scans')
    app.register_blueprint(devices_bp, url_prefix='/api/devices')
    app.register_blueprint(vulnerabilities_bp, url_prefix='/api/vulnerabilities')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')

    # JWT error handlers — with detailed error messages for debugging
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        app.logger.warning(f'JWT expired for user: {jwt_payload.get("sub")}')
        return jsonify({'message': 'Token has expired', 'error': 'token_expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        app.logger.warning(f'Invalid JWT token: {error}')
        return jsonify({'message': f'Invalid token: {error}', 'error': 'invalid_token'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        app.logger.warning(f'Missing JWT token: {error}')
        return jsonify({'message': f'Authorization required: {error}', 'error': 'authorization_required'}), 401

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return False  # No blocklist implemented

    # Global error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'message': 'Bad request', 'error': str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'message': 'Resource not found', 'error': str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'message': 'Internal server error', 'error': str(error)}), 500

    # Health check endpoint
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'healthy', 'message': 'Network Scanner API is running'})

    # Debug endpoint — test JWT auth
    @app.route('/api/debug/auth-test')
    def debug_auth_test():
        """Test endpoint to check if Authorization header is received."""
        auth_header = flask_request.headers.get('Authorization', 'NOT PRESENT')
        has_bearer = auth_header.startswith('Bearer ') if auth_header != 'NOT PRESENT' else False
        token_preview = auth_header[7:27] + '...' if has_bearer and len(auth_header) > 27 else 'N/A'
        return jsonify({
            'auth_header_present': auth_header != 'NOT PRESENT',
            'has_bearer_prefix': has_bearer,
            'token_preview': token_preview,
            'all_headers': dict(flask_request.headers),
        })

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
