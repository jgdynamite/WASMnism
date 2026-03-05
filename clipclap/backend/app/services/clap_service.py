import time
from typing import List, Tuple
from io import BytesIO
import numpy as np
import torch
import laion_clap


class CLAPService:
    _instance = None
    _model = None
    _device = None
    _model_load_time_ms: float = 0.0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            self._load_model()

    def _load_model(self):
        start_time = time.perf_counter()
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load CLAP model - using the 630k-audioset-best checkpoint
        self._model = laion_clap.CLAP_Module(enable_fusion=False)
        self._model.load_ckpt()  # Downloads and loads the default checkpoint
        self._model.eval()

        if self._device == "cuda":
            self._model = self._model.cuda()

        self._model_load_time_ms = (time.perf_counter() - start_time) * 1000
        print(f"CLAP model loaded on {self._device} in {self._model_load_time_ms:.2f}ms")

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def model_load_time(self) -> float:
        return self._model_load_time_ms

    def classify(
        self, audio_bytes: bytes, labels: List[str]
    ) -> Tuple[List[Tuple[str, float, float]], dict]:
        """
        Classify audio against a list of text labels.
        Returns sorted results (label, softmax_prob, raw_similarity) and timing metrics.
        """
        import tempfile
        import os

        metrics = {
            "model_load_ms": 0.0,  # Already loaded
            "input_encoding_ms": 0.0,
            "text_encoding_ms": 0.0,
            "similarity_ms": 0.0,
            "total_inference_ms": 0.0,
            "num_candidates": len(labels),
        }

        total_start = time.perf_counter()

        # Encode audio
        input_start = time.perf_counter()

        # Save to temp file for librosa to load (CLAP expects file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # Get audio embedding using CLAP's method
            audio_embed = self._model.get_audio_embedding_from_filelist(
                [tmp_path], use_tensor=True
            )
            if self._device == "cuda":
                audio_embed = audio_embed.cuda()
            audio_embed = audio_embed / audio_embed.norm(dim=-1, keepdim=True)
        finally:
            os.unlink(tmp_path)

        metrics["input_encoding_ms"] = (time.perf_counter() - input_start) * 1000

        # Encode text labels
        text_start = time.perf_counter()
        text_embed = self._model.get_text_embedding(labels, use_tensor=True)
        if self._device == "cuda":
            text_embed = text_embed.cuda()
        text_embed = text_embed / text_embed.norm(dim=-1, keepdim=True)
        metrics["text_encoding_ms"] = (time.perf_counter() - text_start) * 1000

        # Compute similarities
        sim_start = time.perf_counter()
        with torch.no_grad():
            similarities = (audio_embed @ text_embed.T).squeeze(0)
            # Convert to probabilities via softmax
            probs = similarities.softmax(dim=-1)
        metrics["similarity_ms"] = (time.perf_counter() - sim_start) * 1000

        metrics["total_inference_ms"] = (time.perf_counter() - total_start) * 1000

        # Build results with both softmax probs and raw cosine similarities
        probs_list = probs.cpu().numpy().tolist()
        sims_list = similarities.cpu().numpy().tolist()
        results = list(zip(labels, probs_list, sims_list))
        results.sort(key=lambda x: x[1], reverse=True)

        return results, metrics


# Singleton instance
clap_service = CLAPService()
