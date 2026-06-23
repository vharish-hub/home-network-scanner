import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FiShield, FiUser, FiLock } from 'react-icons/fi';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-toastify';

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) { toast.error('Please fill in all fields'); return; }
    setLoading(true);
    try {
      await login(username, password);
      toast.success('Login successful!');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.message || 'Login failed');
    } finally { setLoading(false); }
  };

  return (
    <div className="auth-page">
      <div className="auth-bg-grid" />
      <div className="auth-card glass-card">
        <div className="auth-icon"><FiShield size={36} /></div>
        <h2>Welcome Back</h2>
        <p className="auth-subtitle">Sign in to your security dashboard</p>
        <form onSubmit={handleSubmit}>
          <div className="auth-input-group">
            <FiUser className="input-icon" />
            <input type="text" placeholder="Username" value={username}
              onChange={(e) => setUsername(e.target.value)} className="auth-input" autoFocus />
          </div>
          <div className="auth-input-group">
            <FiLock className="input-icon" />
            <input type="password" placeholder="Password" value={password}
              onChange={(e) => setPassword(e.target.value)} className="auth-input" />
          </div>
          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <p className="auth-link">Don't have an account? <Link to="/register">Register</Link></p>
      </div>
      <style>{`
        .auth-page { min-height: 100vh; display: flex; align-items: center; justify-content: center;
          position: relative; overflow: hidden; }
        .auth-bg-grid { position: fixed; top: 0; left: 0; right: 0; bottom: 0;
          background-image: radial-gradient(circle at 1px 1px, rgba(0,212,255,0.05) 1px, transparent 0);
          background-size: 40px 40px; }
        .auth-card { position: relative; z-index: 1; width: 100%; max-width: 420px; padding: 40px;
          border-radius: 20px; background: rgba(19,23,56,0.85); backdrop-filter: blur(20px);
          border: 1px solid rgba(0,212,255,0.1); text-align: center;
          box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
        .auth-icon { width: 72px; height: 72px; border-radius: 50%; margin: 0 auto 20px;
          background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(0,255,136,0.1));
          display: flex; align-items: center; justify-content: center; color: #00d4ff;
          border: 1px solid rgba(0,212,255,0.2); }
        .auth-card h2 { color: #e4e6f0; margin-bottom: 6px; font-size: 1.5rem; }
        .auth-subtitle { color: #8b8fa3; margin-bottom: 28px; font-size: 0.9rem; }
        .auth-input-group { position: relative; margin-bottom: 16px; }
        .input-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
          color: #8b8fa3; font-size: 16px; }
        .auth-input { width: 100%; padding: 14px 14px 14px 42px; border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.03);
          color: #e4e6f0; font-size: 0.95rem; outline: none; transition: border-color 0.3s; }
        .auth-input:focus { border-color: rgba(0,212,255,0.4); }
        .auth-input::placeholder { color: #555; }
        .auth-btn { width: 100%; padding: 14px; border: none; border-radius: 10px;
          background: linear-gradient(135deg, #00d4ff, #0099cc); color: #fff; font-weight: 600;
          font-size: 1rem; cursor: pointer; transition: all 0.3s; margin-top: 8px; }
        .auth-btn:hover:not(:disabled) { box-shadow: 0 4px 20px rgba(0,212,255,0.4); transform: translateY(-1px); }
        .auth-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .auth-link { margin-top: 20px; color: #8b8fa3; font-size: 0.9rem; }
        .auth-link a { color: #00d4ff; text-decoration: none; }
        .auth-link a:hover { text-decoration: underline; }
      `}</style>
    </div>
  );
}

export default LoginPage;
