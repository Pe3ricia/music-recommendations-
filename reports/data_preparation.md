# Data preparation report

- Catalogue: **1080 tracks**
- Synthetic intents: **1248 queries for 416 tracks**
- Queries per track: **3**
- Cleaned boilerplate prefixes: **745 queries**
- Ambiguous/duplicate-text rows: **101**
- Queries containing exact BPM: **100**
- Likely truncated queries: **136**
- Missing catalogue tracks: **0**

## Track-wise split

| Split | Tracks | Queries |
|---|---:|---:|
| train | 291 | 873 |
| dev | 62 | 186 |
| test | 63 | 189 |

## Cleaning examples

| Raw caption | Clean query |
|---|---|
| this melancholic folk song with spoken word and ambient synth textures evokes a somber and introspective mood, set in | melancholic folk song with spoken word and ambient synth textures evokes a somber and introspective mood, set in |
| the track has a medium tempo | a medium tempo |
| this upbeat pop track features a catchy, danceable beat and a youthful, fun vibe. with its bright and lively sound | upbeat pop track features a catchy, danceable beat and a youthful, fun vibe. with its bright and lively sound |
| this energetic track is perfect for dancing with its 109 bpm tempo, blending catchy pop hooks and powerful rock instrumentation | energetic track is perfect for dancing with its 109 bpm tempo, blending catchy pop hooks and powerful rock instrumentation |
| this orchestral piece exudes a whimsical and playful mood, blending elements of classical and light jazz. the arrangement features | orchestral piece exudes a whimsical and playful mood, blending elements of classical and light jazz. the arrangement features |
| this energetic track features a fast-paced rhythm at 162.2 bpm, with a driving 4/4 | energetic track features a fast-paced rhythm at 162.2 bpm, with a driving 4/4 |
| this upbeat and energetic indie rock track showcases a fast tempo and a blend of jangly guitars and catchy melodies, embody | upbeat and energetic indie rock track showcases a fast tempo and a blend of jangly guitars and catchy melodies, embody |
| this energetic track is driven by a fast-paced rhythm, creating an upbeat and lively atmosphere | energetic track is driven by a fast-paced rhythm, creating an upbeat and lively atmosphere |

The original CSV and Parquet files are not modified. Quality flags are retained in `queries.parquet`; questionable rows are marked rather than silently deleted.
