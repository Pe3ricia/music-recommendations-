from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREPARED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "tracks.parquet"
DEFAULT_DATA_PATH = (
    PREPARED_DATA_PATH
    if PREPARED_DATA_PATH.exists()
    else PROJECT_ROOT / "data" / "descriptions" / "descriptions_merged.parquet"
)


def _stable_track_id(row: pd.Series) -> str:
    source = str(row.get("path") or "").strip()
    if not source:
        source = f"{row.get('artist', '')}|{row.get('title', '')}|{row.name}"
    return hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]


def load_tracks(path: str | Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Load and normalize a track catalogue without reading embedded audio bytes."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() == ".parquet":
        import pyarrow.parquet as pq

        # schema_arrow.names returns only top-level columns. schema.names also
        # contains nested audio fields (bytes/path), which would make pandas try
        # to read a non-existent top-level "path" column.
        available = pd.Index(pq.ParquetFile(path).schema_arrow.names)
        wanted = [
            column
            for column in ("track_id", "path", "title", "name", "artist", "description")
            if column in available
        ]
        tracks = pd.read_parquet(path, columns=wanted)
    elif path.suffix.lower() == ".csv":
        tracks = pd.read_csv(path)
    else:
        raise ValueError("Supported catalogue formats: .parquet and .csv")

    if "description" not in tracks.columns:
        raise ValueError("The catalogue must contain a 'description' column")
    if "title" not in tracks.columns and "name" in tracks.columns:
        tracks = tracks.rename(columns={"name": "title"})

    for column in ("title", "artist"):
        if column not in tracks.columns:
            tracks[column] = ""

    tracks["description"] = tracks["description"].fillna("").astype(str).str.strip()
    tracks = tracks[tracks["description"].ne("")].copy()
    tracks = tracks.reset_index(drop=True)

    if "track_id" not in tracks.columns:
        tracks["track_id"] = tracks.apply(_stable_track_id, axis=1)
    else:
        missing = tracks["track_id"].isna() | tracks["track_id"].astype(str).str.strip().eq("")
        tracks.loc[missing, "track_id"] = tracks[missing].apply(_stable_track_id, axis=1)
        tracks["track_id"] = tracks["track_id"].astype(str)

    tracks = tracks.drop_duplicates(subset=["track_id"], keep="first")
    return tracks[["track_id", "artist", "title", "description"]].reset_index(drop=True)
