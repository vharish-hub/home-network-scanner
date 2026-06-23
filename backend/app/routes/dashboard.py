from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app.extensions import db
from app.models import Scan, Device, Vulnerability

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def summary():
    """Return a high-level summary of the user's network security posture.

    Returns:
        200: Summary object with total_devices, total_vulnerabilities,
             critical_issues, risk_score, total_scans, and latest scan info.
    """
    current_user_id = get_jwt_identity()

    # Total scans for this user
    total_scans = Scan.query.filter_by(user_id=current_user_id).count()

    # Get user's scan IDs
    user_scan_ids = db.session.query(Scan.id).filter_by(user_id=current_user_id).subquery()

    # Total unique devices across all scans
    total_devices = Device.query.filter(Device.scan_id.in_(user_scan_ids)).count()

    # Total vulnerabilities across all scans
    total_vulnerabilities = Vulnerability.query.filter(
        Vulnerability.scan_id.in_(user_scan_ids)
    ).count()

    # Critical issues
    critical_issues = Vulnerability.query.filter(
        Vulnerability.scan_id.in_(user_scan_ids),
        Vulnerability.severity == 'critical',
    ).count()

    # Risk score from latest completed scan
    latest_scan = (
        Scan.query
        .filter_by(user_id=current_user_id, status='completed')
        .order_by(Scan.scan_date.desc())
        .first()
    )
    risk_score = latest_scan.risk_score if latest_scan else 0.0

    # High severity count
    high_issues = Vulnerability.query.filter(
        Vulnerability.scan_id.in_(user_scan_ids),
        Vulnerability.severity == 'high',
    ).count()

    summary_data = {
        'total_scans': total_scans,
        'total_devices': total_devices,
        'total_vulnerabilities': total_vulnerabilities,
        'critical_issues': critical_issues,
        'high_issues': high_issues,
        'risk_score': risk_score,
        'latest_scan': latest_scan.to_dict() if latest_scan else None,
    }

    return jsonify({
        'message': 'Dashboard summary retrieved',
        'data': summary_data,
    }), 200


@dashboard_bp.route('/recent-scans', methods=['GET'])
@jwt_required()
def recent_scans():
    """Return the 5 most recent scans with basic information.

    Returns:
        200: List of the 5 most recent scans.
    """
    current_user_id = get_jwt_identity()

    scans = (
        Scan.query
        .filter_by(user_id=current_user_id)
        .order_by(Scan.scan_date.desc())
        .limit(5)
        .all()
    )

    scans_data = [scan.to_dict() for scan in scans]

    return jsonify({
        'message': 'Recent scans retrieved',
        'data': scans_data,
    }), 200


@dashboard_bp.route('/severity-distribution', methods=['GET'])
@jwt_required()
def severity_distribution():
    """Return vulnerability severity counts formatted for a pie chart.

    Query Parameters:
        - scan_id (int, optional): Scope to a specific scan.

    Returns:
        200: List of severity objects with name, value, and color.
    """
    current_user_id = get_jwt_identity()

    user_scan_ids = db.session.query(Scan.id).filter_by(user_id=current_user_id).subquery()
    base_query = Vulnerability.query.filter(Vulnerability.scan_id.in_(user_scan_ids))

    scan_id = request.args.get('scan_id', type=int)
    if scan_id is not None:
        scan = Scan.query.filter_by(id=scan_id, user_id=current_user_id).first()
        if scan is None:
            return jsonify({'message': 'Scan not found', 'error': 'not_found'}), 404
        base_query = Vulnerability.query.filter_by(scan_id=scan_id)

    severity_config = [
        {'key': 'critical', 'name': 'Critical', 'color': '#ff3366'},
        {'key': 'high', 'name': 'High', 'color': '#ff6633'},
        {'key': 'medium', 'name': 'Medium', 'color': '#ffaa00'},
        {'key': 'low', 'name': 'Low', 'color': '#33cc99'},
        {'key': 'info', 'name': 'Info', 'color': '#3399ff'},
    ]

    distribution = []
    for sev in severity_config:
        count = base_query.filter_by(severity=sev['key']).count()
        distribution.append({
            'name': sev['name'],
            'value': count,
            'color': sev['color'],
        })

    return jsonify({
        'message': 'Severity distribution retrieved',
        'data': distribution,
    }), 200


