from __future__ import annotations

import argparse
import json
from pathlib import Path

from music_recommender.preparation import (
    add_track_splits,
    load_and_clean_queries,
    load_lightweight_tracks,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare catalogue and synthetic queries.")
    parser.add_argument(
        "--descriptions",
        type=Path,
        default=PROJECT_ROOT / "data" / "descriptions" / "descriptions_merged.parquet",
    )
    parser.add_argument(
        "--intents-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "sintetic_intents",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=PROJECT_ROOT / "reports" / "data_preparation.md",
    )
    args = parser.parse_args()

    tracks = load_lightweight_tracks(args.descriptions)
    queries = add_track_splits(load_and_clean_queries(args.intents_dir))

    missing_tracks = sorted(set(queries["track_id"]) - set(tracks["track_id"]))
    if missing_tracks:
        raise ValueError(f"Intent tracks missing from catalogue: {missing_tracks[:10]}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    tracks_path = args.output_dir / "tracks.parquet"
    queries_path = args.output_dir / "queries.parquet"
    report_path = args.output_dir / "preparation_report.json"
    tracks.to_parquet(tracks_path, index=False)
    queries.to_parquet(queries_path, index=False)

    changed = queries["query"].ne(queries["query_raw"].str.strip())
    duplicate_query_texts = int(queries.duplicated("query", keep=False).sum())
    report = {
        "catalogue_tracks": len(tracks),
        "query_rows": len(queries),
        "query_tracks": int(queries["track_id"].nunique()),
        "queries_per_track_min": int(queries.groupby("track_id").size().min()),
        "queries_per_track_max": int(queries.groupby("track_id").size().max()),
        "cleaned_queries": int(changed.sum()),
        "duplicate_query_text_rows": duplicate_query_texts,
        "queries_with_exact_bpm": int(queries["has_exact_bpm"].sum()),
        "likely_truncated_queries": int(queries["likely_truncated"].sum()),
        "missing_catalogue_tracks": len(missing_tracks),
        "split_tracks": queries.groupby("split")["track_id"].nunique().to_dict(),
        "split_queries": queries["split"].value_counts().to_dict(),
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    examples = queries.loc[
        queries["query"].ne(queries["query_raw"].str.strip()),
        ["query_raw", "query"],
    ].head(8)
    example_rows = "\n".join(
        f"| {row.query_raw.replace('|', '/')} | {row.query.replace('|', '/')} |"
        for row in examples.itertuples(index=False)
    )
    args.report.write_text(
        "# Data preparation report\n\n"
        f"- Catalogue: **{len(tracks)} tracks**\n"
        f"- Synthetic intents: **{len(queries)} queries for {queries['track_id'].nunique()} tracks**\n"
        f"- Queries per track: **{report['queries_per_track_min']}**\n"
        f"- Cleaned boilerplate prefixes: **{report['cleaned_queries']} queries**\n"
        f"- Ambiguous/duplicate-text rows: **{duplicate_query_texts}**\n"
        f"- Queries containing exact BPM: **{report['queries_with_exact_bpm']}**\n"
        f"- Likely truncated queries: **{report['likely_truncated_queries']}**\n"
        f"- Missing catalogue tracks: **{len(missing_tracks)}**\n\n"
        "## Track-wise split\n\n"
        "| Split | Tracks | Queries |\n|---|---:|---:|\n"
        + "\n".join(
            f"| {split} | {report['split_tracks'][split]} | {report['split_queries'][split]} |"
            for split in ("train", "dev", "test")
        )
        + "\n\n## Cleaning examples\n\n"
        "| Raw caption | Clean query |\n|---|---|\n"
        + example_rows
        + "\n\nThe original CSV and Parquet files are not modified. Quality flags are retained "
        "in `queries.parquet`; questionable rows are marked rather than silently deleted.\n",
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"tracks: {tracks_path}")
    print(f"queries: {queries_path}")
    print(f"report: {report_path}")
    print(f"markdown report: {args.report}")


if __name__ == "__main__":
    main()
