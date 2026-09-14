from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from music.services.spotify import (
    SpotifyAPIError,
    SpotifyService,
)
from users.models import SpotifyConnection

from .models import DiscoverySession
from .services.candidates import CandidateGenerator
from .services.engine import RecommendationEngine
from .services.playlist_candidates import (
    PlaylistCandidateGenerator,
)
from .services.playlist_engine import PlaylistEngine
from .services.playlist_query_builder import (
    PlaylistQueryBuilder,
)
from .services.playlist_scoring import PlaylistScorer
from .services.query_builder import RecommendationQueryBuilder
from .services.recommender import RecommendationRequest
from .services.scoring import (
    RecommendationScorer,
    genres_match,
)


def make_track(
    track_id,
    name,
    artist,
    year=2015,
    popularity=50,
):
    artist_id = (
        f"artist-{artist.lower().replace(' ', '-')}"
    )

    return {
        "id": track_id,
        "name": name,
        "artists": [
            {"id": artist_id, "name": artist},
        ],
        "album": {
            "name": f"Album {track_id}",
            "images": [
                {
                    "url": (
                        f"http://example.com/{track_id}.jpg"
                    ),
                },
            ],
            "release_date": (
                f"{year}-01-01" if year else ""
            ),
        },
        "external_urls": {
            "spotify": (
                f"http://open.spotify.com/track/{track_id}"
            ),
        },
        "popularity": popularity,
    }


def make_playlist(
    playlist_id,
    name,
    description="",
    owner="Test Owner",
    track_count=45,
):
    return {
        "id": playlist_id,
        "name": name,
        "description": description,
        "images": [
            {
                "url": (
                    f"http://example.com/{playlist_id}.jpg"
                ),
            },
        ],
        "external_urls": {
            "spotify": (
                "http://open.spotify.com/playlist/"
                f"{playlist_id}"
            ),
        },
        "owner": {
            "display_name": owner,
            "id": "owner-id",
        },
        "tracks": {"total": track_count},
    }


class FakeSpotifyService:
    def __init__(
        self,
        results=None,
        default_items=None,
        artist_genres=None,
        playlist_results=None,
        default_playlists=None,
    ):
        self.results = results or {}
        self.default_items = default_items or []
        self.artist_genres = artist_genres or {}
        self.playlist_results = playlist_results or {}
        self.default_playlists = default_playlists or []
        self.search_calls = []
        self.artist_calls = []
        self.playlist_search_calls = []

    def search(self, query, search_type="track", limit=10):
        self.search_calls.append(query)
        items = self.results.get(query)
        if items is None:
            items = self.default_items
        return {"tracks": {"items": list(items[:limit])}}

    def search_playlists(self, query, limit=10):
        self.playlist_search_calls.append(query)
        items = self.playlist_results.get(query)
        if items is None:
            items = self.default_playlists
        return [
            item
            for item in items[:limit]
            if item is not None
        ]

    def get_artist(self, artist_id):
        self.artist_calls.append(artist_id)
        return {
            "id": artist_id,
            "genres": self.artist_genres.get(
                artist_id,
                [],
            ),
        }


class RecommendationQueryBuilderTests(TestCase):
    def test_generates_multiple_queries_for_combined_selections(self):
        request = RecommendationRequest(
            artist="Frank Ocean",
            genre="r&b",
            mood="chill",
            era="2010s",
        )
        queries = RecommendationQueryBuilder.build_many(
            request
        )
        self.assertGreaterEqual(len(queries), 3)
        self.assertIn("frank ocean", queries)
        self.assertIn("r&b", queries)
        self.assertIn("chill r&b", queries)
        self.assertIn("r&b 2010", queries)
        self.assertEqual(
            len(queries),
            len({q.lower() for q in queries}),
        )

    def test_no_duplicate_queries_for_single_pair(self):
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
        )
        queries = RecommendationQueryBuilder.build_many(
            request
        )
        self.assertEqual(queries, ["r&b", "r&b 2010"])

    def test_spec_examples(self):
        cases = [
            (
                RecommendationRequest(artist="Frank Ocean"),
                ["frank ocean"],
            ),
            (
                RecommendationRequest(
                    artist="Frank Ocean",
                    genre="r&b",
                ),
                [
                    "frank ocean",
                    "r&b",
                    "frank ocean r&b",
                ],
            ),
            (
                RecommendationRequest(
                    genre="r&b",
                    era="2010s",
                ),
                ["r&b", "r&b 2010"],
            ),
            (
                RecommendationRequest(
                    mood="chill",
                    genre="r&b",
                ),
                ["r&b", "chill r&b"],
            ),
            (
                RecommendationRequest(genre="r&b"),
                ["r&b"],
            ),
            (
                RecommendationRequest(era="2010s"),
                ["2010s music"],
            ),
        ]
        for request, expected in cases:
            with self.subTest(request=request):
                self.assertEqual(
                    RecommendationQueryBuilder.build_many(
                        request
                    ),
                    expected,
                )

    def test_empty_request_produces_no_queries(self):
        self.assertEqual(
            RecommendationQueryBuilder.build_many(
                RecommendationRequest()
            ),
            [],
        )

    def test_build_returns_primary_query(self):
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
        )
        self.assertEqual(
            RecommendationQueryBuilder.build(request),
            "r&b",
        )


