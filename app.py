from __future__ import annotations

import os
import time
from pathlib import Path

import streamlit as st

from music_recommender.data import DEFAULT_DATA_PATH, load_tracks
from music_recommender.qwen_search import DEFAULT_PROMPT_NAME, QUERY_TASKS, QwenMusicSearch
from music_recommender.search import TfidfMusicSearch


st.set_page_config(page_title="Music Search MVP", page_icon="🎧", layout="wide")


@st.cache_data(show_spinner=False)
def cached_tracks(path: str):
    return load_tracks(path)


@st.cache_resource(show_spinner="Building the search index…")
def cached_search(path: str) -> TfidfMusicSearch:
    return TfidfMusicSearch(cached_tracks(path)).fit()


@st.cache_resource(show_spinner="Loading Qwen…")
def cached_qwen_search(path: str) -> QwenMusicSearch:
    project_root = Path(__file__).resolve().parent
    return QwenMusicSearch(
        cached_tracks(path),
        embeddings_path=project_root / "data" / "processed" / "qwen_embeddings.npy",
        track_ids_path=project_root / "data" / "processed" / "qwen_track_ids.json",
        cache_folder=project_root / "models" / "huggingface",
    )


data_path = os.getenv("MUSIC_DATA_PATH", str(DEFAULT_DATA_PATH))

st.title("🎧 Music Search")
st.caption("Find tracks from a free-form description of mood, style, or sound.")

try:
    tracks = cached_tracks(data_path)
except Exception as error:
    st.error(f"Could not load the music catalogue: {error}")
    st.info("Set MUSIC_DATA_PATH to a .parquet or .csv file with a description column.")
    st.stop()

with st.sidebar:
    st.header("Demo status")
    st.metric("Indexed tracks", f"{len(tracks):,}")
    project_root = Path(__file__).resolve().parent
    qwen_ready = (project_root / "data" / "processed" / "qwen_embeddings.npy").exists()
    available_models = ["TF-IDF baseline"]
    if qwen_ready:
        available_models.insert(0, "Qwen3-Embedding-0.6B")
    selected_model = st.selectbox("Search model", available_models)
    prompt_name = DEFAULT_PROMPT_NAME
    if selected_model == "Qwen3-Embedding-0.6B":
        prompt_name = st.selectbox(
            "Qwen query prompt",
            list(QUERY_TASKS),
            index=list(QUERY_TASKS).index(DEFAULT_PROMPT_NAME),
        )
        st.caption(QUERY_TASKS[prompt_name])
    st.write(f"**Data:** `{Path(data_path).name}`")
    top_k = st.slider("Number of results", min_value=3, max_value=15, value=5)
    st.divider()
    st.caption("Offline test · 189 query rows · 1080 candidates")
    st.dataframe(
        {
            "Model": ["TF-IDF", "Qwen 0.6B"],
            "R@1": ["1.06%", "2.13%"],
            "R@5": ["3.72%", "6.38%"],
            "R@10": ["5.85%", "7.45%"],
            "MRR@10": ["2.11%", "3.41%"],
        },
        hide_index=True,
        use_container_width=True,
    )
    if not qwen_ready:
        st.caption("Qwen index is not built yet; using the lexical baseline.")

examples = [
    "energetic punk rock with distorted guitars and fast drums",
    "calm ambient music with piano and evolving textures",
    "dark electronic track with a driving rhythm and no vocals",
]

with st.form("search_form"):
    query = st.text_input(
        "Describe the music you want",
        placeholder=examples[0],
    )
    submitted = st.form_submit_button("Search", type="primary", use_container_width=True)

st.caption("Try: " + " · ".join(f"`{example}`" for example in examples))

if submitted:
    if not query.strip():
        st.warning("Enter a description first.")
        st.stop()

    if selected_model == "Qwen3-Embedding-0.6B":
        engine = cached_qwen_search(data_path)
        engine.prompt_name = prompt_name
    else:
        engine = cached_search(data_path)
    started = time.perf_counter()
    results = engine.search(query, top_k=top_k)
    elapsed_ms = (time.perf_counter() - started) * 1000

    st.subheader(f"Top {len(results)} results")
    st.caption(f"Search latency: {elapsed_ms:.1f} ms")

    for rank, row in results.iterrows():
        title = row.get("title") or "Untitled"
        artist = row.get("artist") or "Unknown artist"
        with st.container(border=True):
            left, right = st.columns([5, 1])
            left.markdown(f"### {rank + 1}. {artist} — {title}")
            right.metric("Score", f"{row['score']:.3f}")
            st.write(row["description"])
            st.caption(f"track_id: {row['track_id']}")
