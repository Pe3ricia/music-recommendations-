from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


BOILERPLATE_PREFIX = re.compile(
    r"^\s*(?:"
    r"this\s+is\s+|"
    r"this\s+(?:track|song|music|audio)\s+(?:is|has|features)\s+|"
    r"the\s+(?:track|song|music|audio)\s+(?:is|has|features)\s+|"
    r"this\s+"
    r")",
    flags=re.IGNORECASE,
)


def clean_query(value: object) -> str:
    """Normalize a generated caption into a short search query."""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("\n", " ").strip().strip("\"'`“”‘’")
    text = re.sub(r"\s+", " ", text)

    # Run repeatedly because strings such as "this is the track is ..." can
    # contain more than one generation scaffold.
    previous = None
    while text != previous:
        previous = text
        text = BOILERPLATE_PREFIX.sub("", text, count=1).lstrip(" ,:;-—")

    text = text.strip().rstrip(" ,:;-—")
    if text:
        text = text[0].lower() + text[1:]
    return text


def _query_id(track_id: str, prompt_id: str) -> str:
    value = f"{track_id}|{prompt_id}".encode("utf-8")
    return hashlib.sha1(value).hexdigest()[:16]


def load_lightweight_tracks(path: str | Path) -> pd.DataFrame:
    """Read metadata and descriptions while skipping embedded audio bytes."""
    table = pq.read_table(
        path,
        columns=["audio.path", "title", "artist", "description"],
    )
    tracks = table.to_pandas().rename(columns={"path": "track_id"})
    tracks["track_id"] = tracks["track_id"].astype(str).str.strip()
    tracks["title"] = tracks["title"].fillna("").astype(str).str.strip()
    tracks["artist"] = tracks["artist"].fillna("").astype(str).str.strip()
    tracks["description"] = tracks["description"].fillna("").astype(str).str.strip()
    tracks = tracks[tracks["track_id"].ne("") & tracks["description"].ne("")]

    if tracks["track_id"].duplicated().any():
        duplicates = tracks.loc[tracks["track_id"].duplicated(), "track_id"].tolist()
        raise ValueError(f"Duplicate track IDs in catalogue: {duplicates[:5]}")
    return tracks.reset_index(drop=True)


def load_and_clean_queries(directory: str | Path) -> pd.DataFrame:
    files = sorted(Path(directory).glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No intent CSV files found in {directory}")

    frames = []
    for path in files:
        frame = pd.read_csv(path)
        required = {"track_name", "prompt_id", "description"}
        if not required.issubset(frame.columns):
            raise ValueError(f"{path.name} must contain {sorted(required)}")
        frame["source_file"] = path.name
        frames.append(frame)

    queries = pd.concat(frames, ignore_index=True)
    queries = queries.rename(
        columns={"track_name": "track_id", "description": "query_raw"}
    )
    queries["track_id"] = queries["track_id"].astype(str).str.strip()
    queries["prompt_id"] = queries["prompt_id"].astype(str).str.strip()
    queries["query_raw"] = queries["query_raw"].fillna("").astype(str)
    queries["query"] = queries["query_raw"].map(clean_query)
    queries = queries[queries["query"].ne("")].copy()

    duplicated = queries.duplicated(["track_id", "prompt_id"], keep=False)
    if duplicated.any():
        examples = queries.loc[duplicated, ["track_id", "prompt_id"]].head().to_dict("records")
        raise ValueError(f"Duplicate track/prompt pairs: {examples}")

    queries["query_id"] = [
        _query_id(track_id, prompt_id)
        for track_id, prompt_id in zip(queries["track_id"], queries["prompt_id"])
    ]
    queries["word_count"] = queries["query"].str.split().str.len()
    queries["duplicate_text_count"] = queries.groupby("query")["query"].transform("size")
    queries["is_ambiguous_query"] = queries["duplicate_text_count"].gt(1)
    queries["has_exact_bpm"] = queries["query"].str.contains(
        r"\b\d+(?:\.\d+)?\s*(?:bpm|beats per minute)\b",
        case=False,
        regex=True,
    )
    queries["likely_truncated"] = queries["query"].str.contains(
        r"\b(?:and|or|with|of|the|a|an|in|at|to|its|that|which|featuring|set)\s*[,.]?$",
        case=False,
        regex=True,
    )
    return queries[
        [
            "query_id",
            "track_id",
            "prompt_id",
            "query",
            "query_raw",
            "source_file",
            "word_count",
            "duplicate_text_count",
            "is_ambiguous_query",
            "has_exact_bpm",
            "likely_truncated",
        ]
    ].reset_index(drop=True)


def add_track_splits(
    queries: pd.DataFrame,
    seed: int = 42,
    train_fraction: float = 0.70,
    dev_fraction: float = 0.15,
) -> pd.DataFrame:
    """Create deterministic track-level splits so no track leaks across splits."""
    track_ids = np.array(sorted(queries["track_id"].unique()))
    rng = np.random.default_rng(seed)
    rng.shuffle(track_ids)

    train_end = round(len(track_ids) * train_fraction)
    dev_end = train_end + round(len(track_ids) * dev_fraction)
    split_by_track = {
        **{track_id: "train" for track_id in track_ids[:train_end]},
        **{track_id: "dev" for track_id in track_ids[train_end:dev_end]},
        **{track_id: "test" for track_id in track_ids[dev_end:]},
    }
    result = queries.copy()
    result["split"] = result["track_id"].map(split_by_track)
    return result
