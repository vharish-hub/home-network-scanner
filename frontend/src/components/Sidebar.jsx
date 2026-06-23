import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { FiShield, FiGrid, FiMonitor, FiAlertTriangle, FiSearch, FiFileText, FiSettings, FiMenu, FiX } from 'react-icons/fi';

const navItems = [
  { path: '/dashboard', icon: FiGrid, label: 'Dashboard' },
  { path: '/devices', icon: FiMonitor, label: 'Devices' },
  { path: '/vulnerabilities', icon: FiAlertTriangle, label: 'Vulnerabilities' },
  { path: '/scan', icon: FiSearch, label: 'Scan' },
  { path: '/reports', icon: FiFileText, label: 'Reports' },
  { path: '/settings', icon: FiSettings, label: 'Settings' },
];

function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      <button className="sidebar-mobile-toggle" onClick={() => setCollapsed(!collapsed)}>
        {collapsed ? <FiX size={20} /> : <FiMenu size={20} />}
      </button>
      <aside className={`app-sidebar ${collapsed ? 'sidebar-open-mobile' : ''}`}>
        <div className="sidebar-brand">
          <FiShield className="brand-icon" size={24} />
          <span className="brand-text">NetScan</span>
        </div>
        <nav className="sidebar-nav">
          {navItems.map(({ path, icon: Icon, label }) => (
            <NavLink key={path} to={path} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
              onClick={() => setCollapsed(false)}>
              <Icon className="sidebar-icon" size={18} />
              <span className="sidebar-label">{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-version">v1.0.0</div>
        </div>
      </aside>
      {collapsed && <div className="sidebar-overlay" onClick={() => setCollapsed(false)} />}
    </>
  );
}

export default Sidebar;
