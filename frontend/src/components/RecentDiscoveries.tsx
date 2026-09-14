import {
  ERA_OPTIONS,
  GENRE_OPTIONS,
  MOOD_OPTIONS,
  STYLE_OPTIONS,
} from "../lib/discoveryOptions";
import type { DiscoverySession } from "../types/discoverySession";

type RecentDiscoveriesProps = {
  isLoading: boolean;
  error: string | null;
  sessions: DiscoverySession[];
  onRetry: () => void;
};

type LabelOption = {
  value: string;
  label: string;
};

function capitalize(value: string): string {
  return value.replace(/\b[a-z]/g, (char) => char.toUpperCase());
}

function labelFor(
  value: string,
  options: LabelOption[]
): string {
  const match = options.find((option) => option.value === value);
  return match ? match.label : capitalize(value);
}

function formatSessionTitle(session: DiscoverySession): string {
  const mood = labelFor(session.mood, MOOD_OPTIONS);
  const genre = labelFor(session.genre, GENRE_OPTIONS);
  const parts = [mood, genre].filter(Boolean);
  const base = parts.length > 0 ? parts.join(" ") : "Discovery";
  return session.artist ? `${base} · ${session.artist}` : base;
}

function formatSessionMeta(session: DiscoverySession): string {
  const era = labelFor(session.era, ERA_OPTIONS);
  const style = labelFor(session.discovery_style, STYLE_OPTIONS);
  return [era, style].filter(Boolean).join(" · ");
}

function formatSessionDate(createdAt: string): string {
  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) return "";

  const now = new Date();
  const startOfToday = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate()
  ).getTime();
  const startOfDay = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate()
  ).getTime();
  const dayDiff = Math.round(
    (startOfToday - startOfDay) / 86400000
  );

  if (dayDiff === 0) return "Today";
  if (dayDiff === 1) return "Yesterday";

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function RecentDiscoveries({
  isLoading,
  error,
  sessions,
  onRetry,
}: RecentDiscoveriesProps) {
  const sessionCount = sessions.length;

  return (
    <section className="recent" aria-label="Recent discoveries">
      <div className="recent__heading">
        <h2 className="recent__title">Recent discoveries</h2>
        {!isLoading && !error && sessionCount > 0 && (
          <p className="recent__note">
            {sessionCount}{" "}
            {sessionCount === 1 ? "session" : "sessions"}
          </p>
        )}
      </div>

      {isLoading ? (
        <div
          className="recent__status"
          aria-label="Loading recent discoveries"
        >
          <div className="loading-eq" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
          </div>
        </div>
      ) : error ? (
        <div className="recent__error" role="alert">
          <p>{error}</p>
          <button
            type="button"
            className="button button--secondary"
            onClick={onRetry}
          >
            Retry
          </button>
        </div>
      ) : sessionCount === 0 ? (
        <div className="recent__empty">
          <p className="recent__empty-heading">No discoveries yet.</p>
          <p className="recent__empty-copy">
            Your recent discovery sessions will appear here.
          </p>
        </div>
      ) : (
        <ul className="recent__grid">
          {sessions.map((session) => (
            <li key={session.id} className="recent__card">
              <div className="recent__card-title">
                {formatSessionTitle(session)}
              </div>
              <div className="recent__card-meta">
                {formatSessionMeta(session)}
              </div>
              <div className="recent__card-date">
                {formatSessionDate(session.created_at)}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default RecentDiscoveries;