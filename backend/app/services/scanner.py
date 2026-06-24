"""
Network Scanning Engine.

Provides the ``NetworkScanner`` class that wraps python-nmap for host
discovery, port scanning, and OS detection.  When nmap is not available
it falls back to basic socket-based scanning.  The ``full_scan`` method
orchestrates the entire scan pipeline and is designed to run in a
background thread.
"""

import logging
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import nmap; set a flag for the fallback path
# ---------------------------------------------------------------------------
try:
    import nmap
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False
    logger.warning("python-nmap is not installed -- falling back to socket-based scanning.")


class NetworkScanner:
    """High-level wrapper around nmap / socket scanning primitives."""

    # Port lists for each scan type
    _QUICK_PORTS = "20-25,53,80,110,135,139,143,161,443,445,993,995,1433,1521,3306,3389,5432,5900,6379,8080,8443,27017"
    _FULL_PORTS = (
        "1-1024,"
        "1080,1433,1434,1521,2049,2082,2083,2086,2087,3000,3128,3306,3389,"
        "4443,5000,5432,5900,5901,6379,6667,8000,8008,8080,8443,8888,"
        "9090,9200,9300,10000,11211,27017,27018,28017"
    )

    # ------------------------------------------------------------------
    # Auto-detect local network range
    # ------------------------------------------------------------------
    @staticmethod
    def get_local_network_range():
        """
        Auto-detect the local network subnet by finding the primary local IP
        address and constructing a /24 CIDR range.

        Returns:
            str: e.g. '192.168.1.0/24'
        """
        local_ip = _get_local_ip()
        # Build /24 from the first three octets
        parts = local_ip.split('.')
        if len(parts) == 4:
            network = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        else:
            network = f"{local_ip}/24"
        logger.info("Detected local network range: %s (from IP %s)", network, local_ip)
        return network

    # ------------------------------------------------------------------
    # Host discovery
    # ------------------------------------------------------------------
    @staticmethod
    def discover_hosts(target_range):
        """
        Discover active hosts on the given network range.

        Uses nmap ping scan (-sn) when available, otherwise falls back to
        a simple ICMP / socket sweep.

        Args:
            target_range: CIDR notation string, e.g. '192.168.1.0/24'.

        Returns:
            list[dict]: Each dict has keys: ip, mac, hostname, vendor, status.
        """
        if NMAP_AVAILABLE:
            return _nmap_discover_hosts(target_range)
        return _fallback_discover_hosts(target_range)

    # ------------------------------------------------------------------
    # Port scanning
    # ------------------------------------------------------------------
    def scan_ports(self, host, scan_type='quick'):
        """
        Scan ports on a single host.

        Args:
            host: IP address string.
            scan_type: 'quick' (top ~100), 'full' (top ~1000), or 'custom' (all 65535).

        Returns:
            list[dict]: Each dict has keys: port, protocol, state, service, version.
        """
        if scan_type == 'quick':
            ports = self._QUICK_PORTS
        elif scan_type == 'full':
            ports = self._FULL_PORTS
        else:  # custom -- all ports
            ports = '1-65535'

        if NMAP_AVAILABLE:
            return _nmap_scan_ports(host, ports)
        return _fallback_scan_ports(host, ports)

    # ------------------------------------------------------------------
    # OS detection
    # ------------------------------------------------------------------
    @staticmethod
    def detect_os(host):
        """
        Detect the operating system of a host using nmap -O.

        Args:
            host: IP address string.

        Returns:
            dict with keys: os_name, os_accuracy (int), os_family.
        """
        if not NMAP_AVAILABLE:
            return {'os_name': 'Unknown', 'os_accuracy': 0, 'os_family': 'Unknown'}

        try:
            nm = nmap.PortScanner()
            nm.scan(host, arguments='-O --osscan-guess')

            if host in nm.all_hosts():
                os_matches = nm[host].get('osmatch', [])
                if os_matches:
                    best = os_matches[0]
                    os_classes = best.get('osclass', [{}])
                    os_family = os_classes[0].get('osfamily', 'Unknown') if os_classes else 'Unknown'
                    return {
                        'os_name': best.get('name', 'Unknown'),
                        'os_accuracy': int(best.get('accuracy', 0)),
                        'os_family': os_family,
                    }
        except Exception as exc:
            logger.warning("OS detection failed for %s: %s", host, exc)

        return {'os_name': 'Unknown', 'os_accuracy': 0, 'os_family': 'Unknown'}

    # ------------------------------------------------------------------
    # Full scan pipeline (background thread entry-point)
    # ------------------------------------------------------------------
    def full_scan(self, target_range, scan_type, scan_id, app):
        """
        Run the complete scan pipeline.  Designed to be called inside a
        background thread; ``app`` is the Flask application instance
        needed to push an application context.

        Steps:
          1. Update scan status to 'running'.
          2. Discover hosts.
          3. For each host: scan ports, detect OS, create Device records.
          4. Run vulnerability assessment.
          5. Calculate network risk score.
          6. Update scan with final results.
          7. On error, mark scan as 'failed'.

        Args:
            target_range: CIDR string.
            scan_type: 'quick', 'full', or 'custom'.
            scan_id: Integer scan ID.
            app: Flask application instance (for app context).
        """
        # Import here to avoid circular imports at module level
        from app.extensions import db
        from app.models.scan import Scan
        from app.models.device import Device
        from app.services.vulnerability_db import assess_vulnerabilities
        from app.services.risk_engine import calculate_network_risk

        with app.app_context():
            start_time = time.time()

            try:
                # 1. Mark scan as running
                scan = db.session.get(Scan, scan_id)
                if scan is None:
                    logger.error("Scan %s not found -- aborting.", scan_id)
                    return
                scan.status = 'running'
                db.session.commit()

                # 2. Discover hosts
                logger.info("Scan %s: discovering hosts on %s", scan_id, target_range)
                hosts = self.discover_hosts(target_range)
                logger.info("Scan %s: found %d hosts", scan_id, len(hosts))

                # 3. Scan each host
                device_info_list = []

                for host_info in hosts:
                    ip = host_info['ip']
                    logger.info("Scan %s: scanning ports on %s", scan_id, ip)

                    # Port scan
                    port_results = self.scan_ports(ip, scan_type)

                    # OS detection
                    os_info = self.detect_os(ip)

                    # Determine device type heuristic
                    device_type = _guess_device_type(
                        os_info.get('os_name', ''),
                        os_info.get('os_family', ''),
                        host_info.get('vendor', ''),
                        port_results,
                    )

                    # Create Device record
                    device = Device(
                        scan_id=scan_id,
                        ip_address=ip,
                        mac_address=host_info.get('mac'),
                        hostname=host_info.get('hostname'),
                        os_name=os_info.get('os_name'),
                        os_accuracy=os_info.get('os_accuracy'),
                        vendor=host_info.get('vendor'),
                        status=host_info.get('status', 'up'),
                        device_type=device_type,
                    )
                    db.session.add(device)
                    db.session.flush()  # get device.id without committing

                    device_info_list.append({
                        'device_id': device.id,
                        'ip_address': ip,
                        'ports': port_results,
                    })

                db.session.commit()

                # 4. Vulnerability assessment
                logger.info("Scan %s: running vulnerability assessment", scan_id)
                created_vulns = assess_vulnerabilities(device_info_list, scan_id)

                # 5. Calculate risk score
                logger.info("Scan %s: calculating risk score", scan_id)
                risk_score = calculate_network_risk(scan_id)

                # 6. Finalise scan record
                duration = time.time() - start_time
                scan = db.session.get(Scan, scan_id)
                scan.status = 'completed'
                scan.total_hosts = len(hosts)
                scan.total_vulns = len(created_vulns)
                scan.risk_score = risk_score
                scan.duration = round(duration, 2)
                scan.completed_at = datetime.now(timezone.utc)
                db.session.commit()

                logger.info(
                    "Scan %s completed in %.1fs -- hosts=%d, vulns=%d, risk=%.1f",
                    scan_id, duration, len(hosts), len(created_vulns), risk_score,
                )

            except Exception as exc:
                db.session.rollback()
                duration = time.time() - start_time
                logger.exception("Scan %s failed: %s", scan_id, exc)

                try:
                    scan = db.session.get(Scan, scan_id)
                    if scan:
                        scan.status = 'failed'
                        scan.error_message = str(exc)[:2000]
                        scan.duration = round(duration, 2)
                        scan.completed_at = datetime.now(timezone.utc)
                        db.session.commit()
                except Exception:
                    db.session.rollback()
                    logger.exception("Failed to update scan %s status to 'failed'", scan_id)


