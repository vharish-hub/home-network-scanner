"""Security recommendations engine."""
from app.extensions import db
from app.models import Vulnerability, Device

RECOMMENDATION_DATABASE = {
    'disable_telnet': {
        'text': 'Disable Telnet service and use SSH for remote access instead.',
        'priority': 'critical',
        'category': 'service',
        'steps': ['Stop the Telnet service', 'Disable Telnet in system services', 'Install and configure OpenSSH', 'Configure key-based authentication']
    },
    'disable_ftp': {
        'text': 'Replace FTP with SFTP or SCP for secure file transfer.',
        'priority': 'critical',
        'category': 'service',
        'steps': ['Stop FTP service', 'Install OpenSSH with SFTP subsystem', 'Migrate FTP users to SFTP', 'Remove FTP server software']
    },
    'close_smb': {
        'text': 'Restrict SMB access to internal networks only and update to latest version.',
        'priority': 'critical',
        'category': 'network',
        'steps': ['Disable SMBv1', 'Enable SMBv3 with encryption', 'Configure firewall to block external SMB', 'Apply latest security patches']
    },
    'close_rdp': {
        'text': 'Restrict RDP access and enable Network Level Authentication (NLA).',
        'priority': 'high',
        'category': 'network',
        'steps': ['Enable NLA for RDP', 'Use VPN for remote access', 'Limit RDP users', 'Enable account lockout policies']
    },
    'update_apache': {
        'text': 'Update Apache HTTP Server to the latest stable version.',
        'priority': 'high',
        'category': 'update',
        'steps': ['Backup current configuration', 'Download latest Apache release', 'Test in staging environment', 'Apply update and restart service']
    },
    'update_nginx': {
        'text': 'Update Nginx to the latest stable version to patch known vulnerabilities.',
        'priority': 'high',
        'category': 'update',
        'steps': ['Check current Nginx version', 'Review changelog for security fixes', 'Update via package manager', 'Verify configuration and restart']
    },
    'update_openssh': {
        'text': 'Update OpenSSH to the latest version and disable weak ciphers.',
        'priority': 'high',
        'category': 'update',
        'steps': ['Update OpenSSH package', 'Disable weak ciphers in sshd_config', 'Disable root login', 'Restart SSH service']
    },
    'update_mysql': {
        'text': 'Update MySQL to the latest version and review access controls.',
        'priority': 'high',
        'category': 'update',
        'steps': ['Backup databases', 'Update MySQL server', 'Review user privileges', 'Remove unused accounts']
    },
    'secure_database': {
        'text': 'Ensure database services are not exposed to external networks.',
        'priority': 'high',
        'category': 'configuration',
        'steps': ['Bind database to localhost', 'Configure firewall rules', 'Use strong authentication', 'Enable audit logging']
    },
    'secure_redis': {
        'text': 'Set authentication password for Redis and bind to localhost.',
        'priority': 'critical',
        'category': 'configuration',
        'steps': ['Set requirepass in redis.conf', 'Bind to 127.0.0.1', 'Disable dangerous commands', 'Enable protected mode']
    },
    'secure_mongodb': {
        'text': 'Enable authentication on MongoDB and restrict network access.',
        'priority': 'critical',
        'category': 'configuration',
        'steps': ['Enable authentication', 'Create admin user with strong password', 'Bind to specific interface', 'Enable TLS/SSL']
    },
    'close_unused_ports': {
        'text': 'Close unnecessary open ports to reduce attack surface.',
        'priority': 'medium',
        'category': 'network',
        'steps': ['Audit all open ports', 'Identify unnecessary services', 'Stop and disable unused services', 'Configure firewall to block ports']
    },
    'enable_firewall': {
        'text': 'Enable and configure host-based firewall rules.',
        'priority': 'medium',
        'category': 'network',
        'steps': ['Enable firewall', 'Set default deny policy', 'Allow only required services', 'Log blocked connections']
    },
    'enable_https': {
        'text': 'Enable HTTPS with valid TLS certificates for all web services.',
        'priority': 'medium',
        'category': 'configuration',
        'steps': ['Obtain TLS certificate', 'Configure HTTPS on web server', 'Redirect HTTP to HTTPS', 'Enable HSTS header']
    },
    'change_default_credentials': {
        'text': 'Change all default passwords on network devices and services.',
        'priority': 'critical',
        'category': 'password',
        'steps': ['Inventory all devices with default creds', 'Generate strong unique passwords', 'Update all default accounts', 'Store passwords in password manager']
    },
    'strong_passwords': {
        'text': 'Implement strong password policies across all services.',
        'priority': 'medium',
        'category': 'password',
        'steps': ['Require minimum 12 characters', 'Enforce complexity requirements', 'Enable account lockout', 'Implement password rotation']
    },
    'enable_encryption': {
        'text': 'Enable encryption for data in transit on all services.',
        'priority': 'high',
        'category': 'configuration',
        'steps': ['Enable TLS/SSL on all services', 'Disable unencrypted protocols', 'Use strong cipher suites', 'Verify certificate validity']
    },
    'secure_snmp': {
        'text': 'Update SNMP to v3 with authentication and encryption.',
        'priority': 'high',
        'category': 'service',
        'steps': ['Disable SNMPv1 and v2c', 'Configure SNMPv3 with auth and encryption', 'Change community strings', 'Restrict SNMP access by IP']
    },
    'disable_netbios': {
        'text': 'Disable NetBIOS if not required to prevent information leakage.',
        'priority': 'medium',
        'category': 'service',
        'steps': ['Disable NetBIOS over TCP/IP', 'Block ports 137-139', 'Use DNS for name resolution', 'Verify network connectivity']
    },
    'secure_vnc': {
        'text': 'Secure VNC with strong passwords and tunnel through SSH or VPN.',
        'priority': 'high',
        'category': 'service',
        'steps': ['Set strong VNC password', 'Configure SSH tunneling', 'Restrict access to trusted IPs', 'Consider replacing with more secure solution']
    },
    'update_firmware': {
        'text': 'Update firmware on IoT devices and network equipment.',
        'priority': 'medium',
        'category': 'update',
        'steps': ['Check vendor websites for updates', 'Backup current firmware', 'Apply updates during maintenance window', 'Verify functionality after update']
    },
    'segment_network': {
        'text': 'Implement network segmentation to isolate IoT devices.',
        'priority': 'medium',
        'category': 'network',
        'steps': ['Create separate VLAN for IoT', 'Configure firewall rules between segments', 'Limit IoT access to internet only', 'Monitor cross-segment traffic']
    },
    'enable_logging': {
        'text': 'Enable security logging and monitoring on all devices.',
        'priority': 'low',
        'category': 'configuration',
        'steps': ['Enable syslog on network devices', 'Configure log retention', 'Set up log analysis tools', 'Create alerts for suspicious activity']
    },
    'disable_unnecessary_services': {
        'text': 'Disable unnecessary network services to reduce attack surface.',
        'priority': 'medium',
        'category': 'service',
        'steps': ['Audit running services', 'Identify non-essential services', 'Disable and remove unused services', 'Document required services']
    },
    'regular_scanning': {
        'text': 'Schedule regular vulnerability scans to detect new issues.',
        'priority': 'low',
        'category': 'configuration',
        'steps': ['Configure scheduled scans', 'Review scan results regularly', 'Track remediation progress', 'Update scan configurations as network changes']
    },
}


