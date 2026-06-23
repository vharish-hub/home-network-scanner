from datetime import datetime, timezone
from app.extensions import db


class Scan(db.Model):
    """Scan model to track network scan sessions."""
    __tablename__ = 'scans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    scan_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    scan_type = db.Column(db.String(50), default='quick', nullable=False)  # quick, full, custom
    target_range = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    # Status: pending, running, completed, failed, cancelled
    total_hosts = db.Column(db.Integer, default=0)
    total_vulns = db.Column(db.Integer, default=0)
    risk_score = db.Column(db.Float, default=0.0)
    duration = db.Column(db.Float, nullable=True)  # Duration in seconds
    completed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    # Relationships
    devices = db.relationship('Device', backref='scan', lazy=True, cascade='all, delete-orphan')
    vulnerabilities = db.relationship('Vulnerability', backref='scan', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """Serialize scan to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'scan_date': self.scan_date.isoformat() if self.scan_date else None,
            'scan_type': self.scan_type,
            'target_range': self.target_range,
            'status': self.status,
            'total_hosts': self.total_hosts,
            'total_vulns': self.total_vulns,
            'risk_score': self.risk_score,
            'duration': self.duration,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
        }

    def __repr__(self):
        return f'<Scan {self.id} - {self.status}>'
