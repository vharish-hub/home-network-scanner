import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="loading-container"><div className="cyber-spinner"><div className="spinner-ring" /><div className="spinner-ring" /><div className="spinner-ring" /></div></div>;
  return isAuthenticated ? children : <Navigate to="/login" />;
}

export default ProtectedRoute;
