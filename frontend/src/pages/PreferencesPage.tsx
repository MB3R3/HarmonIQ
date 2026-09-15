import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  ERA_OPTIONS,
  GENRE_OPTIONS,
  MOOD_OPTIONS,
  STYLE_OPTIONS,
} from "../lib/discoveryOptions";
import {
  clearPreferences,
  getPreferences,
  updatePreferences,
} from "../services/preferences";
import type { UserPreferences } from "../types/preferences";

const FREQUENCY_OPTIONS: { value: string; label: string }[] = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "on_demand", label: "On demand" },
];

function sameStringList(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false;
  const sortedA = [...a].sort();
  const sortedB = [...b].sort();
  return sortedA.every((value, index) => value === sortedB[index]);
}

function preferencesEqual(
  a: UserPreferences,
  b: UserPreferences
): boolean {
  return (
    sameStringList(a.favorite_genres, b.favorite_genres) &&
    sameStringList(a.preferred_eras, b.preferred_eras) &&
    a.default_mood === b.default_mood &&
    a.discovery_style === b.discovery_style &&
    a.recommendation_frequency === b.recommendation_frequency
  );
}

function toggleInList(list: string[], value: string): string[] {
  return list.includes(value)
    ? list.filter((item) => item !== value)
    : [...list, value];
}

type Option = {
  value: string;
  label: string;
};

type PillGroupProps = {
  options: Option[];
  selectedValues: string[];
  onToggle: (value: string) => void;
};

