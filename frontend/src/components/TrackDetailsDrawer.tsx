import { useEffect, useRef } from "react";

import type { Recommendation } from "../types/recommendation";

type TrackDetailsDrawerProps = {
  track: Recommendation;
  isSaved: boolean;
  isPending: boolean;
  saveError: string | null;
  onToggleSave: (track: Recommendation) => void;
  onClose: () => void;
};

const FOCUSABLE_SELECTOR = [
  "button:not([disabled])",
  "input:not([disabled])",
  "textarea:not([disabled])",
  "select:not([disabled])",
  "[href]",
].join(", ");

function TrackDetailsDrawer({
  track,
  isSaved,
  isPending,
  saveError,
  onToggleSave,
  onClose,
}: TrackDetailsDrawerProps) {
  const drawerRef = useRef<HTMLElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab") return;
      const root = drawerRef.current;
      if (!root) return;
      const focusable = Array.from(
        root.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
      ).filter((el) => el.getAttribute("tabindex") !== "-1");
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (event.shiftKey) {
        if (active === first || !root.contains(active)) {
          event.preventDefault();
          last.focus();
        }
      } else if (active === last || !root.contains(active)) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [onClose]);

  return (
    <div
      className="drawer-backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <aside
        ref={drawerRef}
        className="drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="track-details-title"
        aria-describedby="track-details-summary"
      >
        <div className="drawer__topbar">
          <p className="drawer__eyebrow">Track details</p>
          <button
            ref={closeButtonRef}
            type="button"
            className="modal__close"
            aria-label="Close track details"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        <div className="drawer__art">
          {track.artwork_url ? (
            <img
              src={track.artwork_url}
              alt={`Album artwork for ${track.album}`}
            />
          ) : (
            <span className="drawer__art-fallback" aria-hidden="true">
              {track.name.charAt(0) || "♪"}
            </span>
          )}
        </div>

        <div className="drawer__body">
          <h2 id="track-details-title" className="drawer__title">
            {track.name}
          </h2>

          <div className="drawer__meta" id="track-details-summary">
            <p className="drawer__artist">{track.artist}</p>
            <p className="drawer__album">{track.album}</p>
          </div>

          {typeof track.score === "number" && (
            <p className="drawer__match">
              Match <strong>{Math.round(track.score)}%</strong>
            </p>
          )}

          <div className="drawer__reasons">
            <h3 className="drawer__reasons-heading">Why this fits</h3>
            <ul>
              {track.reasons.length > 0 ? (
                track.reasons.map((reason) => <li key={reason}>{reason}</li>)
              ) : (
                <li>Matched your discovery direction.</li>
              )}
            </ul>
          </div>
        </div>

        <div className="drawer__footer">
          {saveError && (
            <p className="drawer__error" role="alert">
              {saveError}
            </p>
          )}

          <div className="drawer__actions">
            <button
              type="button"
              className={`save-toggle save-toggle--drawer${
                isSaved ? " save-toggle--saved" : ""
              }${isPending ? " save-toggle--pending" : ""}`}
              aria-pressed={isSaved}
              disabled={isPending}
              onClick={() => onToggleSave(track)}
            >
              {isPending
                ? isSaved
                  ? "Removing…"
                  : "Saving…"
                : isSaved
                  ? "Saved"
                  : "Save"}
            </button>

            {track.spotify_url && (
              <a
                href={track.spotify_url}
                target="_blank"
                rel="noopener noreferrer"
                className="button button--secondary drawer__open"
              >
                Open in Spotify <span aria-hidden="true">&rarr;</span>
              </a>
            )}
          </div>
        </div>
      </aside>
    </div>
  );
}

export default TrackDetailsDrawer;