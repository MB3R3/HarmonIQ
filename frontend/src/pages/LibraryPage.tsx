import { useCallback, useEffect, useRef, useState } from "react";

import SavedTrackCard from "../components/SavedTrackCard";
import { deleteSavedTrack, getSavedTracks } from "../services/savedTracks";
import type { SavedTrack } from "../types/savedTrack";

type LibraryPageProps = {
  onNavigate?: (page: string) => void;
};

function LibraryPage({ onNavigate }: LibraryPageProps) {
  const [tracks, setTracks] = useState<SavedTrack[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [removingIds, setRemovingIds] = useState<Set<number>>(new Set());
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const deleteErrorTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleRetry = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getSavedTracks();
      setTracks(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load your library. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    getSavedTracks()
      .then((data) => {
        setTracks(data);
        setIsLoading(false);
      })
      .catch((err) => {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load your library. Please try again."
        );
        setIsLoading(false);
      });
  }, []);

  const showDeleteError = useCallback((message: string) => {
    if (deleteErrorTimer.current) clearTimeout(deleteErrorTimer.current);
    setDeleteError(message);
    deleteErrorTimer.current = setTimeout(() => setDeleteError(null), 4000);
  }, []);

  const handleRemove = useCallback(
    async (track: SavedTrack) => {
      if (removingIds.has(track.id)) return;

      setRemovingIds((prev) => new Set(prev).add(track.id));
      setDeleteError(null);

      try {
        await deleteSavedTrack(track.id);
        setTracks((prev) => prev.filter((t) => t.id !== track.id));
      } catch (err) {
        showDeleteError(
          err instanceof Error
            ? err.message
            : "Unable to remove this track. Please try again."
        );
      } finally {
        setRemovingIds((prev) => {
          const next = new Set(prev);
          next.delete(track.id);
          return next;
        });
      }
    },
    [removingIds, showDeleteError]
  );

  return (
    <section className="library">
      <header className="library__header">
        <p className="eyebrow">Library</p>
        <h1 className="library__title">Your saved tracks</h1>
        <p className="library__subtitle">
          Tracks you save from Discover show up here.
        </p>
      </header>

      {deleteError && (
        <p className="library__notice" role="alert">
          {deleteError}
        </p>
      )}

      {isLoading ? (
        <div className="library__loading" aria-label="Loading your library">
          <div className="loading-eq">
            <span />
            <span />
            <span />
            <span />
          </div>
        </div>
      ) : error ? (
        <div className="library__error">
          <p>{error}</p>
          <button
            type="button"
            className="button button--secondary"
            onClick={handleRetry}
          >
            Try again
          </button>
        </div>
      ) : tracks.length === 0 ? (
        <div className="library__empty">
          <p className="library__empty-heading">
            Your library is waiting for its first track.
          </p>
          <p className="library__empty-copy">
            Save songs from Discover and they'll appear here.
          </p>
          <button
            type="button"
            className="button button--primary"
            onClick={() => onNavigate?.("discover")}
          >
            Go to Discover
          </button>
        </div>
      ) : (
        <>
          <p className="library__count">
            {tracks.length} saved {tracks.length === 1 ? "track" : "tracks"}
          </p>
          <ul className="library__grid">
            {tracks.map((track, index) => (
              <SavedTrackCard
                key={track.id}
                track={track}
                isRemoving={removingIds.has(track.id)}
                onRemove={handleRemove}
                index={index}
              />
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

export default LibraryPage;
