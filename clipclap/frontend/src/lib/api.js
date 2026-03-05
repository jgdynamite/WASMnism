const API_BASE = '';

export async function classifyImage(imageFile, labels) {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('labels', JSON.stringify(labels));

  const response = await fetch(`${API_BASE}/api/clip/classify`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Classification failed');
  }

  return response.json();
}

export async function classifyAudio(audioFile, labels) {
  const formData = new FormData();
  formData.append('audio', audioFile);
  formData.append('labels', JSON.stringify(labels));

  const response = await fetch(`${API_BASE}/api/clap/classify`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Classification failed');
  }

  return response.json();
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE}/api/health`);
  return response.json();
}

export async function fetchSampleFile(path) {
  const response = await fetch(`${API_BASE}/samples/${path}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch sample: ${path}`);
  }
  const blob = await response.blob();
  const filename = path.split('/').pop();
  return new File([blob], filename, { type: blob.type });
}