class CandidateGeneratorTests(TestCase):
    def test_search_many_deduplicates_tracks(self):
        fake = FakeSpotifyService(
            results={
                "r&b": [
                    make_track(
                        "1", "A", "Alice"
                    ),
                    make_track(
                        "2", "B", "Bob"
                    ),
                ],
                "r&b 2010": [
                    make_track(
                        "1", "A", "Alice"
                    ),
                    make_track(
                        "3", "C", "Carol"
                    ),
                ],
            }
        )
        generator = CandidateGenerator(fake)
        candidates = generator.search_many(
            ["r&b", "r&b 2010"]
        )
        ids = [c.track["id"] for c in candidates]
        self.assertEqual(len(ids), 3)
        self.assertEqual(len(ids), len(set(ids)))

    def test_search_many_skips_empty_queries(self):
        generator = CandidateGenerator(
            FakeSpotifyService()
        )
        self.assertEqual(
            generator.search_many([]),
            [],
        )
        self.assertEqual(
            generator.search_many(["  ", ""]),
            [],
        )

    def test_search_many_tolerates_spotify_errors(self):
        class FlakySpotify(FakeSpotifyService):
            def search(
                self,
                query,
                search_type="track",
                limit=10,
            ):
                if query == "broken":
                    raise SpotifyAPIError("boom")
                return super().search(
                    query,
                    search_type,
                    limit,
                )

        fake = FlakySpotify(
            results={
                "ok": [
                    make_track(
                        "1", "A", "Alice"
                    ),
                ],
            }
        )
        generator = CandidateGenerator(fake)
        candidates = generator.search_many(
            ["broken", "ok"]
        )
        self.assertEqual(
            [c.track["id"] for c in candidates],
            ["1"],
        )

    def test_fetch_artist_genres_is_bounded(self):
        artists = [
            f"Artist {i}" for i in range(20)
        ]
        pool = [
            make_track(
                str(i),
                f"T{i}",
                artists[i],
                2015,
            )
            for i in range(20)
        ]
        fake = FakeSpotifyService(
            default_items=pool
        )
        generator = CandidateGenerator(fake)
        candidates = generator.search_many(["r&b"])
        generator.fetch_artist_genres(
            candidates,
            limit=6,
        )
        self.assertLessEqual(
            len(fake.artist_calls),
            6,
        )


class RecommendationScorerTests(TestCase):
    def setUp(self):
        self.scorer = RecommendationScorer()

    def test_scores_stay_within_0_and_100(self):
        request = RecommendationRequest(
            mood="chill",
            genre="r&b",
            era="2010s",
            artist="Frank Ocean",
            discovery_style="familiar",
        )
        track = make_track(
            "1",
            "Nights",
            "Frank Ocean",
            year=2016,
            popularity=80,
        )
        artist_id = track["artists"][0]["id"]
        score, reasons, relevance = self.scorer.score(
            track,
            request,
            artist_genres={
                artist_id: ["contemporary r&b"],
            },
            source_query="chill r&b",
        )
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        self.assertEqual(score, 100)
        self.assertIn(
            "Related to Frank Ocean",
            reasons,
        )
        self.assertIn(
            "Matches your r&b preference",
            reasons,
        )
        self.assertIn(
            "Released in the 2010s",
            reasons,
        )
        self.assertIn(
            "Matched your chill search",
            reasons,
        )
        # relevance excludes the discovery-style bonus.
        self.assertEqual(relevance, 90)

    def test_artist_matching(self):
        request = RecommendationRequest(
            artist="Frank Ocean"
        )
        track = make_track(
            "1",
            "Nights",
            "Frank Ocean",
        )
        score, reasons, _ = self.scorer.score(
            track,
            request,
        )
        self.assertEqual(score, 40)
        self.assertIn(
            "Related to Frank Ocean",
            reasons,
        )

    def test_era_matching(self):
        request = RecommendationRequest(
            era="2010s"
        )
        match = make_track(
            "1",
            "A",
            "Alice",
            year=2015,
        )
        score, reasons, relevance = self.scorer.score(
            match,
            request,
        )
        self.assertEqual(score, 20)
        self.assertIn(
            "Released in the 2010s",
            reasons,
        )

        miss = make_track(
            "2",
            "B",
            "Bob",
            year=2005,
        )
        _, _, relevance_miss = self.scorer.score(
            miss,
            request,
        )
        self.assertEqual(relevance_miss, 0)

    def test_genre_verified_scores_full_weight(self):
        request = RecommendationRequest(
            genre="r&b"
        )
        track = make_track("1", "A", "Alice")
        artist_id = track["artists"][0]["id"]
        score, reasons, relevance = self.scorer.score(
            track,
            request,
            artist_genres={
                artist_id: ["alternative r&b"],
            },
            source_query="r&b",
        )
        self.assertEqual(score, 20)
        self.assertEqual(relevance, 20)
        self.assertIn(
            "Matches your r&b preference",
            reasons,
        )

    def test_genre_query_level_scores_partial(self):
        request = RecommendationRequest(
            genre="r&b"
        )
        track = make_track("1", "A", "Alice")
        score, reasons, relevance = self.scorer.score(
            track,
            request,
            artist_genres={},
            source_query="chill r&b",
        )
        self.assertEqual(score, 10)
        self.assertEqual(relevance, 10)
        self.assertIn(
            "Found in your r&b search",
            reasons,
        )

    def test_genre_absent_when_unverified_and_unrelated(self):
        request = RecommendationRequest(
            genre="r&b"
        )
        track = make_track("1", "A", "Alice")
        _, reasons, relevance = self.scorer.score(
            track,
            request,
            artist_genres={},
            source_query="frank ocean",
        )
        self.assertEqual(relevance, 0)
        self.assertEqual(reasons, [])

    def test_mood_is_query_level_signal_only(self):
        track = make_track("1", "A", "Alice")

        request = RecommendationRequest(
            mood="chill"
        )
        score, reasons, _ = self.scorer.score(
            track,
            request,
            source_query="chill r&b",
        )
        self.assertEqual(score, 10)
        self.assertIn(
            "Matched your chill search",
            reasons,
        )

        _, _, relevance_miss = self.scorer.score(
            track,
            request,
            source_query="happy pop",
        )
        self.assertEqual(relevance_miss, 0)

    def test_genres_match_normalizes_variants(self):
        self.assertTrue(genres_match("hip-hop", ["hip hop"]))
        self.assertTrue(genres_match("afrobeats", ["afrobeat"]))
        self.assertTrue(genres_match("r&b", ["contemporary r&b"]))
        self.assertFalse(genres_match("rock", ["jazz"]))


