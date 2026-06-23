import axios from 'axios';

const RAW_BASE = import.meta.env.VITE_API_URL;
const _base =
  RAW_BASE !== undefined && RAW_BASE !== null && String(RAW_BASE).length > 0
    ? String(RAW_BASE).replace(/\/$/, '')
    : 'http://localhost:8000';
// Tüm backend endpoint'leri /api/v1 prefix'i altında
export const API_BASE = `${_base}/api/v1`;

const TOKEN_KEY = 'token';
const REFRESH_KEY = 'refresh_token';

export function getStoredToken() {
  return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY);
}

export function getStoredRefreshToken() {
  return localStorage.getItem(REFRESH_KEY) || sessionStorage.getItem(REFRESH_KEY);
}

export function setAuthToken(token, rememberMe, refreshToken) {
  try {
    localStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    sessionStorage.removeItem(REFRESH_KEY);

    const storage = rememberMe ? localStorage : sessionStorage;
    storage.setItem(TOKEN_KEY, token);
    if (refreshToken) {
      // Refresh token'ı her zaman localStorage'da sakla (sekme kapansa bile hatırlansın)
      localStorage.setItem(REFRESH_KEY, refreshToken);
    }
  } catch {
    localStorage.setItem(TOKEN_KEY, token);
    if (refreshToken) localStorage.setItem(REFRESH_KEY, refreshToken);
  }
}

export function clearAuthToken() {
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  sessionStorage.removeItem(REFRESH_KEY);
}

// ── Axios instance ────────────────────────────────────────────────────────────
const api = axios.create({
  baseURL: API_BASE,
});

// Request: her istekte geçerli access token'ı header'a ekle
api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response: 401 alındığında refresh token ile yeni access token al
let _isRefreshing = false;
let _failedQueue = [];

const processQueue = (error, token = null) => {
  _failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve(token);
  });
  _failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    // Refresh endpoint'inin kendisi 401 dönerse sonsuz döngüye girme
    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url?.includes('/refresh')) {
      if (_isRefreshing) {
        // Başka bir refresh devam ediyorsa kuyruğa ekle
        return new Promise((resolve, reject) => {
          _failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        }).catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      _isRefreshing = true;

      const refreshToken = getStoredRefreshToken();
      if (!refreshToken) {
        _isRefreshing = false;
        clearAuthToken();
        window.dispatchEvent(new CustomEvent('auth:expired'));
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post(`${API_BASE}/refresh`, { refresh_token: refreshToken });
        const newAccessToken = data.access_token;
        // Yeni access token'ı kaydet (rememberMe durumunu koru)
        const inLocal = !!localStorage.getItem(TOKEN_KEY);
        (inLocal ? localStorage : sessionStorage).setItem(TOKEN_KEY, newAccessToken);
        processQueue(null, newAccessToken);
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearAuthToken();
        window.dispatchEvent(new CustomEvent('auth:expired'));
        return Promise.reject(refreshError);
      } finally {
        _isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

function parseDetail(error) {
  const data = error?.response?.data;
  const d = data?.detail;
  if (d == null) return error?.message || 'İstek başarısız';
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join(', ');
  return String(d);
}

export async function fetchMe() {
  try {
    const res = await api.get('/me');
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
}

export async function fetchAccountSummary() {
  try {
    const res = await api.get('/me/account');
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
}

export async function changePassword(currentPassword, newPassword) {
  try {
    const res = await api.post('/me/password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
}

export const uploadFile = async (file, projectId = null) => {
  const formData = new FormData();
  formData.append('file', file);
  if (projectId != null && projectId !== '') {
    formData.append('project_id', String(projectId));
  }
  try {
    const res = await api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const analyzeData = async (datasetId) => {
  try {
    const res = await api.get(`/analyze/${datasetId}`);
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const getDatasetStatus = async (datasetId) => {
  try {
    const res = await api.get(`/datasets/${datasetId}/status`);
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const fetchDatasetWorkspace = async (datasetId) => {
  try {
    const res = await api.get(`/datasets/${datasetId}/workspace`);
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const applyClean = async (datasetId, selections) => {
  try {
    const res = await api.post(`/apply/${datasetId}`, { selections });
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const registerUser = async (email, password) => {
  try {
    const res = await api.post('/register', { email, password });
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const loginUser = async (email, password) => {
  try {
    const res = await api.post('/login', { email, password });
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const forgotPassword = async (email) => {
  try {
    const res = await api.post('/forgot-password', { email });
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const resetPassword = async (token, newPassword) => {
  try {
    const res = await api.post('/reset-password', { token, new_password: newPassword });
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const fetchMyDatasets = async (projectId = null) => {
  const params = projectId != null && projectId !== '' ? { project_id: projectId } : {};
  try {
    const res = await api.get('/me/datasets', { params });
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const updateDatasetProject = async (datasetId, projectId) => {
  try {
    const res = await api.put(`/datasets/${datasetId}/project`, {
      project_id: projectId === '' ? null : Number(projectId)
    });
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const deleteDataset = async (datasetId) => {
  try {
    const res = await api.delete(`/datasets/${datasetId}`);
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const fetchProjects = async () => {
  try {
    const res = await api.get('/projects');
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const createProject = async (name, description = null) => {
  try {
    const res = await api.post('/projects', { name, description });
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const deleteProject = async (projectId) => {
  try {
    const res = await api.delete(`/projects/${projectId}`);
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const fetchTemplates = async () => {
  try {
    const res = await api.get('/me/templates');
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const saveTemplate = async (name, selections) => {
  try {
    const res = await api.post('/me/templates', { name, selections });
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const deleteTemplate = async (templateId) => {
  try {
    const res = await api.delete(`/me/templates/${templateId}`);
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const applyTemplateToDataset = async (datasetId, templateId) => {
  try {
    const res = await api.post(`/datasets/${datasetId}/apply-template/${templateId}`);
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export const fetchProjectTimeline = async (projectId) => {
  try {
    const res = await api.get(`/projects/${projectId}/timeline`);
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
};

export async function downloadAuditExport(datasetId) {
  try {
    const res = await api.get(`/datasets/${datasetId}/audit-export`, { responseType: 'blob' });
    const dispo = res.headers['content-disposition'];
    let name = `denetim_${datasetId}.csv`;
    const m = dispo && /filename="?([^";]+)"?/i.exec(dispo);
    if (m) name = m[1];
    const url = URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    throw new Error(parseDetail(e));
  }
}

export async function sendAssistantChat(messages) {
  try {
    const res = await api.post('/assistant/chat', { messages });
    return res.data;
  } catch (e) {
    throw new Error(parseDetail(e));
  }
}

export async function downloadCleanedDataset(datasetId, filenameHint = 'temizlenmis.csv') {
  try {
    const res = await api.get(`/download/${datasetId}`, { responseType: 'blob' });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = filenameHint;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    throw new Error(parseDetail(e));
  }
}

export async function downloadQualityReport(datasetId, format = 'html', reportId = null) {
  let urlStr = `/datasets/${datasetId}/report?format=${format}`;
  if (reportId) {
    urlStr += `&report_id=${reportId}`;
  }
  try {
    const res = await api.get(urlStr, { responseType: 'blob' });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = reportId ? `kalite_raporu_${datasetId}_${reportId}.${format}` : `kalite_raporu_${datasetId}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    throw new Error(parseDetail(e));
  }
}
