import unittest

import pandas as pd

from music_recommender.search import TfidfMusicSearch
from music_recommender.preparation import clean_query


class SearchTest(unittest.TestCase):
    def test_clean_query_removes_generation_scaffolding(self):
        examples = {
            "this is an energetic techno track": "an energetic techno track",
            "This upbeat rock song has loud guitars": "upbeat rock song has loud guitars",
            "the track is slow and atmospheric": "slow and atmospheric",
            "the song features soft piano": "soft piano",
        }
        for raw, expected in examples.items():
            with self.subTest(raw=raw):
                self.assertEqual(clean_query(raw), expected)

    def test_search_returns_most_relevant_track_first(self):
        tracks = pd.DataFrame(
            [
                {
                    "track_id": "ambient",
                    "artist": "A",
                    "title": "Calm",
                    "description": "calm ambient piano with soft evolving textures",
                },
                {
                    "track_id": "punk",
                    "artist": "B",
                    "title": "Fast",
                    "description": "energetic punk rock with distorted guitars and fast drums",
                },
            ]
        )

        results = TfidfMusicSearch(tracks).fit().search("fast punk guitars", top_k=1)

        self.assertEqual(results.iloc[0]["track_id"], "punk")
        self.assertGreater(results.iloc[0]["score"], 0)


if __name__ == "__main__":
    unittest.main()