@dashboard_bp.route('/device-vulns', methods=['GET'])
@jwt_required()
def device_vulnerabilities():
    """Return vulnerability counts per device for a bar chart.

    Query Parameters:
        - scan_id (int, optional): Scope to a specific scan. Defaults to latest completed scan.

    Returns:
        200: List of device objects with hostname and severity breakdown.
    """
    current_user_id = get_jwt_identity()

    scan_id = request.args.get('scan_id', type=int)

    if scan_id is not None:
        scan = Scan.query.filter_by(id=scan_id, user_id=current_user_id).first()
        if scan is None:
            return jsonify({'message': 'Scan not found', 'error': 'not_found'}), 404
    else:
        # Default to latest completed scan
        scan = (
            Scan.query
            .filter_by(user_id=current_user_id, status='completed')
            .order_by(Scan.scan_date.desc())
            .first()
        )
        if scan is None:
            return jsonify({
                'message': 'No completed scans found',
                'data': [],
            }), 200

    devices = Device.query.filter_by(scan_id=scan.id).all()

    device_vuln_data = []
    for device in devices:
        vulns = Vulnerability.query.filter_by(device_id=device.id, scan_id=scan.id).all()

        severity_breakdown = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for v in vulns:
            if v.severity in severity_breakdown:
                severity_breakdown[v.severity] += 1

        # Only include devices that have at least one vulnerability
        total = sum(severity_breakdown.values())
        if total > 0:
            device_vuln_data.append({
                'device': device.hostname or device.ip_address,
                'ip_address': device.ip_address,
                'critical': severity_breakdown['critical'],
                'high': severity_breakdown['high'],
                'medium': severity_breakdown['medium'],
                'low': severity_breakdown['low'],
                'info': severity_breakdown['info'],
                'total': total,
            })

    # Sort by total vulnerabilities descending
    device_vuln_data.sort(key=lambda x: x['total'], reverse=True)

    return jsonify({
        'message': 'Device vulnerability breakdown retrieved',
        'data': device_vuln_data,
    }), 200


@dashboard_bp.route('/port-analysis', methods=['GET'])
@jwt_required()
def port_analysis():
    """Return open port analysis across discovered services.

    Query Parameters:
        - scan_id (int, optional): Scope to a specific scan. Defaults to latest completed scan.

    Returns:
        200: List of port objects with port number, service name, device count, and risk level.
    """
    current_user_id = get_jwt_identity()

    scan_id = request.args.get('scan_id', type=int)

    if scan_id is not None:
        scan = Scan.query.filter_by(id=scan_id, user_id=current_user_id).first()
        if scan is None:
            return jsonify({'message': 'Scan not found', 'error': 'not_found'}), 404
        target_scan_id = scan.id
    else:
        scan = (
            Scan.query
            .filter_by(user_id=current_user_id, status='completed')
            .order_by(Scan.scan_date.desc())
            .first()
        )
        if scan is None:
            return jsonify({
                'message': 'No completed scans found',
                'data': [],
            }), 200
        target_scan_id = scan.id

    # Aggregate ports from vulnerabilities (each vulnerability record represents an open service)
    port_data = (
        db.session.query(
            Vulnerability.port,
            Vulnerability.service,
            func.count(func.distinct(Vulnerability.device_id)).label('device_count'),
            func.max(Vulnerability.cvss_score).label('max_cvss'),
        )
        .filter(
            Vulnerability.scan_id == target_scan_id,
            Vulnerability.port.isnot(None),
        )
        .group_by(Vulnerability.port, Vulnerability.service)
        .order_by(func.count(func.distinct(Vulnerability.device_id)).desc())
        .all()
    )

    # Classify risk based on the port and max CVSS score
    high_risk_ports = {21, 23, 25, 110, 135, 139, 445, 3389, 5900, 8080}
    medium_risk_ports = {22, 53, 80, 443, 993, 995, 3306, 5432, 8443}

    port_analysis_data = []
    for row in port_data:
        port_num = row.port
        max_cvss = row.max_cvss or 0.0

        if max_cvss >= 9.0 or port_num in high_risk_ports:
            risk = 'high'
        elif max_cvss >= 4.0 or port_num in medium_risk_ports:
            risk = 'medium'
        else:
            risk = 'low'

        port_analysis_data.append({
            'port': port_num,
            'service': row.service or 'unknown',
            'count': row.device_count,
            'risk': risk,
            'max_cvss': max_cvss,
        })

    return jsonify({
        'message': 'Port analysis retrieved',
        'data': port_analysis_data,
    }), 200
