import csv
import io
import json
import os
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Scan, Device, Vulnerability
from app.utils.decorators import log_action

reports_bp = Blueprint('reports', __name__)


def _get_reports_folder():
    """Return the absolute path to the reports folder, creating it if needed."""
    folder = current_app.config.get('REPORTS_FOLDER', os.path.join(os.getcwd(), 'reports'))
    os.makedirs(folder, exist_ok=True)
    return folder


@reports_bp.route('/generate/<int:scan_id>', methods=['POST'])
@jwt_required()
@log_action('report_generated')
def generate_report(scan_id):
    """Generate a report for a completed scan.

    Expects JSON body:
        - format (str, required): 'pdf' or 'html'

    Args:
        scan_id: The ID of the scan to generate a report for.

    Returns:
        201: Report generated successfully with file info.
        400: Invalid format or scan not completed.
        404: Scan not found.
    """
    current_user_id = get_jwt_identity()
    scan = Scan.query.filter_by(id=scan_id, user_id=current_user_id).first()

    if scan is None:
        return jsonify({'message': 'Scan not found', 'error': 'not_found'}), 404

    if scan.status != 'completed':
        return jsonify({
            'message': 'Report can only be generated for completed scans',
            'error': 'invalid_status',
        }), 400

    data = request.get_json() or {}
    report_format = data.get('format', 'html').lower()

    if report_format not in ('pdf', 'html'):
        return jsonify({
            'message': 'Invalid format. Must be "pdf" or "html"',
            'error': 'validation_error',
        }), 400

    # Build report data
    devices = Device.query.filter_by(scan_id=scan_id).all()
    vulns = Vulnerability.query.filter_by(scan_id=scan_id).all()

    report_data = {
        'scan': scan.to_dict(),
        'devices': [d.to_dict() for d in devices],
        'vulnerabilities': [v.to_dict() for v in vulns],
        'summary': {
            'total_hosts': scan.total_hosts,
            'total_vulns': scan.total_vulns,
            'risk_score': scan.risk_score,
            'critical': sum(1 for v in vulns if v.severity == 'critical'),
            'high': sum(1 for v in vulns if v.severity == 'high'),
            'medium': sum(1 for v in vulns if v.severity == 'medium'),
            'low': sum(1 for v in vulns if v.severity == 'low'),
            'info': sum(1 for v in vulns if v.severity == 'info'),
        },
    }

    reports_folder = _get_reports_folder()
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    filename = f'scan_{scan_id}_{timestamp}.{report_format}'
    filepath = os.path.join(reports_folder, filename)

    try:
        if report_format == 'pdf':
            try:
                from app.services.report_generator import PDFReportGenerator
                generator = PDFReportGenerator(scan, devices, vulns, scan.risk_score)
                generator.generate(filepath)
            except ImportError:
                # Fallback: create a text-based report if PDF generator is unavailable
                _generate_text_report(report_data, filepath)
        else:
            try:
                from app.services.report_generator import HTMLReportGenerator
                generator = HTMLReportGenerator(scan, devices, vulns, scan.risk_score)
                generator.generate(filepath)
            except ImportError:
                # Fallback: generate HTML manually
                _generate_html_report(report_data, filepath)
    except Exception as e:
        return jsonify({
            'message': f'Failed to generate report: {str(e)}',
            'error': 'generation_failed',
        }), 500

    file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

    return jsonify({
        'message': 'Report generated successfully',
        'data': {
            'filename': filename,
            'format': report_format,
            'scan_id': scan_id,
            'file_size': file_size,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'download_url': f'/api/reports/download/{filename}',
        },
    }), 201


