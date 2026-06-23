import React, { useState, useEffect, useRef } from 'react';
import { FiSearch, FiPlay, FiSquare, FiClock, FiTrash2 } from 'react-icons/fi';
import LoadingSpinner from '../components/LoadingSpinner';
import scanService from '../services/scanService';
import { toast } from 'react-toastify';

function ScanPage() {
  const [targetRange, setTargetRange] = useState('192.168.1.0/24');
  const [scanType, setScanType] = useState('quick');
  const [scanning, setScanning] = useState(false);
  const [activeScan, setActiveScan] = useState(null);
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const pollRef = useRef(null);

  useEffect(() => {
    fetchScans();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const fetchScans = async () => {
    try {
      const res = await scanService.getScans();
      setScans(res.data?.data?.items || res.data?.scans || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const startScan = async () => {
    if (!targetRange) { toast.error('Please enter a target range'); return; }
    setScanning(true);
    try {
      const res = await scanService.startScan({ target_range: targetRange, scan_type: scanType });
      const scan = res.data?.data || res.data?.scan || res.data;
      setActiveScan(scan);
      toast.success('Scan started!');
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await scanService.getScanStatus(scan.id);
          const updated = statusRes.data?.data || statusRes.data?.scan || statusRes.data;
          setActiveScan(updated);
          if (updated.status === 'completed' || updated.status === 'failed') {
            clearInterval(pollRef.current);
            setScanning(false);
            setActiveScan(null);
            fetchScans();
            toast.info(`Scan ${updated.status}!`);
          }
        } catch { /* continue polling */ }
      }, 3000);
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to start scan');
      setScanning(false);
    }
  };

  const deleteScan = async (id) => {
    try {
      await scanService.deleteScan(id);
      setScans(scans.filter(s => s.id !== id));
      toast.success('Scan deleted');
    } catch { toast.error('Delete failed'); }
  };

  const scanTypes = [
    { id: 'quick', label: 'Quick Scan', desc: 'Top 100 ports, fast results (~1 min)' },
    { id: 'full', label: 'Full Scan', desc: 'Top 1000 ports with version detection (~5 min)' },
    { id: 'custom', label: 'Custom Scan', desc: 'All ports, comprehensive analysis (~15 min)' },
  ];

  return (
    <div className="scan-page">
      <h1 className="page-title"><FiSearch /> Network Scan</h1>

      {/* New Scan Section */}
      <div className="glass-card scan-form">
        <h3 className="card-title">Start New Scan</h3>
        <div className="scan-config">
          <div className="input-group">
            <label>Target Range</label>
            <input type="text" value={targetRange} onChange={e => setTargetRange(e.target.value)}
              placeholder="e.g., 192.168.1.0/24" className="scan-input" disabled={scanning} />
          </div>
          <div className="scan-types">
            {scanTypes.map(t => (
              <div key={t.id} className={`type-card ${scanType === t.id ? 'selected' : ''}`}
                onClick={() => !scanning && setScanType(t.id)}>
                <strong>{t.label}</strong>
                <p>{t.desc}</p>
              </div>
            ))}
          </div>
          <button className="scan-btn" onClick={startScan} disabled={scanning}>
            {scanning ? <><FiSquare /> Scanning...</> : <><FiPlay /> Start Scan</>}
          </button>
        </div>
      </div>

      {/* Active Scan Progress */}
      {activeScan && (
        <div className="glass-card active-scan">
          <h3 className="card-title">Scan in Progress</h3>
          <div className="progress-container">
            <div className="progress-bar">
              <div className="progress-fill" style={{
                width: activeScan.status === 'running' ? '60%' : activeScan.status === 'completed' ? '100%' : '10%',
                background: 'linear-gradient(90deg, #00d4ff, #00ff88)',
              }} />
            </div>
            <span className="progress-status">{activeScan.status}</span>
          </div>
          <div className="scan-info-row">
            <span>Target: {activeScan.target_range}</span>
            <span>Type: {activeScan.scan_type}</span>
            {activeScan.total_hosts > 0 && <span>Hosts found: {activeScan.total_hosts}</span>}
          </div>
        </div>
      )}

      {/* Scan History */}
      <div className="glass-card">
        <h3 className="card-title"><FiClock size={16} /> Scan History</h3>
        {loading ? <LoadingSpinner text="Loading scans..." /> : (
          <div className="table-responsive">
            <table className="data-table">
              <thead><tr><th>ID</th><th>Date</th><th>Target</th><th>Type</th><th>Hosts</th><th>Vulns</th><th>Score</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {scans.length === 0 ? (
                  <tr><td colSpan="9" style={{ textAlign: 'center', color: '#8b8fa3', padding: 40 }}>No scans yet. Start your first scan above!</td></tr>
                ) : scans.map(scan => (
                  <tr key={scan.id}>
                    <td>#{scan.id}</td>
                    <td>{scan.scan_date ? new Date(scan.scan_date).toLocaleDateString() : '-'}</td>
                    <td style={{ fontFamily: 'monospace', color: '#00d4ff' }}>{scan.target_range}</td>
                    <td><span className="type-badge">{scan.scan_type}</span></td>
                    <td>{scan.total_hosts}</td>
                    <td>{scan.total_vulns}</td>
                    <td>{scan.risk_score?.toFixed(0) || '-'}</td>
                    <td><span className={`status-badge status-${scan.status}`}>{scan.status}</span></td>
                    <td><button className="icon-btn" onClick={() => deleteScan(scan.id)}><FiTrash2 size={14} /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <style>{`
        .scan-page { max-width: 1200px; }
        .page-title { font-size: 1.8rem; font-weight: 700; color: #e4e6f0; display: flex; align-items: center; gap: 10px; margin-bottom: 24px; }
        .glass-card { padding: 24px; border-radius: 16px; background: rgba(19,23,56,0.6); border: 1px solid rgba(255,255,255,0.05); margin-bottom: 20px; }
        .card-title { font-size: 1rem; color: #e4e6f0; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
        .scan-config { display: flex; flex-direction: column; gap: 16px; }
        .input-group label { display: block; color: #8b8fa3; font-size: 0.85rem; margin-bottom: 6px; }
        .scan-input { width: 100%; max-width: 400px; padding: 12px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.03); color: #e4e6f0; font-size: 0.95rem; font-family: monospace; outline: none; }
        .scan-input:focus { border-color: rgba(0,212,255,0.4); }
        .scan-types { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
        .type-card { padding: 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.02); cursor: pointer; transition: all 0.3s; }
        .type-card:hover { border-color: rgba(0,212,255,0.2); }
        .type-card.selected { border-color: #00d4ff; background: rgba(0,212,255,0.08); }
        .type-card strong { color: #e4e6f0; font-size: 0.95rem; }
        .type-card p { color: #8b8fa3; font-size: 0.8rem; margin: 4px 0 0; }
        .scan-btn { display: inline-flex; align-items: center; gap: 8px; padding: 12px 28px; border: none;
          border-radius: 10px; background: linear-gradient(135deg, #00d4ff, #0099cc); color: #fff;
          font-weight: 600; font-size: 1rem; cursor: pointer; transition: all 0.3s; }
        .scan-btn:hover:not(:disabled) { box-shadow: 0 4px 20px rgba(0,212,255,0.4); transform: translateY(-1px); }
        .scan-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .active-scan { border-color: rgba(0,212,255,0.2); }
        .progress-container { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
        .progress-bar { flex: 1; height: 8px; border-radius: 4px; background: rgba(255,255,255,0.05); overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 4px; transition: width 1s ease; animation: shimmer 2s infinite; }
        @keyframes shimmer { 0% { opacity: 0.8; } 50% { opacity: 1; } 100% { opacity: 0.8; } }
        .progress-status { color: #00d4ff; font-weight: 600; font-size: 0.85rem; text-transform: capitalize; }
        .scan-info-row { display: flex; gap: 20px; color: #8b8fa3; font-size: 0.85rem; }
        .data-table { width: 100%; border-collapse: collapse; }
        .data-table th { padding: 10px 12px; text-align: left; color: #00d4ff; font-size: 0.8rem; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.08); }
        .data-table td { padding: 10px 12px; color: #b0b3c6; font-size: 0.9rem; border-bottom: 1px solid rgba(255,255,255,0.03); }
        .data-table tr:hover { background: rgba(0,212,255,0.03); }
        .type-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; background: rgba(0,212,255,0.1); color: #00d4ff; text-transform: capitalize; }
        .status-badge { padding: 3px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: capitalize; }
        .status-completed { background: rgba(0,255,136,0.15); color: #00ff88; }
        .status-running { background: rgba(0,212,255,0.15); color: #00d4ff; }
        .status-failed { background: rgba(255,51,102,0.15); color: #ff3366; }
        .status-pending { background: rgba(255,184,0,0.15); color: #ffb800; }
        .icon-btn { background: none; border: none; color: #8b8fa3; cursor: pointer; padding: 4px; transition: color 0.2s; }
        .icon-btn:hover { color: #ff3366; }
      `}</style>
    </div>
  );
}

export default ScanPage;
