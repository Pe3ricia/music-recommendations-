from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer


class TfidfMusicSearch:
    """Fast, deterministic lexical baseline for the first UI iteration."""

    def __init__(self, tracks: pd.DataFrame):
        self.tracks = tracks.reset_index(drop=True).copy()
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.98,
            sublinear_tf=True,
            norm="l2",
        )
        self.document_matrix: csr_matrix | None = None

    def fit(self) -> "TfidfMusicSearch":
        self.document_matrix = self.vectorizer.fit_transform(self.tracks["description"])
        return self

    def search(self, query: str, top_k: int = 5) -> pd.DataFrame:
        if self.document_matrix is None:
            raise RuntimeError("Call fit() before search().")
        if not query.strip():
            raise ValueError("Query must not be empty.")

        query_vector = self.vectorizer.transform([query])
        scores = (self.document_matrix @ query_vector.T).toarray().ravel()
        top_k = min(top_k, len(scores))
        top_indices = np.argsort(-scores, kind="stable")[:top_k]

        results = self.tracks.iloc[top_indices].copy()
        results["score"] = scores[top_indices]
        return results.reset_index(drop=True)