class RecommendationEngineTests(TestCase):
    def test_irrelevant_candidates_are_filtered(self):
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
            mood="chill",
        )
        pool = [
            make_track(
                "era-hit",
                "Late Night",
                "Sango",
                year=2013,
            ),
            make_track(
                "unrelated",
                "Old Jam",
                "Legacy",
                year=2004,
            ),
        ]
        engine = RecommendationEngine(
            FakeSpotifyService(default_items=pool)
        )
        results = engine.generate(request)
        self.assertEqual(
            [r.spotify_track_id for r in results],
            ["era-hit"],
        )

    def test_results_are_ranked(self):
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
            artist="Frank Ocean",
        )
        pool = [
            make_track(
                "artist-track",
                "Nights",
                "Frank Ocean",
                year=2016,
            ),
            make_track(
                "era-track",
                "Long Time",
                "Activity",
                year=2014,
            ),
            make_track(
                "weak-track",
                "Weekend",
                "Maya",
                year=2012,
            ),
        ]
        engine = RecommendationEngine(
            FakeSpotifyService(default_items=pool)
        )
        results = engine.generate(request)

        scores = [r.score for r in results]
        self.assertEqual(
            scores,
            sorted(scores, reverse=True),
        )
        self.assertEqual(
            [r.spotify_track_id for r in results],
            ["artist-track", "era-track", "weak-track"],
        )

    def test_artist_diversity_limits_tracks_per_artist(self):
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
        )
        pool = (
            [
                make_track(
                    f"drako{i}",
                    f"D{i}",
                    "Drake",
                    year=2013,
                )
                for i in range(5)
            ]
            + [
                make_track(
                    f"ken{i}",
                    f"K{i}",
                    "Kendrick",
                    year=2013,
                )
                for i in range(3)
            ]
        )
        engine = RecommendationEngine(
            FakeSpotifyService(default_items=pool)
        )
        results = engine.generate(request)

        drake = sum(
            1
            for r in results
            if r.artist == "Drake"
        )
        kendrick = sum(
            1
            for r in results
            if r.artist == "Kendrick"
        )
        self.assertLessEqual(drake, 2)
        self.assertLessEqual(kendrick, 2)

    def test_requested_artist_exceeds_default_cap(self):
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
            artist="Drake",
        )
        pool = (
            [
                make_track(
                    f"drako{i}",
                    f"D{i}",
                    "Drake",
                    year=2013,
                )
                for i in range(5)
            ]
            + [
                make_track(
                    f"ken{i}",
                    f"K{i}",
                    "Kendrick",
                    year=2013,
                )
                for i in range(3)
            ]
        )
        engine = RecommendationEngine(
            FakeSpotifyService(default_items=pool)
        )
        results = engine.generate(request)

        drake = [
            r for r in results if r.artist == "Drake"
        ]
        kendrick = [
            r for r in results
            if r.artist == "Kendrick"
        ]
        self.assertEqual(len(drake), 5)
        self.assertLessEqual(len(kendrick), 2)

    def test_empty_pool_returns_empty_results(self):
        engine = RecommendationEngine(
            FakeSpotifyService(default_items=[])
        )
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
        )
        self.assertEqual(engine.generate(request), [])


