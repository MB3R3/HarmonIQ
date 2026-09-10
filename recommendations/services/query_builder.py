import re

from .recommender import RecommendationRequest


class RecommendationQueryBuilder:

    MAX_QUERIES = 4

    @staticmethod
    def build(request: RecommendationRequest) -> str:
        """Return a single primary query (V1-compatible entry point)."""
        queries = RecommendationQueryBuilder.build_many(request)
        return queries[0] if queries else ""

    @staticmethod
    def build_many(
        request: RecommendationRequest,
        max_queries: int = MAX_QUERIES,
    ) -> list[str]:
        """Generate several search queries derived from the user's selections.

        Queries are ordered by expected usefulness so callers can truncate
        to ``max_queries`` without losing the most valuable searches.
        """
        genre = request.genre.strip().lower()
        mood = request.mood.strip().lower()
        era = request.era.strip()
        artist = request.artist.strip().lower()

        era_decade = RecommendationQueryBuilder.decade_from_era(era)

        queries = []
        seen = set()

        def add(query):
            query = " ".join(query.split())
            if not query:
                return
            key = RecommendationQueryBuilder._canonical_key(
                query,
                era,
                era_decade,
            )
            if key in seen:
                return
            seen.add(key)
            queries.append(query)

        # Artist-focused.
        if artist:
            add(artist)

        # Genre-focused.
        if genre:
            add(genre)
            if mood:
                add(f"{mood} {genre}")
            if era_decade:
                add(f"{genre} {era_decade}")

        # Era-focused.
        if era and genre:
            add(f"{era} {genre}")
        elif era and not artist:
            add(f"{era} music")

        # Artist cross-overs (lower priority than genre breadth).
        if artist:
            if genre:
                add(f"{artist} {genre}")
            if mood:
                add(f"{artist} {mood}")

        # Mood-only fallback (mood alone has no stronger companion).
        if mood and not genre and not artist:
            add(mood)

        return queries[:max_queries]

    @staticmethod
    def decade_from_era(era) -> str:
        """Map an era label such as ``2010s`` to its decade year ``2010``."""
        digits = re.sub(r"\D", "", era or "")
        if not digits:
            return ""
        year = int(digits)
        return str(year - (year % 10))

    @staticmethod
    def _canonical_key(query, era, era_decade) -> str:
        """Produce a normalized key so word-order or era variant queries dedupe."""
        key = query.lower()
        if era and era_decade:
            key = key.replace(era.lower(), era_decade)
        return " ".join(sorted(key.split()))