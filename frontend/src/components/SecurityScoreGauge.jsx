import React, { useEffect, useState } from 'react';

function SecurityScoreGauge({ score = 0, size = 180, label = 'Security Score' }) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (animatedScore / 100) * circumference;
  const offset = circumference - progress;

  useEffect(() => {
    let start = 0;
    const step = score / 40;
    const timer = setInterval(() => {
      start += step;
      if (start >= score) { setAnimatedScore(score); clearInterval(timer); }
      else { setAnimatedScore(Math.round(start)); }
    }, 20);
    return () => clearInterval(timer);
  }, [score]);

  const getColor = (s) => {
    if (s >= 76) return '#00ff88';
    if (s >= 51) return '#ffb800';
    if (s >= 26) return '#ff6b35';
    return '#ff3366';
  };

  const color = getColor(animatedScore);

  return (
    <div className="score-gauge" style={{ textAlign: 'center' }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
          transform={`rotate(-90 ${size/2} ${size/2})`}
          style={{ transition: 'stroke-dashoffset 0.8s ease, stroke 0.5s ease', filter: `drop-shadow(0 0 6px ${color}66)` }} />
        <text x="50%" y="45%" textAnchor="middle" fill={color} fontSize={size * 0.22} fontWeight="700"
          fontFamily="'Inter', sans-serif">{animatedScore}</text>
        <text x="50%" y="62%" textAnchor="middle" fill="#8b8fa3" fontSize={size * 0.08}
          fontFamily="'Inter', sans-serif">{label}</text>
      </svg>
    </div>
  );
}

export default SecurityScoreGauge;
