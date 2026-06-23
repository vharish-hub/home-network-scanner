import React from 'react';

function LoadingSpinner({ text = 'Loading...' }) {
  return (
    <div className="loading-container">
      <div className="cyber-spinner">
        <div className="spinner-ring" />
        <div className="spinner-ring" />
        <div className="spinner-ring" />
      </div>
      <p className="loading-text">{text}</p>
    </div>
  );
}

export default LoadingSpinner;
