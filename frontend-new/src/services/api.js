import axios from 'axios';

const RAW_BASE = import.meta.env.VITE_API_URL;
export const API_BASE =
  RAW_BASE !== undefined && RAW_BASE !== null && String(RAW_BASE).length > 0
    ? String(RAW_BASE).replace(/\/$/, '')
    : 'http://localhost:8000';

export function getStoredToken() {
  return sessionStorage.getItem('token') || localStorage.getItem('token');
}

export function setAuthToken(token, rememberMe) {
  try {
    localStorage.removeItem('token');
    sessionStorage.removeItem('token');
    if (rememberMe) {
      localStorage.setItem('token', token);
    } else {
      sessionStorage.setItem('token', token);
    }
  } catch {
    localStorage.setItem('token', token);
  }
}

export function clearAuthToken() {
  localStorage.removeItem('token');
  sessionStorage.removeItem('token');
}

// Create Axios instance
const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

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
