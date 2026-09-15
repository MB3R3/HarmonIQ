import re

TOKEN_PATTERN = re.compile(r"[a-z0-9&]+")

_DECADE_RE = re.compile(r"(?<!\d)(19[0-9]0|20[0-2]0)\b")
_SHORT_DECADE_RE = re.compile(r"(?<!\d)(([6-9]0|00))['\u2019]?s\b")
_YEAR_RE = re.compile(r"(?<!\d)(19[5-9]\d|20[0-2]\d)(?!\d)")
_REQUEST_DECADE_RE = re.compile(r"(19[0-9]0|2000|20[0-2]\d)")


def normalize_text(text):
    return " ".join(
        (text or "").lower().replace("-", " ").split()
    )


def playlist_text(playlist):
    """Normalized name + description metadata used for token/era checks."""
    name = normalize_text(playlist.get("name", ""))
    description = normalize_text(
        playlist.get("description", "")
    )
    return f"{name} {description}".strip()


def _tokenize(text):
    return set(TOKEN_PATTERN.findall(text))


def term_in_text(term, text):
    """Match a single token exactly or a multi-word phrase as substring."""
    term = normalize_text(term)
    if not term:
        return False
    if " " in term:
        return term in text
    return term in _tokenize(text)


def genre_matches(genre, text):
    genre = normalize_text(genre)
    if not genre:
        return False
    if term_in_text(genre, text):
        return True
    if genre.endswith("s") and len(genre) > 4:
        return term_in_text(genre[:-1], text)
    return False


def era_matches(era, text):
    label = era.strip().lower()
    decade = "".join(
        char for char in label if char.isdigit()
    )
    if term_in_text(label, text):
        return True
    if len(decade) >= 3 and decade in text:
        return True
    return False


def mentioned_decades(text):
    """Return sorted decade names (e.g. "2000s") explicitly signalled by text.

    Signals come from decade labels ("2010s", "90's"), full decade years,
    and 4-digit years that imply a decade ("2026" implies the 2020s).
    """
    decades = set()

    for match in _DECADE_RE.finditer(text):
        decade = (int(match.group(1)) // 10) * 10
        decades.add(f"{decade}s")

    for match in _SHORT_DECADE_RE.finditer(text):
        digits = match.group(1)
        if digits == "00":
            decades.add("2000s")
        else:
            decades.add(f"19{digits}s")

    for match in _YEAR_RE.finditer(text):
        year = int(match.group(1))
        decade = (year // 10) * 10
        decades.add(f"{decade}s")

    return sorted(decades)


def requested_decade(era):
    """Return the decade name (e.g. "2010s") implied by the request era."""
    match = _REQUEST_DECADE_RE.search(era or "")
    if not match:
        return None
    decade = (int(match.group(1)) // 10) * 10
    return f"{decade}s"


def era_conflicts(era, text):
    """True when the playlist signals a different era than requested.

    A playlist is only considered conflicting when it explicitly signals
    at least one decade and the requested decade is not among them. A
    mixed-era playlist that covers the requested decade is not penalized.
    """
    target = requested_decade(era)
    if target is None:
        return False
    mentioned = set(mentioned_decades(text))
    if not mentioned:
        return False
    return target not in mentioned


def playlist_era_conflict(playlist, era):
    """True when playlist metadata explicitly signals a conflicting era."""
    return era_conflicts(era, playlist_text(playlist))


class PlaylistScorer:

    ARTIST_WEIGHT = 35
    GENRE_WEIGHT = 30
    ERA_WEIGHT = 20
    MOOD_WEIGHT = 15

    # An explicit era conflict is the strongest negative signal: it exceeds
    # every positive signal combined (100) so a conflicting playlist always
    # scores at the floor and is excluded from results by the engine.
    ERA_CONFLICT_PENALTY = 100

    # Bonus for a playlist whose name spells out the search query.
    EXACT_QUERY_POINTS = 10

    MAX_SCORE = 100

    def score(self, playlist, request, source_query=""):
        """Score a playlist on transparent metadata/query relevance.

        Returns ``(score, reasons, relevance)`` where ``relevance`` covers
        only the positive metadata signals for the user's selections. The
        exact-query bonus and era-conflict penalty are excluded from
        ``relevance`` so a playlist cannot be rescued by a query match
        alone, and reasons are only ever produced from actual evidence.
        """
        name = normalize_text(playlist.get("name", ""))
        text = playlist_text(playlist)

        score = 0
        reasons = []
        relevance = 0

        # Artist.
        if request.artist:
            if term_in_text(request.artist, text):
                score += self.ARTIST_WEIGHT
                relevance += self.ARTIST_WEIGHT
                reasons.append(
                    f"Related to {request.artist.strip()}"
                )

        # Genre.
        if request.genre:
            if genre_matches(request.genre, text):
                score += self.GENRE_WEIGHT
                relevance += self.GENRE_WEIGHT
                reasons.append(
                    f"Matches your {request.genre.strip()} preference"
                )

        # Era.
        if request.era:
            if era_matches(request.era, text):
                score += self.ERA_WEIGHT
                relevance += self.ERA_WEIGHT
                reasons.append(
                    f"Matches your {request.era.strip()} preference"
                )
            elif era_conflicts(request.era, text):
                score -= self.ERA_CONFLICT_PENALTY
                reasons.append(
                    f"Conflicts with your {request.era.strip()} preference"
                )

        # Mood.
        if request.mood:
            if term_in_text(request.mood, text):
                score += self.MOOD_WEIGHT
                relevance += self.MOOD_WEIGHT
                reasons.append(
                    f"Fits a {request.mood.strip().lower()} mood"
                )

        # Exact query relevance: the playlist name spells out the query.
        query = " ".join(
            (source_query or "").lower().split()
        )
        if query and query in name:
            score += self.EXACT_QUERY_POINTS
            reasons.append(
                f"Name matches your {query} search"
            )

        score = max(0, min(score, self.MAX_SCORE))

        return score, reasons, relevance