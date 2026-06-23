import React from 'react';

const severityConfig = {
  critical: { color: '#ff3366', bg: 'rgba(255,51,102,0.15)' },
  high: { color: '#ff6b35', bg: 'rgba(255,107,53,0.15)' },
  medium: { color: '#ffb800', bg: 'rgba(255,184,0,0.15)' },
  low: { color: '#00d4ff', bg: 'rgba(0,212,255,0.15)' },
  info: { color: '#8b8fa3', bg: 'rgba(139,143,163,0.15)' },
};

function SeverityBadge({ severity }) {
  const config = severityConfig[severity?.toLowerCase()] || severityConfig.info;
  return (
    <span className="severity-badge" style={{
      color: config.color, background: config.bg,
      padding: '3px 10px', borderRadius: '4px', fontSize: '0.75rem',
      fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px',
      boxShadow: `0 0 8px ${config.color}33`,
    }}>
      {severity || 'info'}
    </span>
  );
}

export default SeverityBadge;
