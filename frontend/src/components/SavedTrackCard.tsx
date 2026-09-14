import type { SavedTrack } from "../types/savedTrack";

type SavedTrackCardProps = {
  track: SavedTrack;
  isRemoving: boolean;
  onRemove: (track: SavedTrack) => void;
  index: number;
};

function SavedTrackCard({
  track,
  isRemoving,
  onRemove,
  index,
}: SavedTrackCardProps) {
  return (
    <li
      className="track-card"
      style={{ animationDelay: `${Math.min(index * 0.06, 0.5)}s` }}
    >
      <div className="track-card__art">
        {track.artwork_url ? (
          <img
            src={track.artwork_url}
            alt={`Album artwork for ${track.album_name}`}
            loading="lazy"
          />
        ) : (
          <span className="track-card__art-fallback" aria-hidden="true">
            {track.track_name.charAt(0) || "\u266A"}
          </span>
        )}
      </div>

      <div className="track-card__body">
        <h3 className="track-card__title">{track.track_name}</h3>
        <p className="track-card__artist">{track.artist_name}</p>
        <p className="track-card__album">{track.album_name}</p>

        <div className="track-card__footer">
          <div className="track-card__actions">
            <button
              type="button"
              className={`save-toggle save-toggle--saved${isRemoving ? " save-toggle--pending" : ""}`}
              disabled={isRemoving}
              onClick={() => onRemove(track)}
            >
              {isRemoving ? "Removing\u2026" : "Remove"}
            </button>

            <a
              href={track.spotify_url}
              target="_blank"
              rel="noopener noreferrer"
              className="track-card__link"
            >
              Listen on Spotify <span aria-hidden="true">&rarr;</span>
            </a>
          </div>
        </div>
      </div>
    </li>
  );
}

export default SavedTrackCard;
