import api from './api';

const reportService = {
  generateReport: (scanId, data) => api.post(`/reports/generate/${scanId}`, data),
  getReports: () => api.get('/reports'),
  downloadReport: (filename) => api.get(`/reports/download/${filename}`, { responseType: 'blob' }),
  deleteReport: (filename) => api.delete(`/reports/${filename}`),
  exportReport: (scanId, format) => api.get(`/reports/export/${scanId}/${format}`, { responseType: 'blob' }),
};

export default reportService;
