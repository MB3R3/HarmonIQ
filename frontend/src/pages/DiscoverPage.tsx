import { useCallback, useEffect, useRef, useState } from "react";

import CreatePlaylistModal from "../components/CreatePlaylistModal";
import DiscoveryBuilder from "../components/DiscoveryBuilder";
import RecentDiscoveries from "../components/RecentDiscoveries";
import RecommendationResults from "../components/RecommendationResults";
import { useAuth } from "../context/useAuth";
import { API_BASE_URL } from "../services/api";
import {
  deleteSavedTrack,
  getSavedTracks,
  saveTrack,
} from "../services/savedTracks";
import { discoverMusic } from "../services/recommendations";
import { getDiscoverySessions } from "../services/discoverySessions";
import { getPreferences } from "../services/preferences";
import {
  ERA_OPTIONS,
  GENRE_OPTIONS,
  MOOD_OPTIONS,
  STYLE_OPTIONS,
} from "../lib/discoveryOptions";
import type { DiscoveryForm, Era, Genre } from "../types/discovery";
import type { DiscoverySession } from "../types/discoverySession";
import type {
  PlaylistRecommendation,
  Recommendation,
} from "../types/recommendation";
import type { PreferencesUpdate } from "../types/preferences";
import type { SaveTrackPayload, SavedTrack } from "../types/savedTrack";

const SPOTIFY_LOGIN_URL = `${API_BASE_URL}/api/users/spotify/login/`;

const INITIAL_FORM: DiscoveryForm = {
  mood: null,
  genre: null,
  era: null,
  artist: "",
  discoveryStyle: "balanced",
};

function greetingForLocalHour(hour: number): string {
  if (hour >= 5 && hour < 12) return "Good morning";
  if (hour >= 12 && hour < 17) return "Good afternoon";
  return "Good evening";
}

function prefillFromPreferences(
  prefs: PreferencesUpdate,
  current: DiscoveryForm
): DiscoveryForm | null {
  const genre = prefs.favorite_genres
    .map((value) => GENRE_OPTIONS.find((option) => option.value === value)?.value)
    .find((value): value is Genre => Boolean(value));
  const era = prefs.preferred_eras
    .map((value) => ERA_OPTIONS.find((option) => option.value === value)?.value)
    .find((value): value is Era => Boolean(value));
  const mood = MOOD_OPTIONS.find(
    (option) => option.value === prefs.default_mood
  )?.value;
  const style = STYLE_OPTIONS.find(
    (option) => option.value === prefs.discovery_style
  )?.value;

  const next: DiscoveryForm = {
    mood: mood ?? current.mood,
    genre: genre ?? current.genre,
    era: era ?? current.era,
    artist: current.artist,
    discoveryStyle: style ?? current.discoveryStyle,
  };

  const applied =
    next.mood !== current.mood ||
    next.genre !== current.genre ||
    next.era !== current.era ||
    next.discoveryStyle !== current.discoveryStyle;

  return applied ? next : null;
}

