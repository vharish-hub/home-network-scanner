import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: '#131738', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '10px 14px' }}>
        <p style={{ color: '#e4e6f0', fontWeight: 600, marginBottom: 4 }}>{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color, margin: '2px 0', fontSize: '0.85rem' }}>
            {p.name}: {p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

function DeviceVulnBarChart({ data = [] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} barGap={2}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="device" stroke="#8b8fa3" fontSize={11} angle={-20} textAnchor="end" height={60} />
        <YAxis stroke="#8b8fa3" fontSize={11} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ color: '#8b8fa3', fontSize: '0.85rem' }} />
        <Bar dataKey="critical" stackId="a" fill="#ff3366" radius={[0,0,0,0]} />
        <Bar dataKey="high" stackId="a" fill="#ff6b35" />
        <Bar dataKey="medium" stackId="a" fill="#ffb800" />
        <Bar dataKey="low" stackId="a" fill="#00d4ff" radius={[4,4,0,0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export default DeviceVulnBarChart;
