import React, { useState, useEffect } from 'react';
import { FiFileText, FiDownload, FiTrash2, FiFile } from 'react-icons/fi';
import LoadingSpinner from '../components/LoadingSpinner';
import reportService from '../services/reportService';
import scanService from '../services/scanService';
import { toast } from 'react-toastify';

function ReportsPage() {
  const [scans, setScans] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedScan, setSelectedScan] = useState('');
  const [format, setFormat] = useState('pdf');

  useEffect(() => {
    const fetch = async () => {
      try {
        const [scanRes, reportRes] = await Promise.all([scanService.getScans(), reportService.getReports()]);
        setScans(scanRes.data?.data?.items || scanRes.data?.scans || []);
        setReports(reportRes.data?.data || reportRes.data?.reports || []);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    fetch();
  }, []);

  const generateReport = async () => {
    if (!selectedScan) { toast.error('Please select a scan'); return; }
    setGenerating(true);
    try {
      await reportService.generateReport(selectedScan, { format });
      toast.success('Report generated!');
      const res = await reportService.getReports();
      setReports(res.data?.data || res.data?.reports || []);
    } catch (err) { toast.error(err.response?.data?.message || 'Failed to generate report'); }
    finally { setGenerating(false); }
  };

  const downloadReport = async (filename) => {
    try {
      const res = await reportService.downloadReport(filename);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch { toast.error('Download failed'); }
  };

  const deleteReport = async (filename) => {
    try {
      await reportService.deleteReport(filename);
      setReports(reports.filter(r => r.filename !== filename));
      toast.success('Report deleted');
    } catch { toast.error('Delete failed'); }
  };

  if (loading) return <LoadingSpinner text="Loading reports..." />;

  return (
    <div className="reports-page">
      <h1 className="page-title"><FiFileText /> Reports</h1>

      <div className="glass-card gen-section">
        <h3 className="card-title">Generate Report</h3>
        <div className="gen-form">
          <div className="form-group">
            <label>Select Scan</label>
            <select value={selectedScan} onChange={e => setSelectedScan(e.target.value)} className="form-select">
              <option value="">-- Choose a scan --</option>
              {scans.filter(s => s.status === 'completed').map(s => (
                <option key={s.id} value={s.id}>
                  Scan #{s.id} - {s.target_range} ({new Date(s.scan_date).toLocaleDateString()})
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Format</label>
            <div className="format-options">
              {['pdf', 'html', 'csv', 'json'].map(f => (
                <button key={f} className={`format-btn ${format === f ? 'selected' : ''}`}
                  onClick={() => setFormat(f)}>{f.toUpperCase()}</button>
              ))}
            </div>
          </div>
          <button className="gen-btn" onClick={generateReport} disabled={generating}>
            {generating ? 'Generating...' : 'Generate Report'}
          </button>
        </div>
      </div>

      <div className="glass-card">
        <h3 className="card-title">Generated Reports</h3>
        {reports.length === 0 ? (
          <div className="empty-state"><FiFile size={40} /><p>No reports generated yet</p></div>
        ) : (
          <div className="reports-list">
            {reports.map((report, i) => (
              <div key={i} className="report-item">
                <div className="report-info">
                  <FiFileText size={20} className="report-icon" />
                  <div>
                    <div className="report-name">{report.filename}</div>
                    <div className="report-meta">
                      {report.size && <span>{(report.size / 1024).toFixed(1)} KB</span>}
                      {report.created && <span>{new Date(report.created).toLocaleString()}</span>}
                    </div>
                  </div>
                </div>
                <div className="report-actions">
                  <button className="action-btn download" onClick={() => downloadReport(report.filename)}>
                    <FiDownload size={14} /> Download
                  </button>
                  <button className="action-btn delete" onClick={() => deleteReport(report.filename)}>
                    <FiTrash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style>{`
        .reports-page { max-width: 1000px; }
        .page-title { font-size: 1.8rem; font-weight: 700; color: #e4e6f0; display: flex; align-items: center; gap: 10px; margin-bottom: 24px; }
        .glass-card { padding: 24px; border-radius: 16px; background: rgba(19,23,56,0.6); border: 1px solid rgba(255,255,255,0.05); margin-bottom: 20px; }
        .card-title { font-size: 1rem; color: #e4e6f0; margin-bottom: 16px; }
        .gen-form { display: flex; flex-direction: column; gap: 16px; }
        .form-group label { display: block; color: #8b8fa3; font-size: 0.85rem; margin-bottom: 6px; }
        .form-select { width: 100%; max-width: 500px; padding: 12px 16px; border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.08); background: rgba(19,23,56,0.8); color: #e4e6f0; font-size: 0.9rem; outline: none; }
        .format-options { display: flex; gap: 8px; }
        .format-btn { padding: 8px 18px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.02); color: #8b8fa3; cursor: pointer; font-weight: 600; font-size: 0.85rem; transition: all 0.2s; }
        .format-btn.selected { border-color: #00d4ff; color: #00d4ff; background: rgba(0,212,255,0.08); }
        .gen-btn { display: inline-flex; align-items: center; gap: 8px; padding: 12px 28px; border: none;
          border-radius: 10px; background: linear-gradient(135deg, #00d4ff, #0099cc); color: #fff;
          font-weight: 600; cursor: pointer; transition: all 0.3s; }
        .gen-btn:hover:not(:disabled) { box-shadow: 0 4px 20px rgba(0,212,255,0.4); }
        .gen-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .reports-list { display: flex; flex-direction: column; gap: 8px; }
        .report-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px;
          border-radius: 10px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.03);
          transition: border-color 0.2s; }
        .report-item:hover { border-color: rgba(0,212,255,0.1); }
        .report-info { display: flex; align-items: center; gap: 12px; }
        .report-icon { color: #00d4ff; }
        .report-name { color: #e4e6f0; font-size: 0.9rem; font-weight: 500; }
        .report-meta { display: flex; gap: 12px; font-size: 0.8rem; color: #8b8fa3; margin-top: 2px; }
        .report-actions { display: flex; gap: 8px; }
        .action-btn { display: flex; align-items: center; gap: 4px; padding: 6px 12px; border-radius: 6px;
          border: none; cursor: pointer; font-size: 0.8rem; font-weight: 500; transition: all 0.2s; }
        .action-btn.download { background: rgba(0,212,255,0.1); color: #00d4ff; }
        .action-btn.download:hover { background: rgba(0,212,255,0.2); }
        .action-btn.delete { background: rgba(255,51,102,0.1); color: #ff3366; }
        .action-btn.delete:hover { background: rgba(255,51,102,0.2); }
        .empty-state { text-align: center; padding: 40px; color: #8b8fa3; }
        .empty-state p { margin-top: 10px; }
      `}</style>
    </div>
  );
}

export default ReportsPage;
