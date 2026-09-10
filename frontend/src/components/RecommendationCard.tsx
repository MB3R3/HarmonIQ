import type { Recommendation } from "../types/recommendation";

type RecommendationCardProps = {
  track: Recommendation;
  isSaved: boolean;
  onToggleSave: (trackId: string) => void;
  index: number;
};

function RecommendationCard({
  track,
  isSaved,
  onToggleSave,
  index,
}: RecommendationCardProps) {
  return (
    <li
      className="track-card"
      style={{ animationDelay: `${Math.min(index * 0.06, 0.5)}s` }}
    >
      <div className="track-card__art">
        {track.artwork_url ? (
          <img
            src={track.artwork_url}
            alt={`Album artwork for ${track.album}`}
            loading="lazy"
          />
        ) : (
          <span className="track-card__art-fallback" aria-hidden="true">
            {track.name.charAt(0) || "♪"}
          </span>
        )}
      </div>

      <div className="track-card__body">
        <h3 className="track-card__title">{track.name}</h3>
        <p className="track-card__artist">{track.artist}</p>
        <p className="track-card__album">{track.album}</p>

        {track.reasons.length > 0 && (
          <ul className="track-card__reasons">
            {track.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        )}

        <div className="track-card__footer">
          {typeof track.score === "number" && (
            <span className="track-card__score">
              match {Math.round(track.score)}%
            </span>
          )}

          <div className="track-card__actions">
            <button
              type="button"
              className={`save-toggle${isSaved ? " save-toggle--saved" : ""}`}
              aria-pressed={isSaved}
              onClick={() => onToggleSave(track.spotify_track_id)}
            >
              {isSaved ? "Saved" : "Save"}
            </button>

            {track.spotify_url && (
              <a
                href={track.spotify_url}
                target="_blank"
                rel="noopener noreferrer"
                className="track-card__link"
              >
                Listen on Spotify <span aria-hidden="true">&rarr;</span>
              </a>
            )}
          </div>
        </div>
      </div>
    </li>
  );
}

export default RecommendationCard;