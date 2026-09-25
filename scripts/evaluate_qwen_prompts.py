from __future__ import annotations

from pathlib import Path

import pandas as pd

from music_recommender.data import DEFAULT_DATA_PATH, load_tracks
from music_recommender.qwen_search import QUERY_PROMPTS, QwenMusicSearch
from scripts.evaluate import evaluate


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    queries = pd.read_parquet(project_root / "data" / "processed" / "queries.parquet")
    queries = queries[queries["split"].eq("test")].rename(
        columns={"track_id": "relevant_track_id"}
    )
    engine = QwenMusicSearch(
        load_tracks(DEFAULT_DATA_PATH),
        project_root / "data" / "processed" / "qwen_embeddings.npy",
        project_root / "data" / "processed" / "qwen_track_ids.json",
        project_root / "models" / "huggingface",
    )

    rows = []
    for prompt_name in QUERY_PROMPTS:
        engine.prompt_name = prompt_name
        metrics = evaluate(engine, queries)
        rows.append({"prompt": prompt_name, **metrics})

    results = pd.DataFrame(rows).sort_values("mrr@10", ascending=False)
    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