def _generate_html_report(report_data, filepath):
    """Generate an HTML report file from scan data.

    Args:
        report_data: Dictionary containing scan, devices, vulnerabilities, and summary.
        filepath: Full path where the HTML file will be written.
    """
    scan = report_data['scan']
    summary = report_data['summary']
    devices = report_data['devices']
    vulnerabilities = report_data['vulnerabilities']

    severity_colors = {
        'critical': '#ff3366',
        'high': '#ff6633',
        'medium': '#ffaa00',
        'low': '#33cc99',
        'info': '#3399ff',
    }

    vuln_rows = ''
    for v in vulnerabilities:
        color = severity_colors.get(v.get('severity', 'info'), '#3399ff')
        vuln_rows += f'''
        <tr>
            <td>{v.get('cve_id', 'N/A')}</td>
            <td>{v.get('title', '')}</td>
            <td style="color: {color}; font-weight: bold;">{v.get('severity', '').upper()}</td>
            <td>{v.get('cvss_score', 'N/A')}</td>
            <td>{v.get('port', 'N/A')}</td>
            <td>{v.get('service', 'N/A')}</td>
            <td>{v.get('recommendation', 'N/A')}</td>
        </tr>'''

    device_rows = ''
    for d in devices:
        device_rows += f'''
        <tr>
            <td>{d.get('ip_address', '')}</td>
            <td>{d.get('hostname', 'N/A')}</td>
            <td>{d.get('os_name', 'N/A')}</td>
            <td>{d.get('vendor', 'N/A')}</td>
            <td>{d.get('device_type', 'N/A')}</td>
            <td>{d.get('vulnerability_count', 0)}</td>
        </tr>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Scan Report - Scan #{scan.get('id', '')}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #333; }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #16213e; padding-bottom: 10px; }}
        h2 {{ color: #16213e; margin-top: 30px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .summary-card {{ background: #f8f9fa; border-radius: 8px; padding: 20px; text-align: center; border-left: 4px solid #16213e; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; color: #16213e; }}
        .summary-card .label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #16213e; color: white; font-weight: 600; }}
        tr:hover {{ background: #f5f5f5; }}
        .meta {{ color: #666; font-size: 0.9em; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 0.85em; }}
    </style>
</head>
<body>
    <h1>Network Vulnerability Scan Report</h1>
    <div class="meta">
        <p><strong>Scan ID:</strong> {scan.get('id', '')} |
           <strong>Type:</strong> {scan.get('scan_type', '').capitalize()} |
           <strong>Target:</strong> {scan.get('target_range', '')} |
           <strong>Date:</strong> {scan.get('scan_date', '')} |
           <strong>Status:</strong> {scan.get('status', '').capitalize()}</p>
    </div>

    <h2>Summary</h2>
    <div class="summary-grid">
        <div class="summary-card">
            <div class="value">{summary.get('total_hosts', 0)}</div>
            <div class="label">Devices Found</div>
        </div>
        <div class="summary-card">
            <div class="value">{summary.get('total_vulns', 0)}</div>
            <div class="label">Vulnerabilities</div>
        </div>
        <div class="summary-card">
            <div class="value" style="color: #ff3366;">{summary.get('critical', 0)}</div>
            <div class="label">Critical</div>
        </div>
        <div class="summary-card">
            <div class="value" style="color: #ff6633;">{summary.get('high', 0)}</div>
            <div class="label">High</div>
        </div>
        <div class="summary-card">
            <div class="value" style="color: #ffaa00;">{summary.get('medium', 0)}</div>
            <div class="label">Medium</div>
        </div>
        <div class="summary-card">
            <div class="value">{summary.get('risk_score', 0)}</div>
            <div class="label">Risk Score</div>
        </div>
    </div>

    <h2>Discovered Devices ({len(devices)})</h2>
    <table>
        <thead>
            <tr><th>IP Address</th><th>Hostname</th><th>OS</th><th>Vendor</th><th>Type</th><th>Vulns</th></tr>
        </thead>
        <tbody>{device_rows}</tbody>
    </table>

    <h2>Vulnerabilities ({len(vulnerabilities)})</h2>
    <table>
        <thead>
            <tr><th>CVE ID</th><th>Title</th><th>Severity</th><th>CVSS</th><th>Port</th><th>Service</th><th>Recommendation</th></tr>
        </thead>
        <tbody>{vuln_rows}</tbody>
    </table>

    <div class="footer">
        <p>Generated by Home Network Vulnerability Scanner | {scan.get('scan_date', '')}</p>
    </div>
</body>
</html>'''

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)