# ==========================================================================
# nmap-based implementations
# ==========================================================================

def _nmap_discover_hosts(target_range):
    """Host discovery using nmap -sn (ping scan)."""
    try:
        nm = nmap.PortScanner()
        nm.scan(hosts=target_range, arguments='-sn')
    except (nmap.PortScannerError, Exception) as exc:
        logger.error("nmap host discovery failed: %s", exc)
        return _fallback_discover_hosts(target_range)

    hosts = []
    for host in nm.all_hosts():
        host_data = nm[host]
        mac = ''
        vendor = ''

        addresses = host_data.get('addresses', {})
        mac = addresses.get('mac', '')

        vendor_info = host_data.get('vendor', {})
        if vendor_info:
            vendor = list(vendor_info.values())[0] if vendor_info.values() else ''

        hostnames = host_data.get('hostnames', [{}])
        hostname = hostnames[0].get('name', '') if hostnames else ''

        status = host_data.get('status', {}).get('state', 'up')

        hosts.append({
            'ip': host,
            'mac': mac,
            'hostname': hostname,
            'vendor': vendor,
            'status': status,
        })

    return hosts


def _nmap_scan_ports(host, ports):
    """Port scan using nmap -sT -sV."""
    try:
        nm = nmap.PortScanner()
        nm.scan(host, ports=ports, arguments='-sT -sV')
    except (nmap.PortScannerError, Exception) as exc:
        logger.error("nmap port scan failed for %s: %s", host, exc)
        return _fallback_scan_ports(host, ports)

    results = []
    if host not in nm.all_hosts():
        return results

    for proto in nm[host].all_protocols():
        port_list = sorted(nm[host][proto].keys())
        for port in port_list:
            port_info = nm[host][proto][port]
            results.append({
                'port': port,
                'protocol': proto,
                'state': port_info.get('state', 'unknown'),
                'service': port_info.get('name', ''),
                'version': port_info.get('version', ''),
            })

    return results


