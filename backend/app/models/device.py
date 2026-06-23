from app.extensions import db


class Device(db.Model):
    """Device model representing a discovered network device."""
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False)  # Supports IPv6
    mac_address = db.Column(db.String(17), nullable=True)
    hostname = db.Column(db.String(255), nullable=True)
    os_name = db.Column(db.String(255), nullable=True)
    os_accuracy = db.Column(db.Integer, nullable=True)
    vendor = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='up', nullable=False)  # up, down
    device_type = db.Column(db.String(100), nullable=True)  # router, laptop, phone, iot, etc.

    # Relationships
    vulnerabilities = db.relationship('Vulnerability', backref='device', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """Serialize device to dictionary."""
        return {
            'id': self.id,
            'scan_id': self.scan_id,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'hostname': self.hostname,
            'os_name': self.os_name,
            'os_accuracy': self.os_accuracy,
            'vendor': self.vendor,
            'status': self.status,
            'device_type': self.device_type,
            'vulnerability_count': len(self.vulnerabilities) if self.vulnerabilities else 0,
        }

    def __repr__(self):
        return f'<Device {self.ip_address} - {self.hostname}>'