function DiscoverPage() {
  const { user } = useAuth();
  const [form, setForm] = useState<DiscoveryForm>(INITIAL_FORM);
  const [submittedForm, setSubmittedForm] =
    useState<DiscoveryForm>(INITIAL_FORM);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<Recommendation[]>([]);
  const [playlists, setPlaylists] = useState<PlaylistRecommendation[]>([]);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const [savedTracks, setSavedTracks] = useState<SavedTrack[]>([]);
  const [pendingSaves, setPendingSaves] = useState<Set<string>>(new Set());
  const [saveError, setSaveError] = useState<string | null>(null);
  const saveErrorTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [selectedTrackIds, setSelectedTrackIds] = useState<Set<string>>(
    new Set()
  );
  const [isCreatePlaylistOpen, setIsCreatePlaylistOpen] = useState(false);

  const [discoverySessions, setDiscoverySessions] = useState<
    DiscoverySession[]
  >([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const [preferencesApplied, setPreferencesApplied] = useState(false);
  const formEditedRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    getPreferences()
      .then((prefs) => {
        if (cancelled) return;
        if (formEditedRef.current) return;
        const prefill = prefillFromPreferences(prefs, INITIAL_FORM);
        if (prefill) {
          setForm(prefill);
          setPreferencesApplied(true);
        }
      })
      .catch(() => {
        // Preferences are optional on Discover — keep untampered defaults.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleFormChange = useCallback((next: DiscoveryForm) => {
    formEditedRef.current = true;
    setForm(next);
  }, []);

  useEffect(() => {
    getDiscoverySessions()
      .then(setDiscoverySessions)
      .catch(() =>
        setHistoryError("Couldn't load recent discoveries.")
      )
      .finally(() => setIsHistoryLoading(false));
  }, []);

  const retryDiscoveryHistory = useCallback(() => {
    setHistoryError(null);
    setIsHistoryLoading(true);
    getDiscoverySessions()
      .then(setDiscoverySessions)
      .catch(() =>
        setHistoryError("Couldn't load recent discoveries.")
      )
      .finally(() => setIsHistoryLoading(false));
  }, []);

  useEffect(() => {
    getSavedTracks()
      .then(setSavedTracks)
      .catch(() => {
        // Silently ignore — saved state will just be empty until next refresh.
      });
  }, []);

  const savedIdMap = useRef<Map<string, number>>(new Map());
  useEffect(() => {
    const next = new Map<string, number>();
    for (const record of savedTracks) {
      next.set(record.spotify_track_id, record.id);
    }
    savedIdMap.current = next;
  }, [savedTracks]);

  const showSaveError = useCallback((message: string) => {
    if (saveErrorTimer.current) clearTimeout(saveErrorTimer.current);
    setSaveError(message);
    saveErrorTimer.current = setTimeout(() => setSaveError(null), 4000);
  }, []);

  const handleToggleSave = useCallback(
    async (track: Recommendation) => {
      const trackId = track.spotify_track_id;
      if (pendingSaves.has(trackId)) return;

      setPendingSaves((prev) => new Set(prev).add(trackId));
      setSaveError(null);

      const isSaved = savedIdMap.current.has(trackId);

      try {
        if (isSaved) {
          const recordId = savedIdMap.current.get(trackId)!;
          await deleteSavedTrack(recordId);
          setSavedTracks((prev) =>
            prev.filter((r) => r.spotify_track_id !== trackId)
          );
        } else {
          const payload: SaveTrackPayload = {
            spotify_track_id: track.spotify_track_id,
            track_name: track.name,
            artist_name: track.artist,
            album_name: track.album,
            artwork_url: track.artwork_url,
          };
          const record = await saveTrack(payload);
          setSavedTracks((prev) => {
            if (prev.some((r) => r.spotify_track_id === trackId)) return prev;
            return [...prev, record];
          });
        }
      } catch (err) {
        showSaveError(
          err instanceof Error
            ? err.message
            : "Unable to save this track. Please try again."
        );
      } finally {
        setPendingSaves((prev) => {
          const next = new Set(prev);
          next.delete(trackId);
          return next;
        });
      }
    },
    [pendingSaves, showSaveError]
  );

  const handleToggleSelect = useCallback((track: Recommendation) => {
    setSelectedTrackIds((prev) => {
      const next = new Set(prev);
      if (next.has(track.spotify_track_id)) {
        next.delete(track.spotify_track_id);
      } else {
        next.add(track.spotify_track_id);
      }
      return next;
    });
  }, []);

  const handleOpenCreatePlaylist = useCallback(() => {
    setIsCreatePlaylistOpen(true);
  }, []);

  const handleCloseCreatePlaylist = useCallback(() => {
    setIsCreatePlaylistOpen(false);
  }, []);

  const handlePlaylistCreated = useCallback(() => {
    setSelectedTrackIds(new Set());
  }, []);

  const handleSubmit = async (next: DiscoveryForm) => {
    setError(null);
    setIsLoading(true);
    setHasSubmitted(true);
    setSelectedTrackIds(new Set());

    try {
      const response = await discoverMusic(next);
      setResults(response.results);
      setPlaylists(response.playlists);
      setSubmittedForm(next);
    } catch (err) {
      setResults([]);
      setPlaylists([]);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to discover music right now. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const savedIds = new Set(
    savedTracks.map((r) => r.spotify_track_id)
  );

  const greeting = `${greetingForLocalHour(new Date().getHours())}, ${
    user?.username ?? "music lover"
  }`;

  return (
    <section className="discover">
      {user && !user.spotify_connected && (
        <div className="discover__connect">
          <div className="discover__connect-copy">
            <p className="discover__connect-title">Connect Spotify</p>
            <p className="discover__connect-text">
              Connect your Spotify account to personalize your music
              discovery.
            </p>
          </div>
          <a
            href={SPOTIFY_LOGIN_URL}
            className="button button--primary discover__connect-action"
          >
            Connect Spotify
          </a>
        </div>
      )}

      <header className="discover__header">
        <p className="eyebrow">Discover</p>
        <h1 className="discover__title">{greeting}.</h1>
        <p className="discover__subtitle">
          What are you in the mood to hear?
        </p>
        <p className="discover__support">
          Shape a discovery and HarmonIQ will find something that fits.
        </p>
        {preferencesApplied && (
          <p className="discover__prefs-note">Using your preferences</p>
        )}
      </header>

      <DiscoveryBuilder form={form} onChange={handleFormChange} onSubmit={handleSubmit} />

      <RecommendationResults
        form={submittedForm}
        hasSubmitted={hasSubmitted}
        isLoading={isLoading}
        error={error}
        results={results}
        playlists={playlists}
        savedIds={savedIds}
        pendingSaves={pendingSaves}
        selectedIds={selectedTrackIds}
        onToggleSave={handleToggleSave}
        onToggleSelect={handleToggleSelect}
        onCreatePlaylist={handleOpenCreatePlaylist}
        saveError={saveError}
        onRetry={() => handleSubmit(form)}
      />

      <RecentDiscoveries
        isLoading={isHistoryLoading}
        error={historyError}
        sessions={discoverySessions}
        onRetry={retryDiscoveryHistory}
      />

      {isCreatePlaylistOpen && (
        <CreatePlaylistModal
          trackIds={Array.from(selectedTrackIds)}
          onClose={handleCloseCreatePlaylist}
          onCreated={handlePlaylistCreated}
        />
      )}
    </section>
  );
}

export default DiscoverPage;