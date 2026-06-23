from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Device, Scan, Vulnerability
from app.utils.helpers import paginate_query

devices_bp = Blueprint('devices', __name__)


@devices_bp.route('/', methods=['GET'])
@jwt_required()
def list_devices():
    """List devices discovered across scans, with optional filtering.

    Query Parameters:
        - scan_id (int, optional): Filter by a specific scan.
        - device_type (str, optional): Filter by device type (e.g., 'router', 'laptop').
        - status (str, optional): Filter by device status ('up' or 'down').
        - page (int, optional): Page number. Defaults to 1.
        - per_page (int, optional): Items per page. Defaults to 20.

    Returns:
        200: Paginated list of devices with vulnerability counts.
    """
    current_user_id = get_jwt_identity()

    # Only show devices from the current user's scans
    user_scan_ids = db.session.query(Scan.id).filter_by(user_id=current_user_id).subquery()
    query = Device.query.filter(Device.scan_id.in_(user_scan_ids))

    # Apply optional filters
    scan_id = request.args.get('scan_id', type=int)
    if scan_id is not None:
        # Verify the scan belongs to the current user
        scan = Scan.query.filter_by(id=scan_id, user_id=current_user_id).first()
        if scan is None:
            return jsonify({'message': 'Scan not found', 'error': 'not_found'}), 404
        query = query.filter_by(scan_id=scan_id)

    device_type = request.args.get('device_type')
    if device_type:
        query = query.filter(Device.device_type.ilike(f'%{device_type}%'))

    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Device.ip_address)

    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 20)
    result = paginate_query(query, page, per_page)

    return jsonify({
        'message': 'Devices retrieved',
        'data': result,
    }), 200


@devices_bp.route('/<int:device_id>', methods=['GET'])
@jwt_required()
def get_device(device_id):
    """Get detailed information about a specific device.

    Includes all vulnerabilities found on the device.

    Args:
        device_id: The ID of the device to retrieve.

    Returns:
        200: Device details with vulnerabilities.
        404: Device not found or not owned by current user.
    """
    current_user_id = get_jwt_identity()

    device = Device.query.get(device_id)
    if device is None:
        return jsonify({'message': 'Device not found', 'error': 'not_found'}), 404

    # Verify the device belongs to a scan owned by the current user
    scan = Scan.query.filter_by(id=device.scan_id, user_id=current_user_id).first()
    if scan is None:
        return jsonify({'message': 'Device not found', 'error': 'not_found'}), 404

    device_data = device.to_dict()
    device_data['vulnerabilities'] = [v.to_dict() for v in device.vulnerabilities]
    device_data['scan_info'] = {
        'scan_id': scan.id,
        'scan_date': scan.scan_date.isoformat() if scan.scan_date else None,
        'scan_type': scan.scan_type,
    }

    return jsonify({
        'message': 'Device details retrieved',
        'data': device_data,
    }), 200