class PlaylistQueryBuilderTests(TestCase):
    def test_spec_examples(self):
        cases = [
            (
                RecommendationRequest(genre="r&b"),
                ["r&b"],
            ),
            (
                RecommendationRequest(
                    genre="r&b",
                    mood="chill",
                ),
                ["r&b", "chill r&b"],
            ),
            (
                RecommendationRequest(
                    genre="r&b",
                    era="2010s",
                ),
                ["r&b", "2010s r&b"],
            ),
            (
                RecommendationRequest(artist="Frank Ocean"),
                ["frank ocean"],
            ),
            (
                RecommendationRequest(
                    artist="Frank Ocean",
                    genre="r&b",
                ),
                [
                    "frank ocean",
                    "r&b",
                    "frank ocean r&b",
                ],
            ),
            (
                RecommendationRequest(
                    artist="Frank Ocean",
                    mood="chill",
                ),
                ["frank ocean", "frank ocean chill"],
            ),
        ]
        for request, expected in cases:
            with self.subTest(request=request):
                self.assertEqual(
                    PlaylistQueryBuilder.build_many(
                        request
                    ),
                    expected,
                )

    def test_generates_bounded_unique_queries(self):
        request = RecommendationRequest(
            artist="Frank Ocean",
            genre="r&b",
            mood="chill",
            era="2010s",
        )
        queries = PlaylistQueryBuilder.build_many(request)
        self.assertLessEqual(
            len(queries),
            PlaylistQueryBuilder.MAX_QUERIES,
        )
        self.assertEqual(
            [q for q in queries if not q],
            [],
        )
        self.assertEqual(
            len(queries),
            len({q.lower() for q in queries}),
        )
        for query in (
            "frank ocean",
            "r&b",
            "chill 2010s r&b",
            "2010s r&b",
            "chill r&b",
        ):
            self.assertIn(query, queries)

    def test_generates_combined_mood_era_genre_query(self):
        request = RecommendationRequest(
            mood="chill",
            genre="r&b",
            era="2010s",
        )
        queries = PlaylistQueryBuilder.build_many(request)
        self.assertEqual(queries[0], "r&b")
        self.assertIn("chill 2010s r&b", queries)
        self.assertIn("2010s r&b", queries)
        self.assertIn("chill r&b", queries)

    def test_empty_request_produces_no_queries(self):
        self.assertEqual(
            PlaylistQueryBuilder.build_many(
                RecommendationRequest()
            ),
            [],
        )


class PlaylistCandidateGeneratorTests(TestCase):
    def test_search_many_deduplicates_playlists(self):
        fake = FakeSpotifyService(
            playlist_results={
                "r&b": [
                    make_playlist("1", "R&B Jams"),
                    make_playlist("2", "Chill R&B"),
                ],
                "chill r&b": [
                    make_playlist("1", "R&B Jams"),
                    make_playlist("3", "Night Drive"),
                ],
            }
        )
        generator = PlaylistCandidateGenerator(fake)
        candidates = generator.search_many(
            ["r&b", "chill r&b"]
        )
        ids = [c.playlist["id"] for c in candidates]
        self.assertEqual(len(ids), 3)
        self.assertEqual(len(ids), len(set(ids)))

    def test_search_many_skips_empty_queries(self):
        generator = PlaylistCandidateGenerator(
            FakeSpotifyService()
        )
        self.assertEqual(generator.search_many([]), [])
        self.assertEqual(generator.search_many(["", "  "]), [])

    def test_search_many_tolerates_spotify_errors(self):
        class FlakySpotify(FakeSpotifyService):
            def search_playlists(self, query, limit=10):
                if query == "broken":
                    raise SpotifyAPIError("boom")
                return super().search_playlists(
                    query,
                    limit,
                )

        fake = FlakySpotify(
            playlist_results={
                "ok": [make_playlist("1", "Good Vibes")],
            }
        )
        generator = PlaylistCandidateGenerator(fake)
        candidates = generator.search_many(
            ["broken", "ok"]
        )
        self.assertEqual(
            [c.playlist["id"] for c in candidates],
            ["1"],
        )

    def test_search_many_respects_max_candidates(self):
        pool = [
            make_playlist(str(i), f"P{i}")
            for i in range(40)
        ]
        fake = FakeSpotifyService(
            default_playlists=pool,
        )
        generator = PlaylistCandidateGenerator(fake)
        candidates = generator.search_many(
            ["playlist search"],
            per_query=40,
            max_candidates=25,
        )
        self.assertEqual(len(candidates), 25)

    def test_search_by_query_returns_items(self):
        fake = FakeSpotifyService(
            playlist_results={
                "chill r&b": [
                    make_playlist("1", "Chill R&B"),
                ],
            }
        )
        generator = PlaylistCandidateGenerator(fake)
        items = generator.search_by_query("chill r&b")
        self.assertEqual(len(items), 1)
        self.assertEqual(fake.playlist_search_calls, ["chill r&b"])


