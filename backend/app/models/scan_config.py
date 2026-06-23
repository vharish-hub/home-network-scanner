from datetime import datetime, timezone
from app.extensions import db


class ScanConfig(db.Model):
    """Scan configuration model for saved scan presets."""
    __tablename__ = 'scan_configs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    target_range = db.Column(db.String(100), nullable=False)
    scan_type = db.Column(db.String(50), default='quick', nullable=False)
    ports = db.Column(db.String(500), nullable=True)  # Custom port ranges
    is_scheduled = db.Column(db.Boolean, default=False)
    schedule_cron = db.Column(db.String(100), nullable=True)
    email_notify = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        """Serialize scan config to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'target_range': self.target_range,
            'scan_type': self.scan_type,
            'ports': self.ports,
            'is_scheduled': self.is_scheduled,
            'schedule_cron': self.schedule_cron,
            'email_notify': self.email_notify,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<ScanConfig {self.name}>'
