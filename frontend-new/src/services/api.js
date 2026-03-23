const BASE_URL = 'http://localhost:8000';

export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
};

export const analyzeData = async (filename) => {
  const res = await fetch(`${BASE_URL}/analyze?filename=${encodeURIComponent(filename)}`);
  if (!res.ok) throw new Error('Analysis failed');
  return res.json();
};

export const applyClean = async (filename, steps) => {
  const res = await fetch(`${BASE_URL}/apply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, steps }),
  });
  if (!res.ok) throw new Error('Apply failed');
  return res.json();
};
