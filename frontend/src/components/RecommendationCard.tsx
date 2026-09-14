import type { Recommendation } from "../types/recommendation";

type RecommendationCardProps = {
  track: Recommendation;
  isSaved: boolean;
  isPending: boolean;
  isSelected: boolean;
  onToggleSave: (track: Recommendation) => void;
  onToggleSelect: (track: Recommendation) => void;
  onOpenDetails: (track: Recommendation) => void;
  index: number;
};

function RecommendationCard({
  track,
  isSaved,
  isPending,
  isSelected,
  onToggleSave,
  onToggleSelect,
  onOpenDetails,
  index,
}: RecommendationCardProps) {
  const actionLabel = isSaved ? "Saved" : "Save";

  return (
    <li
      className="track-card"
      style={{ animationDelay: `${Math.min(index * 0.06, 0.5)}s` }}
    >
      <button
        type="button"
        className="track-card__open"
        aria-label={`View details for ${track.name} by ${track.artist}`}
        onClick={() => onOpenDetails(track)}
      />

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
              className={`select-toggle${
                isSelected ? " select-toggle--selected" : ""
              }`}
              aria-pressed={isSelected}
              onClick={() => onToggleSelect(track)}
            >
              {isSelected ? "✓ Selected" : "Select"}
            </button>

            <button
              type="button"
              className={`save-toggle${isSaved ? " save-toggle--saved" : ""}${
                isPending ? " save-toggle--pending" : ""
              }`}
              aria-pressed={isSaved}
              disabled={isPending}
              onClick={() => onToggleSave(track)}
            >
              {isPending
                ? isSaved
                  ? "Removing…"
                  : "Saving…"
                : actionLabel}
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