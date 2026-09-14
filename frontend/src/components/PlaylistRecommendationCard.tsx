import type { PlaylistRecommendation } from "../types/recommendation";

type PlaylistRecommendationCardProps = {
  playlist: PlaylistRecommendation;
  index: number;
};

function PlaylistRecommendationCard({
  playlist,
  index,
}: PlaylistRecommendationCardProps) {
  return (
    <li
      className="playlist-card"
      style={{ animationDelay: `${Math.min(index * 0.06, 0.5)}s` }}
    >
      <div className="playlist-card__art">
        {playlist.artwork_url ? (
          <img
            src={playlist.artwork_url}
            alt={`Playlist artwork for ${playlist.name}`}
            loading="lazy"
          />
        ) : (
          <span className="playlist-card__art-fallback" aria-hidden="true">
            {playlist.name.charAt(0) || "♪"}
          </span>
        )}
      </div>

      <div className="playlist-card__body">
        <h3 className="playlist-card__title">{playlist.name}</h3>

        {playlist.owner_name && (
          <p className="playlist-card__owner">{playlist.owner_name}</p>
        )}

        {playlist.description && (
          <p className="playlist-card__description">
            {playlist.description}
          </p>
        )}

        {playlist.reasons.length > 0 && (
          <ul className="playlist-card__reasons">
            {playlist.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        )}

        <div className="playlist-card__footer">
          <span className="playlist-card__meta">
            {playlist.track_count.toLocaleString()}{" "}
            {playlist.track_count === 1 ? "track" : "tracks"}
          </span>

          {playlist.spotify_url && (
            <a
              href={playlist.spotify_url}
              target="_blank"
              rel="noopener noreferrer"
              className="playlist-card__link"
              aria-label={`Open ${playlist.name} on Spotify`}
            >
              Open in Spotify <span aria-hidden="true">&rarr;</span>
            </a>
          )}
        </div>
      </div>
    </li>
  );
}

export default PlaylistRecommendationCard;