class PlaylistScorerTests(TestCase):
    def setUp(self):
        self.scorer = PlaylistScorer()

    def test_scores_stay_within_0_and_100(self):
        request = RecommendationRequest(
            artist="Frank Ocean",
            genre="r&b",
            era="2010s",
            mood="chill",
        )
        playlist = make_playlist(
            "1",
            "Frank Ocean R&B Chill",
            description="Best 2010s late night vibes",
        )
        score, reasons, relevance = self.scorer.score(
            playlist,
            request,
            source_query="chill r&b",
        )
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        self.assertEqual(score, 100)
        self.assertEqual(relevance, 100)
        self.assertIn(
            "Related to Frank Ocean",
            reasons,
        )
        self.assertIn(
            "Matches your r&b preference",
            reasons,
        )
        self.assertIn(
            "Fits a chill mood",
            reasons,
        )
        self.assertIn(
            "Matches your 2010s preference",
            reasons,
        )

    def test_artist_signal(self):
        request = RecommendationRequest(
            artist="Frank Ocean"
        )
        playlist = make_playlist(
            "1",
            "Frank Ocean Essentials",
            description="Deep cuts and rarities",
        )
        score, reasons, relevance = self.scorer.score(
            playlist,
            request,
        )
        self.assertEqual(score, 35)
        self.assertEqual(relevance, 35)
        self.assertIn(
            "Related to Frank Ocean",
            reasons,
        )

    def test_genre_signal_found_in_description(self):
        request = RecommendationRequest(genre="r&b")
        playlist = make_playlist(
            "1",
            "Night Drive",
            description="Best of contemporary R&B",
        )
        score, _, relevance = self.scorer.score(
            playlist,
            request,
        )
        self.assertEqual(score, 30)
        self.assertEqual(relevance, 30)

    def test_era_signal_matches_label_and_decade(self):
        request = RecommendationRequest(era="2010s")
        label_playlist = make_playlist(
            "1",
            "2010s Classics",
        )
        score, reasons, _ = self.scorer.score(
            label_playlist,
            request,
        )
        self.assertEqual(score, 20)
        self.assertIn(
            "Matches your 2010s preference",
            reasons,
        )

        decade_playlist = make_playlist(
            "2",
            "Top 2010 Songs",
        )
        score, _, _ = self.scorer.score(
            decade_playlist,
            request,
        )
        self.assertEqual(score, 20)

    def test_mood_signal(self):
        request = RecommendationRequest(mood="chill")
        playlist = make_playlist("1", "Chill Vibes")
        score, reasons, relevance = self.scorer.score(
            playlist,
            request,
        )
        self.assertEqual(score, 15)
        self.assertEqual(relevance, 15)
        self.assertIn("Fits a chill mood", reasons)

    def test_genre_plural_variant_matches(self):
        request = RecommendationRequest(genre="afrobeats")
        playlist = make_playlist(
            "1",
            "Afrobeat Essentials",
        )
        score, _, _ = self.scorer.score(
            playlist,
            request,
        )
        self.assertEqual(score, 30)

    def test_pop_does_not_match_popular(self):
        request = RecommendationRequest(genre="pop")
        playlist = make_playlist("1", "Popular Songs")
        score, reasons, relevance = self.scorer.score(
            playlist,
            request,
        )
        self.assertEqual(score, 0)
        self.assertEqual(relevance, 0)
        self.assertEqual(reasons, [])

    def test_exact_query_bonus_only_adds_points(self):
        request = RecommendationRequest(
            genre="r&b",
            mood="chill",
        )
        playlist = make_playlist("1", "Chill R&B Mix")
        score, reasons, relevance = self.scorer.score(
            playlist,
            request,
            source_query="chill r&b",
        )
        self.assertEqual(relevance, 45)
        self.assertEqual(score, 55)
        self.assertIn(
            "Name matches your chill r&b search",
            reasons,
        )

    def test_no_signals_no_points_no_reasons(self):
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
        )
        playlist = make_playlist(
            "1",
            "Random Collection",
            description="Just a mix of songs",
        )
        score, reasons, relevance = self.scorer.score(
            playlist,
            request,
        )
        self.assertEqual(score, 0)
        self.assertEqual(relevance, 0)
        self.assertEqual(reasons, [])

    def test_wrong_era_is_penalized(self):
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
        )
        playlist = make_playlist(
            "1",
            "2000s R&B",
            description="Best of the 2000s",
        )
        score, reasons, relevance = self.scorer.score(
            playlist,
            request,
        )
        self.assertEqual(score, 0)
        self.assertEqual(relevance, 30)
        self.assertIn(
            "Conflicts with your 2010s preference",
            reasons,
        )

    def test_requested_era_beats_wrong_era(self):
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
        )
        wrong = make_playlist("1", "2000s R&B")
        right = make_playlist("2", "2010s R&B")
        wrong_score, _, _ = self.scorer.score(
            wrong,
            request,
        )
        right_score, _, _ = self.scorer.score(
            right,
            request,
        )
        self.assertGreater(right_score, wrong_score)

    def test_genre_plus_era_beats_genre_only(self):
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
        )
        genre_only = make_playlist(
            "1",
            "Smooth R&B Mix",
        )
        genre_era = make_playlist(
            "2",
            "2010s R&B Essentials",
        )
        genre_score, _, _ = self.scorer.score(
            genre_only,
            request,
        )
        genre_era_score, _, _ = self.scorer.score(
            genre_era,
            request,
        )
        self.assertGreater(genre_era_score, genre_score)

    def test_genre_plus_era_plus_mood_beats_genre_only(self):
        request = RecommendationRequest(
            mood="chill",
            genre="r&b",
            era="2010s",
        )
        genre_only = make_playlist(
            "1",
            "Smooth R&B Mix",
        )
        genre_era_mood = make_playlist(
            "2",
            "2010s R&B",
            description="Chill late night vibes",
        )
        genre_score, _, _ = self.scorer.score(
            genre_only,
            request,
        )
        full_score, _, _ = self.scorer.score(
            genre_era_mood,
            request,
        )
        self.assertGreater(full_score, genre_score)

    def test_current_year_playlist_does_not_rank_for_past_era(self):
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
        )
        playlist = make_playlist(
            "1",
            "R&B 2026",
            description="New R&B hits of the year",
        )
        score, reasons, _ = self.scorer.score(
            playlist,
            request,
            source_query="r&b",
        )
        self.assertEqual(score, 0)
        self.assertIn(
            "Conflicts with your 2010s preference",
            reasons,
        )

    def test_era_conflicts_ignores_unrelated_text(self):
        from .services.playlist_scoring import (
            era_conflicts,
            mentioned_decades,
            requested_decade,
        )

        self.assertEqual(requested_decade("2010s"), "2010s")
        self.assertEqual(requested_decade("2010's"), "2010s")
        self.assertEqual(requested_decade(""), None)

        self.assertEqual(
            mentioned_decades("R&B Classics 90s & 2000s"),
            ["1990s", "2000s"],
        )
        self.assertEqual(
            mentioned_decades("R&B 2026"),
            ["2020s"],
        )
        self.assertEqual(
            mentioned_decades("Top 2010 Songs"),
            ["2010s"],
        )
        self.assertEqual(mentioned_decades("Chill Vibes"), [])

        self.assertTrue(
            era_conflicts("2010s", "Best of the 2000s")
        )
        self.assertFalse(
            era_conflicts("2010s", "2010s - 2020s mix")
        )
        self.assertFalse(
            era_conflicts("2010s", "Random chill mix")
        )
        self.assertFalse(
            era_conflicts("", "2000s R&B")
        )


