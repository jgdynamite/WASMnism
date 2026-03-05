import time
from typing import List, Tuple
from io import BytesIO
import torch
import open_clip
from PIL import Image


class CLIPService:
    _instance = None
    _model = None
    _preprocess = None
    _tokenizer = None
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

        # Load OpenCLIP model (ViT-B-32 with OpenAI's pretrained weights)
        self._model, _, self._preprocess = open_clip.create_model_and_transforms(
            'ViT-B-32', pretrained='openai'
        )
        self._model = self._model.to(self._device)
        self._model.eval()
        self._tokenizer = open_clip.get_tokenizer('ViT-B-32')

        self._model_load_time_ms = (time.perf_counter() - start_time) * 1000
        print(f"CLIP model loaded on {self._device} in {self._model_load_time_ms:.2f}ms")

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def model_load_time(self) -> float:
        return self._model_load_time_ms

    def classify(
        self, image_bytes: bytes, labels: List[str]
    ) -> Tuple[List[Tuple[str, float, float]], dict]:
        """
        Classify an image against a list of text labels.
        Returns sorted results (label, softmax_prob, raw_similarity) and timing metrics.
        """
        metrics = {
            "model_load_ms": 0.0,  # Already loaded
            "input_encoding_ms": 0.0,
            "text_encoding_ms": 0.0,
            "similarity_ms": 0.0,
            "total_inference_ms": 0.0,
            "num_candidates": len(labels),
        }

        total_start = time.perf_counter()

        # Encode image
        input_start = time.perf_counter()
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image_input = self._preprocess(image).unsqueeze(0).to(self._device)
        with torch.no_grad():
            image_features = self._model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
        metrics["input_encoding_ms"] = (time.perf_counter() - input_start) * 1000

        # Encode text labels
        text_start = time.perf_counter()
        text_tokens = self._tokenizer(labels).to(self._device)
        with torch.no_grad():
            text_features = self._model.encode_text(text_tokens)
            text_features /= text_features.norm(dim=-1, keepdim=True)
        metrics["text_encoding_ms"] = (time.perf_counter() - text_start) * 1000

        # Compute similarities
        sim_start = time.perf_counter()
        with torch.no_grad():
            similarities = (image_features @ text_features.T).squeeze(0)
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
clip_service = CLIPService()