# ==========================================================================
# Fallback socket-based implementations (no nmap required)
# ==========================================================================

def _fallback_discover_hosts(target_range):
    """
    Simple host discovery by attempting TCP connections on the target /24 range in parallel.
    """
    import concurrent.futures

    # Parse the base network (assumes /24)
    base = target_range.split('/')[0]
    parts = base.split('.')
    if len(parts) != 4:
        logger.error("Cannot parse target range: %s", target_range)
        return []

    prefix = f"{parts[0]}.{parts[1]}.{parts[2]}"
    hosts = []

    def check_ip(ip):
        if _is_host_up(ip):
            hostname = _resolve_hostname(ip)
            return {
                'ip': ip,
                'mac': '',
                'hostname': hostname,
                'vendor': '',
                'status': 'up',
            }
        return None

    # Generate IP list, including localhost (127.0.0.1) as a guarantee
    ips = [f"{prefix}.{i}" for i in range(1, 255)]
    if '127.0.0.1' not in ips:
        ips.append('127.0.0.1')

    # Run checks concurrently (max 50 workers)
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(check_ip, ips)
        for res in results:
            if res:
                hosts.append(res)

    return hosts


def _fallback_scan_ports(host, ports_str):
    """
    Scan ports using plain sockets in parallel.  Parses the nmap-style port string
    (e.g. '22,80,443' or '1-1024').
    """
    import concurrent.futures
    port_list = _parse_port_string(ports_str)
    results = []

    def check_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                service = _guess_service(port)
                return {
                    'port': port,
                    'protocol': 'tcp',
                    'state': 'open',
                    'service': service,
                    'version': '',
                }
        except (socket.error, OSError):
            pass
        return None

    # Run checks concurrently (max 20 workers)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        res_list = executor.map(check_port, port_list)
        for res in res_list:
            if res:
                results.append(res)

    return results


