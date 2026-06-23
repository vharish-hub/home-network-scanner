import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiShield, FiBell, FiUser, FiLogOut, FiSettings, FiSearch } from 'react-icons/fi';
import { Dropdown } from 'react-bootstrap';
import { useAuth } from '../context/AuthContext';

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="app-navbar">
      <div className="navbar-left">
        <div className="navbar-search">
          <FiSearch className="search-icon" />
          <input type="text" placeholder="Search devices, vulnerabilities..." value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)} className="search-input" />
        </div>
      </div>
      <div className="navbar-right">
        <button className="navbar-icon-btn notification-btn">
          <FiBell size={18} />
          <span className="notification-badge">3</span>
        </button>
        <Dropdown align="end">
          <Dropdown.Toggle as="button" className="navbar-user-btn">
            <div className="user-avatar">
              <FiUser size={16} />
            </div>
            <span className="user-name">{user?.username || 'User'}</span>
          </Dropdown.Toggle>
          <Dropdown.Menu className="user-dropdown">
            <Dropdown.Item onClick={() => navigate('/settings')}>
              <FiSettings size={14} /> <span>Settings</span>
            </Dropdown.Item>
            <Dropdown.Divider />
            <Dropdown.Item onClick={handleLogout}>
              <FiLogOut size={14} /> <span>Logout</span>
            </Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown>
      </div>
    </nav>
  );
}

export default Navbar;
