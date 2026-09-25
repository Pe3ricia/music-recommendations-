from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from music_recommender.data import DEFAULT_DATA_PATH, load_tracks
from music_recommender.qwen_search import QWEN_MODEL_NAME


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Qwen music description index.")
    parser.add_argument("--tracks", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=PROJECT_ROOT / "models" / "huggingface",
    )
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()

    # Imported here so command-line help and data preparation stay lightweight.
    import torch
    from sentence_transformers import SentenceTransformer

    tracks = load_tracks(args.tracks)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_kwargs = {"torch_dtype": torch.float16} if device == "cuda" else None
    print(f"Loading {QWEN_MODEL_NAME} on {device.upper()}...")
    model = SentenceTransformer(
        QWEN_MODEL_NAME,
        device=device,
        cache_folder=str(args.cache_dir),
        model_kwargs=model_kwargs,
    )
    model.max_seq_length = 512

    print(f"Encoding {len(tracks)} track descriptions...")
    embeddings = model.encode_document(
        tracks["description"].tolist(),
        batch_size=args.batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype(np.float32)

    embeddings_path = args.output_dir / "qwen_embeddings.npy"
    track_ids_path = args.output_dir / "qwen_track_ids.json"
    metadata_path = args.output_dir / "qwen_index_metadata.json"
    np.save(embeddings_path, embeddings)
    track_ids_path.write_text(
        json.dumps(tracks["track_id"].astype(str).tolist()),
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(
            {
                "model": QWEN_MODEL_NAME,
                "tracks": len(tracks),
                "embedding_dimension": int(embeddings.shape[1]),
                "normalized": True,
                "max_sequence_length": model.max_seq_length,
                "device": device,
                "dtype": "float16" if device == "cuda" else "float32",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved {embeddings.shape} embeddings to {embeddings_path}")


if __name__ == "__main__":
    main()
