# CLIP & CLAP Edge Inference Demo

A single-page web application demonstrating **CLIP** (Contrastive Language-Image Pre-Training) and **CLAP** (Contrastive Language-Audio Pretraining) for zero-shot classification. Built for a live demo showcasing these models as ideal candidates for inference at the edge.

## Key Narrative

**Language is a universal bridge for perception.** Contrastive models like CLIP and CLAP are:
- Lightweight enough to deploy at the edge (~350MB)
- Flexible enough for zero-shot classification without retraining
- Operationally simple: update text labels, not model artifacts

## Features

- **CLIP Demo**: Upload/select images and classify against custom text labels
- **CLAP Demo**: Upload/select audio and classify against custom text labels
- **Metrics Panel**: Real-time performance visualization showing:
  - Input encoding time
  - Text encoding time (scales with label count)
  - Similarity computation time
  - Request history with scaling visualization

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- ~2GB disk space for models (downloaded on first run)

### Setup

```bash
# Clone and enter directory
cd clipclap

# Install all dependencies
make setup

# Download sample data
make samples
```

### Running the Demo

Open **two terminals**:

**Terminal 1 - Backend:**
```bash
make dev-backend
# API runs at http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
make dev-frontend
# App runs at http://localhost:5173
```

Open http://localhost:5173 in your browser.

## Manual Setup (without Make)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python download_samples.py
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
clipclap/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── routers/          # API endpoints
│   │   │   ├── clip.py       # POST /api/clip/classify
│   │   │   └── clap.py       # POST /api/clap/classify
│   │   ├── services/         # Model inference logic
│   │   │   ├── clip_service.py
│   │   │   └── clap_service.py
│   │   └── models/
│   │       └── schemas.py    # Pydantic models
│   ├── samples/              # Sample images and audio
│   ├── requirements.txt
│   └── download_samples.py
├── frontend/
│   ├── src/
│   │   ├── App.svelte        # Main application
│   │   ├── components/
│   │   │   ├── ClipDemo.svelte
│   │   │   ├── ClapDemo.svelte
│   │   │   ├── MetricsPanel.svelte
│   │   │   └── ResultsDisplay.svelte
│   │   └── lib/
│   │       └── api.js        # API client
│   ├── package.json
│   └── vite.config.js
├── Makefile
└── README.md
```

## API Endpoints

### POST /api/clip/classify
Classify an image against text labels.

```bash
curl -X POST http://localhost:8000/api/clip/classify \
  -F "image=@photo.jpg" \
  -F 'labels=["cat", "dog", "bird"]'
```

### POST /api/clap/classify
Classify audio against text labels.

```bash
curl -X POST http://localhost:8000/api/clap/classify \
  -F "audio=@sound.wav" \
  -F 'labels=["dog barking", "music", "speech"]'
```

### Response Format

```json
{
  "results": [
    { "label": "cat", "score": 0.85, "similarity": 0.287 },
    { "label": "dog", "score": 0.12, "similarity": 0.203 },
    { "label": "bird", "score": 0.03, "similarity": 0.156 }
  ],
  "metrics": {
    "model_load_ms": 0,
    "input_encoding_ms": 45.2,
    "text_encoding_ms": 12.8,
    "similarity_ms": 0.3,
    "total_inference_ms": 58.3,
    "num_candidates": 3
  }
}
```

**Score types:**
- `score`: Softmax probability (0-1, sums to 1 across all labels) - relative ranking
- `similarity`: Raw cosine similarity (-1 to 1) - absolute match strength. 0.25+ is good, 0.30+ is strong
```

## Demo Tips

### Key Demo Moments

1. **Zero-shot flexibility**: Change labels on the fly and re-run classification instantly
2. **Scaling visualization**: Run with 10, then 100, then 500 labels and watch metrics change
3. **Cross-modal symmetry**: Same architecture, different modalities (image vs audio)

### Talking Points

- **Sweet spot**: 300-400 candidate labels for reliable discrimination
- **Upper limit**: ~1000 labels before inference time becomes noticeable
- **Model sizes**: CLIP ViT-B/32 ~350MB, CLAP similar
- **vs YOLO**: YOLO gives bounding boxes; CLIP/CLAP give classification. Different tools.
- **Operational win**: Update a config file (labels), not retrain a model

## Troubleshooting

### Models not loading
Models are downloaded on first inference. Ensure you have internet access and ~2GB free disk space.

### CUDA not detected
The app works on CPU. GPU acceleration is automatic if CUDA is available.

### Audio classification slow
Audio encoding is more compute-intensive than image encoding. This is expected.

### CORS errors
Ensure the Vite proxy is configured and both servers are running.

## Tech Stack

- **Backend**: Python, FastAPI, PyTorch, OpenAI CLIP, LAION CLAP
- **Frontend**: Svelte 4, Vite 5
- **Models**: CLIP ViT-B/32, CLAP (630k-audioset-best)
