"""PDF and HTML report generation with CSV/JSON export."""
import csv
import json
import os
from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)

from app.extensions import db
from app.models import Scan, Device, Vulnerability

# Color scheme
NAVY = colors.HexColor('#0a0e27')
DARK_BLUE = colors.HexColor('#131738')
ACCENT_BLUE = colors.HexColor('#00d4ff')
ACCENT_GREEN = colors.HexColor('#00ff88')
WARNING_AMBER = colors.HexColor('#ffb800')
DANGER_RED = colors.HexColor('#ff3366')
WHITE = colors.white
LIGHT_GRAY = colors.HexColor('#e4e6f0')
GRAY = colors.HexColor('#8b8fa3')

SEVERITY_COLORS = {
    'critical': DANGER_RED,
    'high': colors.HexColor('#ff6b35'),
    'medium': WARNING_AMBER,
    'low': ACCENT_BLUE,
    'info': GRAY
}


class PDFReportGenerator:
    """Generate professional PDF security reports using ReportLab."""

    def __init__(self, scan, devices, vulnerabilities, risk_score):
        self.scan = scan
        self.devices = devices
        self.vulnerabilities = vulnerabilities
        self.risk_score = risk_score
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Define custom paragraph styles for the report."""
        self.styles.add(ParagraphStyle(
            'ReportTitle', parent=self.styles['Title'],
            fontSize=28, textColor=NAVY, spaceAfter=6, alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            'ReportSubtitle', parent=self.styles['Normal'],
            fontSize=14, textColor=GRAY, spaceAfter=20, alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            'SectionHeader', parent=self.styles['Heading1'],
            fontSize=16, textColor=NAVY, spaceBefore=20, spaceAfter=10,
            borderWidth=1, borderColor=ACCENT_BLUE, borderPadding=5
        ))
        self.styles.add(ParagraphStyle(
            'SubSection', parent=self.styles['Heading2'],
            fontSize=13, textColor=DARK_BLUE, spaceBefore=12, spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            'BodyText2', parent=self.styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#333333'), spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            'SmallText', parent=self.styles['Normal'],
            fontSize=8, textColor=GRAY
        ))

    def _header_footer(self, canvas, doc):
        """Add header and footer to each page."""
        canvas.saveState()
        # Header line
        canvas.setStrokeColor(ACCENT_BLUE)
        canvas.setLineWidth(2)
        canvas.line(30, A4[1] - 40, A4[0] - 30, A4[1] - 40)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(GRAY)
        canvas.drawString(30, A4[1] - 35, "Network Vulnerability Scanner - Security Report")

        # Footer
        canvas.setStrokeColor(ACCENT_BLUE)
        canvas.line(30, 40, A4[0] - 30, 40)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(30, 28, f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        canvas.drawRightString(A4[0] - 30, 28, f"Page {doc.page}")
        canvas.restoreState()

    def generate(self, output_path):
        """Generate the complete PDF report."""
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            topMargin=50, bottomMargin=50,
            leftMargin=30, rightMargin=30
        )
        elements = []

        # Cover Page
        elements.append(Spacer(1, 100))
        elements.append(Paragraph("🛡️ NETWORK SECURITY REPORT", self.styles['ReportTitle']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Home Network Vulnerability Assessment", self.styles['ReportSubtitle']))
        elements.append(Spacer(1, 30))

        cover_data = [
            ['Scan Date', self.scan.scan_date.strftime('%Y-%m-%d %H:%M') if self.scan.scan_date else 'N/A'],
            ['Target Range', self.scan.target_range or 'N/A'],
            ['Scan Type', (self.scan.scan_type or 'quick').title()],
            ['Security Score', f"{self.risk_score:.0f}/100"],
        ]
        cover_table = Table(cover_data, colWidths=[150, 300])
        cover_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), NAVY),
            ('TEXTCOLOR', (0, 0), (0, -1), WHITE),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f0f2ff')),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, ACCENT_BLUE),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(cover_table)
        elements.append(PageBreak())

        # Executive Summary
        elements.append(Paragraph("1. Executive Summary", self.styles['SectionHeader']))
        severity_counts = {}
        for v in self.vulnerabilities:
            sev = v.severity or 'info'
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        summary_text = (
            f"This report presents the findings of a network vulnerability assessment conducted on "
            f"<b>{self.scan.target_range}</b>. The scan discovered <b>{len(self.devices)} devices</b> "
            f"and identified <b>{len(self.vulnerabilities)} vulnerabilities</b>. "
            f"The overall network security score is <b>{self.risk_score:.0f}/100</b>."
        )
        elements.append(Paragraph(summary_text, self.styles['BodyText2']))
        elements.append(Spacer(1, 10))

        summary_data = [['Severity', 'Count']]
        for sev in ['critical', 'high', 'medium', 'low', 'info']:
            summary_data.append([sev.title(), str(severity_counts.get(sev, 0))])
        summary_table = Table(summary_data, colWidths=[200, 100])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9ff')]),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 15))

        # Scan Information
        elements.append(Paragraph("2. Scan Information", self.styles['SectionHeader']))
        scan_data = [
            ['Parameter', 'Value'],
            ['Scan ID', str(self.scan.id)],
            ['Date', self.scan.scan_date.strftime('%Y-%m-%d %H:%M:%S UTC') if self.scan.scan_date else 'N/A'],
            ['Target Range', self.scan.target_range or 'N/A'],
            ['Scan Type', (self.scan.scan_type or 'quick').title()],
            ['Status', (self.scan.status or 'unknown').title()],
            ['Duration', f"{self.scan.duration:.1f}s" if self.scan.duration else 'N/A'],
            ['Hosts Found', str(len(self.devices))],
            ['Vulnerabilities', str(len(self.vulnerabilities))],
        ]
        scan_table = Table(scan_data, colWidths=[200, 300])
        scan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9ff')]),
        ]))
        elements.append(scan_table)
        elements.append(Spacer(1, 15))

        # Device Inventory
        elements.append(Paragraph("3. Device Inventory", self.styles['SectionHeader']))
        device_data = [['IP Address', 'Hostname', 'OS', 'Vendor', 'Status']]
        for d in self.devices:
            device_data.append([
                d.ip_address or '', d.hostname or 'Unknown',
                d.os_name or 'Unknown', d.vendor or 'Unknown',
                (d.status or 'up').title()
            ])
        device_table = Table(device_data, colWidths=[100, 120, 120, 100, 60])
        device_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9ff')]),
        ]))
        elements.append(device_table)
        elements.append(Spacer(1, 15))

        # Vulnerability Details
        elements.append(Paragraph("4. Vulnerability Details", self.styles['SectionHeader']))
        sorted_vulns = sorted(self.vulnerabilities,
                              key=lambda v: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}.get(v.severity, 5))
        for vuln in sorted_vulns:
            sev = (vuln.severity or 'info').upper()
            elements.append(Paragraph(
                f"[{sev}] {vuln.title or 'Untitled'}",
                self.styles['SubSection']
            ))
            vuln_details = []
            if vuln.cve_id:
                vuln_details.append(f"<b>CVE:</b> {vuln.cve_id}")
            if vuln.cvss_score is not None:
                vuln_details.append(f"<b>CVSS Score:</b> {vuln.cvss_score}")
            if vuln.port:
                vuln_details.append(f"<b>Port:</b> {vuln.port}/{vuln.protocol or 'tcp'}")
            if vuln.service:
                svc = vuln.service
                if vuln.version:
                    svc += f" {vuln.version}"
                vuln_details.append(f"<b>Service:</b> {svc}")
            for detail in vuln_details:
                elements.append(Paragraph(detail, self.styles['BodyText2']))
            if vuln.description:
                elements.append(Paragraph(f"<b>Description:</b> {vuln.description}", self.styles['BodyText2']))
            if vuln.recommendation:
                elements.append(Paragraph(f"<b>Recommendation:</b> {vuln.recommendation}", self.styles['BodyText2']))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
            elements.append(Spacer(1, 5))

        # Risk Analysis
        elements.append(PageBreak())
        elements.append(Paragraph("5. Risk Analysis", self.styles['SectionHeader']))
        if self.risk_score >= 76:
            risk_label = "Low Risk"
            risk_desc = "The network is in good condition with minor improvements recommended."
        elif self.risk_score >= 51:
            risk_label = "Medium Risk"
            risk_desc = "Several vulnerabilities require attention to improve security posture."
        elif self.risk_score >= 26:
            risk_label = "High Risk"
            risk_desc = "Significant vulnerabilities detected. Immediate action required."
        else:
            risk_label = "Critical Risk"
            risk_desc = "The network has severe security issues requiring urgent remediation."

        elements.append(Paragraph(f"<b>Network Security Score: {self.risk_score:.0f}/100 ({risk_label})</b>", self.styles['BodyText2']))
        elements.append(Paragraph(risk_desc, self.styles['BodyText2']))
        elements.append(Spacer(1, 15))

        # Security Recommendations
        elements.append(Paragraph("6. Security Recommendations", self.styles['SectionHeader']))
        recommendations_by_sev = {}
        for v in sorted_vulns:
            if v.recommendation:
                sev = v.severity or 'info'
                if sev not in recommendations_by_sev:
                    recommendations_by_sev[sev] = []
                if v.recommendation not in recommendations_by_sev[sev]:
                    recommendations_by_sev[sev].append(v.recommendation)

        for sev in ['critical', 'high', 'medium', 'low', 'info']:
            recs = recommendations_by_sev.get(sev, [])
            if recs:
                elements.append(Paragraph(f"<b>{sev.title()} Priority:</b>", self.styles['SubSection']))
                for rec in recs:
                    elements.append(Paragraph(f"• {rec}", self.styles['BodyText2']))
                elements.append(Spacer(1, 8))

        # Conclusion
        elements.append(Paragraph("7. Conclusion", self.styles['SectionHeader']))
        elements.append(Paragraph(
            f"This assessment identified {len(self.vulnerabilities)} vulnerabilities across "
            f"{len(self.devices)} network devices. The overall security score of {self.risk_score:.0f}/100 "
            f"indicates a {risk_label.lower()} level. It is recommended to address critical and high "
            f"severity findings immediately and schedule regular scans to maintain security posture.",
            self.styles['BodyText2']
        ))

        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        return output_path


class HTMLReportGenerator:
    """Generate styled HTML security reports."""

    def __init__(self, scan, devices, vulnerabilities, risk_score):
        self.scan = scan
        self.devices = devices
        self.vulnerabilities = vulnerabilities
        self.risk_score = risk_score

    def _severity_color(self, severity):
        colors_map = {
            'critical': '#ff3366', 'high': '#ff6b35',
            'medium': '#ffb800', 'low': '#00d4ff', 'info': '#8b8fa3'
        }
        return colors_map.get(severity, '#8b8fa3')

    def generate(self, output_path):
        """Generate complete styled HTML report."""
        severity_counts = {}
        for v in self.vulnerabilities:
            sev = v.severity or 'info'
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        sorted_vulns = sorted(self.vulnerabilities,
                              key=lambda v: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}.get(v.severity, 5))

        if self.risk_score >= 76:
            risk_label, score_color = "Low Risk", "#00ff88"
        elif self.risk_score >= 51:
            risk_label, score_color = "Medium Risk", "#ffb800"
        elif self.risk_score >= 26:
            risk_label, score_color = "High Risk", "#ff6b35"
        else:
            risk_label, score_color = "Critical Risk", "#ff3366"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Network Security Report - {self.scan.target_range}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0e27; color: #e4e6f0; padding: 40px; }}
.container {{ max-width: 1000px; margin: 0 auto; }}
h1 {{ font-size: 2rem; margin-bottom: 8px; color: #00d4ff; }}
h2 {{ font-size: 1.4rem; color: #00d4ff; margin: 30px 0 15px; padding-bottom: 8px; border-bottom: 2px solid rgba(0,212,255,0.3); }}
h3 {{ font-size: 1.1rem; color: #e4e6f0; margin: 15px 0 8px; }}
p {{ line-height: 1.7; margin-bottom: 10px; color: #b0b3c6; }}
.header {{ text-align: center; padding: 40px 0; border-bottom: 2px solid rgba(0,212,255,0.2); margin-bottom: 30px; }}
.header .subtitle {{ color: #8b8fa3; font-size: 1.1rem; }}
.score-box {{ display: inline-block; background: rgba(19,23,56,0.8); border: 2px solid {score_color}; border-radius: 12px; padding: 20px 40px; margin: 20px 0; text-align: center; }}
.score-box .score {{ font-size: 3rem; font-weight: 700; color: {score_color}; }}
.score-box .label {{ color: #8b8fa3; font-size: 0.9rem; }}
table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
th {{ background: #131738; color: #00d4ff; padding: 10px 12px; text-align: left; font-size: 0.9rem; }}
td {{ padding: 8px 12px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.9rem; }}
tr:hover {{ background: rgba(0,212,255,0.03); }}
.badge {{ display: inline-block; padding: 3px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
.badge-critical {{ background: rgba(255,51,102,0.2); color: #ff3366; }}
.badge-high {{ background: rgba(255,107,53,0.2); color: #ff6b35; }}
.badge-medium {{ background: rgba(255,184,0,0.2); color: #ffb800; }}
.badge-low {{ background: rgba(0,212,255,0.2); color: #00d4ff; }}
.badge-info {{ background: rgba(139,143,163,0.2); color: #8b8fa3; }}
.vuln-card {{ background: rgba(19,23,56,0.6); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 15px; margin: 10px 0; }}
.vuln-card .meta {{ color: #8b8fa3; font-size: 0.85rem; margin-top: 5px; }}
.rec {{ padding: 8px 15px; margin: 5px 0; background: rgba(0,212,255,0.05); border-left: 3px solid #00d4ff; border-radius: 0 4px 4px 0; }}
.footer {{ text-align: center; padding: 30px 0; margin-top: 40px; border-top: 1px solid rgba(255,255,255,0.05); color: #8b8fa3; font-size: 0.8rem; }}
@media print {{ body {{ background: white; color: #333; }} th {{ background: #1a237e; color: white; }} }}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>🛡️ Network Security Report</h1>
<p class="subtitle">Home Network Vulnerability Assessment</p>
<div class="score-box">
<div class="score">{self.risk_score:.0f}/100</div>
<div class="label">{risk_label}</div>
</div>
</div>

<h2>1. Executive Summary</h2>
<p>Scan of <strong>{self.scan.target_range}</strong> discovered <strong>{len(self.devices)} devices</strong>
and <strong>{len(self.vulnerabilities)} vulnerabilities</strong>.</p>
<table>
<tr><th>Severity</th><th>Count</th></tr>
{"".join(f'<tr><td><span class="badge badge-{s}">{s.title()}</span></td><td>{severity_counts.get(s, 0)}</td></tr>' for s in ['critical','high','medium','low','info'])}
</table>

<h2>2. Scan Information</h2>
<table>
<tr><th>Parameter</th><th>Value</th></tr>
<tr><td>Scan Date</td><td>{self.scan.scan_date.strftime('%Y-%m-%d %H:%M UTC') if self.scan.scan_date else 'N/A'}</td></tr>
<tr><td>Target Range</td><td>{self.scan.target_range}</td></tr>
<tr><td>Scan Type</td><td>{(self.scan.scan_type or 'quick').title()}</td></tr>
<tr><td>Duration</td><td>{f'{self.scan.duration:.1f}s' if self.scan.duration else 'N/A'}</td></tr>
</table>

<h2>3. Device Inventory</h2>
<table>
<tr><th>IP Address</th><th>Hostname</th><th>OS</th><th>Vendor</th><th>Status</th></tr>
{"".join(f'<tr><td>{d.ip_address}</td><td>{d.hostname or "Unknown"}</td><td>{d.os_name or "Unknown"}</td><td>{d.vendor or "Unknown"}</td><td>{(d.status or "up").title()}</td></tr>' for d in self.devices)}
</table>

<h2>4. Vulnerability Details</h2>
{"".join(self._vuln_card_html(v) for v in sorted_vulns)}

<h2>5. Conclusion</h2>
<p>This assessment identified {len(self.vulnerabilities)} vulnerabilities across {len(self.devices)} devices.
The security score of {self.risk_score:.0f}/100 indicates {risk_label.lower()}. Address critical and high
severity findings immediately.</p>

<div class="footer">
<p>Generated by Network Vulnerability Scanner | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
</div>
</div>
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path

    def _vuln_card_html(self, vuln):
        sev = vuln.severity or 'info'
        return f"""<div class="vuln-card">
