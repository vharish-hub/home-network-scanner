import api from './api';

const scanService = {
  startScan: (data) => api.post('/scans/start', data),
  getScans: () => api.get('/scans'),
  getScan: (id) => api.get(`/scans/${id}`),
  getScanStatus: (id) => api.get(`/scans/${id}/status`),
  deleteScan: (id) => api.delete(`/scans/${id}`),
};

export default scanService;
