from .recommender import RecommendationRequest


class PlaylistQueryBuilder:

    MAX_QUERIES = 5

    @staticmethod
    def build_many(
        request: RecommendationRequest,
        max_queries: int = MAX_QUERIES,
    ) -> list[str]:
        """Generate playlist search queries from the user's selections.

        Queries are ordered by expected usefulness so callers can truncate
        to ``max_queries`` without losing the most valuable searches.
        """
        genre = request.genre.strip().lower()
        mood = request.mood.strip().lower()
        era = request.era.strip().lower()
        artist = request.artist.strip().lower()

        queries = []
        seen = set()

        def add(query):
            query = " ".join(query.split())
            if not query:
                return
            key = PlaylistQueryBuilder._canonical_key(
                query,
                era,
            )
            if key in seen:
                return
            seen.add(key)
            queries.append(query)

        # Artist-focused.
        if artist:
            add(artist)

        # Genre anchor.
        if genre:
            add(genre)

        # Combined mood + era + genre surfaces the most specific matches:
        # without it Spotify often only returns wrong-era or era-only mixes.
        if genre and mood and era:
            add(f"{mood} {era} {genre}")

        # Genre + era.
        if genre and era:
            add(f"{era} {genre}")

        # Genre + mood.
        if genre and mood:
            add(f"{mood} {genre}")

        # Artist cross-overs.
        if artist:
            if genre:
                add(f"{artist} {genre}")
            if mood:
                add(f"{artist} {mood}")

        # Era-only fallback.
        if era and not genre and not artist:
            add(era)

        # Mood-only fallback.
        if mood and not genre and not artist:
            add(mood)

        return queries[:max_queries]

    @staticmethod
    def _canonical_key(query, era) -> str:
        """Produce a normalized key so word-order or era-variant queries dedupe."""
        key = " ".join(query.lower().split())

        if era:
            decade = "".join(
                char for char in era if char.isdigit()
            )

            if decade:
                key = key.replace(era, decade)

                label = era.rstrip("s")
                if label:
                    key = key.replace(label, decade)

        return " ".join(sorted(key.split()))