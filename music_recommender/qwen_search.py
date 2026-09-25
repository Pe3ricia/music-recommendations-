from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


QWEN_MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
QUERY_TASKS = {
    "listener_search": (
        "Given a listener's natural-language music search request, retrieve track "
        "descriptions that best match the requested listening experience"
    ),
    "caption_match": (
        "Given a short description of music, retrieve track descriptions for music "
        "with the same mood, style, energy, rhythm, instruments, vocals, and sound"
    ),
    "balanced": (
        "Given a natural-language description of desired music, retrieve tracks whose "
        "musical style, mood, energy, instrumentation, and vocals best match the request"
    ),
}
QUERY_PROMPTS = {
    name: f"Instruct: {task}\nQuery: " for name, task in QUERY_TASKS.items()
}
QUERY_TASKS["no_prompt"] = "Encode the query without an instruction"
QUERY_PROMPTS["no_prompt"] = None
DEFAULT_PROMPT_NAME = "caption_match"


class QwenMusicSearch:
    """Dense music retrieval using a precomputed Qwen document index."""

    def __init__(
        self,
        tracks: pd.DataFrame,
        embeddings_path: str | Path,
        track_ids_path: str | Path,
        cache_folder: str | Path,
        model_name: str = QWEN_MODEL_NAME,
        prompt_name: str = DEFAULT_PROMPT_NAME,
    ):
        import torch
        from sentence_transformers import SentenceTransformer

        self.tracks = tracks.reset_index(drop=True).copy()
        self.embeddings = np.load(embeddings_path)
        indexed_ids = json.loads(Path(track_ids_path).read_text(encoding="utf-8"))
        current_ids = self.tracks["track_id"].astype(str).tolist()

        if indexed_ids != current_ids:
            raise ValueError("Qwen index does not match the current track catalogue.")
        if len(self.embeddings) != len(self.tracks):
            raise ValueError("Qwen embedding count does not match the catalogue.")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model_kwargs = {"torch_dtype": torch.float16} if device == "cuda" else None
        self.model = SentenceTransformer(
            model_name,
            device=device,
            cache_folder=str(cache_folder),
            local_files_only=True,
            model_kwargs=model_kwargs,
        )
        self.model.max_seq_length = 512
        self.prompt_name = prompt_name

    def search(self, query: str, top_k: int = 5) -> pd.DataFrame:
        if not query.strip():
            raise ValueError("Query must not be empty.")

        scores = self.score_queries([query], batch_size=1)[0]
        top_k = min(top_k, len(scores))
        top_indices = np.argsort(-scores, kind="stable")[:top_k]

        results = self.tracks.iloc[top_indices].copy()
        results["score"] = scores[top_indices]
        return results.reset_index(drop=True)

    def score_queries(self, queries: list[str], batch_size: int = 4) -> np.ndarray:
        """Return cosine scores with shape (queries, catalogue tracks)."""
        if self.prompt_name not in QUERY_PROMPTS:
            raise ValueError(f"Unknown Qwen prompt: {self.prompt_name}")
        query_embeddings = self.model.encode(
            queries,
            prompt=QUERY_PROMPTS[self.prompt_name],
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return query_embeddings @ self.embeddings.T
