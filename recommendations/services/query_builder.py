from .recommender import RecommendationRequest


class RecommendationQueryBuilder:

    @staticmethod
    def build(request: RecommendationRequest) -> str:

        parts = []

        if request.genre:
            parts.append(request.genre)

        if request.artist:
            parts.append(request.artist)

        if request.mood:
            parts.append(request.mood)

        if request.era:
            parts.append(request.era)

        return " ".join(parts)