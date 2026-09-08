def get_release_year(track):
    release_date = (
        track.get("album", {}).get("release_date", "")
    )

    if not release_date:
        return None

    return int(release_date[:4])


class RecommendationScorer:

    def score(self, track, request):

        score = 0
        reasons = []

        track_name = track.get("name", "")

        artists = track.get("artists", [])

        artist_names = [
            artist.get("name", "")
            for artist in artists
        ]

        combined_text = (
            f"{track_name} "
            f"{' '.join(artist_names)}"
        ).lower()

        # Artist matching
        if request.artist:
            if request.artist.lower() in combined_text:
                score += 40

                reasons.append(
                    f"Related to {request.artist}"
                )

        # Genre signal
        #
        # Temporary query-level signal.
        # We'll improve this later using
        # richer catalog/user data.
        if request.genre:
            score += 20

            reasons.append(
                f"Matches {request.genre}"
            )

        # Mood signal
        #
        # This is intentionally lightweight
        # until we have a reliable source of
        # mood metadata.
        if request.mood:
            score += 15

            reasons.append(
                f"Fits a {request.mood} mood"
            )

        # Era matching
        if request.era:

            release_year = get_release_year(track)

            if release_year:

                era_start = self.get_era_start(
                    request.era
                )

                if era_start is not None:

                    era_end = era_start + 9

                    if era_start <= release_year <= era_end:

                        score += 25

                        reasons.append(
                            f"Released in the {request.era}"
                        )

        return score, reasons

    @staticmethod
    def get_era_start(era):

        era = era.lower().replace("s", "")

        try:
            return int(era)
        except ValueError:
            return None