# ==========================================================================
# Utility helpers
# ==========================================================================

def _get_local_ip():
    """Return the primary local IP address."""
    try:
        # This does not actually send data; it is used to determine the
        # outbound interface IP.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def _is_host_up(ip, timeout=0.3):
    """Quick connectivity check via TCP SYN to common ports."""
    for port in (80, 443, 22, 445, 139):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                return True
        except (socket.error, OSError):
            continue
    return False


def _resolve_hostname(ip):
    """Attempt reverse DNS lookup."""
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except (socket.herror, socket.gaierror, OSError):
        return ''


def _parse_port_string(ports_str):
    """
    Parse an nmap-style port string into a sorted list of unique port ints.
    Handles individual ports ('80'), ranges ('1-1024'), and comma-separated
    combinations ('22,80,443,1000-2000').
    """
    ports = set()
    for segment in ports_str.split(','):
        segment = segment.strip()
        if '-' in segment:
            try:
                low, high = segment.split('-', 1)
                for p in range(int(low), int(high) + 1):
                    ports.add(p)
            except ValueError:
                continue
        else:
            try:
                ports.add(int(segment))
            except ValueError:
                continue
    return sorted(ports)


def _guess_service(port):
    """Return a common service name for well-known ports."""
    _COMMON = {
        20: 'ftp-data', 21: 'ftp', 22: 'ssh', 23: 'telnet', 25: 'smtp',
        53: 'domain', 80: 'http', 110: 'pop3', 135: 'msrpc', 139: 'netbios-ssn',
        143: 'imap', 161: 'snmp', 443: 'https', 445: 'microsoft-ds',
        993: 'imaps', 995: 'pop3s', 1433: 'ms-sql-s', 1521: 'oracle',
        3306: 'mysql', 3389: 'ms-wbt-server', 5432: 'postgresql',
        5900: 'vnc', 6379: 'redis', 8080: 'http-proxy', 8443: 'https-alt',
        27017: 'mongod',
    }
    return _COMMON.get(port, 'unknown')


def _guess_device_type(os_name, os_family, vendor, ports):
    """
    Heuristically guess the device type from OS / vendor / port information.
    """
    os_lower = (os_name or '').lower()
    family_lower = (os_family or '').lower()
    vendor_lower = (vendor or '').lower()
    open_ports = {p['port'] for p in ports if p.get('state') == 'open'}

    # Router / gateway indicators
    router_vendors = ['cisco', 'mikrotik', 'ubiquiti', 'netgear', 'tp-link',
                       'asus', 'linksys', 'd-link', 'zyxel', 'juniper']
    if any(rv in vendor_lower for rv in router_vendors):
        return 'router'
    if 'router' in os_lower or 'ios' in os_lower:
        return 'router'

    # Printer
    if 'printer' in os_lower or 'print' in vendor_lower:
        return 'printer'
    if 9100 in open_ports or 631 in open_ports:
        return 'printer'

    # IoT
    iot_vendors = ['espressif', 'raspberry', 'arduino', 'tuya',
                   'philips hue', 'ring', 'nest', 'sonos']
    if any(iv in vendor_lower for iv in iot_vendors):
        return 'iot'

    # Phone / mobile
    if 'android' in os_lower or 'ios' in family_lower:
        return 'phone'
    phone_vendors = ['apple', 'samsung', 'huawei', 'xiaomi', 'oneplus', 'google']
    if any(pv in vendor_lower for pv in phone_vendors):
        return 'phone'

    # Server indicators
    server_ports = {25, 53, 80, 443, 3306, 5432, 8080, 8443}
    if len(open_ports & server_ports) >= 3:
        return 'server'
    if 'server' in os_lower:
        return 'server'

    # Windows / Linux / Mac desktops
    if 'windows' in os_lower:
        return 'desktop'
    if 'linux' in os_lower or 'ubuntu' in os_lower or 'debian' in os_lower:
        return 'laptop'
    if 'mac' in os_lower or 'darwin' in os_lower:
        return 'laptop'

    return 'unknown'
