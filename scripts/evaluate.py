from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from music_recommender.data import DEFAULT_DATA_PATH, load_tracks
from music_recommender.search import TfidfMusicSearch


def evaluate(engine: TfidfMusicSearch, queries: pd.DataFrame) -> dict[str, float]:
    ranks: list[int | None] = []
    catalogue_size = len(engine.tracks)
    grouped_queries = list(queries.groupby("query", sort=False))

    # Identical generic queries can correctly describe more than one track.
    # Treat all labelled tracks for the same text as relevant (multi-positive).
    if hasattr(engine, "score_queries"):
        texts = [query for query, _ in grouped_queries]
        score_matrix = engine.score_queries(texts)
        track_ids = engine.tracks["track_id"].astype(str).to_numpy()
        for scores, (_, group) in zip(score_matrix, grouped_queries):
            relevant = set(group["relevant_track_id"].astype(str))
            order = np.argsort(-scores, kind="stable")
            relevant_positions = np.flatnonzero(np.isin(track_ids[order], list(relevant)))
            ranks.append(int(relevant_positions[0]) + 1 if len(relevant_positions) else None)
    else:
        for query, group in grouped_queries:
            relevant = set(group["relevant_track_id"].astype(str))
            results = engine.search(query, top_k=catalogue_size)
            matches = results.index[results["track_id"].astype(str).isin(relevant)]
            ranks.append(int(matches[0]) + 1 if len(matches) else None)

    total = len(ranks)
    if total == 0:
        raise ValueError("The evaluation file contains no queries.")

    metrics: dict[str, float] = {
        "query_rows": float(len(queries)),
        "unique_queries": float(total),
    }
    for k in (1, 5, 10):
        metrics[f"recall@{k}"] = sum(rank is not None and rank <= k for rank in ranks) / total
    metrics["mrr@10"] = sum(
        1 / rank for rank in ranks if rank is not None and rank <= 10
    ) / total
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the TF-IDF retrieval baseline.")
    parser.add_argument("queries", type=Path, help="CSV with query,relevant_track_id columns")
    parser.add_argument("--tracks", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--model", choices=("tfidf", "qwen"), default="tfidf")
    parser.add_argument(
        "--qwen-prompt",
        choices=("listener_search", "caption_match", "balanced", "no_prompt"),
        default="caption_match",
    )
    parser.add_argument(
        "--split",
        choices=("train", "dev", "test", "all"),
        default="test",
        help="Evaluate one prepared split (default: test).",
    )
    args = parser.parse_args()

    if args.queries.suffix.lower() == ".parquet":
        queries = pd.read_parquet(args.queries)
    else:
        queries = pd.read_csv(args.queries, dtype={"relevant_track_id": str})
    if "relevant_track_id" not in queries.columns and "track_id" in queries.columns:
        queries = queries.rename(columns={"track_id": "relevant_track_id"})
    if args.split != "all" and "split" in queries.columns:
        queries = queries[queries["split"].eq(args.split)].copy()
    required = {"query", "relevant_track_id"}
    if not required.issubset(queries.columns):
        raise ValueError(f"Evaluation CSV must contain: {sorted(required)}")

    tracks = load_tracks(args.tracks)
    if args.model == "qwen":
        from music_recommender.qwen_search import QwenMusicSearch

        project_root = Path(__file__).resolve().parents[1]
        engine = QwenMusicSearch(
            tracks,
            project_root / "data" / "processed" / "qwen_embeddings.npy",
            project_root / "data" / "processed" / "qwen_track_ids.json",
            project_root / "models" / "huggingface",
            prompt_name=args.qwen_prompt,
        )
    else:
        engine = TfidfMusicSearch(tracks).fit()
    metrics = evaluate(engine, queries)
    print(pd.Series(metrics).to_string())


if __name__ == "__main__":
    main()
