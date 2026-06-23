import React, { useState, useEffect } from 'react';
import { FiAlertTriangle, FiSearch, FiChevronDown, FiChevronUp } from 'react-icons/fi';
import LoadingSpinner from '../components/LoadingSpinner';
import SeverityBadge from '../components/SeverityBadge';
import vulnerabilityService from '../services/vulnerabilityService';

const tabs = ['all', 'critical', 'high', 'medium', 'low', 'info'];

function VulnerabilitiesPage() {
  const [vulns, setVulns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState(null);
  const [sortBy, setSortBy] = useState('severity');

  useEffect(() => {
    const fetch = async () => {
      try {
        const params = {};
        if (activeTab !== 'all') params.severity = activeTab;
        const res = await vulnerabilityService.getVulnerabilities(params);
        setVulns(res.data?.data?.items || res.data?.vulnerabilities || []);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    setLoading(true);
    fetch();
  }, [activeTab]);

  const sevOrder = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
  const filtered = vulns
    .filter(v => (v.title || '').toLowerCase().includes(search.toLowerCase()) ||
      (v.cve_id || '').toLowerCase().includes(search.toLowerCase()) ||
      (v.service || '').toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (sortBy === 'severity') return (sevOrder[a.severity] || 5) - (sevOrder[b.severity] || 5);
      if (sortBy === 'cvss') return (b.cvss_score || 0) - (a.cvss_score || 0);
      return 0;
    });

  const counts = {};
  vulns.forEach(v => { counts[v.severity] = (counts[v.severity] || 0) + 1; });

  if (loading) return <LoadingSpinner text="Loading vulnerabilities..." />;

  return (
    <div className="vulns-page">
      <div className="page-header">
        <h1 className="page-title"><FiAlertTriangle /> Vulnerabilities <span className="count-badge">{vulns.length}</span></h1>
        <div className="header-actions">
          <select className="sort-select" value={sortBy} onChange={e => setSortBy(e.target.value)}>
            <option value="severity">Sort by Severity</option>
            <option value="cvss">Sort by CVSS</option>
          </select>
          <div className="search-box">
            <FiSearch className="search-icon" />
            <input type="text" placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
        </div>
      </div>

      <div className="severity-tabs">
        {tabs.map(tab => (
          <button key={tab} className={`sev-tab ${activeTab === tab ? 'active' : ''} sev-tab-${tab}`}
            onClick={() => setActiveTab(tab)}>
            {tab === 'all' ? 'All' : tab.charAt(0).toUpperCase() + tab.slice(1)}
            <span className="tab-count">{tab === 'all' ? vulns.length : (counts[tab] || 0)}</span>
          </button>
        ))}
      </div>

      <div className="vulns-list">
        {filtered.length === 0 ? (
          <div className="empty-state glass-card"><FiAlertTriangle size={40} /><p>No vulnerabilities found</p></div>
        ) : filtered.map(vuln => (
          <div key={vuln.id} className={`vuln-item glass-card ${expanded === vuln.id ? 'expanded' : ''}`}>
            <div className="vuln-header" onClick={() => setExpanded(expanded === vuln.id ? null : vuln.id)}>
              <div className="vuln-left">
                <SeverityBadge severity={vuln.severity} />
                <div className="vuln-title-block">
                  <h4 className="vuln-title">{vuln.title}</h4>
                  <div className="vuln-meta">
                    {vuln.cve_id && <span className="cve-tag">{vuln.cve_id}</span>}
                    {vuln.port && <span>Port {vuln.port}/{vuln.protocol || 'tcp'}</span>}
                    {vuln.service && <span>{vuln.service}</span>}
                  </div>
                </div>
              </div>
              <div className="vuln-right">
                {vuln.cvss_score != null && (
                  <div className="cvss-bar">
                    <div className="cvss-fill" style={{
                      width: `${(vuln.cvss_score / 10) * 100}%`,
                      background: vuln.cvss_score >= 9 ? '#ff3366' : vuln.cvss_score >= 7 ? '#ff6b35' :
                        vuln.cvss_score >= 4 ? '#ffb800' : '#00d4ff'
                    }} />
                    <span className="cvss-value">{vuln.cvss_score}</span>
                  </div>
                )}
                {expanded === vuln.id ? <FiChevronUp /> : <FiChevronDown />}
              </div>
            </div>
            {expanded === vuln.id && (
              <div className="vuln-details">
                {vuln.description && <div className="detail-section"><strong>Description:</strong><p>{vuln.description}</p></div>}
                {vuln.recommendation && <div className="detail-section rec"><strong>Recommendation:</strong><p>{vuln.recommendation}</p></div>}
                <div className="detail-tags">
                  {vuln.exploit_available && <span className="exploit-tag">⚠ Exploit Available</span>}
                  {vuln.version && <span className="version-tag">v{vuln.version}</span>}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <style>{`
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
        .page-title { font-size: 1.8rem; font-weight: 700; color: #e4e6f0; display: flex; align-items: center; gap: 10px; }
        .count-badge { font-size: 0.9rem; padding: 2px 10px; border-radius: 8px; background: rgba(0,212,255,0.1); color: #00d4ff; }
        .header-actions { display: flex; gap: 10px; align-items: center; }
        .sort-select { padding: 10px 14px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08);
          background: rgba(19,23,56,0.8); color: #e4e6f0; font-size: 0.85rem; outline: none; }
        .search-box { position: relative; }
        .search-box .search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #8b8fa3; }
        .search-box input { padding: 10px 14px 10px 38px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08);
          background: rgba(19,23,56,0.8); color: #e4e6f0; outline: none; width: 220px; font-size: 0.9rem; }
        .severity-tabs { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
        .sev-tab { padding: 8px 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);
          background: rgba(19,23,56,0.5); color: #8b8fa3; cursor: pointer; font-size: 0.85rem;
          font-weight: 500; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }
        .sev-tab.active { border-color: rgba(0,212,255,0.3); color: #e4e6f0; background: rgba(0,212,255,0.08); }
        .sev-tab-critical.active { border-color: #ff336644; color: #ff3366; background: rgba(255,51,102,0.08); }
        .sev-tab-high.active { border-color: #ff6b3544; color: #ff6b35; background: rgba(255,107,53,0.08); }
        .sev-tab-medium.active { border-color: #ffb80044; color: #ffb800; background: rgba(255,184,0,0.08); }
        .sev-tab-low.active { border-color: #00d4ff44; color: #00d4ff; background: rgba(0,212,255,0.08); }
        .tab-count { padding: 1px 6px; border-radius: 4px; font-size: 0.7rem; background: rgba(255,255,255,0.05); }
        .vulns-list { display: flex; flex-direction: column; gap: 10px; }
        .vuln-item { padding: 16px 20px; border-radius: 12px; background: rgba(19,23,56,0.6);
          border: 1px solid rgba(255,255,255,0.05); transition: border-color 0.3s; }
        .vuln-item:hover { border-color: rgba(0,212,255,0.1); }
        .vuln-header { display: flex; justify-content: space-between; align-items: center; cursor: pointer; gap: 16px; }
        .vuln-left { display: flex; align-items: center; gap: 14px; flex: 1; min-width: 0; }
        .vuln-title { color: #e4e6f0; font-size: 0.95rem; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .vuln-meta { display: flex; gap: 12px; margin-top: 4px; font-size: 0.8rem; color: #8b8fa3; }
        .cve-tag { color: #00d4ff; font-weight: 600; font-family: monospace; }
        .vuln-right { display: flex; align-items: center; gap: 16px; color: #8b8fa3; flex-shrink: 0; }
        .cvss-bar { display: flex; align-items: center; gap: 8px; width: 100px; }
        .cvss-fill { height: 6px; border-radius: 3px; transition: width 0.5s; }
        .cvss-value { font-size: 0.85rem; font-weight: 600; color: #e4e6f0; min-width: 24px; }
        .vuln-details { margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.05); }
        .detail-section { margin-bottom: 12px; }
        .detail-section strong { color: #e4e6f0; font-size: 0.85rem; }
        .detail-section p { color: #8b8fa3; font-size: 0.9rem; margin: 4px 0 0; line-height: 1.6; }
        .detail-section.rec { padding: 10px 14px; border-left: 3px solid #00d4ff; background: rgba(0,212,255,0.05); border-radius: 0 8px 8px 0; }
        .detail-tags { display: flex; gap: 8px; margin-top: 10px; }
        .exploit-tag { padding: 3px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;
          background: rgba(255,51,102,0.15); color: #ff3366; }
        .version-tag { padding: 3px 10px; border-radius: 4px; font-size: 0.75rem; background: rgba(255,255,255,0.05); color: #8b8fa3; }
        .empty-state { text-align: center; padding: 60px; color: #8b8fa3; }
      `}</style>
    </div>
  );
}

export default VulnerabilitiesPage;
