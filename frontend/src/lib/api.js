import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const api = axios.create({
  baseURL: `${API_URL}/api`,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
    }
    return Promise.reject(error);
  }
);

// Payout APIs
export const getPayoutSummary = () => api.get('/payouts/summary');
export const getPayoutLedger = (status, page = 1) => api.get('/payouts/ledger', { params: { status, page } });
export const requestSettlement = () => api.post('/payouts/settle');
export const getSettlements = () => api.get('/payouts/settlements');

// Analytics APIs
export const getShopAnalytics = () => api.get('/analytics/shop');
export const getBikeAnalytics = (bikeId) => api.get(`/analytics/bike/${bikeId}`);
export const getPlatformAnalytics = () => api.get('/analytics/platform');

// Travel Agent APIs
export const getAgentDashboard = () => api.get('/travel-agent/dashboard');
export const generateReferralLink = (bikeId) => api.post('/travel-agent/generate-link', { bike_id: bikeId || null });
export const getCommissionLedger = (page = 1) => api.get('/travel-agent/commission-ledger', { params: { page } });

// Availability APIs
export const getBikeAvailability = (bikeId, month, year) => api.get(`/availability/${bikeId}`, { params: { month, year } });
export const checkBikeAvailability = (bikeId, startDate, endDate) => api.get(`/availability/${bikeId}/check`, { params: { start_date: startDate, end_date: endDate } });

// Review APIs
export const submitReview = (bookingId, rating, comment) => api.post('/reviews', { booking_id: bookingId, rating, comment });

// Admin APIs
export const getAdminDashboard = () => api.get('/admin/dashboard');
export const getAdminUsers = (params) => api.get('/admin/users', { params });
export const updateAdminUser = (userId, data) => api.put(`/admin/users/${userId}`, data);
export const getAdminPayouts = (params) => api.get('/admin/payouts', { params });
export const adminSettleShop = (shopId) => api.post(`/admin/payouts/${shopId}/settle`);
export const getAdminKyc = (params) => api.get('/admin/kyc', { params });
export const reviewKyc = (userId, status, notes) => api.post(`/admin/kyc/${userId}/review`, { status, notes });

// Application APIs
export const submitApplication = (data) => api.post('/applications/submit', data);
export const getApplications = (params) => api.get('/applications', { params });
export const approveApplication = (appId) => api.post(`/applications/${appId}/approve`);
export const rejectApplication = (appId, reason) => api.post(`/applications/${appId}/reject`, { reason });

// Auth extras
export const changePassword = (newPassword) => api.post('/auth/change-password', { new_password: newPassword });

export default api;
