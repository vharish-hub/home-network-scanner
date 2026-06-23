import React, { useState, useEffect } from 'react';
import { FiMonitor, FiAlertTriangle, FiAlertOctagon, FiActivity, FiClock } from 'react-icons/fi';
import SecurityScoreGauge from '../components/SecurityScoreGauge';
import SeverityPieChart from '../components/charts/SeverityPieChart';
import DeviceVulnBarChart from '../components/charts/DeviceVulnBarChart';
import PortAnalysisChart from '../components/charts/PortAnalysisChart';
import LoadingSpinner from '../components/LoadingSpinner';
import SeverityBadge from '../components/SeverityBadge';
import dashboardService from '../services/dashboardService';

function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [severityData, setSeverityData] = useState([]);
  const [deviceVulns, setDeviceVulns] = useState([]);
  const [portData, setPortData] = useState([]);
  const [recentScans, setRecentScans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sumRes, sevRes, devRes, portRes, scanRes] = await Promise.all([
          dashboardService.getSummary(),
          dashboardService.getSeverityDistribution(),
          dashboardService.getDeviceVulns(),
          dashboardService.getPortAnalysis(),
          dashboardService.getRecentScans(),
        ]);
        setSummary(sumRes.data?.data || sumRes.data);
        setSeverityData(sevRes.data?.data || []);
        setDeviceVulns(devRes.data?.data || []);
        setPortData(portRes.data?.data || []);
        setRecentScans(scanRes.data?.data || scanRes.data?.scans || []);
      } catch (err) { console.error('Dashboard load error:', err); }
      finally { setLoading(false); }
    };
    fetchData();
  }, []);

  if (loading) return <LoadingSpinner text="Loading dashboard..." />;

  const stats = [
    { icon: FiMonitor, label: 'Total Devices', value: summary?.total_devices || 0, color: '#00d4ff' },
    { icon: FiAlertTriangle, label: 'Vulnerabilities', value: summary?.total_vulnerabilities || 0, color: '#ffb800' },
    { icon: FiAlertOctagon, label: 'Critical Issues', value: summary?.critical_issues || 0, color: '#ff3366' },
    { icon: FiActivity, label: 'Total Scans', value: summary?.total_scans || 0, color: '#00ff88' },
  ];

  return (
    <div className="dashboard-page">
      <h1 className="page-title">Dashboard</h1>

      {/* Stat Cards */}
      <div className="stats-grid">
        {stats.map(({ icon: Icon, label, value, color }, i) => (
          <div key={i} className="stat-card glass-card">
            <div className="stat-icon" style={{ background: `${color}15`, color }}><Icon size={22} /></div>
            <div className="stat-info">
              <div className="stat-value" style={{ color }}>{value}</div>
              <div className="stat-label">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Security Score */}
      <div className="dashboard-row">
        <div className="glass-card score-section">
          <h3 className="card-title">Network Security Score</h3>
          <SecurityScoreGauge score={summary?.risk_score || 0} size={200} />
        </div>
        <div className="glass-card chart-section">
          <h3 className="card-title">Severity Distribution</h3>
          <SeverityPieChart data={severityData} />
        </div>
      </div>

      {/* Charts Row */}
      <div className="dashboard-row">
        <div className="glass-card chart-section">
          <h3 className="card-title">Vulnerabilities by Device</h3>
          <DeviceVulnBarChart data={deviceVulns} />
        </div>
        <div className="glass-card chart-section">
          <h3 className="card-title">Open Ports Analysis</h3>
          <PortAnalysisChart data={portData} />
        </div>
      </div>

      {/* Recent Scans */}
      <div className="glass-card">
        <h3 className="card-title"><FiClock size={16} /> Recent Scans</h3>
        <div className="table-responsive">
          <table className="data-table">
            <thead><tr><th>ID</th><th>Date</th><th>Target</th><th>Type</th><th>Hosts</th><th>Vulns</th><th>Score</th><th>Status</th></tr></thead>
            <tbody>
              {recentScans.length === 0 ? (
                <tr><td colSpan="8" style={{ textAlign: 'center', color: '#8b8fa3' }}>No scans yet</td></tr>
              ) : recentScans.map(scan => (
                <tr key={scan.id}>
                  <td>#{scan.id}</td>
                  <td>{scan.scan_date ? new Date(scan.scan_date).toLocaleDateString() : 'N/A'}</td>
                  <td>{scan.target_range}</td>
                  <td><span className="type-badge">{scan.scan_type}</span></td>
                  <td>{scan.total_hosts}</td>
                  <td>{scan.total_vulns}</td>
                  <td>{scan.risk_score?.toFixed(0)}</td>
                  <td><span className={`status-badge status-${scan.status}`}>{scan.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <style>{`
        .dashboard-page { max-width: 1400px; }
        .page-title { font-size: 1.8rem; font-weight: 700; color: #e4e6f0; margin-bottom: 24px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .stat-card { display: flex; align-items: center; gap: 16px; padding: 20px; border-radius: 14px;
          background: rgba(19,23,56,0.7); border: 1px solid rgba(255,255,255,0.05);
          transition: transform 0.3s, border-color 0.3s; }
        .stat-card:hover { transform: translateY(-2px); border-color: rgba(0,212,255,0.15); }
        .stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
        .stat-value { font-size: 1.8rem; font-weight: 700; }
        .stat-label { font-size: 0.85rem; color: #8b8fa3; }
        .dashboard-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .glass-card { padding: 24px; border-radius: 16px; background: rgba(19,23,56,0.6);
          border: 1px solid rgba(255,255,255,0.05); backdrop-filter: blur(10px); }
        .card-title { font-size: 1rem; color: #e4e6f0; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
        .score-section { display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .data-table { width: 100%; border-collapse: collapse; }
        .data-table th { padding: 10px 12px; text-align: left; color: #00d4ff; font-size: 0.8rem;
          text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid rgba(255,255,255,0.08); }
        .data-table td { padding: 10px 12px; color: #b0b3c6; font-size: 0.9rem;
          border-bottom: 1px solid rgba(255,255,255,0.03); }
        .data-table tr:hover { background: rgba(0,212,255,0.03); }
        .type-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;
          background: rgba(0,212,255,0.1); color: #00d4ff; text-transform: capitalize; }
        .status-badge { padding: 3px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: capitalize; }
        .status-completed { background: rgba(0,255,136,0.15); color: #00ff88; }
        .status-running { background: rgba(0,212,255,0.15); color: #00d4ff; }
        .status-failed { background: rgba(255,51,102,0.15); color: #ff3366; }
        .status-pending { background: rgba(255,184,0,0.15); color: #ffb800; }
        @media (max-width: 900px) { .dashboard-row { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  );
}

export default DashboardPage;
