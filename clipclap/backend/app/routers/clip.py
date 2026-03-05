from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import json

from ..models.schemas import ClassificationResponse, ClassificationResult, InferenceMetrics
from ..services.clip_service import clip_service

router = APIRouter(prefix="/api/clip", tags=["CLIP"])


@router.post("/classify", response_model=ClassificationResponse)
async def classify_image(
    image: UploadFile = File(...),
    labels: str = Form(...),  # JSON array or comma-separated string
):
    """
    Classify an image against candidate text labels using CLIP.

    - **image**: Image file (JPEG, PNG, etc.)
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

    # Read image
    image_bytes = await image.read()

    try:
        results, metrics = clip_service.classify(image_bytes, label_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

    return ClassificationResponse(
        results=[
            ClassificationResult(label=label, score=score, similarity=sim)
            for label, score, sim in results
        ],
        metrics=InferenceMetrics(**metrics),
    )
