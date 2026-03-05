from pydantic import BaseModel
from typing import List, Optional


class ClassificationResult(BaseModel):
    label: str
    score: float  # Softmax probability (0-1, sums to 1 across all labels)
    similarity: float  # Raw cosine similarity (-1 to 1, higher = better match)


class InferenceMetrics(BaseModel):
    model_load_ms: float = 0.0
    input_encoding_ms: float
    text_encoding_ms: float
    similarity_ms: float
    total_inference_ms: float
    num_candidates: int


class ClassificationResponse(BaseModel):
    results: List[ClassificationResult]
    metrics: InferenceMetrics


class HealthResponse(BaseModel):
    status: str
    clip_loaded: bool
    clap_loaded: bool
