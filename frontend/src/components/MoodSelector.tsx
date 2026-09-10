import type { Mood } from "../types/discovery";
import { MOOD_OPTIONS } from "../lib/discoveryOptions";

type MoodSelectorProps = {
  selected: Mood | null;
  onChange: (mood: Mood | null) => void;
};

const ORBIT_ANGLE = 60;

function MoodSelector({ selected, onChange }: MoodSelectorProps) {
  const centerLabel =
    MOOD_OPTIONS.find((mood) => mood.value === selected)?.label ?? "Mood";

  return (
    <fieldset className="selector selector--wide">
      <legend className="selector__label sr-only">Mood</legend>

      <div className="mood-orbit">
        <span className="mood-orbit__center" aria-hidden="true">
          {centerLabel}
        </span>

        {MOOD_OPTIONS.map((mood, index) => {
          const isSelected = selected === mood.value;
          return (
            <span
              key={mood.value}
              className="mood-orbit__slot"
              style={{
                transform: `rotate(${index * ORBIT_ANGLE}deg) translate(var(--orbit-radius)) rotate(${-index * ORBIT_ANGLE}deg)`,
              }}
            >
              <button
                type="button"
                className={`pill mood-orbit__button${isSelected ? " pill--selected" : ""}`}
                aria-pressed={isSelected}
                onClick={() =>
                  onChange(isSelected ? null : mood.value)
                }
              >
                {mood.label}
              </button>
            </span>
          );
        })}
      </div>
    </fieldset>
  );
}

export default MoodSelector;