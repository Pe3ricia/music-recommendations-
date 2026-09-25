# Music recommendation demo

A minimal text-to-music retrieval demo. The current model is a deterministic
TF-IDF baseline; an instruction-aware embedding model can be added behind the
same search interface.

## Data

Prepare the newly generated descriptions and intents first:

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_data
```

This creates lightweight files without embedded audio bytes:

- `data/processed/tracks.parquet`
- `data/processed/queries.parquet`
- `data/processed/preparation_report.json`

The default catalogue after preparation is:

`data/processed/tracks.parquet`

CSV and Parquet catalogues are supported. Required column: `description`.
Optional columns: `track_id`, `artist`, `title` (or `name`), and `path`.
Embedded audio byte columns are deliberately not loaded.

To use a newly generated catalogue in PowerShell:

```powershell
$env:MUSIC_DATA_PATH = "K:\path\to\new_descriptions.parquet"
```

## Run the UI

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Build the Qwen index

The model cache is stored on the project drive under `models/huggingface`.

This laptop uses the CUDA-enabled PyTorch build:

```powershell
.\.venv\Scripts\python.exe -m pip install --force-reinstall --no-deps "torch==2.12.1+cu130" --index-url https://download.pytorch.org/whl/cu130
```

```powershell
.\.venv\Scripts\python.exe -m scripts.build_qwen_index
```

After the embeddings are saved, the UI automatically enables the
`Qwen3-Embedding-0.6B` model option.

## Evaluate

Prepare a CSV with one row per query:

```csv
query,relevant_track_id
energetic punk with distorted guitars,abc123
calm ambient piano,def456
```

Then run:

```powershell
.\.venv\Scripts\python.exe -m scripts.evaluate data\processed\queries.parquet
.\.venv\Scripts\python.exe -m scripts.evaluate data\processed\queries.parquet --model qwen
```

The script reports Recall@1/5/10 and MRR@10 over the complete catalogue.
