import React from 'react';
import { Link } from 'react-router-dom';
import { FiShield, FiWifi, FiSearch, FiBarChart2, FiFileText, FiArrowRight, FiLock, FiActivity } from 'react-icons/fi';

function HomePage() {
  return (
    <div className="home-page">
      {/* Animated Background */}
      <div className="home-bg-grid" />

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-icon-wrapper">
            <FiShield size={48} className="hero-icon" />
          </div>
          <h1 className="hero-title">
            Home Network <span className="text-gradient">Vulnerability Scanner</span>
          </h1>
          <p className="hero-subtitle">
            Secure your network with professional-grade vulnerability assessment.
            Discover devices, identify threats, and generate detailed security reports.
          </p>
          <div className="hero-actions">
            <Link to="/login" className="btn-glow btn-primary-glow">
              <FiSearch size={18} /> Start Scanning <FiArrowRight size={16} />
            </Link>
            <Link to="/register" className="btn-glow btn-secondary-glow">
              Create Account
            </Link>
          </div>

          {/* Floating Nodes Animation */}
          <div className="hero-nodes">
            {[...Array(6)].map((_, i) => (
              <div key={i} className={`floating-node node-${i}`}>
                <div className="node-dot" />
              </div>
            ))}
            <svg className="hero-lines" viewBox="0 0 600 300">
              <line x1="100" y1="80" x2="300" y2="150" stroke="#00d4ff" strokeWidth="0.5" opacity="0.3" />
              <line x1="300" y1="150" x2="500" y2="100" stroke="#00d4ff" strokeWidth="0.5" opacity="0.3" />
              <line x1="200" y1="200" x2="400" y2="50" stroke="#00ff88" strokeWidth="0.5" opacity="0.2" />
              <line x1="150" y1="50" x2="450" y2="250" stroke="#00d4ff" strokeWidth="0.5" opacity="0.15" />
            </svg>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <h2 className="section-title">Key Features</h2>
        <div className="features-grid">
          {[
            { icon: FiWifi, title: 'Network Discovery', desc: 'Automatically detect all devices connected to your network with OS and vendor identification.' },
            { icon: FiSearch, title: 'Vulnerability Assessment', desc: 'Identify security vulnerabilities with CVE mapping and CVSS scoring for accurate risk evaluation.' },
            { icon: FiBarChart2, title: 'Risk Analysis', desc: 'Calculate comprehensive risk scores with weighted severity analysis and exploit availability tracking.' },
            { icon: FiFileText, title: 'Report Generation', desc: 'Generate professional PDF and HTML reports with executive summaries and remediation steps.' },
          ].map(({ icon: Icon, title, desc }, i) => (
            <div key={i} className="feature-card glass-card">
              <div className="feature-icon-wrap">
                <Icon size={28} />
              </div>
              <h3>{title}</h3>
              <p>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="how-section">
        <h2 className="section-title">How It Works</h2>
        <div className="steps-grid">
          {[
            { num: '01', icon: FiLock, title: 'Login', desc: 'Sign in to your secure dashboard' },
            { num: '02', icon: FiWifi, title: 'Scan Network', desc: 'Discover all connected devices' },
            { num: '03', icon: FiActivity, title: 'Analyze', desc: 'Identify vulnerabilities and risks' },
            { num: '04', icon: FiFileText, title: 'Report', desc: 'Generate and download reports' },
          ].map(({ num, icon: Icon, title, desc }, i) => (
            <div key={i} className="step-card">
              <div className="step-number">{num}</div>
              <Icon size={24} className="step-icon" />
              <h4>{title}</h4>
              <p>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="home-footer">
        <p>© 2024 Network Vulnerability Scanner. For authorized use only.</p>
      </footer>

      <style>{`
        .home-page { min-height: 100vh; position: relative; overflow: hidden; }
        .home-bg-grid { position: fixed; top: 0; left: 0; right: 0; bottom: 0;
          background-image: radial-gradient(circle at 1px 1px, rgba(0,212,255,0.05) 1px, transparent 0);
          background-size: 40px 40px; pointer-events: none; z-index: 0; }
        .hero-section { position: relative; z-index: 1; min-height: 85vh; display: flex; align-items: center;
          justify-content: center; text-align: center; padding: 40px 20px; }
        .hero-content { max-width: 800px; position: relative; }
        .hero-icon-wrapper { width: 90px; height: 90px; border-radius: 50%;
          background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(0,255,136,0.1));
          display: flex; align-items: center; justify-content: center; margin: 0 auto 24px;
          border: 1px solid rgba(0,212,255,0.3); animation: pulse 3s infinite; }
        .hero-icon { color: #00d4ff; }
        .hero-title { font-size: 3rem; font-weight: 800; color: #e4e6f0; margin-bottom: 16px; line-height: 1.1; }
        .text-gradient { background: linear-gradient(135deg, #00d4ff, #00ff88); -webkit-background-clip: text;
          -webkit-text-fill-color: transparent; background-clip: text; }
        .hero-subtitle { font-size: 1.15rem; color: #8b8fa3; max-width: 600px; margin: 0 auto 32px; line-height: 1.7; }
        .hero-actions { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
        .btn-glow { display: inline-flex; align-items: center; gap: 8px; padding: 14px 28px; border-radius: 10px;
          font-weight: 600; font-size: 1rem; text-decoration: none; transition: all 0.3s ease; }
        .btn-primary-glow { background: linear-gradient(135deg, #00d4ff, #0099cc); color: #fff;
          box-shadow: 0 4px 20px rgba(0,212,255,0.3); }
        .btn-primary-glow:hover { transform: translateY(-2px); box-shadow: 0 6px 30px rgba(0,212,255,0.5); color: #fff; }
        .btn-secondary-glow { background: rgba(255,255,255,0.05); color: #e4e6f0;
          border: 1px solid rgba(255,255,255,0.1); }
        .btn-secondary-glow:hover { background: rgba(255,255,255,0.1); color: #e4e6f0; transform: translateY(-2px); }
        .hero-nodes { position: absolute; top: 0; left: 50%; transform: translateX(-50%);
          width: 600px; height: 300px; pointer-events: none; opacity: 0.6; }
        .hero-lines { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
        .floating-node { position: absolute; animation: floatNode 6s ease-in-out infinite; }
        .node-dot { width: 8px; height: 8px; background: #00d4ff; border-radius: 50%;
          box-shadow: 0 0 10px #00d4ff66; }
        .node-0 { top: 25%; left: 15%; animation-delay: 0s; }
        .node-1 { top: 50%; left: 50%; animation-delay: 1s; }
        .node-2 { top: 30%; left: 80%; animation-delay: 2s; }
        .node-3 { top: 70%; left: 30%; animation-delay: 0.5s; }
        .node-4 { top: 15%; left: 60%; animation-delay: 1.5s; }
        .node-5 { top: 80%; left: 70%; animation-delay: 3s; }
        @keyframes floatNode { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-15px); } }
        @keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(0,212,255,0.2); }
          50% { box-shadow: 0 0 0 15px rgba(0,212,255,0); } }
        .features-section, .how-section { position: relative; z-index: 1; max-width: 1100px;
          margin: 0 auto; padding: 60px 20px; }
        .section-title { font-size: 2rem; font-weight: 700; text-align: center; margin-bottom: 40px;
          color: #e4e6f0; }
        .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; }
        .feature-card { padding: 30px; border-radius: 16px; background: rgba(19,23,56,0.6);
          border: 1px solid rgba(255,255,255,0.05); backdrop-filter: blur(10px);
          transition: transform 0.3s, border-color 0.3s; }
        .feature-card:hover { transform: translateY(-4px); border-color: rgba(0,212,255,0.2); }
        .feature-icon-wrap { width: 56px; height: 56px; border-radius: 12px;
          background: linear-gradient(135deg, rgba(0,212,255,0.1), rgba(0,255,136,0.05));
          display: flex; align-items: center; justify-content: center; margin-bottom: 16px; color: #00d4ff; }
        .feature-card h3 { font-size: 1.1rem; color: #e4e6f0; margin-bottom: 8px; }
        .feature-card p { font-size: 0.9rem; color: #8b8fa3; line-height: 1.6; }
        .steps-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 24px; }
        .step-card { text-align: center; padding: 24px; }
        .step-number { font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #00d4ff33, #00ff8833);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .step-icon { color: #00d4ff; margin: 12px 0; }
        .step-card h4 { color: #e4e6f0; margin-bottom: 6px; }
        .step-card p { color: #8b8fa3; font-size: 0.9rem; }
        .home-footer { position: relative; z-index: 1; text-align: center; padding: 30px;
          color: #8b8fa3; font-size: 0.85rem; border-top: 1px solid rgba(255,255,255,0.05); }
        @media (max-width: 768px) { .hero-title { font-size: 2rem; } .hero-nodes { display: none; } }
      `}</style>
    </div>
  );
}

export default HomePage;
