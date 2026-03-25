const BASE_URL = 'http://localhost:8000';

// 1. Dosya yükleme → { dataset_id, meta } döner
export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Upload failed');
  return res.json(); // { dataset_id, meta }
};

// 2. Analiz → /analyze/{dataset_id}
export const analyzeData = async (datasetId) => {
  const res = await fetch(`${BASE_URL}/analyze/${datasetId}`);
  if (!res.ok) throw new Error('Analysis failed');
  return res.json(); // { profile, recommendations }
};

// 3. Pipeline uygula → /apply/{dataset_id} + { selections: [{category, column, method}] }
export const applyClean = async (datasetId, selections) => {
  const res = await fetch(`${BASE_URL}/apply/${datasetId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selections }),
  });
  if (!res.ok) throw new Error('Apply failed');
  return res.json();
};