class PlaylistEngineTests(TestCase):
    def test_returns_top_scored_playlists(self):
        request = RecommendationRequest(
            genre="r&b",
            era="2010s",
            mood="chill",
        )
        pool = [
            make_playlist(
                "a",
                "Chill R&B",
                description="2010s favorites",
            ),
            make_playlist("b", "2010s R&B Bangers"),
            make_playlist("c", "Random Stuff"),
        ]
        engine = PlaylistEngine(
            FakeSpotifyService(default_playlists=pool)
        )
        results = engine.generate(request)
        ids = [p.spotify_playlist_id for p in results]
        self.assertNotIn("c", ids)
        self.assertEqual(ids[0], "a")
        scores = [p.score for p in results]
        self.assertEqual(
            scores,
            sorted(scores, reverse=True),
        )

    def test_irrelevant_playlists_are_not_ranked_highly(self):
        request = RecommendationRequest(
            artist="Frank Ocean",
            genre="r&b",
        )
        pool = [
            make_playlist(
                "irrelevant",
                "Generic Mix",
                description="Random songs compiled",
            ),
            make_playlist("artist", "Frank Ocean R&B"),
        ]
        engine = PlaylistEngine(
            FakeSpotifyService(default_playlists=pool)
        )
        results = engine.generate(request)
        self.assertEqual(
            [p.spotify_playlist_id for p in results],
            ["artist"],
        )

    def test_result_count_is_bounded(self):
        request = RecommendationRequest(genre="r&b")
        pool = [
            make_playlist(str(i), "R&B Essentials")
            for i in range(20)
        ]
        engine = PlaylistEngine(
            FakeSpotifyService(default_playlists=pool)
        )
        results = engine.generate(request)
        self.assertLessEqual(
            len(results),
            PlaylistEngine.MAX_PLAYLISTS,
        )

    def test_empty_response_returns_empty(self):
        engine = PlaylistEngine(
            FakeSpotifyService(default_playlists=[])
        )
        self.assertEqual(
            engine.generate(
                RecommendationRequest(genre="r&b")
            ),
            [],
        )

    def test_empty_request_returns_empty(self):
        engine = PlaylistEngine(FakeSpotifyService())
        self.assertEqual(
            engine.generate(RecommendationRequest()),
            [],
        )

    def test_playlist_metadata_conversion(self):
        request = RecommendationRequest(genre="r&b")
        playlist = make_playlist(
            "p1",
            "R&B Jams",
            description="Smooth",
            owner="Curator",
            track_count=87,
        )
        engine = PlaylistEngine(
            FakeSpotifyService(default_playlists=[playlist])
        )
        results = engine.generate(request)
        result = results[0]
        self.assertEqual(
            result.spotify_playlist_id,
            "p1",
        )
        self.assertEqual(result.name, "R&B Jams")
        self.assertEqual(result.description, "Smooth")
        self.assertEqual(result.owner_name, "Curator")
        self.assertEqual(result.track_count, 87)
        self.assertEqual(
            result.artwork_url,
            "http://example.com/p1.jpg",
        )
        self.assertEqual(
            result.spotify_url,
            "http://open.spotify.com/playlist/p1",
        )

    def test_track_count_extracted_from_search_items_field(self):
        request = RecommendationRequest(genre="r&b")
        playlist = {
            "id": "p1",
            "name": "R&B Jams",
            "description": "Smooth",
            "images": [{"url": "http://example.com/p1.jpg"}],
            "external_urls": {
                "spotify": (
                    "http://open.spotify.com/playlist/p1"
                ),
            },
            "owner": {
                "display_name": "Curator",
                "id": "owner-id",
            },
            "items": {"href": "https://...", "total": 146},
        }
        engine = PlaylistEngine(
            FakeSpotifyService(default_playlists=[playlist])
        )
        results = engine.generate(request)
        self.assertEqual(results[0].track_count, 146)

    def test_correct_era_beats_wrong_era_in_rendered_playlists(self):
        request = RecommendationRequest(
            mood="chill",
            genre="r&b",
            era="2010s",
        )
        pool = [
            make_playlist(
                "wrong",
                "2000s R&B",
                description="Best hip hop R&B of the 2000s",
            ),
            make_playlist(
                "current",
                "R&B 2026",
                description="New R&B hits",
            ),
            make_playlist(
                "genre-only",
                "Smooth R&B Mix",
                description="Chill late night vibes",
            ),
            make_playlist(
                "right",
                "2010s R&B",
                description="Chill R&B of the 2010s",
            ),
        ]
        engine = PlaylistEngine(
            FakeSpotifyService(default_playlists=pool)
        )
        results = engine.generate(request)
        ids = [p.spotify_playlist_id for p in results]

        # Explicit wrong-era playlists are excluded outright rather than
        # merely docked points.
        self.assertIn("right", ids)
        self.assertNotIn("wrong", ids)
        self.assertNotIn("current", ids)
        self.assertEqual(ids[0], "right")

        scores = {
            p.spotify_playlist_id: p.score
            for p in results
        }
        self.assertGreater(
            scores["right"],
            scores["genre-only"],
        )

    def test_wrong_era_excluded_even_with_rescue_signals(self):
        request = RecommendationRequest(
            mood="chill",
            genre="r&b",
            era="2010s",
        )
        pool = [
            make_playlist(
                "wrong",
                "R&B 2026",
                description="Chill new R&B hits",
            ),
            make_playlist(
                "right",
                "2010s R&B Chill",
                description="Smooth",
            ),
        ]
        engine = PlaylistEngine(
            FakeSpotifyService(default_playlists=pool)
        )
        results = engine.generate(request)
        ids = [p.spotify_playlist_id for p in results]
        self.assertEqual(ids, ["right"])
        self.assertNotIn("wrong", ids)

    def test_track_count_extracted_from_real_search_payload(self):
        request = RecommendationRequest(genre="r&b")
        pool = [
            None,
            {
                "id": "p1",
                "name": "R&B Jams",
                "description": "Smooth",
                "images": [{"url": "http://example.com/p1.jpg"}],
                "external_urls": {
                    "spotify": (
                        "http://open.spotify.com/playlist/p1"
                    ),
                },
                "owner": {
                    "display_name": "Curator",
                    "id": "owner-id",
                },
                "items": {
                    "href": (
                        "https://api.spotify.com/v1/playlists/"
                        "p1/items"
                    ),
                    "total": 100,
                },
            },
        ]
        engine = PlaylistEngine(
            FakeSpotifyService(default_playlists=pool)
        )
        results = engine.generate(request)

        # The live Spotify search payload carries the count under ``items``
        # and interleaves null entries; both are handled end-to-end.
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].track_count, 100)


