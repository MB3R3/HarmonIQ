import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { createSpotifyPlaylist } from "../services/playlists";
import type { CreatedPlaylist } from "../types/playlist";

type CreatePlaylistModalProps = {
  trackIds: string[];
  onClose: () => void;
  onCreated: () => void;
};

const FOCUSABLE_SELECTOR = [
  "button:not([disabled])",
  "input:not([disabled])",
  "textarea:not([disabled])",
  "select:not([disabled])",
  "[href]",
].join(", ");

const DEFAULT_NAME = "HarmonIQ Playlist";

function CreatePlaylistModal({
  trackIds,
  onClose,
  onCreated,
}: CreatePlaylistModalProps) {
  const [name, setName] = useState(DEFAULT_NAME);
  const [description, setDescription] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [status, setStatus] = useState<"idle" | "success">("idle");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<CreatedPlaylist | null>(null);

  const dialogRef = useRef<HTMLDivElement>(null);
  const successHeadingRef = useRef<HTMLHeadingElement>(null);
  const isSubmittingRef = useRef(false);

  const trackCount = trackIds.length;

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        if (!isSubmittingRef.current) onClose();
        return;
      }
      if (event.key !== "Tab") return;
      const root = dialogRef.current;
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

  useEffect(() => {
    if (status === "success") {
      successHeadingRef.current?.focus();
    }
  }, [status]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const trimmedName = name.trim();
    if (isSubmittingRef.current || trackCount === 0 || !trimmedName) return;

    isSubmittingRef.current = true;
    setIsSubmitting(true);
    setError(null);

    try {
      const playlist = await createSpotifyPlaylist({
        name: trimmedName,
        description: description.trim(),
        public: isPublic,
        track_ids: trackIds,
      });
      setCreated(playlist);
      setStatus("success");
      onCreated();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create your playlist. Please try again."
      );
    } finally {
      isSubmittingRef.current = false;
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="modal-backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget && !isSubmittingRef.current) {
          onClose();
        }
      }}
    >
      <div
        ref={dialogRef}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={
          status === "success"
            ? "create-playlist-success-title"
            : "create-playlist-title"
        }
      >
        {status === "success" && created ? (
          <>
            <div className="modal__header">
              <h2
                id="create-playlist-success-title"
                className="modal__title"
                tabIndex={-1}
                ref={successHeadingRef}
              >
                Playlist created ✓
              </h2>
              <button
                type="button"
                className="modal__close"
                aria-label="Close playlist confirmation"
                onClick={onClose}
              >
                ×
              </button>
            </div>

            <div className="modal__body">
              <div className="modal__success">
                <h3 className="modal__success-title">{created.name}</h3>
                <p className="modal__success-copy">
                  Your playlist was created with{" "}
                  {created.track_count}{" "}
                  {created.track_count === 1 ? "track" : "tracks"}.
                </p>

                <div className="modal__success-actions">
                  <a
                    href={created.spotify_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="button button--primary"
                  >
                    Open in Spotify <span aria-hidden="true">&rarr;</span>
                  </a>
                  <button
                    type="button"
                    className="button button--secondary"
                    onClick={onClose}
                  >
                    Done
                  </button>
                </div>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="modal__header">
              <div>
                <h2 id="create-playlist-title" className="modal__title">
                  Create Playlist
                </h2>
                <p className="modal__subtitle">
                  Build a Spotify playlist from {trackCount}{" "}
                  {trackCount === 1 ? "track" : "tracks"} you selected.
                </p>
              </div>
              <button
                type="button"
                className="modal__close"
                aria-label="Close create playlist dialog"
                onClick={onClose}
              >
                ×
              </button>
            </div>

            <form className="modal__body" onSubmit={handleSubmit}>
              {error && (
                <p className="modal__error" role="alert">
                  {error}
                </p>
              )}

              <div className="modal-field">
                <label className="selector__label" htmlFor="playlist-name">
                  Playlist name
                </label>
                <input
                  id="playlist-name"
                  className="input"
                  type="text"
                  value={name}
                  maxLength={100}
                  autoFocus
                  onChange={(event) => setName(event.target.value)}
                />
              </div>

              <div className="modal-field">
                <label
                  className="selector__label"
                  htmlFor="playlist-description"
                >
                  Description (optional)
                </label>
                <textarea
                  id="playlist-description"
                  className="input modal__textarea"
                  value={description}
                  maxLength={300}
                  rows={3}
                  onChange={(event) => setDescription(event.target.value)}
                />
              </div>

              <div className="modal-field">
                <span
                  className="selector__label"
                  id="playlist-visibility-label"
                >
                  Visibility
                </span>
                <div
                  className="selector__options"
                  role="group"
                  aria-labelledby="playlist-visibility-label"
                >
                  <button
                    type="button"
                    className={`pill pill--compact${
                      isPublic ? "" : " pill--selected"
                    }`}
                    aria-pressed={!isPublic}
                    onClick={() => setIsPublic(false)}
                  >
                    Private
                  </button>
                  <button
                    type="button"
                    className={`pill pill--compact${
                      isPublic ? " pill--selected" : ""
                    }`}
                    aria-pressed={isPublic}
                    onClick={() => setIsPublic(true)}
                  >
                    Public
                  </button>
                </div>
              </div>

              <div className="modal__actions">
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={onClose}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="button button--primary"
                  disabled={isSubmitting || !name.trim() || trackCount === 0}
                >
                  {isSubmitting ? "Creating…" : "Create Playlist"}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

export default CreatePlaylistModal;