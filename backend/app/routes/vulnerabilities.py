from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app.extensions import db
from app.models import Vulnerability, Scan, Device
from app.utils.helpers import paginate_query

vulnerabilities_bp = Blueprint('vulnerabilities', __name__)


@vulnerabilities_bp.route('/', methods=['GET'])
@jwt_required()
def list_vulnerabilities():
    """List vulnerabilities with optional filtering.

    Query Parameters:
        - scan_id (int, optional): Filter by scan ID.
        - device_id (int, optional): Filter by device ID.
        - severity (str, optional): Filter by severity level (critical, high, medium, low, info).
        - cve_id (str, optional): Filter by CVE identifier.
        - page (int, optional): Page number. Defaults to 1.
        - per_page (int, optional): Items per page. Defaults to 20.

    Returns:
        200: Paginated list of vulnerabilities.
    """
    current_user_id = get_jwt_identity()

    # Only show vulnerabilities from the current user's scans
    user_scan_ids = db.session.query(Scan.id).filter_by(user_id=current_user_id).subquery()
    query = Vulnerability.query.filter(Vulnerability.scan_id.in_(user_scan_ids))

    # Apply optional filters
    scan_id = request.args.get('scan_id', type=int)
    if scan_id is not None:
        scan = Scan.query.filter_by(id=scan_id, user_id=current_user_id).first()
        if scan is None:
            return jsonify({'message': 'Scan not found', 'error': 'not_found'}), 404
        query = query.filter_by(scan_id=scan_id)

    device_id = request.args.get('device_id', type=int)
    if device_id is not None:
        query = query.filter_by(device_id=device_id)

    severity = request.args.get('severity')
    if severity:
        valid_severities = ('critical', 'high', 'medium', 'low', 'info')
        if severity.lower() in valid_severities:
            query = query.filter_by(severity=severity.lower())

    cve_id = request.args.get('cve_id')
    if cve_id:
        query = query.filter(Vulnerability.cve_id.ilike(f'%{cve_id}%'))

    query = query.order_by(Vulnerability.cvss_score.desc().nullslast(), Vulnerability.id)

    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 20)
    result = paginate_query(query, page, per_page)

    return jsonify({
        'message': 'Vulnerabilities retrieved',
        'data': result,
    }), 200


@vulnerabilities_bp.route('/<int:vuln_id>', methods=['GET'])
@jwt_required()
def get_vulnerability(vuln_id):
    """Get detailed information about a specific vulnerability.

    Args:
        vuln_id: The ID of the vulnerability to retrieve.

    Returns:
        200: Vulnerability details including device and scan info.
        404: Vulnerability not found or not owned by current user.
    """
    current_user_id = get_jwt_identity()

    vuln = Vulnerability.query.get(vuln_id)
    if vuln is None:
        return jsonify({'message': 'Vulnerability not found', 'error': 'not_found'}), 404

    # Verify ownership
    scan = Scan.query.filter_by(id=vuln.scan_id, user_id=current_user_id).first()
    if scan is None:
        return jsonify({'message': 'Vulnerability not found', 'error': 'not_found'}), 404

    vuln_data = vuln.to_dict()

    # Enrich with device info
    device = db.session.get(Device, vuln.device_id)
    if device:
        vuln_data['device_info'] = {
            'ip_address': device.ip_address,
            'hostname': device.hostname,
            'device_type': device.device_type,
            'os_name': device.os_name,
        }

    vuln_data['scan_info'] = {
        'scan_id': scan.id,
        'scan_date': scan.scan_date.isoformat() if scan.scan_date else None,
        'scan_type': scan.scan_type,
    }

    return jsonify({
        'message': 'Vulnerability details retrieved',
        'data': vuln_data,
    }), 200


@vulnerabilities_bp.route('/stats', methods=['GET'])
@jwt_required()
def vulnerability_stats():
    """Return aggregated vulnerability statistics.

    Query Parameters:
        - scan_id (int, optional): Scope statistics to a specific scan.

    Returns:
        200: Statistics including total count, severity breakdown, top CVEs, and average CVSS.
    """
    current_user_id = get_jwt_identity()

    # Base query scoped to user's scans
    user_scan_ids = db.session.query(Scan.id).filter_by(user_id=current_user_id).subquery()
    base_query = Vulnerability.query.filter(Vulnerability.scan_id.in_(user_scan_ids))

    scan_id = request.args.get('scan_id', type=int)
    if scan_id is not None:
        scan = Scan.query.filter_by(id=scan_id, user_id=current_user_id).first()
        if scan is None:
            return jsonify({'message': 'Scan not found', 'error': 'not_found'}), 404
        base_query = Vulnerability.query.filter_by(scan_id=scan_id)

    # Total count
    total_count = base_query.count()

    # Counts by severity
    severity_counts = {}
    for severity_level in ('critical', 'high', 'medium', 'low', 'info'):
        count = base_query.filter_by(severity=severity_level).count()
        severity_counts[severity_level] = count

    # Top CVEs (most frequent)
    top_cves_query = (
        db.session.query(
            Vulnerability.cve_id,
            Vulnerability.title,
            Vulnerability.severity,
            Vulnerability.cvss_score,
            func.count(Vulnerability.id).label('occurrence_count'),
        )
        .filter(
            Vulnerability.scan_id.in_(
                db.session.query(Scan.id).filter_by(user_id=current_user_id)
            ),
            Vulnerability.cve_id.isnot(None),
        )
    )

    if scan_id is not None:
        top_cves_query = top_cves_query.filter(Vulnerability.scan_id == scan_id)

    top_cves = (
        top_cves_query
        .group_by(Vulnerability.cve_id, Vulnerability.title, Vulnerability.severity, Vulnerability.cvss_score)
        .order_by(func.count(Vulnerability.id).desc())
        .limit(10)
        .all()
    )

    top_cves_list = [
        {
            'cve_id': row.cve_id,
            'title': row.title,
            'severity': row.severity,
            'cvss_score': row.cvss_score,
            'count': row.occurrence_count,
        }
        for row in top_cves
    ]

    # Average CVSS score
    avg_cvss_result = base_query.with_entities(func.avg(Vulnerability.cvss_score)).scalar()
    avg_cvss = round(float(avg_cvss_result), 2) if avg_cvss_result else 0.0

    # Exploit availability count
    exploit_count = base_query.filter_by(exploit_available=True).count()

    stats = {
        'total_vulnerabilities': total_count,
        'severity_counts': severity_counts,
        'top_cves': top_cves_list,
        'average_cvss': avg_cvss,
        'exploitable_count': exploit_count,
    }

    return jsonify({
        'message': 'Vulnerability statistics retrieved',
        'data': stats,
    }), 200
