"""Seed database with realistic sample data for demonstration."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Scan, Device, Vulnerability


def seed():
    app = create_app('development')
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()

        # Create Users
        admin = User(username='admin', email='admin@scanner.local', role='admin')
        admin.set_password('admin123')
        user = User(username='user', email='user@scanner.local', role='user')
        user.set_password('user123')
        db.session.add_all([admin, user])
        db.session.commit()
        print(f"Created users: admin (id={admin.id}), user (id={user.id})")

        now = datetime.now(timezone.utc)

        # Scan 1: Full scan, 2 days ago
        scan1 = Scan(user_id=admin.id, scan_date=now - timedelta(days=2),
                     scan_type='full', target_range='192.168.1.0/24',
                     status='completed', duration=245.7, completed_at=now - timedelta(days=2, hours=-1))
        # Scan 2: Quick scan, 1 day ago
        scan2 = Scan(user_id=admin.id, scan_date=now - timedelta(days=1),
                     scan_type='quick', target_range='192.168.1.0/24',
                     status='completed', duration=48.3, completed_at=now - timedelta(days=1, hours=-1))
        # Scan 3: Full scan, today
        scan3 = Scan(user_id=admin.id, scan_date=now - timedelta(hours=3),
                     scan_type='full', target_range='10.0.0.0/24',
                     status='completed', duration=312.5, completed_at=now - timedelta(hours=2))
        db.session.add_all([scan1, scan2, scan3])
        db.session.commit()

        # Devices for Scan 1
        devices_s1 = [
            Device(scan_id=scan1.id, ip_address='192.168.1.1', mac_address='AA:BB:CC:DD:EE:01',
                   hostname='gateway-router', os_name='Linux 3.x', os_accuracy=92, vendor='Netgear',
                   status='up', device_type='router'),
            Device(scan_id=scan1.id, ip_address='192.168.1.10', mac_address='AA:BB:CC:DD:EE:02',
                   hostname='desktop-pc', os_name='Windows 11', os_accuracy=95, vendor='Dell',
                   status='up', device_type='computer'),
            Device(scan_id=scan1.id, ip_address='192.168.1.15', mac_address='AA:BB:CC:DD:EE:03',
                   hostname='macbook-pro', os_name='macOS 14 Sonoma', os_accuracy=90, vendor='Apple',
                   status='up', device_type='computer'),
            Device(scan_id=scan1.id, ip_address='192.168.1.20', mac_address='AA:BB:CC:DD:EE:04',
                   hostname='samsung-tv', os_name='Tizen 7.0', os_accuracy=70, vendor='Samsung',
                   status='up', device_type='smart_tv'),
            Device(scan_id=scan1.id, ip_address='192.168.1.25', mac_address='AA:BB:CC:DD:EE:05',
                   hostname='pixel-phone', os_name='Android 14', os_accuracy=85, vendor='Google',
                   status='up', device_type='phone'),
            Device(scan_id=scan1.id, ip_address='192.168.1.30', mac_address='AA:BB:CC:DD:EE:06',
                   hostname='security-cam', os_name='Linux 4.x', os_accuracy=60, vendor='Hikvision',
                   status='up', device_type='iot'),
            Device(scan_id=scan1.id, ip_address='192.168.1.35', mac_address='AA:BB:CC:DD:EE:07',
                   hostname='nas-server', os_name='Linux 5.x DSM', os_accuracy=88, vendor='Synology',
                   status='up', device_type='nas'),
            Device(scan_id=scan1.id, ip_address='192.168.1.40', mac_address='AA:BB:CC:DD:EE:08',
                   hostname='echo-dot', os_name='Fire OS', os_accuracy=55, vendor='Amazon',
                   status='up', device_type='iot'),
            Device(scan_id=scan1.id, ip_address='192.168.1.45', mac_address='AA:BB:CC:DD:EE:09',
                   hostname='hp-printer', os_name='Embedded', os_accuracy=40, vendor='HP',
                   status='up', device_type='printer'),
            Device(scan_id=scan1.id, ip_address='192.168.1.50', mac_address='AA:BB:CC:DD:EE:10',
                   hostname='ps5-console', os_name='FreeBSD 13', os_accuracy=65, vendor='Sony',
                   status='up', device_type='gaming'),
        ]
        db.session.add_all(devices_s1)
        db.session.commit()

        # Vulnerabilities for Scan 1
        vulns_s1 = [
            # Critical
            Vulnerability(device_id=devices_s1[0].id, scan_id=scan1.id, port=23, protocol='tcp',
                          service='telnet', cve_id='CVE-2020-10188', title='Telnet Service Enabled',
                          description='Telnet transmits data including credentials in cleartext, making it vulnerable to eavesdropping.',
                          severity='critical', cvss_score=9.8, exploit_available=True,
                          recommendation='Disable Telnet and use SSH for remote management.'),
            Vulnerability(device_id=devices_s1[5].id, scan_id=scan1.id, port=80, protocol='tcp',
                          service='http', version='Apache 2.4.49', cve_id='CVE-2021-41773',
                          title='Apache HTTP Server Path Traversal',
                          description='Apache 2.4.49 contains a path traversal vulnerability that allows reading files outside the document root.',
                          severity='critical', cvss_score=9.8, exploit_available=True,
                          recommendation='Update Apache to 2.4.51 or later immediately.'),
            Vulnerability(device_id=devices_s1[6].id, scan_id=scan1.id, port=443, protocol='tcp',
                          service='https', version='OpenSSL 3.0.1', cve_id='CVE-2022-0778',
                          title='OpenSSL Infinite Loop Vulnerability',
                          description='An attacker can craft a malicious certificate to cause an infinite loop in OpenSSL.',
                          severity='critical', cvss_score=7.5, exploit_available=True,
                          recommendation='Update OpenSSL to 3.0.2 or later.'),
            # High
            Vulnerability(device_id=devices_s1[0].id, scan_id=scan1.id, port=445, protocol='tcp',
                          service='microsoft-ds', cve_id='CVE-2017-0144', title='SMBv1 EternalBlue Vulnerability',
                          description='SMBv1 is vulnerable to remote code execution via the EternalBlue exploit.',
                          severity='high', cvss_score=8.1, exploit_available=True,
                          recommendation='Disable SMBv1 and update to SMBv3 with encryption.'),
            Vulnerability(device_id=devices_s1[1].id, scan_id=scan1.id, port=3389, protocol='tcp',
                          service='ms-wbt-server', cve_id='CVE-2019-0708', title='RDP BlueKeep Vulnerability',
                          description='Remote Desktop Protocol vulnerability allowing remote code execution.',
                          severity='high', cvss_score=9.8, exploit_available=True,
                          recommendation='Enable NLA, apply patches, and restrict RDP access.'),
            Vulnerability(device_id=devices_s1[5].id, scan_id=scan1.id, port=554, protocol='tcp',
                          service='rtsp', title='Default Credentials on IP Camera',
                          description='The IP camera is accessible with default manufacturer credentials.',
                          severity='high', cvss_score=8.8, exploit_available=True,
                          recommendation='Change default credentials immediately.'),
            Vulnerability(device_id=devices_s1[8].id, scan_id=scan1.id, port=9100, protocol='tcp',
                          service='jetdirect', title='Unsecured Print Service',
                          description='JetDirect port is open and accessible without authentication.',
                          severity='high', cvss_score=7.5, exploit_available=False,
                          recommendation='Restrict printer access to authorized IPs only.'),
            Vulnerability(device_id=devices_s1[6].id, scan_id=scan1.id, port=22, protocol='tcp',
                          service='ssh', version='OpenSSH 7.4', cve_id='CVE-2023-38408',
                          title='OpenSSH Agent Forwarding RCE',
                          description='Vulnerability in ssh-agent forwarding allows remote code execution.',
                          severity='high', cvss_score=9.8, exploit_available=True,
                          recommendation='Update OpenSSH to 9.3p2 or later.'),
            # Medium
            Vulnerability(device_id=devices_s1[1].id, scan_id=scan1.id, port=80, protocol='tcp',
                          service='http', title='HTTP Service Without TLS',
                          description='Web service running on HTTP without TLS encryption.',
                          severity='medium', cvss_score=5.3, exploit_available=False,
                          recommendation='Enable HTTPS with valid TLS certificate.'),
            Vulnerability(device_id=devices_s1[2].id, scan_id=scan1.id, port=5900, protocol='tcp',
                          service='vnc', title='VNC Service Exposed',
                          description='VNC remote desktop service is accessible on the network.',
                          severity='medium', cvss_score=6.5, exploit_available=False,
                          recommendation='Secure VNC with strong password and SSH tunnel.'),
            Vulnerability(device_id=devices_s1[3].id, scan_id=scan1.id, port=8080, protocol='tcp',
                          service='http-proxy', title='Smart TV Web Interface Exposed',
                          description='Smart TV management interface accessible without authentication.',
                          severity='medium', cvss_score=5.0, exploit_available=False,
                          recommendation='Disable web interface or restrict to local access.'),
            Vulnerability(device_id=devices_s1[0].id, scan_id=scan1.id, port=161, protocol='udp',
                          service='snmp', title='SNMP Community String Default',
                          description='SNMP using default community string "public".',
                          severity='medium', cvss_score=5.3, exploit_available=False,
                          recommendation='Change SNMP community strings and upgrade to SNMPv3.'),
            Vulnerability(device_id=devices_s1[6].id, scan_id=scan1.id, port=3306, protocol='tcp',
                          service='mysql', version='MySQL 5.7.38', title='MySQL Exposed to Network',
                          description='MySQL database port accessible from the network.',
                          severity='medium', cvss_score=5.9, exploit_available=False,
                          recommendation='Bind MySQL to localhost and use SSH tunnels.'),
            # Low
            Vulnerability(device_id=devices_s1[4].id, scan_id=scan1.id, port=53, protocol='udp',
                          service='dns', title='DNS Service Information Disclosure',
                          description='DNS service reveals version information.',
                          severity='low', cvss_score=3.7, exploit_available=False,
                          recommendation='Configure DNS to hide version information.'),
            Vulnerability(device_id=devices_s1[7].id, scan_id=scan1.id, port=443, protocol='tcp',
                          service='https', title='TLS Certificate Self-Signed',
                          description='Device uses a self-signed TLS certificate.',
                          severity='low', cvss_score=3.1, exploit_available=False,
                          recommendation='Replace with CA-signed certificate if possible.'),
            Vulnerability(device_id=devices_s1[9].id, scan_id=scan1.id, port=3478, protocol='udp',
                          service='stun', title='STUN Service Detected',
                          description='STUN/TURN service detected for NAT traversal.',
                          severity='info', cvss_score=0.0, exploit_available=False,
                          recommendation='Ensure STUN service is necessary for gaming.'),
            Vulnerability(device_id=devices_s1[2].id, scan_id=scan1.id, port=631, protocol='tcp',
                          service='ipp', title='CUPS Printing Service Exposed',
                          description='CUPS Internet Printing Protocol service is accessible.',
                          severity='low', cvss_score=3.3, exploit_available=False,
                          recommendation='Restrict CUPS access to localhost.'),
            # Info
            Vulnerability(device_id=devices_s1[1].id, scan_id=scan1.id, port=135, protocol='tcp',
                          service='msrpc', title='Windows RPC Service Detected',
                          description='Microsoft RPC endpoint mapper detected.',
                          severity='info', cvss_score=0.0, exploit_available=False,
                          recommendation='Ensure firewall blocks external RPC access.'),
            Vulnerability(device_id=devices_s1[0].id, scan_id=scan1.id, port=53, protocol='tcp',
                          service='dns', title='DNS Service Running',
                          description='DNS resolver service running on router.',
                          severity='info', cvss_score=0.0, exploit_available=False,
                          recommendation='Normal for router operation. Ensure DNS is up to date.'),
        ]
        db.session.add_all(vulns_s1)

        # Devices for Scan 2 (fewer devices for quick scan)
        devices_s2 = [
            Device(scan_id=scan2.id, ip_address='192.168.1.1', mac_address='AA:BB:CC:DD:EE:01',
                   hostname='gateway-router', os_name='Linux 3.x', os_accuracy=92, vendor='Netgear',
                   status='up', device_type='router'),
            Device(scan_id=scan2.id, ip_address='192.168.1.10', mac_address='AA:BB:CC:DD:EE:02',
                   hostname='desktop-pc', os_name='Windows 11', os_accuracy=95, vendor='Dell',
                   status='up', device_type='computer'),
            Device(scan_id=scan2.id, ip_address='192.168.1.15', mac_address='AA:BB:CC:DD:EE:03',
                   hostname='macbook-pro', os_name='macOS 14 Sonoma', os_accuracy=90, vendor='Apple',
                   status='up', device_type='computer'),
            Device(scan_id=scan2.id, ip_address='192.168.1.25', mac_address='AA:BB:CC:DD:EE:05',
                   hostname='pixel-phone', os_name='Android 14', os_accuracy=85, vendor='Google',
                   status='up', device_type='phone'),
            Device(scan_id=scan2.id, ip_address='192.168.1.30', mac_address='AA:BB:CC:DD:EE:06',
                   hostname='security-cam', os_name='Linux 4.x', os_accuracy=60, vendor='Hikvision',
                   status='up', device_type='iot'),
            Device(scan_id=scan2.id, ip_address='192.168.1.35', mac_address='AA:BB:CC:DD:EE:07',
                   hostname='nas-server', os_name='Linux 5.x DSM', os_accuracy=88, vendor='Synology',
                   status='up', device_type='nas'),
        ]
        db.session.add_all(devices_s2)
        db.session.commit()

        vulns_s2 = [
            Vulnerability(device_id=devices_s2[0].id, scan_id=scan2.id, port=23, protocol='tcp',
                          service='telnet', title='Telnet Service Enabled', severity='critical',
                          cvss_score=9.8, exploit_available=True,
                          recommendation='Disable Telnet and use SSH.'),
            Vulnerability(device_id=devices_s2[4].id, scan_id=scan2.id, port=80, protocol='tcp',
                          service='http', title='Default Credentials on IP Camera',
                          severity='high', cvss_score=8.8, exploit_available=True,
                          recommendation='Change default credentials immediately.'),
            Vulnerability(device_id=devices_s2[1].id, scan_id=scan2.id, port=3389, protocol='tcp',
                          service='ms-wbt-server', title='RDP Service Exposed',
                          severity='high', cvss_score=7.6, exploit_available=False,
                          recommendation='Restrict RDP access and enable NLA.'),
            Vulnerability(device_id=devices_s2[5].id, scan_id=scan2.id, port=22, protocol='tcp',
                          service='ssh', version='OpenSSH 7.4', title='Outdated OpenSSH Version',
                          severity='medium', cvss_score=5.3, exploit_available=False,
                          recommendation='Update OpenSSH to latest version.'),
            Vulnerability(device_id=devices_s2[2].id, scan_id=scan2.id, port=5900, protocol='tcp',
                          service='vnc', title='VNC Service Exposed', severity='medium',
                          cvss_score=6.5, exploit_available=False,
                          recommendation='Secure VNC with strong password and SSH tunnel.'),
            Vulnerability(device_id=devices_s2[3].id, scan_id=scan2.id, port=53, protocol='udp',
                          service='dns', title='DNS Version Disclosure', severity='low',
                          cvss_score=3.7, exploit_available=False,
                          recommendation='Hide DNS version information.'),
        ]
        db.session.add_all(vulns_s2)

        # Devices for Scan 3
        devices_s3 = [
            Device(scan_id=scan3.id, ip_address='10.0.0.1', mac_address='BB:CC:DD:EE:FF:01',
                   hostname='core-router', os_name='Cisco IOS 15.x', os_accuracy=88, vendor='Cisco',
                   status='up', device_type='router'),
            Device(scan_id=scan3.id, ip_address='10.0.0.10', mac_address='BB:CC:DD:EE:FF:02',
                   hostname='web-server', os_name='Ubuntu 22.04', os_accuracy=96, vendor='Dell',
                   status='up', device_type='server'),
            Device(scan_id=scan3.id, ip_address='10.0.0.20', mac_address='BB:CC:DD:EE:FF:03',
                   hostname='db-server', os_name='CentOS 8', os_accuracy=93, vendor='HP',
                   status='up', device_type='server'),
            Device(scan_id=scan3.id, ip_address='10.0.0.30', mac_address='BB:CC:DD:EE:FF:04',
                   hostname='dev-laptop', os_name='Windows 11', os_accuracy=95, vendor='Lenovo',
                   status='up', device_type='computer'),
            Device(scan_id=scan3.id, ip_address='10.0.0.40', mac_address='BB:CC:DD:EE:FF:05',
                   hostname='wifi-ap', os_name='Linux Embedded', os_accuracy=50, vendor='Ubiquiti',
                   status='up', device_type='router'),
            Device(scan_id=scan3.id, ip_address='10.0.0.50', mac_address='BB:CC:DD:EE:FF:06',
                   hostname='ip-phone', os_name='Embedded RTOS', os_accuracy=40, vendor='Cisco',
                   status='up', device_type='iot'),
            Device(scan_id=scan3.id, ip_address='10.0.0.60', mac_address='BB:CC:DD:EE:FF:07',
                   hostname='smart-thermostat', os_name='Linux Embedded', os_accuracy=35, vendor='Nest',
                   status='up', device_type='iot'),
            Device(scan_id=scan3.id, ip_address='10.0.0.70', mac_address='BB:CC:DD:EE:FF:08',
                   hostname='backup-nas', os_name='FreeNAS 13', os_accuracy=80, vendor='iXsystems',
                   status='up', device_type='nas'),
        ]
        db.session.add_all(devices_s3)
        db.session.commit()

        vulns_s3 = [
            Vulnerability(device_id=devices_s3[1].id, scan_id=scan3.id, port=80, protocol='tcp',
                          service='http', version='nginx 1.18.0', cve_id='CVE-2021-23017',
                          title='Nginx DNS Resolver Vulnerability',
                          description='Off-by-one error in nginx resolver allows remote attackers to cause denial of service.',
                          severity='critical', cvss_score=9.4, exploit_available=True,
                          recommendation='Update Nginx to 1.21.0 or later.'),
            Vulnerability(device_id=devices_s3[2].id, scan_id=scan3.id, port=6379, protocol='tcp',
                          service='redis', version='Redis 6.0.5', cve_id='CVE-2022-24735',
                          title='Redis Lua Sandbox Escape',
                          description='Redis allows Lua script execution that can escape sandbox.',
                          severity='critical', cvss_score=8.8, exploit_available=True,
                          recommendation='Update Redis and set requirepass.'),
            Vulnerability(device_id=devices_s3[2].id, scan_id=scan3.id, port=3306, protocol='tcp',
                          service='mysql', version='MySQL 8.0.28', cve_id='CVE-2023-21977',
                          title='MySQL Server Optimizer Vulnerability',
                          description='Vulnerability in MySQL Server optimizer allows high privileged attacker to cause DoS.',
                          severity='high', cvss_score=6.5, exploit_available=False,
                          recommendation='Apply latest MySQL patches.'),
            Vulnerability(device_id=devices_s3[0].id, scan_id=scan3.id, port=161, protocol='udp',
                          service='snmp', title='SNMPv2 with Default Community String',
                          description='SNMP using default "public" community string allows information disclosure.',
                          severity='high', cvss_score=7.5, exploit_available=True,
                          recommendation='Change community strings and upgrade to SNMPv3.'),
            Vulnerability(device_id=devices_s3[3].id, scan_id=scan3.id, port=445, protocol='tcp',
                          service='microsoft-ds', title='SMB Signing Not Required',
                          description='SMB signing is not enforced, allowing man-in-the-middle attacks.',
                          severity='medium', cvss_score=5.9, exploit_available=False,
                          recommendation='Enable mandatory SMB signing.'),
            Vulnerability(device_id=devices_s3[1].id, scan_id=scan3.id, port=443, protocol='tcp',
                          service='https', title='TLS 1.0/1.1 Supported',
                          description='Web server supports deprecated TLS versions.',
                          severity='medium', cvss_score=5.3, exploit_available=False,
                          recommendation='Disable TLS 1.0/1.1 and enforce TLS 1.2+.'),
            Vulnerability(device_id=devices_s3[4].id, scan_id=scan3.id, port=80, protocol='tcp',
                          service='http', title='WiFi AP Default Admin Interface',
                          description='Access point management interface accessible with weak credentials.',
                          severity='high', cvss_score=8.0, exploit_available=True,
                          recommendation='Change default credentials and restrict management access.'),
            Vulnerability(device_id=devices_s3[5].id, scan_id=scan3.id, port=5060, protocol='udp',
                          service='sip', title='SIP Service Exposed',
                          description='SIP VoIP service accessible without encryption.',
                          severity='medium', cvss_score=5.3, exploit_available=False,
                          recommendation='Enable SRTP/TLS for SIP communications.'),
            Vulnerability(device_id=devices_s3[6].id, scan_id=scan3.id, port=80, protocol='tcp',
                          service='http', title='IoT Device Unencrypted Management',
                          description='Smart thermostat management interface uses HTTP.',
                          severity='medium', cvss_score=4.3, exploit_available=False,
                          recommendation='Segment IoT devices into separate VLAN.'),
            Vulnerability(device_id=devices_s3[7].id, scan_id=scan3.id, port=22, protocol='tcp',
                          service='ssh', version='OpenSSH 8.2', title='SSH Weak Key Exchange',
                          description='SSH supports weak key exchange algorithms.',
                          severity='low', cvss_score=3.7, exploit_available=False,
                          recommendation='Disable weak key exchange algorithms in sshd_config.'),
            Vulnerability(device_id=devices_s3[3].id, scan_id=scan3.id, port=135, protocol='tcp',
                          service='msrpc', title='Windows RPC Endpoint Mapper',
                          description='RPC endpoint mapper service detected.',
                          severity='info', cvss_score=0.0, exploit_available=False,
                          recommendation='Block external RPC access with firewall.'),
        ]
        db.session.add_all(vulns_s3)
        db.session.commit()

        # Update scan totals
        for scan, devices, vulns in [(scan1, devices_s1, vulns_s1), (scan2, devices_s2, vulns_s2), (scan3, devices_s3, vulns_s3)]:
            scan.total_hosts = len(devices)
            scan.total_vulns = len(vulns)
            # Calculate simple risk score
            severity_weights = {'critical': 10, 'high': 7, 'medium': 4, 'low': 1, 'info': 0}
            weighted_sum = sum(severity_weights.get(v.severity, 0) for v in vulns)
            max_possible = len(vulns) * 10
            scan.risk_score = round(max(0, 100 - (weighted_sum / max(max_possible, 1) * 100)), 1)
        db.session.commit()

        print(f"\nSeed data created successfully!")
        print(f"  Users: 2 (admin, user)")
        print(f"  Scans: 3")
        print(f"  Scan 1: {len(devices_s1)} devices, {len(vulns_s1)} vulnerabilities, score={scan1.risk_score}")
        print(f"  Scan 2: {len(devices_s2)} devices, {len(vulns_s2)} vulnerabilities, score={scan2.risk_score}")
        print(f"  Scan 3: {len(devices_s3)} devices, {len(vulns_s3)} vulnerabilities, score={scan3.risk_score}")
        print(f"\nDefault credentials:")
        print(f"  Admin: admin / admin123")
        print(f"  User:  user / user123")


if __name__ == '__main__':
    seed()