def _generate_text_report(report_data, filepath):
    """Generate a plain text report as a PDF fallback.

    Args:
        report_data: Dictionary containing scan, devices, vulnerabilities, and summary.
        filepath: Full path where the text file will be written.
    """
    scan = report_data['scan']
    summary = report_data['summary']
    devices = report_data['devices']
    vulnerabilities = report_data['vulnerabilities']

    lines = [
        '=' * 70,
        'NETWORK VULNERABILITY SCAN REPORT',
        '=' * 70,
        '',
        f'Scan ID:      {scan.get("id", "")}',
        f'Scan Type:    {scan.get("scan_type", "")}',
        f'Target:       {scan.get("target_range", "")}',
        f'Date:         {scan.get("scan_date", "")}',
        f'Status:       {scan.get("status", "")}',
        f'Risk Score:   {summary.get("risk_score", 0)}',
        '',
        '-' * 70,
        'SUMMARY',
        '-' * 70,
        f'  Total Hosts:           {summary.get("total_hosts", 0)}',
        f'  Total Vulnerabilities: {summary.get("total_vulns", 0)}',
        f'  Critical:              {summary.get("critical", 0)}',
        f'  High:                  {summary.get("high", 0)}',
        f'  Medium:                {summary.get("medium", 0)}',
        f'  Low:                   {summary.get("low", 0)}',
        f'  Info:                  {summary.get("info", 0)}',
        '',
        '-' * 70,
        f'DISCOVERED DEVICES ({len(devices)})',
        '-' * 70,
    ]

    for d in devices:
        lines.append(f'  {d.get("ip_address", ""):16s} {d.get("hostname", "N/A"):20s} '
                     f'{d.get("os_name", "N/A"):20s} {d.get("vendor", "N/A"):15s} '
                     f'Vulns: {d.get("vulnerability_count", 0)}')

    lines.extend([
        '',
        '-' * 70,
        f'VULNERABILITIES ({len(vulnerabilities)})',
        '-' * 70,
    ])

    for v in vulnerabilities:
        lines.append(f'  [{v.get("severity", "").upper():8s}] {v.get("cve_id", "N/A"):16s} '
                     f'{v.get("title", "")[:50]:50s} CVSS: {v.get("cvss_score", "N/A")}')
        if v.get('recommendation'):
            lines.append(f'            Recommendation: {v["recommendation"][:60]}')
        lines.append('')

    lines.extend([
        '=' * 70,
        'Generated by Home Network Vulnerability Scanner',
        '=' * 70,
    ])

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


@reports_bp.route('/', methods=['GET'])
@jwt_required()
def list_reports():
    """List all generated report files.

    Returns:
        200: List of report files with metadata.
    """
    reports_folder = _get_reports_folder()

    reports = []
    if os.path.isdir(reports_folder):
        for filename in sorted(os.listdir(reports_folder), reverse=True):
            filepath = os.path.join(reports_folder, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)

                # Parse scan_id from filename pattern: scan_{id}_{timestamp}.{ext}
                scan_id = None
                parts = filename.split('_')
                if len(parts) >= 2 and parts[0] == 'scan':
                    try:
                        scan_id = int(parts[1])
                    except ValueError:
                        pass

                # Determine format from extension
                ext = os.path.splitext(filename)[1].lstrip('.')

                reports.append({
                    'filename': filename,
                    'format': ext,
                    'scan_id': scan_id,
                    'file_size': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                    'download_url': f'/api/reports/download/{filename}',
                })

    return jsonify({
        'message': 'Reports retrieved',
        'data': reports,
    }), 200


