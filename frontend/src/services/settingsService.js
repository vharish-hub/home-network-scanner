import api from './api';

const settingsService = {
  getScanConfigs: () => api.get('/settings/scan-configs'),
  createScanConfig: (data) => api.post('/settings/scan-configs', data),
  updateScanConfig: (id, data) => api.put(`/settings/scan-configs/${id}`, data),
  deleteScanConfig: (id) => api.delete(`/settings/scan-configs/${id}`),
  getProfile: () => api.get('/settings/profile'),
  updateProfile: (data) => api.put('/settings/profile', data),
  changePassword: (data) => api.put('/settings/password', data),
};

export default settingsService;
