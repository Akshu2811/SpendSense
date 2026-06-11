import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Token lives only in module memory — never in localStorage/sessionStorage/cookies
let _token = null;

export const setToken = (token) => { _token = token; };
export const clearToken = () => { _token = null; };
export const getToken = () => _token;
export const isAuthenticated = () => Boolean(_token);

// Attach token on every request
api.interceptors.request.use((config) => {
  if (_token) {
    config.headers.Authorization = `Bearer ${_token}`;
  }
  return config;
});

// On 401 clear token and send to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearToken();
      window.location = '/login';
    }
    return Promise.reject(error);
  }
);

// ── Auth ────────────────────────────────────────────────────────────────────
export const register = (username, password) =>
  api.post('/auth/register', { username, password }).then((r) => r.data);

export const login = async (username, password) => {
  const data = await api.post('/auth/login', { username, password }).then((r) => r.data);
  setToken(data.access_token);
  return data;
};

export const logout = () => {
  clearToken();
};

// ── Wallet ───────────────────────────────────────────────────────────────────
export const getWalletState = () =>
  api.get('/wallet-state').then((r) => r.data);

// ── Budget ───────────────────────────────────────────────────────────────────
export const setupBudget = (masterMonthly, categories) =>
  api.post('/budget/setup', { master_monthly: masterMonthly, categories }).then((r) => r.data);

export const updateBudget = (data) =>
  api.put('/budget/update', data).then((r) => r.data);

export const getCurrentBudget = () =>
  api.get('/budget/current').then((r) => r.data);

// ── Transactions ──────────────────────────────────────────────────────────────
export const syncTransactions = () =>
  api.post('/transactions/sync').then((r) => r.data);

export const uploadCsv = (file) => {
  const form = new FormData();
  form.append('file', file);
  return api.post('/transactions/upload-csv', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
};

export const getRecentTransactions = () =>
  api.get('/transactions/recent').then((r) => r.data);

export const getTransactionSummary = () =>
  api.get('/transactions/summary').then((r) => r.data);

// ── Purchases ────────────────────────────────────────────────────────────────
export const uploadScreenshot = (file) => {
  const form = new FormData();
  form.append('file', file);
  return api.post('/purchases/screenshot', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
};

export const uploadScreenshots = (files) => {
  const formData = new FormData();
  files.forEach((file, i) => {
    formData.append(`file_${i}`, file);
  });
  formData.append('file_count', files.length);
  return api.post('/purchases/screenshot-multi', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
};

export const addManual = (itemName, platform, amount, category) =>
  api.post('/purchases/manual', { item_name: itemName, platform, amount, category }).then((r) => r.data);

export const checkBeforeBuy = (file) => {
  const form = new FormData();
  form.append('file', file);
  return api.post('/purchases/check', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
};

export const getPurchaseHistory = () =>
  api.get('/purchases/history').then((r) => r.data);

// ── Nudges ───────────────────────────────────────────────────────────────────
export const fireNudge = (triggerType, platform, context) =>
  api.post('/nudges/fire', { trigger_type: triggerType, platform, context }).then((r) => r.data);

export const respondToNudge = (nudgeId, response) =>
  api.post('/nudges/respond', { nudge_id: nudgeId, response }).then((r) => r.data);

export const getNudgeHistory = () =>
  api.get('/nudges/history').then((r) => r.data);

// ── Reports ──────────────────────────────────────────────────────────────────
export const getCurrentReport = () =>
  api.get('/report/current-month').then((r) => r.data);

export const deleteAccount = () =>
  api.delete('/auth/account').then((r) => r.data);

// ── Agent ────────────────────────────────────────────────────────────────────
export const morningCheck = () =>
  api.post('/agent/morning-check').then((r) => r.data);

export const preShopCheck = (platform) =>
  api.post('/agent/pre-shop-check', { platform }).then((r) => r.data);

export default api;
