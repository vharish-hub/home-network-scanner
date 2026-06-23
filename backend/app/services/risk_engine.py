"""
Risk Engine Service — Network and Device Security Scoring.

Calculates quantitative risk scores for individual devices and entire
network scans based on vulnerability severity, exploit availability,
and dangerous-port exposure.
"""

import logging

from app.extensions import db
from app.models.device import Device
from app.models.vulnerability import Vulnerability

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Severity weight table
# ---------------------------------------------------------------------------
SEVERITY_WEIGHTS = {
    'critical': 10,
    'high': 7,
    'medium': 4,
    'low': 1,
    'info': 0,
}

# Ports considered inherently dangerous regardless of service version
_DANGEROUS_PORT_SET = {
    21, 23, 25, 110, 135, 139, 161, 445,
    1433, 1521, 3306, 3389, 5432, 5900,
    6379, 27017,
}


def calculate_device_risk(device):
    """
    Calculate a security risk score (0–100) for a single device.

    The score represents *security health*: 100 = perfectly secure, 0 = critical risk.

    Scoring algorithm:
      1. Sum weighted vulnerability scores using SEVERITY_WEIGHTS.
      2. Add bonus penalty for each vulnerability with a known exploit.
      3. Add penalty for each open dangerous port.
      4. Normalise the raw penalty against a calibration factor and
         clamp to [0, 100].

    Args:
        device: A Device ORM object with its vulnerabilities relationship loaded.

    Returns:
        float: Risk score between 0.0 and 100.0 (higher = more secure).
    """
    vulnerabilities = device.vulnerabilities if device.vulnerabilities else []

    if not vulnerabilities:
        # No vulnerabilities — still penalise if dangerous ports exist
        dangerous_ports_open = _count_dangerous_ports(vulnerabilities)
        return max(0.0, 100.0 - dangerous_ports_open * 2.0)

    # --- Weighted vulnerability sum ---
    weighted_sum = 0.0
    exploit_penalty = 0.0

    for vuln in vulnerabilities:
        severity = (vuln.severity or 'info').lower()
        weight = SEVERITY_WEIGHTS.get(severity, 0)
        weighted_sum += weight

        if vuln.exploit_available:
            exploit_penalty += weight * 0.5  # 50 % extra for exploitable vulns

    # --- Dangerous-port penalty ---
    dangerous_ports_open = _count_dangerous_ports(vulnerabilities)
    port_penalty = dangerous_ports_open * 3.0

    total_penalty = weighted_sum + exploit_penalty + port_penalty

    # Normalisation factor: calibrated so that ~20 medium-severity vulns ≈ 0 score
    normalization_factor = 80.0

    score = max(0.0, 100.0 - (total_penalty / normalization_factor * 100.0))
    return round(min(score, 100.0), 1)


def calculate_network_risk(scan_id):
    """
    Calculate an overall network security score for a completed scan.

    Algorithm:
      1. Retrieve all devices and vulnerabilities for the scan.
      2. Compute each device's risk score.
      3. Calculate a weighted average where devices with more vulnerabilities
         have proportionally more influence.
      4. Apply global penalties:
         - Any critical vulnerability lowers the score by up to 15 points.
         - Any exploitable vulnerability lowers the score by up to 10 points.

    Args:
        scan_id: Integer scan ID.

    Returns:
        float: Network risk score between 0.0 and 100.0 (higher = more secure).
    """
    devices = Device.query.filter_by(scan_id=scan_id).all()

    if not devices:
        return 100.0  # No devices found — nothing at risk

    all_vulns = Vulnerability.query.filter_by(scan_id=scan_id).all()

    # Build per-device risk scores
    device_scores = []
    device_vuln_counts = []

    for device in devices:
        score = calculate_device_risk(device)
        vuln_count = len(device.vulnerabilities) if device.vulnerabilities else 0
        device_scores.append(score)
        device_vuln_counts.append(max(vuln_count, 1))  # minimum weight of 1

    # Weighted average
    total_weight = sum(device_vuln_counts)
    if total_weight == 0:
        weighted_avg = 100.0
    else:
        weighted_avg = sum(
            s * w for s, w in zip(device_scores, device_vuln_counts)
        ) / total_weight

    # --- Global penalties ---
    has_critical = any(
        (v.severity or '').lower() == 'critical' for v in all_vulns
    )
    has_exploit = any(v.exploit_available for v in all_vulns)

    critical_count = sum(
        1 for v in all_vulns if (v.severity or '').lower() == 'critical'
    )
    exploit_count = sum(1 for v in all_vulns if v.exploit_available)

    critical_penalty = min(15.0, critical_count * 3.0) if has_critical else 0.0
    exploit_penalty = min(10.0, exploit_count * 2.0) if has_exploit else 0.0

    network_score = max(0.0, weighted_avg - critical_penalty - exploit_penalty)
    network_score = round(min(network_score, 100.0), 1)

    logger.info(
        "Network risk score for scan %s: %.1f (devices=%d, vulns=%d, "
        "critical_penalty=%.1f, exploit_penalty=%.1f)",
        scan_id, network_score, len(devices), len(all_vulns),
        critical_penalty, exploit_penalty,
    )

    return network_score


def get_risk_level(score):
    """
    Convert a numeric security score to a human-readable risk label.

    Args:
        score: Float between 0 and 100.

    Returns:
        str: One of 'Critical', 'High', 'Medium', 'Low', 'Secure'.
    """
    if score is None:
        return 'Unknown'
    score = float(score)
    if score <= 25:
        return 'Critical'
    if score <= 50:
        return 'High'
    if score <= 75:
        return 'Medium'
    if score <= 90:
        return 'Low'
    return 'Secure'


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _count_dangerous_ports(vulnerabilities):
    """Count unique dangerous ports referenced in a vulnerability list."""
    ports_seen = set()
    for vuln in vulnerabilities:
        if vuln.port and vuln.port in _DANGEROUS_PORT_SET:
            ports_seen.add(vuln.port)
    return len(ports_seen)
