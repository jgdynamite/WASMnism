# ClipClap Repo Inspection

**Date:** March 5, 2025  
**Purpose:** Inform benchmark contract and edge gateway design for WASMnisum.

---

## Repository Structure

```
clipclap/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app, CORS, /api/health
│   │   ├── routers/
│   │   │   ├── clip.py       # POST /api/clip/classify
│   │   │   └── clap.py       # POST /api/clap/classify
│   │   ├── services/
│   │   │   ├── clip_service.py
│   │   │   └── clap_service.py
│   │   └── models/
│   │       └── schemas.py    # Pydantic models
│   ├── samples/              # Sample images/audio (gitignored)
│   ├── requirements.txt
│   └── download_samples.py
├── frontend/
│   ├── src/
│   │   ├── App.svelte
│   │   ├── components/      # ClipDemo, ClapDemo, MetricsPanel, ResultsDisplay
│   │   └── lib/api.js       # API client
│   ├── package.json
│   └── vite.config.js
├── Makefile
└── README.md
```

---

## API Endpoints

### POST /api/clip/classify

**Input:** multipart/form-data
- `image`: file (JPEG, PNG, etc.)
- `labels`: JSON array string or comma-separated (e.g. `["cat", "dog", "bird"]`)

**Constraints:** max 1000 labels

**Response:**
```json
{
  "results": [
    { "label": "cat", "score": 0.85, "similarity": 0.287 },
    { "label": "dog", "score": 0.12, "similarity": 0.203 }
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

### POST /api/clap/classify

**Input:** multipart/form-data
- `audio`: file (WAV, MP3, etc.)
- `labels`: same as CLIP

**Response:** Same schema as CLIP.

### GET /api/health

```json
{
  "status": "healthy",
  "clip_loaded": true,
  "clap_loaded": true
}
```

---

## Schemas (from schemas.py)

| Model | Fields |
|-------|--------|
| `ClassificationResult` | `label`, `score` (softmax 0–1), `similarity` (cosine -1 to 1) |
| `InferenceMetrics` | `model_load_ms`, `input_encoding_ms`, `text_encoding_ms`, `similarity_ms`, `total_inference_ms`, `num_candidates` |
| `ClassificationResponse` | `results: List[ClassificationResult]`, `metrics: InferenceMetrics` |

---

## Gateway Design Implications

1. **Payload format:** Multipart form-data. Edge gateway must either:
   - Forward multipart to inference service (proxy), or
   - Accept base64/URL and translate to multipart for inference.

2. **Gateway-only path:** For pure edge benchmarking (no inference), gateway can:
   - Return mock/deterministic response with same JSON schema, or
   - Implement a `/gateway/health` or `/gateway/echo` that exercises routing/auth/caching only.

3. **Inference service contract:** Gateway → inference needs:
   - `/infer/clip` and `/infer/clap` (or reuse `/api/clip/classify`, `/api/clap/classify`)
   - Timeout and error mapping defined in benchmark_contract.md

4. **Tech stack:** Backend is Python/FastAPI, PyTorch, CLIP, CLAP. Models ~350MB each. Inference stays in Python; gateway is the portable unit.

---

## Existing .gitignore (clipclap)

Already covers: venv, .env, model caches, node_modules, samples, docs/. We extend at WASMnisum root for benchmarks, cost config, Terraform, etc.
