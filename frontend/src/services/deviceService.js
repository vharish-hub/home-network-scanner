import api from './api';

const deviceService = {
  getDevices: (params = {}) => api.get('/devices', { params }),
  getDevice: (id) => api.get(`/devices/${id}`),
};

export default deviceService;
