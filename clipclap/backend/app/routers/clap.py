from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import json

from ..models.schemas import ClassificationResponse, ClassificationResult, InferenceMetrics
from ..services.clap_service import clap_service

router = APIRouter(prefix="/api/clap", tags=["CLAP"])


@router.post("/classify", response_model=ClassificationResponse)
async def classify_audio(
    audio: UploadFile = File(...),
    labels: str = Form(...),  # JSON array or comma-separated string
):
    """
    Classify an audio clip against candidate text labels using CLAP.

    - **audio**: Audio file (WAV, MP3, etc.)
    - **labels**: JSON array of labels or comma-separated string
    """
    # Parse labels
    try:
        label_list = json.loads(labels)
    except json.JSONDecodeError:
        # Try comma-separated
        label_list = [l.strip() for l in labels.split(",") if l.strip()]

    if not label_list:
        raise HTTPException(status_code=400, detail="No labels provided")

    if len(label_list) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Too many labels. Maximum 1000 labels supported for reasonable inference time.",
        )

    # Read audio
    audio_bytes = await audio.read()

    try:
        results, metrics = clap_service.classify(audio_bytes, label_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

    return ClassificationResponse(
        results=[
            ClassificationResult(label=label, score=score, similarity=sim)
            for label, score, sim in results
        ],
        metrics=InferenceMetrics(**metrics),
    )