<span class="badge badge-{sev}">{sev.title()}</span>
<h3>{vuln.title or 'Untitled'}</h3>
<div class="meta">
{f'CVE: {vuln.cve_id} | ' if vuln.cve_id else ''}
{f'CVSS: {vuln.cvss_score} | ' if vuln.cvss_score else ''}
{f'Port: {vuln.port}/{vuln.protocol or "tcp"} | ' if vuln.port else ''}
{f'Service: {vuln.service}' if vuln.service else ''}
</div>
{f'<p>{vuln.description}</p>' if vuln.description else ''}
{f'<div class="rec"><strong>Recommendation:</strong> {vuln.recommendation}</div>' if vuln.recommendation else ''}
</div>"""


def export_csv(scan_id, output_path):
    """Export vulnerability data as CSV."""
    vulns = Vulnerability.query.filter_by(scan_id=scan_id).all()
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Device IP', 'Port', 'Protocol', 'Service', 'Version',
                         'CVE ID', 'Title', 'Severity', 'CVSS Score', 'Description', 'Recommendation'])
        for v in vulns:
            device = db.session.get(Device, v.device_id)
            writer.writerow([
                v.id, device.ip_address if device else '', v.port, v.protocol,
                v.service, v.version, v.cve_id, v.title, v.severity,
                v.cvss_score, v.description, v.recommendation
            ])
    return output_path


def export_json(scan_id, output_path):
    """Export full scan data as JSON."""
    scan = db.session.get(Scan, scan_id)
    if not scan:
        return None
    devices = Device.query.filter_by(scan_id=scan_id).all()
    vulns = Vulnerability.query.filter_by(scan_id=scan_id).all()

    data = {
        'scan': scan.to_dict(),
        'devices': [d.to_dict() for d in devices],
        'vulnerabilities': [v.to_dict() for v in vulns],
        'generated_at': datetime.now(timezone.utc).isoformat()
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    return output_path
