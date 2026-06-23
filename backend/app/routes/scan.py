import threading
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Scan, Device, Vulnerability
from app.utils.decorators import log_action
from app.utils.helpers import validate_ip_range, paginate_query, format_duration

scan_bp = Blueprint('scan', __name__)


def _run_scan_in_background(app, scan_id, target_range, scan_type):
    """Execute a network scan in a background thread.

    This function runs within its own application context and delegates to
    the scanner service's full_scan pipeline.

    Args:
        app: The Flask application instance (needed for app context).
        scan_id: The ID of the Scan record to update.
        target_range: The IP range to scan.
        scan_type: The type of scan ('quick', 'full', 'custom').
    """
    from app.services.scanner import NetworkScanner
    scanner = NetworkScanner()
    scanner.full_scan(target_range, scan_type, scan_id, app)


@scan_bp.route('/start', methods=['POST'])
@jwt_required()
@log_action('scan_started')
def start_scan():
    """Start a new network scan.

    Expects JSON body:
        - target_range (str, optional): IP range in CIDR notation. Defaults to app config.
        - scan_type (str, optional): 'quick', 'full', or 'custom'. Defaults to 'quick'.

    Returns:
        201: Scan created and started.
        400: Invalid target range or scan type.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}

    target_range = data.get('target_range', current_app.config.get('DEFAULT_SCAN_RANGE', '192.168.1.0/24')).strip()
    scan_type = data.get('scan_type', 'quick').strip().lower()

    # Validate target range
    if not validate_ip_range(target_range):
        return jsonify({
            'message': 'Invalid target range. Use CIDR notation (e.g., 192.168.1.0/24)',
            'error': 'validation_error',
        }), 400

    # Validate scan type
    valid_scan_types = ('quick', 'full', 'custom')
    if scan_type not in valid_scan_types:
        return jsonify({
            'message': f'Invalid scan type. Must be one of: {", ".join(valid_scan_types)}',
            'error': 'validation_error',
        }), 400

    # Check for already running scans for this user
    running_scan = Scan.query.filter_by(
        user_id=current_user_id,
        status='running'
    ).first()

    if running_scan:
        return jsonify({
            'message': 'A scan is already running. Please wait for it to complete.',
            'error': 'scan_in_progress',
            'data': running_scan.to_dict(),
        }), 409

    # Create scan record
    scan = Scan(
        user_id=current_user_id,
        scan_type=scan_type,
        target_range=target_range,
        status='pending',
    )
    db.session.add(scan)
    db.session.commit()

    # Launch scan in background thread
    app = current_app._get_current_object()
    scan_thread = threading.Thread(
        target=_run_scan_in_background,
        args=(app, scan.id, target_range, scan_type),
        daemon=True,
    )
    scan_thread.start()

    return jsonify({
        'message': f'{scan_type.capitalize()} scan started on {target_range}',
        'data': scan.to_dict(),
    }), 201


@scan_bp.route('/', methods=['GET'])
@jwt_required()
def list_scans():
    """List all scans for the current user, ordered by date descending.

    Query Parameters:
        - page (int, optional): Page number. Defaults to 1.
        - per_page (int, optional): Items per page. Defaults to 20.
        - status (str, optional): Filter by scan status.
        - scan_type (str, optional): Filter by scan type.

    Returns:
        200: Paginated list of scans.
    """
    current_user_id = get_jwt_identity()

    query = Scan.query.filter_by(user_id=current_user_id)

    # Apply optional filters
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    scan_type = request.args.get('scan_type')
    if scan_type:
        query = query.filter_by(scan_type=scan_type)

    query = query.order_by(Scan.scan_date.desc())

    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 20)
    result = paginate_query(query, page, per_page)

    return jsonify({
        'message': 'Scans retrieved',
        'data': result,
    }), 200


@scan_bp.route('/<int:scan_id>', methods=['GET'])
@jwt_required()
def get_scan(scan_id):
    """Get detailed information about a specific scan.

    Includes all discovered devices and their vulnerabilities.

    Args:
        scan_id: The ID of the scan to retrieve.

    Returns:
        200: Scan details with devices and vulnerabilities.
        404: Scan not found.
    """
    current_user_id = get_jwt_identity()
    scan = Scan.query.filter_by(id=scan_id, user_id=current_user_id).first()

    if scan is None:
        return jsonify({'message': 'Scan not found', 'error': 'not_found'}), 404

    scan_data = scan.to_dict()
    scan_data['devices'] = []

    for device in scan.devices:
        device_data = device.to_dict()
        device_data['vulnerabilities'] = [v.to_dict() for v in device.vulnerabilities]
        scan_data['devices'].append(device_data)

    scan_data['duration_formatted'] = format_duration(scan.duration)

    return jsonify({
        'message': 'Scan details retrieved',
        'data': scan_data,
    }), 200


@scan_bp.route('/<int:scan_id>/status', methods=['GET'])
@jwt_required()
def get_scan_status(scan_id):
    """Get the current status of a scan (for polling during active scans).

    Args:
        scan_id: The ID of the scan to check.

    Returns:
        200: Current scan status and progress.
        404: Scan not found.
    """
    current_user_id = get_jwt_identity()
    scan = Scan.query.filter_by(id=scan_id, user_id=current_user_id).first()

    if scan is None:
        return jsonify({'message': 'Scan not found', 'error': 'not_found'}), 404

    status_data = {
        'id': scan.id,
        'status': scan.status,
        'scan_type': scan.scan_type,
        'target_range': scan.target_range,
        'total_hosts': scan.total_hosts,
        'total_vulns': scan.total_vulns,
        'risk_score': scan.risk_score,
        'duration': scan.duration,
        'duration_formatted': format_duration(scan.duration),
        'error_message': scan.error_message,
        'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
    }

    return jsonify({
        'message': 'Scan status retrieved',
        'data': status_data,
    }), 200


@scan_bp.route('/<int:scan_id>', methods=['DELETE'])
@jwt_required()
@log_action('scan_deleted')
def delete_scan(scan_id):
    """Delete a scan and all associated data (devices, vulnerabilities).

    Args:
        scan_id: The ID of the scan to delete.

    Returns:
        200: Scan deleted successfully.
        404: Scan not found.
        409: Cannot delete a running scan.
    """
    current_user_id = get_jwt_identity()
    scan = Scan.query.filter_by(id=scan_id, user_id=current_user_id).first()

    if scan is None:
        return jsonify({'message': 'Scan not found', 'error': 'not_found'}), 404

    if scan.status == 'running':
        return jsonify({
            'message': 'Cannot delete a running scan. Wait for it to complete or cancel it first.',
            'error': 'scan_in_progress',
        }), 409

    db.session.delete(scan)
    db.session.commit()

    return jsonify({
        'message': 'Scan deleted successfully',
        'data': None,
    }), 200
