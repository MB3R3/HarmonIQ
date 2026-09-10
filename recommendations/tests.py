from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from music.services.spotify import SpotifyAPIError
from users.models import SpotifyConnection

from .models import DiscoverySession
from .services.candidates import CandidateGenerator
from .services.engine import RecommendationEngine
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


class FakeSpotifyService:
    def __init__(
        self,
        results=None,
        default_items=None,
        artist_genres=None,
    ):
        self.results = results or {}
        self.default_items = default_items or []
        self.artist_genres = artist_genres or {}
        self.search_calls = []
        self.artist_calls = []

    def search(self, query, search_type="track", limit=10):
        self.search_calls.append(query)
        items = self.results.get(query)
        if items is None:
            items = self.default_items
        return {"tracks": {"items": list(items[:limit])}}

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