def get_release_year(track):
    release_date = (
        track.get("album", {}).get("release_date", "")
    )

    if not release_date:
        return None

    try:
        return int(release_date[:4])
    except (TypeError, ValueError):
        return None


def genres_match(user_genre, artist_genres):
    """Fuzzy-match a requested genre against verified artist genres."""
    user_norm = user_genre.lower().replace("-", " ").strip()

    if not user_norm:
        return False

    for genre in artist_genres:
        genre_norm = (
            (genre or "").lower().replace("-", " ").strip()
        )

        if not genre_norm:
            continue

        if user_norm == genre_norm:
            return True

        if (
            user_norm in genre_norm
            or genre_norm in user_norm
        ):
            return True

    return False


class RecommendationScorer:

    ARTIST_WEIGHT = 40
    GENRE_WEIGHT = 20
    ERA_WEIGHT = 20
    MOOD_WEIGHT = 10
    DISCOVERY_STYLE_WEIGHT = 10

    # Unverified genre signal derived from the search query itself.
    QUERY_LEVEL_GENRE_POINTS = 10

    def score(
        self,
        track,
        request,
        artist_genres=None,
        source_query="",
    ):
        """Score a candidate on a 0-100 scale.

        Returns ``(score, reasons, relevance_points)``. ``relevance_points``
        excludes the discovery-style bonus so irrelevant tracks cannot be
        rescued by style alone.
        """
        artist_genres = artist_genres or {}

        score = 0
        reasons = []
        relevance_points = 0

        track_name = track.get("name", "")

        artists = track.get("artists", [])

        artist_names = [
            artist.get("name", "")
            for artist in artists
        ]

        artist_ids = [
            artist.get("id")
            for artist in artists
        ]

        combined_text = (
            f"{track_name} "
            f"{' '.join(artist_names)}"
        ).lower()

        # Artist relevance.
        if request.artist:
            if request.artist.lower() in combined_text:
                score += self.ARTIST_WEIGHT
                relevance_points += self.ARTIST_WEIGHT

                reasons.append(
                    f"Related to {request.artist}"
                )

        # Genre relevance.
        #
        # Preferred signal: verified artist genres from the bounded
        # metadata lookup. Fallback: query/search relevance only.
        if request.genre:
            genre_points = 0

            if any(
                artist_id in artist_genres
                and genres_match(
                    request.genre,
                    artist_genres[artist_id],
                )
                for artist_id in artist_ids
            ):
                genre_points = self.GENRE_WEIGHT

                reasons.append(
                    f"Matches your {request.genre} preference"
                )

            elif (
                request.genre.lower()
                in (source_query or "").lower()
            ):
                genre_points = (
                    self.QUERY_LEVEL_GENRE_POINTS
                )

                reasons.append(
                    f"Found in your {request.genre} search"
                )

            score += genre_points
            relevance_points += genre_points

        # Era relevance (verified via release date).
        if request.era:
            release_year = get_release_year(track)

            era_start = self.get_era_start(
                request.era
            )

            if release_year and era_start is not None:

                era_end = era_start + 9

                if era_start <= release_year <= era_end:

                    score += self.ERA_WEIGHT
                    relevance_points += (
                        self.ERA_WEIGHT
                    )

                    reasons.append(
                        f"Released in the {request.era}"
                    )

        # Mood relevance.
        #
        # Spotify track metadata does not expose a reliable mood
        # field, so this is an honest query/search relevance signal:
        # the candidate surfaced through a query that asked for the
        # mood, nothing more.
        if request.mood:
            if request.mood.lower() in (
                source_query or ""
            ).lower():
                score += self.MOOD_WEIGHT
                relevance_points += self.MOOD_WEIGHT

                reasons.append(
                    f"Matched your {request.mood} search"
                )

        # Discovery style.
        #
        # Track popularity is used as a rough familiarity signal.
        if request.discovery_style == "familiar":
            if track.get("popularity", 0) >= 65:
                score += self.DISCOVERY_STYLE_WEIGHT

                reasons.append(
                    "A popular pick for your familiar "
                    "style"
                )

        elif request.discovery_style == "new":
            if track.get("popularity", 0) <= 35:
                score += self.DISCOVERY_STYLE_WEIGHT

                reasons.append(
                    "An under-the-radar pick for your "
                    "new style"
                )

        return score, reasons, relevance_points

    @staticmethod
    def relevance_threshold(request) -> int:
        """Minimum evidence required for a candidate to stay relevant.

        Combination requests (genre/era plus at least one other selection)
        demand more evidence so unrelated tracks cannot slip in on weak
        query-level points alone.

        """
        present = [
            value
            for value in (
                request.genre,
                request.era,
                request.mood,
                request.artist,
            )
            if value
        ]

        if (
            len(present) >= 2
            and (request.genre or request.era)
        ):
            return 20

        return 10

    @staticmethod
    def get_era_start(era):

        era = era.lower().replace("s", "")

        try:
            return int(era)
        except ValueError:
            return None