@reports_bp.route('/download/<filename>', methods=['GET'])
@jwt_required()
def download_report(filename):
    """Download a report file.

    Args:
        filename: The name of the report file to download.

    Returns:
        200: The report file.
        404: File not found.
    """
    reports_folder = _get_reports_folder()

    # Sanitize filename to prevent directory traversal
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(reports_folder, safe_filename)

    if not os.path.isfile(filepath):
        return jsonify({'message': 'Report not found', 'error': 'not_found'}), 404

    return send_from_directory(
        reports_folder,
        safe_filename,
        as_attachment=True,
        download_name=safe_filename,
    )


@reports_bp.route('/<filename>', methods=['DELETE'])
@jwt_required()
@log_action('report_deleted')
def delete_report(filename):
    """Delete a report file.

    Args:
        filename: The name of the report file to delete.

    Returns:
        200: Report deleted successfully.
        404: File not found.
    """
    reports_folder = _get_reports_folder()

    safe_filename = os.path.basename(filename)
    filepath = os.path.join(reports_folder, safe_filename)

    if not os.path.isfile(filepath):
        return jsonify({'message': 'Report not found', 'error': 'not_found'}), 404

    os.remove(filepath)

    return jsonify({
        'message': 'Report deleted successfully',
        'data': None,
    }), 200


@reports_bp.route('/export/<int:scan_id>/<export_format>', methods=['GET'])
@jwt_required()
@log_action('data_exported')
def export_scan_data(scan_id, export_format):
    """Export scan data as CSV or JSON.

    Args:
        scan_id: The ID of the scan to export.
        export_format: The export format ('csv' or 'json').

    Returns:
        200: Exported data as a downloadable file.
        400: Invalid format.
        404: Scan not found.
    """
    current_user_id = get_jwt_identity()

    if export_format not in ('csv', 'json'):
        return jsonify({
            'message': 'Invalid format. Must be "csv" or "json"',
            'error': 'validation_error',
        }), 400

    scan = Scan.query.filter_by(id=scan_id, user_id=current_user_id).first()
    if scan is None:
        return jsonify({'message': 'Scan not found', 'error': 'not_found'}), 404

    devices = Device.query.filter_by(scan_id=scan_id).all()
    vulns = Vulnerability.query.filter_by(scan_id=scan_id).all()

    reports_folder = _get_reports_folder()
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

    if export_format == 'json':
        export_data = {
            'scan': scan.to_dict(),
            'devices': [d.to_dict() for d in devices],
            'vulnerabilities': [v.to_dict() for v in vulns],
        }
        filename = f'export_scan_{scan_id}_{timestamp}.json'
        filepath = os.path.join(reports_folder, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)

    else:  # csv
        filename = f'export_scan_{scan_id}_{timestamp}.csv'
        filepath = os.path.join(reports_folder, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Device IP', 'Hostname', 'OS', 'Vendor', 'Device Type',
                'CVE ID', 'Vulnerability Title', 'Severity', 'CVSS Score',
                'Port', 'Protocol', 'Service', 'Version',
                'Exploit Available', 'Recommendation',
            ])

            for vuln in vulns:
                device = db.session.get(Device, vuln.device_id)
                writer.writerow([
                    device.ip_address if device else '',
                    device.hostname if device else '',
                    device.os_name if device else '',
                    device.vendor if device else '',
                    device.device_type if device else '',
                    vuln.cve_id or '',
                    vuln.title,
                    vuln.severity,
                    vuln.cvss_score or '',
                    vuln.port or '',
                    vuln.protocol or '',
                    vuln.service or '',
                    vuln.version or '',
                    'Yes' if vuln.exploit_available else 'No',
                    vuln.recommendation or '',
                ])

    return send_from_directory(
        reports_folder,
        filename,
        as_attachment=True,
        download_name=filename,
    )