def get_recommendations_for_scan(scan_id):
    """Generate prioritized recommendations for a scan grouped by severity."""
    vulns = Vulnerability.query.filter_by(scan_id=scan_id).all()
    recommendations = {}

    for vuln in vulns:
        rec_keys = _match_vuln_to_recommendations(vuln)
        for key in rec_keys:
            rec = RECOMMENDATION_DATABASE.get(key)
            if rec and key not in recommendations:
                recommendations[key] = {
                    'key': key,
                    'text': rec['text'],
                    'priority': rec['priority'],
                    'category': rec['category'],
                    'steps': rec['steps'],
                    'related_vulns': []
                }
            if key in recommendations:
                recommendations[key]['related_vulns'].append({
                    'id': vuln.id,
                    'title': vuln.title,
                    'severity': vuln.severity
                })

    grouped = {'critical': [], 'high': [], 'medium': [], 'low': []}
    for rec in recommendations.values():
        priority = rec['priority']
        if priority in grouped:
            grouped[priority].append(rec)

    return grouped


def get_recommendations_for_device(device_id):
    """Generate recommendations for a specific device."""
    vulns = Vulnerability.query.filter_by(device_id=device_id).all()
    recommendations = []
    seen = set()

    for vuln in vulns:
        rec_keys = _match_vuln_to_recommendations(vuln)
        for key in rec_keys:
            if key not in seen:
                seen.add(key)
                rec = RECOMMENDATION_DATABASE.get(key)
                if rec:
                    recommendations.append({
                        'key': key,
                        'text': rec['text'],
                        'priority': rec['priority'],
                        'category': rec['category'],
                        'steps': rec['steps']
                    })

    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    recommendations.sort(key=lambda r: priority_order.get(r['priority'], 4))
    return recommendations


def get_recommendation_summary(scan_id):
    """Return summary counts by category."""
    grouped = get_recommendations_for_scan(scan_id)
    by_category = {}
    total = 0
    for priority, recs in grouped.items():
        for rec in recs:
            cat = rec['category']
            by_category[cat] = by_category.get(cat, 0) + 1
            total += 1

    return {
        'total': total,
        'by_category': by_category,
        'by_priority': {k: len(v) for k, v in grouped.items()}
    }


def _match_vuln_to_recommendations(vuln):
    """Match a vulnerability to relevant recommendation keys."""
    keys = []
    service = (vuln.service or '').lower()
    port = vuln.port
    title = (vuln.title or '').lower()
    desc = (vuln.description or '').lower()

    if port == 23 or 'telnet' in service:
        keys.append('disable_telnet')
    if port == 21 or 'ftp' in service:
        keys.append('disable_ftp')
    if port == 445 or 'smb' in service or 'microsoft-ds' in service:
        keys.append('close_smb')
    if port == 3389 or 'rdp' in service:
        keys.append('close_rdp')
    if 'apache' in service or 'apache' in title:
        keys.append('update_apache')
    if 'nginx' in service or 'nginx' in title:
        keys.append('update_nginx')
    if 'ssh' in service or 'openssh' in title:
        keys.append('update_openssh')
    if 'mysql' in service or port == 3306:
        keys.append('update_mysql')
    if port in (3306, 5432, 1433, 1521, 27017):
        keys.append('secure_database')
    if 'redis' in service or port == 6379:
        keys.append('secure_redis')
    if 'mongodb' in service or port == 27017:
        keys.append('secure_mongodb')
    if 'vnc' in service or port == 5900:
        keys.append('secure_vnc')
    if port == 161 or 'snmp' in service:
        keys.append('secure_snmp')
    if port == 139 or 'netbios' in service:
        keys.append('disable_netbios')
    if 'default' in title or 'default' in desc or 'credential' in title:
        keys.append('change_default_credentials')
    if port == 80 or ('http' in service and 'https' not in service):
        keys.append('enable_https')
    if 'encrypt' in title or 'unencrypt' in desc or 'cleartext' in desc:
        keys.append('enable_encryption')

    if not keys:
        keys.append('close_unused_ports')

    return keys