class SpotifyServicePlaylistSearchTests(TestCase):
    def test_search_playlists_requests_playlist_type(self):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "playlists": {
                "items": [
                    {"id": "p1", "name": "Chill R&B"},
                ],
            },
        }

        with patch(
            "music.services.spotify.requests.get",
            return_value=mock_response,
        ) as mock_get:
            items = SpotifyService(
                "access-token"
            ).search_playlists("chill r&b", limit=5)

        mock_get.assert_called_once()
        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["q"], "chill r&b")
        self.assertEqual(params["type"], "playlist")
        self.assertEqual(params["limit"], 5)
        self.assertEqual(
            items,
            [{"id": "p1", "name": "Chill R&B"}],
        )

    def test_search_playlists_clamps_limit(self):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "playlists": {"items": []},
        }

        with patch(
            "music.services.spotify.requests.get",
            return_value=mock_response,
        ) as mock_get:
            items = SpotifyService(
                "access-token"
            ).search_playlists("test", limit=50)

        self.assertEqual(
            mock_get.call_args.kwargs["params"]["limit"],
            10,
        )
        self.assertEqual(items, [])

    def test_search_playlists_filters_null_items(self):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "playlists": {
                "items": [
                    None,
                    {"id": "p1", "name": "R&B 2026"},
                    None,
                    {"id": "p2", "name": "Calm RnB vibes"},
                ],
            },
        }

        with patch(
            "music.services.spotify.requests.get",
            return_value=mock_response,
        ) as mock_get:
            items = SpotifyService(
                "access-token"
            ).search_playlists("r&b", limit=5)

        self.assertEqual(
            [item["id"] for item in items],
            ["p1", "p2"],
        )


