import { useEffect, useRef } from "react";

import RecommendationCard from "./RecommendationCard";
import {
  ERA_OPTIONS,
  GENRE_OPTIONS,
  MOOD_OPTIONS,
  STYLE_LABELS,
} from "../lib/discoveryOptions";
import type { DiscoveryForm } from "../types/discovery";
import type { Recommendation } from "../types/recommendation";

type RecommendationResultsProps = {
  form: DiscoveryForm;
  hasSubmitted: boolean;
  isLoading: boolean;
  error: string | null;
  results: Recommendation[];
  savedTracks: string[];
  onToggleSave: (trackId: string) => void;
  onRetry: () => void;
};

function labelFor<T>(
  options: { value: T; label: string }[],
  value: T | null
): string | null {
  const option = options.find((entry) => entry.value === value);
  return option ? option.label : null;
}

function buildHeading(form: DiscoveryForm): string {
  const mood = labelFor(MOOD_OPTIONS, form.mood);
  const genre = labelFor(GENRE_OPTIONS, form.genre);
  const era = labelFor(ERA_OPTIONS, form.era);
  const artist = form.artist.trim();

  if (era && genre) return `Your ${era} ${genre} discoveries`;
  if (mood) return `Something ${mood.toLowerCase()} for you`;
  if (genre) return `Fresh ${genre} finds`;
  if (era) return `The best of the ${era}`;
  if (artist) return `Discoveries with ${artist}`;
  return "Your discovery";
}

function buildSummary(form: DiscoveryForm): string[] {
  const parts: (string | null)[] = [
    labelFor(MOOD_OPTIONS, form.mood),
    labelFor(GENRE_OPTIONS, form.genre),
    labelFor(ERA_OPTIONS, form.era),
    form.artist.trim() || null,
    STYLE_LABELS[form.discoveryStyle],
  ];
  return parts.filter((part): part is string => part !== null && part.length > 0);
}

function RecommendationResults({
  form,
  hasSubmitted,
  isLoading,
  error,
  results,
  savedTracks,
  onToggleSave,
  onRetry,
}: RecommendationResultsProps) {
  const panelRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (results.length === 0) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    panelRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [results.length]);

  if (isLoading) {
    return (
      <section
        ref={panelRef}
        className="result-panel"
        role="status"
        aria-live="polite"
      >
        <p className="result-panel__eyebrow">HarmonIQ</p>
        <p className="result-panel__title">Finding your next sound&hellip;</p>
        <p className="result-panel__copy">
          Scanning for tracks that match your direction.
        </p>
        <div className="loading-eq" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section
        ref={panelRef}
        className="result-panel result-panel--error"
        role="alert"
      >
        <p className="result-panel__eyebrow">Something went wrong</p>
        <p className="result-panel__title">
          Unable to discover music right now.
        </p>
        <p className="result-panel__copy">{error}</p>
        <button
          type="button"
          className="button button--secondary result-panel__retry"
          onClick={onRetry}
        >
          Try again
        </button>
      </section>
    );
  }

  if (results.length > 0) {
    const summary = buildSummary(form);

    return (
      <section
        ref={panelRef}
        className="results-panel"
        aria-label="Your discoveries"
      >
        <header className="results-panel__header">
          <div>
            <h2 className="results-panel__heading">{buildHeading(form)}</h2>
            {summary.length > 0 && (
              <p className="results-panel__summary">{summary.join(" · ")}</p>
            )}
          </div>
          <p className="results-panel__count">
            {results.length} {results.length === 1 ? "track" : "tracks"} found
          </p>
        </header>

        <ul className="results-grid">
          {results.map((track, index) => (
            <RecommendationCard
              key={track.spotify_track_id}
              track={track}
              index={index}
              isSaved={savedTracks.includes(track.spotify_track_id)}
              onToggleSave={onToggleSave}
            />
          ))}
        </ul>
      </section>
    );
  }

  return (
    <section
      ref={panelRef}
      className="result-panel"
      aria-label="Your discovery"
    >
      <h2 className="result-panel__title">
        {hasSubmitted ? "No matches found." : "Your next discovery is waiting."}
      </h2>
      <p className="result-panel__copy">
        {hasSubmitted
          ? "Try adjusting your mood, genre, era, or artist and discover again."
          : "Set your direction above and let HarmonIQ find something worth hearing."}
      </p>
    </section>
  );
}

export default RecommendationResults;