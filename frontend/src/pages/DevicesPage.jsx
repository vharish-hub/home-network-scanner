import React, { useState, useEffect } from 'react';
import { FiMonitor, FiSearch, FiWifi, FiSmartphone, FiPrinter, FiServer, FiHardDrive } from 'react-icons/fi';
import { Modal } from 'react-bootstrap';
import LoadingSpinner from '../components/LoadingSpinner';
import SeverityBadge from '../components/SeverityBadge';
import deviceService from '../services/deviceService';

const deviceIcons = {
  router: FiWifi, computer: FiMonitor, phone: FiSmartphone, printer: FiPrinter,
  server: FiServer, nas: FiHardDrive, iot: FiServer, smart_tv: FiMonitor, gaming: FiMonitor,
};

function DevicesPage() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await deviceService.getDevices();
        setDevices(res.data?.data?.items || res.data?.devices || []);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    fetch();
  }, []);

  const openDevice = async (device) => {
    try {
      const res = await deviceService.getDevice(device.id);
      setSelected(res.data?.data || res.data);
      setShowModal(true);
    } catch { setSelected(device); setShowModal(true); }
  };

  const filtered = devices.filter(d =>
    (d.hostname || '').toLowerCase().includes(search.toLowerCase()) ||
    (d.ip_address || '').includes(search) ||
    (d.os_name || '').toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <LoadingSpinner text="Loading devices..." />;

  return (
    <div className="devices-page">
      <div className="page-header">
        <h1 className="page-title"><FiMonitor /> Devices <span className="count-badge">{devices.length}</span></h1>
        <div className="search-box">
          <FiSearch className="search-icon" />
          <input type="text" placeholder="Search devices..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      <div className="devices-grid">
        {filtered.length === 0 ? (
          <div className="empty-state glass-card"><FiMonitor size={40} /><p>No devices found</p></div>
        ) : filtered.map(device => {
          const Icon = deviceIcons[device.device_type] || FiMonitor;
          return (
            <div key={device.id} className="device-card glass-card" onClick={() => openDevice(device)}>
              <div className="device-card-header">
                <div className="device-icon-wrap"><Icon size={22} /></div>
                <span className={`status-dot ${device.status === 'up' ? 'online' : 'offline'}`} />
              </div>
              <h3 className="device-name">{device.hostname || 'Unknown'}</h3>
              <p className="device-ip">{device.ip_address}</p>
              <div className="device-meta">
                <span>{device.os_name || 'Unknown OS'}</span>
                <span>{device.vendor || ''}</span>
              </div>
              {device.vulnerability_count > 0 && (
                <div className="vuln-count-badge">{device.vulnerability_count} vulns</div>
              )}
            </div>
          );
        })}
      </div>

      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg" centered
        contentClassName="modal-dark">
        {selected && (
          <>
            <Modal.Header closeButton closeVariant="white" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <Modal.Title style={{ color: '#e4e6f0' }}>{selected.hostname || selected.device?.hostname || 'Device Details'}</Modal.Title>
            </Modal.Header>
            <Modal.Body style={{ background: '#0d1130', color: '#b0b3c6' }}>
              <div className="detail-grid">
                {[['IP Address', selected.ip_address || selected.device?.ip_address],
                  ['MAC Address', selected.mac_address || selected.device?.mac_address || 'N/A'],
                  ['OS', selected.os_name || selected.device?.os_name || 'Unknown'],
                  ['Vendor', selected.vendor || selected.device?.vendor || 'Unknown'],
                  ['Type', selected.device_type || selected.device?.device_type || 'Unknown'],
                  ['Status', selected.status || selected.device?.status || 'up']
                ].map(([k, v], i) => (
                  <div key={i} className="detail-item"><span className="detail-label">{k}</span><span>{v}</span></div>
                ))}
              </div>
              {(selected.vulnerabilities || []).length > 0 && (
                <>
                  <h5 style={{ color: '#e4e6f0', margin: '20px 0 12px' }}>Vulnerabilities</h5>
                  <div className="table-responsive">
                    <table className="data-table" style={{ width: '100%' }}>
                      <thead><tr><th>Severity</th><th>Title</th><th>Port</th><th>CVSS</th></tr></thead>
                      <tbody>
                        {selected.vulnerabilities.map((v, i) => (
                          <tr key={i}>
                            <td><SeverityBadge severity={v.severity} /></td>
                            <td style={{ color: '#e4e6f0' }}>{v.title}</td>
                            <td>{v.port || '-'}</td>
                            <td>{v.cvss_score || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </Modal.Body>
          </>
        )}
      </Modal>

      <style>{`
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-wrap: wrap; gap: 16px; }
        .page-title { font-size: 1.8rem; font-weight: 700; color: #e4e6f0; display: flex; align-items: center; gap: 10px; }
        .count-badge { font-size: 0.9rem; padding: 2px 10px; border-radius: 8px; background: rgba(0,212,255,0.1); color: #00d4ff; }
        .search-box { position: relative; }
        .search-box .search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #8b8fa3; }
        .search-box input { padding: 10px 14px 10px 38px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08);
          background: rgba(19,23,56,0.8); color: #e4e6f0; outline: none; width: 260px; font-size: 0.9rem; }
        .search-box input:focus { border-color: rgba(0,212,255,0.3); }
        .devices-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
        .device-card { padding: 20px; border-radius: 14px; background: rgba(19,23,56,0.6); border: 1px solid rgba(255,255,255,0.05);
          cursor: pointer; transition: all 0.3s; position: relative; }
        .device-card:hover { transform: translateY(-3px); border-color: rgba(0,212,255,0.2); box-shadow: 0 8px 25px rgba(0,0,0,0.3); }
        .device-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .device-icon-wrap { width: 42px; height: 42px; border-radius: 10px; background: rgba(0,212,255,0.1);
          display: flex; align-items: center; justify-content: center; color: #00d4ff; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; }
        .status-dot.online { background: #00ff88; box-shadow: 0 0 8px #00ff8866; }
        .status-dot.offline { background: #8b8fa3; }
        .device-name { font-size: 1rem; color: #e4e6f0; margin-bottom: 4px; }
        .device-ip { font-size: 0.85rem; color: #00d4ff; margin-bottom: 8px; font-family: monospace; }
        .device-meta { display: flex; justify-content: space-between; font-size: 0.8rem; color: #8b8fa3; }
        .vuln-count-badge { position: absolute; top: 12px; right: 12px; padding: 2px 8px; border-radius: 6px;
          font-size: 0.7rem; font-weight: 600; background: rgba(255,184,0,0.15); color: #ffb800; }
        .empty-state { text-align: center; padding: 60px; color: #8b8fa3; grid-column: 1 / -1; }
        .empty-state p { margin-top: 12px; }
        .modal-dark { background: #0d1130 !important; border: 1px solid rgba(255,255,255,0.08); }
        .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .detail-item { display: flex; flex-direction: column; padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.02); }
        .detail-label { font-size: 0.75rem; color: #8b8fa3; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
        .data-table th { padding: 8px 12px; color: #00d4ff; font-size: 0.8rem; border-bottom: 1px solid rgba(255,255,255,0.08); text-align: left; }
        .data-table td { padding: 8px 12px; border-bottom: 1px solid rgba(255,255,255,0.03); font-size: 0.85rem; }
      `}</style>
    </div>
  );
}

export default DevicesPage;