class RecommendationDiscoverViewTests(TestCase):
    def test_api_response_structure_is_compatible(self):
        user = get_user_model().objects.create_user(
            username="discoverer",
            password="pw12345",
        )
        SpotifyConnection.objects.create(
            user=user,
            spotify_account_id="spotify-account",
            access_token="access-token",
            refresh_token="refresh-token",
            token_expires_at=(
                timezone.now() + timedelta(hours=1)
            ),
        )

        pool = [
            make_track(
                "1",
                "Nights",
                "Frank Ocean",
                year=2016,
            ),
            make_track(
                "2",
                "Blonde",
                "Frank Ocean",
                year=2016,
            ),
            make_track(
                "3",
                "Long Time",
                "The Weeknd",
                year=2015,
            ),
        ]
        fake = FakeSpotifyService(
            default_items=pool
        )

        client = APIClient()
        client.force_authenticate(user=user)

        with patch(
            "recommendations.views.SpotifyService",
            return_value=fake,
        ):
            response = client.post(
                "/api/recommendations/discover/",
                {
                    "mood": "chill",
                    "genre": "r&b",
                    "era": "2010s",
                    "discovery_style": "balanced",
                },
                format="json",
            )

        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("request", payload)
        self.assertIn("results", payload)
        self.assertIn("playlists", payload)
        self.assertEqual(payload["playlists"], [])

        self.assertEqual(
            payload["request"]["genre"],
            "r&b",
        )
        self.assertEqual(
            payload["request"]["era"],
            "2010s",
        )

        for result in payload["results"]:
            for field in (
                "spotify_track_id",
                "name",
                "artist",
                "album",
                "artwork_url",
                "spotify_url",
                "score",
                "reasons",
            ):
                self.assertIn(field, result)

            self.assertIsInstance(
                result["spotify_track_id"],
                str,
            )
            self.assertIsInstance(result["score"], float)
            self.assertIsInstance(result["reasons"], list)
            self.assertGreaterEqual(result["score"], 0)
            self.assertLessEqual(result["score"], 100)

        ids = [
            r["spotify_track_id"]
            for r in payload["results"]
        ]
        self.assertEqual(len(ids), len(set(ids)))

        self.assertEqual(
            DiscoverySession.objects.count(),
            1,
        )

    def test_api_response_includes_playlists(self):
        user = get_user_model().objects.create_user(
            username="playlist-seeker",
            password="pw12345",
        )
        SpotifyConnection.objects.create(
            user=user,
            spotify_account_id="spotify-account-2",
            access_token="access-token",
            refresh_token="refresh-token",
            token_expires_at=(
                timezone.now() + timedelta(hours=1)
            ),
        )

        fake = FakeSpotifyService(
            default_items=[
                make_track(
                    "1",
                    "Nights",
                    "Frank Ocean",
                    year=2016,
                ),
            ],
            default_playlists=[
                make_playlist(
                    "p1",
                    "Chill R&B",
                    description="2010s late night vibes",
                ),
                make_playlist(
                    "p2",
                    "Random Mix",
                    description="Unrelated tracks",
                ),
            ],
        )

        client = APIClient()
        client.force_authenticate(user=user)

        with patch(
            "recommendations.views.SpotifyService",
            return_value=fake,
        ):
            response = client.post(
                "/api/recommendations/discover/",
                {
                    "mood": "chill",
                    "genre": "r&b",
                    "era": "2010s",
                    "discovery_style": "balanced",
                },
                format="json",
            )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertIn("results", payload)
        self.assertEqual(len(payload["results"]), 1)

        self.assertIn("playlists", payload)
        playlists = payload["playlists"]

        self.assertEqual(len(playlists), 1)
        self.assertEqual(
            playlists[0]["spotify_playlist_id"],
            "p1",
        )

        for field in (
            "spotify_playlist_id",
            "name",
            "description",
            "artwork_url",
            "spotify_url",
            "owner_name",
            "track_count",
            "score",
            "reasons",
        ):
            self.assertIn(field, playlists[0])

        self.assertIsInstance(
            playlists[0]["track_count"],
            int,
        )
        self.assertIsInstance(
            playlists[0]["score"],
            float,
        )
        self.assertIn(
            "Matches your r&b preference",
            playlists[0]["reasons"],
        )

        ids = [
            p["spotify_playlist_id"]
            for p in playlists
        ]
        self.assertEqual(ids, ["p1"])


class DiscoverySessionHistoryApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="historian",
            password="pw12345",
        )
        self.stranger = get_user_model().objects.create_user(
            username="stranger",
            password="pw12345",
        )
        self.client = APIClient()
        self.url = "/api/recommendations/sessions/"

    def make_session(self, user, **fields):
        fields.setdefault("discovery_style", "balanced")
        return DiscoverySession.objects.create(
            user=user,
            **fields,
        )

    def test_authenticated_user_receives_their_own_sessions(self):
        self.make_session(
            self.user,
            mood="chill",
            genre="r&b",
        )
        self.make_session(
            self.user,
            mood="happy",
            genre="pop",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_most_recent_sessions_come_first(self):
        first = self.make_session(self.user, mood="chill")
        second = self.make_session(self.user, mood="happy")
        third = self.make_session(self.user, mood="melancholic")

        base = timezone.now() - timedelta(days=1)
        DiscoverySession.objects.filter(pk=first.pk).update(
            created_at=base,
        )
        DiscoverySession.objects.filter(pk=second.pk).update(
            created_at=base + timedelta(hours=1),
        )
        DiscoverySession.objects.filter(pk=third.pk).update(
            created_at=base + timedelta(hours=2),
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(
            [entry["id"] for entry in response.data],
            [third.pk, second.pk, first.pk],
        )

    def test_other_users_sessions_are_excluded(self):
        self.make_session(
            self.user,
            mood="chill",
        )
        self.make_session(
            self.stranger,
            mood="energetic",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["mood"], "chill")

    def test_empty_history_returns_valid_empty_list(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_response_contains_expected_fields(self):
        session = self.make_session(
            self.user,
            mood="chill",
            genre="r&b",
            era="2010s",
            artist="Frank Ocean",
            discovery_style="new",
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        entry = response.data[0]
        self.assertEqual(entry["id"], session.pk)
        for field in (
            "id",
            "mood",
            "genre",
            "era",
            "artist",
            "discovery_style",
            "created_at",
        ):
            self.assertIn(field, entry)
        self.assertEqual(entry["mood"], "chill")
        self.assertEqual(entry["genre"], "r&b")
        self.assertEqual(entry["era"], "2010s")
        self.assertEqual(entry["artist"], "Frank Ocean")
        self.assertEqual(entry["discovery_style"], "new")

    def test_user_field_is_not_exposed(self):
        self.make_session(self.user, mood="chill")
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertNotIn("user", response.data[0])

    def test_history_is_limited_to_most_recent_twenty(self):
        base = timezone.now() - timedelta(hours=25)
        sessions = []
        for index in range(25):
            session = self.make_session(
                self.user,
                mood=f"mood-{index}",
            )
            sessions.append(session)

        for index, session in enumerate(sessions):
            DiscoverySession.objects.filter(pk=session.pk).update(
                created_at=base + timedelta(minutes=index),
            )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(len(response.data), 20)
        oldest_keys = [s.pk for s in sessions[:5]]
        returned_keys = [entry["id"] for entry in response.data]
        for key in oldest_keys:
            self.assertNotIn(key, returned_keys)