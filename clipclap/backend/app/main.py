from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .models.schemas import HealthResponse
from .routers import clip, clap

app = FastAPI(
    title="CLIP & CLAP Edge Inference Demo",
    description="Demonstrates contrastive language-image and language-audio models for edge deployment",
    version="1.0.0",
)

# CORS for local development (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(clip.router)
app.include_router(clap.router)

# Serve sample files
samples_path = Path(__file__).parent.parent / "samples"
if samples_path.exists():
    app.mount("/samples", StaticFiles(directory=str(samples_path)), name="samples")


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check API health and model loading status."""
    from .services.clip_service import clip_service
    from .services.clap_service import clap_service

    return HealthResponse(
        status="healthy",
        clip_loaded=clip_service.is_loaded,
        clap_loaded=clap_service.is_loaded,
    )


@app.on_event("startup")
async def startup_event():
    """Pre-load models on startup for faster first inference."""
    print("Starting CLIP & CLAP Edge Inference Demo API...")
    print("Models will be loaded on first request or can be pre-loaded.")
    # Note: Models are loaded lazily on first use via singleton pattern
    # To pre-load, uncomment below:
    # from .services.clip_service import clip_service
    # from .services.clap_service import clap_service


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
