import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = { Critical: '#ff3366', High: '#ff6b35', Medium: '#ffb800', Low: '#00d4ff', Info: '#8b8fa3' };

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: '#131738', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '10px 14px' }}>
        <p style={{ color: payload[0].payload.color || '#e4e6f0', margin: 0, fontWeight: 600 }}>
          {payload[0].name}: {payload[0].value}
        </p>
      </div>
    );
  }
  return null;
};

function SeverityPieChart({ data = [] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie data={data} cx="50%" cy="50%" outerRadius={100} innerRadius={50} paddingAngle={3}
          dataKey="value" animationBegin={0} animationDuration={800}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.color || COLORS[entry.name] || '#8b8fa3'} stroke="none" />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ color: '#8b8fa3', fontSize: '0.85rem' }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export default SeverityPieChart;
