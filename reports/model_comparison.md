# Retrieval model comparison

Evaluation uses the fixed test split: 63 tracks, 189 query rows (188 unique
query texts), with retrieval over the complete catalogue of 1080 tracks.
Repeated identical query texts are evaluated as multi-positive queries.

| Model | Recall@1 | Recall@5 | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|
| TF-IDF baseline | 1.06% | 3.72% | 5.85% | 2.11% |
| Qwen3-Embedding-0.6B (`caption_match`) | **2.13%** | **6.38%** | **7.45%** | **3.41%** |

## Query prompt ablation

| Prompt | Recall@1 | Recall@5 | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|
| `caption_match` | **2.13%** | **6.38%** | 7.45% | **3.41%** |
| `balanced` | 1.60% | 4.26% | **8.51%** | 3.09% |
| `listener_search` | 1.60% | 5.85% | 7.45% | 3.04% |

Qwen document embeddings are computed without a prompt. Queries use:

```text
Instruct: Given a short description of music, retrieve track descriptions for music with the same mood, style, energy, rhythm, instruments, vocals, and sound
Query: {query}
```

The Qwen index contains 1080 normalized vectors with 1024 dimensions. It was
built on an NVIDIA GeForce GTX 1650 using CUDA and FP16.
