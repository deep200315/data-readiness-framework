const BASE = import.meta.env.VITE_API_URL || '';

export async function uploadFile(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/api/upload`, { method: 'POST', body: form });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Upload failed (${res.status})`);
  }
  return res.json();
}

export function pdfUrl(jobId) {
  return `${BASE}/api/report/${jobId}/pdf`;
}
