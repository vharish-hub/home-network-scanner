import React, { useState, useEffect } from 'react';
import { FiSettings, FiUser, FiLock, FiSliders } from 'react-icons/fi';
import { useAuth } from '../context/AuthContext';
import settingsService from '../services/settingsService';
import { toast } from 'react-toastify';

function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [profile, setProfile] = useState({ username: '', email: '' });
  const [passwords, setPasswords] = useState({ current: '', newPass: '', confirm: '' });
  const [configs, setConfigs] = useState([]);
  const [newConfig, setNewConfig] = useState({ name: '', target_range: '', scan_type: 'quick' });

  useEffect(() => {
    if (user) setProfile({ username: user.username || '', email: user.email || '' });
    fetchConfigs();
  }, [user]);

  const fetchConfigs = async () => {
    try { const res = await settingsService.getScanConfigs(); setConfigs(res.data?.data?.items || res.data?.data || res.data?.configs || []); }
    catch { /* ignore */ }
  };

  const updateProfile = async (e) => {
    e.preventDefault();
    try { await settingsService.updateProfile(profile); toast.success('Profile updated'); }
    catch (err) { toast.error(err.response?.data?.message || 'Update failed'); }
  };

  const changePassword = async (e) => {
    e.preventDefault();
    if (passwords.newPass !== passwords.confirm) { toast.error('Passwords do not match'); return; }
    if (passwords.newPass.length < 6) { toast.error('Password must be at least 6 characters'); return; }
    try {
      await settingsService.changePassword({ current_password: passwords.current, new_password: passwords.newPass });
      toast.success('Password changed');
      setPasswords({ current: '', newPass: '', confirm: '' });
    } catch (err) { toast.error(err.response?.data?.message || 'Failed to change password'); }
  };

  const addConfig = async (e) => {
    e.preventDefault();
    if (!newConfig.name || !newConfig.target_range) { toast.error('Fill in all fields'); return; }
    try {
      await settingsService.createScanConfig(newConfig);
      toast.success('Config saved');
      setNewConfig({ name: '', target_range: '', scan_type: 'quick' });
      fetchConfigs();
    } catch (err) { toast.error('Failed to save config'); }
  };

  const deleteConfig = async (id) => {
    try { await settingsService.deleteScanConfig(id); fetchConfigs(); toast.success('Config deleted'); }
    catch { toast.error('Delete failed'); }
  };

  const tabs = [
    { id: 'profile', icon: FiUser, label: 'Profile' },
    { id: 'security', icon: FiLock, label: 'Security' },
    { id: 'configs', icon: FiSliders, label: 'Scan Configs' },
  ];

  return (
    <div className="settings-page">
      <h1 className="page-title"><FiSettings /> Settings</h1>
      <div className="settings-layout">
        <div className="settings-tabs">
          {tabs.map(({ id, icon: Icon, label }) => (
            <button key={id} className={`settings-tab ${activeTab === id ? 'active' : ''}`}
              onClick={() => setActiveTab(id)}>
              <Icon size={16} /> {label}
            </button>
          ))}
        </div>

        <div className="settings-content glass-card">
          {activeTab === 'profile' && (
            <div>
              <h3 className="section-title">Profile Information</h3>
              <form onSubmit={updateProfile} className="settings-form">
                <div className="form-group">
                  <label>Username</label>
                  <input type="text" value={profile.username} onChange={e => setProfile({ ...profile, username: e.target.value })} className="form-input" />
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input type="email" value={profile.email} onChange={e => setProfile({ ...profile, email: e.target.value })} className="form-input" />
                </div>
                <div className="form-group">
                  <label>Role</label>
                  <input type="text" value={user?.role || 'user'} className="form-input" disabled />
                </div>
                <button type="submit" className="save-btn">Save Changes</button>
              </form>
            </div>
          )}

          {activeTab === 'security' && (
            <div>
              <h3 className="section-title">Change Password</h3>
              <form onSubmit={changePassword} className="settings-form">
                <div className="form-group">
                  <label>Current Password</label>
                  <input type="password" value={passwords.current} onChange={e => setPasswords({ ...passwords, current: e.target.value })} className="form-input" />
                </div>
                <div className="form-group">
                  <label>New Password</label>
                  <input type="password" value={passwords.newPass} onChange={e => setPasswords({ ...passwords, newPass: e.target.value })} className="form-input" />
                </div>
                <div className="form-group">
                  <label>Confirm New Password</label>
                  <input type="password" value={passwords.confirm} onChange={e => setPasswords({ ...passwords, confirm: e.target.value })} className="form-input" />
                </div>
                <button type="submit" className="save-btn">Change Password</button>
              </form>
            </div>
          )}

          {activeTab === 'configs' && (
            <div>
              <h3 className="section-title">Saved Scan Configurations</h3>
              {configs.length > 0 && (
                <div className="configs-list">
                  {configs.map(c => (
                    <div key={c.id} className="config-item">
                      <div><strong>{c.name}</strong><span className="config-meta">{c.target_range} · {c.scan_type}</span></div>
                      <button className="del-btn" onClick={() => deleteConfig(c.id)}>Delete</button>
                    </div>
                  ))}
                </div>
              )}
              <h4 style={{ color: '#e4e6f0', margin: '24px 0 12px' }}>Add New Configuration</h4>
              <form onSubmit={addConfig} className="settings-form">
                <div className="form-group">
                  <label>Name</label>
                  <input type="text" value={newConfig.name} onChange={e => setNewConfig({ ...newConfig, name: e.target.value })} className="form-input" placeholder="e.g., Home Network" />
                </div>
                <div className="form-group">
                  <label>Target Range</label>
                  <input type="text" value={newConfig.target_range} onChange={e => setNewConfig({ ...newConfig, target_range: e.target.value })} className="form-input" placeholder="e.g., 192.168.1.0/24" />
                </div>
                <div className="form-group">
                  <label>Scan Type</label>
                  <select value={newConfig.scan_type} onChange={e => setNewConfig({ ...newConfig, scan_type: e.target.value })} className="form-input">
                    <option value="quick">Quick</option><option value="full">Full</option><option value="custom">Custom</option>
                  </select>
                </div>
                <button type="submit" className="save-btn">Save Configuration</button>
              </form>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .settings-page { max-width: 900px; }
        .page-title { font-size: 1.8rem; font-weight: 700; color: #e4e6f0; display: flex; align-items: center; gap: 10px; margin-bottom: 24px; }
        .settings-layout { display: grid; grid-template-columns: 200px 1fr; gap: 20px; }
        .settings-tabs { display: flex; flex-direction: column; gap: 4px; }
        .settings-tab { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border: none;
          border-radius: 10px; background: transparent; color: #8b8fa3; cursor: pointer; font-size: 0.9rem;
          text-align: left; transition: all 0.2s; }
        .settings-tab:hover { background: rgba(255,255,255,0.03); color: #e4e6f0; }
        .settings-tab.active { background: rgba(0,212,255,0.08); color: #00d4ff; }
        .settings-content { padding: 28px; border-radius: 16px; background: rgba(19,23,56,0.6);
          border: 1px solid rgba(255,255,255,0.05); }
        .section-title { color: #e4e6f0; font-size: 1.1rem; margin-bottom: 20px; }
        .settings-form { display: flex; flex-direction: column; gap: 16px; max-width: 400px; }
        .form-group label { display: block; color: #8b8fa3; font-size: 0.85rem; margin-bottom: 6px; }
        .form-input { width: 100%; padding: 12px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.03); color: #e4e6f0; font-size: 0.9rem; outline: none; }
        .form-input:focus { border-color: rgba(0,212,255,0.4); }
        .form-input:disabled { opacity: 0.5; }
        .save-btn { padding: 12px 24px; border: none; border-radius: 10px; background: linear-gradient(135deg, #00d4ff, #0099cc);
          color: #fff; font-weight: 600; cursor: pointer; transition: all 0.3s; align-self: flex-start; }
        .save-btn:hover { box-shadow: 0 4px 20px rgba(0,212,255,0.4); }
        .configs-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }
        .config-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px;
          border-radius: 10px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.03); }
        .config-item strong { color: #e4e6f0; }
        .config-meta { color: #8b8fa3; font-size: 0.8rem; margin-left: 10px; }
        .del-btn { padding: 4px 12px; border: none; border-radius: 6px; background: rgba(255,51,102,0.1);
          color: #ff3366; cursor: pointer; font-size: 0.8rem; }
        .del-btn:hover { background: rgba(255,51,102,0.2); }
        @media (max-width: 768px) { .settings-layout { grid-template-columns: 1fr; }
          .settings-tabs { flex-direction: row; overflow-x: auto; } }
      `}</style>
    </div>
  );
}

export default SettingsPage;
