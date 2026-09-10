import {
  ERA_OPTIONS,
  GENRE_OPTIONS,
  MOOD_OPTIONS,
  STYLE_LABELS,
} from "../lib/discoveryOptions";
import type { DiscoveryForm } from "../types/discovery";

type RecommendationPreviewProps = {
  request: DiscoveryForm | null;
};

function labelFor<T>(
  options: { value: T; label: string }[],
  value: T | null
): string | null {
  const option = options.find((entry) => entry.value === value);
  return option ? option.label : null;
}

function RecommendationPreview({ request }: RecommendationPreviewProps) {
  if (!request) {
    return (
      <section className="result-panel" aria-label="Your discovery">
        <h2 className="result-panel__title">Your next discovery is waiting.</h2>
        <p className="result-panel__copy">
          Choose your direction above and we&apos;ll build a collection around
          it.
        </p>
      </section>
    );
  }

  const chips: (string | null)[] = [
    labelFor(MOOD_OPTIONS, request.mood),
    labelFor(GENRE_OPTIONS, request.genre),
    labelFor(ERA_OPTIONS, request.era),
    request.artist.trim() || null,
    STYLE_LABELS[request.discoveryStyle],
  ].filter((entry): entry is string => entry !== null && entry.length > 0);

  return (
    <section className="result-panel" aria-label="Your discovery">
      <p className="result-panel__eyebrow">Ready to discover</p>

      {chips.length > 0 ? (
        <ul className="summary-chips">
          {chips.map((chip, index) => (
            <li className="summary-chip" key={index}>
              {chip}
            </li>
          ))}
        </ul>
      ) : (
        <p className="result-panel__copy">
          Add a mood, genre, era, or artist to shape your discovery.
        </p>
      )}

      <p className="result-panel__note">
        Frontend prototype — real recommendations will appear here once
        HarmonIQ is connected to Spotify.
      </p>
    </section>
  );
}

export default RecommendationPreview;