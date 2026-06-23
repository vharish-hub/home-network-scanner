import api from './api';

const dashboardService = {
  getSummary: () => api.get('/dashboard/summary'),
  getRecentScans: () => api.get('/dashboard/recent-scans'),
  getSeverityDistribution: () => api.get('/dashboard/severity-distribution'),
  getDeviceVulns: () => api.get('/dashboard/device-vulns'),
  getPortAnalysis: () => api.get('/dashboard/port-analysis'),
};

export default dashboardService;