function PillGroup({
  options,
  selectedValues,
  onToggle,
}: PillGroupProps) {
  return (
    <div className="preferences__options">
      {options.map((option) => {
        const isSelected = selectedValues.includes(option.value);
        return (
          <button
            key={option.value}
            type="button"
            className={`pill pill--compact${isSelected ? " pill--selected" : ""}`}
            aria-pressed={isSelected}
            onClick={() => onToggle(option.value)}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

function PreferencesPage() {
  const [preferences, setPreferences] =
    useState<UserPreferences | null>(null);
  const [draft, setDraft] = useState<UserPreferences | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const saveSuccessTimer = useRef<ReturnType<typeof setTimeout> | null>(
    null
  );

  const [isClearConfirmOpen, setIsClearConfirmOpen] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [clearError, setClearError] = useState<string | null>(null);
  const [clearSuccess, setClearSuccess] = useState(false);

  const clearDialogRef = useRef<HTMLDivElement>(null);
  const isClearingRef = useRef(false);

  useEffect(() => {
    if (!isClearConfirmOpen) return;

    const previouslyFocused = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        if (!isClearingRef.current) setIsClearConfirmOpen(false);
        return;
      }
      if (event.key !== "Tab") return;
      const root = clearDialogRef.current;
      if (!root) return;
      const focusable = Array.from(
        root.querySelectorAll<HTMLElement>(
          "button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [href]"
        )
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
    const initialFocus =
      clearDialogRef.current?.querySelector<HTMLElement>("button");
    initialFocus?.focus();

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [isClearConfirmOpen]);

  useEffect(() => {
    getPreferences()
      .then((data) => {
        setPreferences(data);
        setDraft(data);
      })
      .catch(() => setLoadError("Couldn't load your preferences."))
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    return () => {
      if (saveSuccessTimer.current) clearTimeout(saveSuccessTimer.current);
    };
  }, []);

  const isDirty = useMemo(() => {
    if (!preferences || !draft) return false;
    return !preferencesEqual(preferences, draft);
  }, [preferences, draft]);

  const handleRetry = () => {
    setIsLoading(true);
    setLoadError(null);
    getPreferences()
      .then((data) => {
        setPreferences(data);
        setDraft(data);
      })
      .catch(() => setLoadError("Couldn't load your preferences."))
      .finally(() => setIsLoading(false));
  };

  const toggleGenre = useCallback((value: string) => {
    setDraft((prev) =>
      prev
        ? {
            ...prev,
            favorite_genres: toggleInList(
              prev.favorite_genres,
              value
            ),
          }
        : prev
    );
  }, []);

  const toggleEra = useCallback((value: string) => {
    setDraft((prev) =>
      prev
        ? {
            ...prev,
            preferred_eras: toggleInList(
              prev.preferred_eras,
              value
            ),
          }
        : prev
    );
  }, []);

  const toggleMood = useCallback((value: string) => {
    setDraft((prev) =>
      prev
        ? {
            ...prev,
            default_mood:
              prev.default_mood === value ? "" : value,
          }
        : prev
    );
  }, []);

  const setStyle = useCallback((value: string) => {
    setDraft((prev) =>
      prev ? { ...prev, discovery_style: value } : prev
    );
  }, []);

  const setFrequency = useCallback((value: string) => {
    setDraft((prev) =>
      prev ? { ...prev, recommendation_frequency: value } : prev
    );
  }, []);

  const showSaved = () => {
    setSaveSuccess(true);
    if (saveSuccessTimer.current) clearTimeout(saveSuccessTimer.current);
    saveSuccessTimer.current = setTimeout(
      () => setSaveSuccess(false),
      3000
    );
  };

  const handleSave = async () => {
    if (!draft) return;
    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      const saved = await updatePreferences(draft);
      setPreferences(saved);
      setDraft(saved);
      showSaved();
    } catch {
      setSaveError(
        "Couldn't save your preferences. Please try again."
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearConfirm = async () => {
    isClearingRef.current = true;
    setIsClearing(true);
    setClearError(null);
    setClearSuccess(false);
    try {
      const defaults = await clearPreferences();
      setPreferences(defaults);
      setDraft(defaults);
      setClearSuccess(true);
      setIsClearConfirmOpen(false);
    } catch {
      setClearError(
        "Couldn't clear your preferences. Please try again."
      );
    } finally {
      isClearingRef.current = false;
      setIsClearing(false);
    }
  };

  const pageHeader = (
    <header className="preferences__header">
      <p className="eyebrow">Preferences</p>
      <h1 className="preferences__title">Preferences</h1>
      <p className="preferences__subtitle">
        Control the sound HarmonIQ starts with.
      </p>
    </header>
  );

  if (isLoading) {
    return (
      <section className="preferences">
        {pageHeader}
        <div
          className="preferences__status"
          aria-label="Loading your preferences"
        >
          <div className="loading-eq" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
          </div>
        </div>
      </section>
    );
  }

  if (loadError) {
    return (
      <section className="preferences">
        {pageHeader}
        <div className="preferences__error" role="alert">
          <p>{loadError}</p>
          <button
            type="button"
            className="button button--secondary"
            onClick={handleRetry}
          >
            Try again
          </button>
        </div>
      </section>
    );
  }

  if (!draft) return null;

  return (
    <section className="preferences">
      {pageHeader}

      <form
        className="preferences__form"
        onSubmit={(event) => {
          event.preventDefault();
          handleSave();
        }}
      >
        <section className="preferences__section">
          <h2 className="preferences__section-title">
            Favorite genres
          </h2>
          <p className="preferences__section-copy">
            Pick the genres you want HarmonIQ to lean on.
          </p>
          <PillGroup
            options={GENRE_OPTIONS}
            selectedValues={draft.favorite_genres}
            onToggle={toggleGenre}
          />
        </section>

        <section className="preferences__section">
          <h2 className="preferences__section-title">
            Preferred eras
          </h2>
          <p className="preferences__section-copy">
            Select the time periods you love most.
          </p>
          <PillGroup
            options={ERA_OPTIONS}
            selectedValues={draft.preferred_eras}
            onToggle={toggleEra}
          />
        </section>

        <section className="preferences__section">
          <h2 className="preferences__section-title">
            Default mood
          </h2>
          <p className="preferences__section-copy">
            Choose one starting mood for new discoveries.
          </p>
          <PillGroup
            options={MOOD_OPTIONS}
            selectedValues={
              draft.default_mood ? [draft.default_mood] : []
            }
            onToggle={toggleMood}
          />
        </section>

        <section className="preferences__section">
          <h2 className="preferences__section-title">
            Discovery style
          </h2>
          <p className="preferences__section-copy">
            How far should HarmonIQ explore?
          </p>
          <div className="style-selector">
            {STYLE_OPTIONS.map((option) => {
              const isSelected =
                draft.discovery_style === option.value;
              return (
                <button
                  key={option.value}
                  type="button"
                  className={`style-option${isSelected ? " style-option--selected" : ""}`}
                  aria-pressed={isSelected}
                  onClick={() => setStyle(option.value)}
                >
                  <span className="style-option__label">
                    {option.label}
                  </span>
                  <span className="style-option__hint">
                    {option.hint}
                  </span>
                </button>
              );
            })}
          </div>
        </section>

        <section className="preferences__section">
          <h2 className="preferences__section-title">
            Recommendation frequency
          </h2>
          <p className="preferences__section-copy">
            How often should HarmonIQ suggest new discoveries?
          </p>
          <PillGroup
            options={FREQUENCY_OPTIONS}
            selectedValues={[draft.recommendation_frequency]}
            onToggle={setFrequency}
          />
        </section>

        <div className="preferences__footer">
          <div className="preferences__footer-status">
            {saveError && (
              <p
                className="preferences__notice preferences__notice--error"
                role="alert"
              >
                {saveError}
              </p>
            )}
            {saveSuccess ? (
              <p
                className="preferences__notice preferences__notice--success"
                role="status"
              >
                Preferences saved.
              </p>
            ) : (
              isDirty && (
                <p className="preferences__hint">
                  You have unsaved changes.
                </p>
              )
            )}
          </div>

          <button
            type="submit"
            className="button button--primary button--large"
            disabled={!isDirty || isSaving}
          >
            {isSaving ? "Saving…" : "Save preferences"}
          </button>
        </div>
      </form>

      <section className="preferences__reset">
        <div className="preferences__reset-copy">
          <h2 className="preferences__reset-title">Reset preferences</h2>
          <p className="preferences__reset-text">
            Clear your saved preferences and return to the default discovery
            settings.
          </p>
          {clearError && (
            <p
              className="preferences__notice preferences__notice--error"
              role="alert"
            >
              {clearError}
            </p>
          )}
          {clearSuccess && (
            <p
              className="preferences__notice preferences__notice--success"
              role="status"
            >
              Preferences cleared. Defaults restored.
            </p>
          )}
        </div>
        <button
          type="button"
          className="button button--secondary preferences__reset-action"
          onClick={() => {
            setClearError(null);
            setIsClearConfirmOpen(true);
          }}
        >
          Clear preferences
        </button>
      </section>

      {isClearConfirmOpen && (
        <div
          className="modal-backdrop"
          onClick={(event) => {
            if (event.target === event.currentTarget && !isClearing) {
              setIsClearConfirmOpen(false);
            }
          }}
        >
          <div
            ref={clearDialogRef}
            className="modal modal--confirm"
            role="dialog"
            aria-modal="true"
            aria-labelledby="clear-preferences-title"
            aria-describedby="clear-preferences-copy"
          >
            <div className="modal__header">
              <h2 id="clear-preferences-title" className="modal__title">
                Clear your saved preferences?
              </h2>
              <button
                type="button"
                className="modal__close"
                aria-label="Close clear preferences dialog"
                onClick={() => setIsClearConfirmOpen(false)}
                disabled={isClearing}
              >
                ×
              </button>
            </div>

            <div className="modal__body">
              <p id="clear-preferences-copy" className="modal__confirm-copy">
                This will remove your saved discovery defaults. Your account,
                Spotify connection and saved tracks will not be affected.
              </p>

              <div className="modal__actions">
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={() => setIsClearConfirmOpen(false)}
                  disabled={isClearing}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="button button--danger"
                  onClick={handleClearConfirm}
                  disabled={isClearing}
                >
                  {isClearing ? "Clearing…" : "Clear preferences"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default PreferencesPage;