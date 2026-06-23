import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const riskColors = { critical: '#ff3366', high: '#ff6b35', medium: '#ffb800', low: '#00d4ff', info: '#8b8fa3' };

function PortAnalysisChart({ data = [] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis type="number" stroke="#8b8fa3" fontSize={11} />
        <YAxis type="category" dataKey="service" stroke="#8b8fa3" fontSize={11} width={80} />
        <Tooltip contentStyle={{ background: '#131738', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
          labelStyle={{ color: '#e4e6f0' }} itemStyle={{ color: '#00d4ff' }} />
        <Bar dataKey="count" radius={[0, 4, 4, 0]} animationDuration={800}>
          {data.map((entry, i) => (
            <Cell key={i} fill={riskColors[entry.risk] || '#00d4ff'} fillOpacity={0.8} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export default PortAnalysisChart;
