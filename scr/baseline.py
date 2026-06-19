import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sentence_transformers.cross_encoder import CrossEncoder


class MusicSearchBaseline:
    def __init__(
        self,
        tracks: pd.DataFrame,
        text_col: str = "description",
        artist_col: str = "artist",
        title_col: str = "name",
        encoder_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        reranker_name: str | None = "cross-encoder/ms-marco-MiniLM-L6-v2",
    ):
        self.tracks = tracks.reset_index(drop=True).copy()
        self.text_col = text_col
        self.artist_col = artist_col
        self.title_col = title_col

        self.encoder_name = encoder_name
        self.reranker_name = reranker_name

        self.encoder = SentenceTransformer(self.encoder_name)
        self.reranker = CrossEncoder(self.reranker_name) if self.reranker_name else None

        self.texts = self.tracks[self.text_col].fillna("").astype(str).tolist()
        self.embeddings = None

    def fit(self, batch_size: int = 64, normalize_embeddings: bool = True):
        self.embeddings = self.encoder.encode(
            self.texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=normalize_embeddings,
        )
        return self

    def encode_query(self, query: str):
        return self.encoder.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]

    def retrieve(self, query: str, top_n: int = 50):
        if self.embeddings is None:
            raise ValueError("Сначала вызови fit(), чтобы посчитать эмбеддинги.")

        query_vec = self.encode_query(query)
        sims = self.embeddings @ query_vec
        top_idx = np.argsort(-sims)[:top_n]

        result = self.tracks.iloc[top_idx].copy()
        result["retrieval_score"] = sims[top_idx]
        result["track_idx"] = top_idx
        return result.reset_index(drop=True)

    def rerank(self, query: str, candidates: pd.DataFrame, final_k: int = 10):
        if self.reranker is None:
            return candidates.head(final_k).copy()

        pairs = [
            [query, str(text)]
            for text in candidates[self.text_col].fillna("").astype(str).tolist()
        ]

        cross_scores = self.reranker.predict(pairs)

        result = candidates.copy()
        result["rerank_score"] = cross_scores
        result = result.sort_values("rerank_score", ascending=False).head(final_k)
        return result.reset_index(drop=True)

    def search(self, query: str, top_n: int = 50, final_k: int = 10, use_rerank: bool = True):
        candidates = self.retrieve(query=query, top_n=top_n)

        if use_rerank and self.reranker is not None:
            result = self.rerank(query=query, candidates=candidates, final_k=final_k)
        else:
            result = candidates.head(final_k).copy()

        cols = [
            self.artist_col,
            self.title_col,
            self.text_col,
            "retrieval_score",
        ]
        if "rerank_score" in result.columns:
            cols.append("rerank_score")
        if "track_idx" in result.columns:
            cols.append("track_idx")

        return result[cols]

    def save_embeddings(self, path: str):
        if self.embeddings is None:
            raise ValueError("Нет эмбеддингов: сначала вызови fit().")
        np.save(path, self.embeddings)

    def load_embeddings(self, path: str):
        self.embeddings = np.load(path)
        return self